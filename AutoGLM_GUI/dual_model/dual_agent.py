"""
双模型协调器

协调大模型(决策)和小模型(执行)的协作
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from queue import Queue

from phone_agent.model.client import ModelConfig

from AutoGLM_GUI.logger import logger
from .decision_model import DecisionModel, Decision, TaskPlan
from .vision_model import VisionModel, ScreenDescription, ExecutionResult
from .protocols import (
    DecisionModelConfig,
    DualModelConfig,
    DualModelState,
    DualModelEvent,
    DualModelEventType,
    ModelRole,
    ModelStage,
)


@dataclass
class DualModelCallbacks:
    """双模型回调接口"""

    # 大模型回调
    on_decision_start: Optional[Callable[[], None]] = None
    on_decision_thinking: Optional[Callable[[str], None]] = None
    on_decision_result: Optional[Callable[[Decision], None]] = None
    on_task_plan: Optional[Callable[[TaskPlan], None]] = None
    on_content_generation: Optional[Callable[[str, str], None]] = None  # (content, purpose)

    # 小模型回调
    on_vision_start: Optional[Callable[[], None]] = None
    on_vision_recognition: Optional[Callable[[ScreenDescription], None]] = None
    on_action_start: Optional[Callable[[dict], None]] = None
    on_action_result: Optional[Callable[[ExecutionResult], None]] = None

    # 整体回调
    on_step_complete: Optional[Callable[[int, bool], None]] = None  # (step, success)
    on_task_complete: Optional[Callable[[bool, str], None]] = None  # (success, message)
    on_error: Optional[Callable[[str], None]] = None


@dataclass
class StepResult:
    """单步执行结果"""
    step: int
    success: bool
    finished: bool
    decision: Optional[Decision] = None
    screen_desc: Optional[ScreenDescription] = None
    execution: Optional[ExecutionResult] = None
    error: Optional[str] = None


class DualModelAgent:
    """
    双模型协调器

    协调大模型(GLM-4.7)和小模型(autoglm-phone)的协作：
    1. 大模型分析任务，制定计划
    2. 小模型识别屏幕，描述内容
    3. 大模型根据屏幕描述做决策
    4. 小模型执行决策
    5. 循环直到任务完成

    Usage:
        agent = DualModelAgent(decision_config, vision_config, device_id)
        result = await agent.run("打开微信发送消息")
    """

    def __init__(
        self,
        decision_config: DecisionModelConfig,
        vision_config: ModelConfig,
        device_id: str,
        max_steps: int = 50,
        callbacks: Optional[DualModelCallbacks] = None,
    ):
        self.decision_model = DecisionModel(decision_config)
        self.vision_model = VisionModel(vision_config, device_id)
        self.device_id = device_id
        self.max_steps = max_steps
        self.callbacks = callbacks or DualModelCallbacks()

        # 状态
        self.state = DualModelState()
        self.current_task: str = ""
        self.task_plan: Optional[TaskPlan] = None
        self.step_count: int = 0
        self.stop_event = threading.Event()

        # 事件队列(用于SSE)
        self.event_queue: Queue[DualModelEvent] = Queue()

        logger.info(f"双模型协调器初始化完成, 设备: {device_id}")

    def _emit_event(self, event_type: DualModelEventType, data: dict, model: Optional[ModelRole] = None):
        """发送事件到队列"""
        event = DualModelEvent(
            type=event_type,
            data=data,
            model=model,
            step=self.step_count,
            timestamp=time.time(),
        )
        self.event_queue.put(event)

    def run(self, task: str) -> dict:
        """
        执行任务(同步版本)

        Args:
            task: 用户任务描述

        Returns:
            执行结果
        """
        self.current_task = task
        self.step_count = 0
        self.stop_event.clear()

        logger.info(f"开始执行任务: {task[:50]}...")

        try:
            # 1. 大模型分析任务
            self._update_state(decision_stage=ModelStage.ANALYZING, decision_active=True)
            self._emit_event(
                DualModelEventType.DECISION_START,
                {"stage": "analyzing", "task": task},
                ModelRole.DECISION,
            )

            if self.callbacks.on_decision_start:
                self.callbacks.on_decision_start()

            # 分析任务，获取计划
            self.task_plan = self.decision_model.analyze_task(
                task,
                on_thinking=self._on_decision_thinking,
                on_answer=self._on_decision_answer,
            )

            self._emit_event(
                DualModelEventType.TASK_PLAN,
                {"plan": self.task_plan.to_dict()},
                ModelRole.DECISION,
            )

            if self.callbacks.on_task_plan:
                self.callbacks.on_task_plan(self.task_plan)

            self.state.task_plan = self.task_plan.steps
            self.state.total_steps = self.task_plan.estimated_actions

            # 2. 执行循环
            finished = False
            last_message = ""

            while not finished and self.step_count < self.max_steps:
                if self.stop_event.is_set():
                    logger.info("任务被中断")
                    return {
                        "success": False,
                        "message": "任务被用户中断",
                        "steps": self.step_count,
                    }

                self.step_count += 1
                logger.info(f"执行步骤 {self.step_count}/{self.max_steps}")

                step_result = self._execute_step()

                if step_result.error:
                    logger.error(f"步骤执行失败: {step_result.error}")
                    if self.callbacks.on_error:
                        self.callbacks.on_error(step_result.error)
                    # 继续尝试下一步
                    continue

                if step_result.finished:
                    finished = True
                    last_message = step_result.decision.reasoning if step_result.decision else "任务完成"

                if self.callbacks.on_step_complete:
                    self.callbacks.on_step_complete(self.step_count, step_result.success)

                # 步骤间延迟
                time.sleep(0.5)

            # 3. 完成
            success = finished
            message = last_message if finished else f"达到最大步数限制({self.max_steps})"

            self._emit_event(
                DualModelEventType.TASK_COMPLETE,
                {"success": success, "message": message, "steps": self.step_count},
            )

            if self.callbacks.on_task_complete:
                self.callbacks.on_task_complete(success, message)

            logger.info(f"任务完成: success={success}, steps={self.step_count}")

            return {
                "success": success,
                "message": message,
                "steps": self.step_count,
            }

        except Exception as e:
            logger.exception(f"任务执行异常: {e}")
            self._emit_event(
                DualModelEventType.ERROR,
                {"message": str(e)},
            )
            return {
                "success": False,
                "message": f"执行异常: {e}",
                "steps": self.step_count,
            }

    def _execute_step(self) -> StepResult:
        """执行单步操作"""
        try:
            # 2.1 小模型识别屏幕
            self._update_state(
                vision_stage=ModelStage.RECOGNIZING,
                vision_active=True,
                decision_active=False,
            )
            self._emit_event(
                DualModelEventType.VISION_START,
                {"stage": "recognizing"},
                ModelRole.VISION,
            )

            if self.callbacks.on_vision_start:
                self.callbacks.on_vision_start()

            # 截图并识别
            screenshot_base64, width, height = self.vision_model.capture_screenshot()
            screen_desc = self.vision_model.describe_screen(screenshot_base64)

            self._update_state(
                vision_description=screen_desc.description[:200],
                vision_stage=ModelStage.IDLE,
            )
            self._emit_event(
                DualModelEventType.VISION_RECOGNITION,
                {
                    "description": screen_desc.description,
                    "current_app": screen_desc.current_app,
                    "elements": screen_desc.elements,
                },
                ModelRole.VISION,
            )

            if self.callbacks.on_vision_recognition:
                self.callbacks.on_vision_recognition(screen_desc)

            # 2.2 大模型决策
            self._update_state(
                decision_stage=ModelStage.DECIDING,
                decision_active=True,
                vision_active=False,
            )
            self._emit_event(
                DualModelEventType.DECISION_START,
                {"stage": "deciding"},
                ModelRole.DECISION,
            )

            if self.callbacks.on_decision_start:
                self.callbacks.on_decision_start()

            # 调用决策模型
            decision = self.decision_model.make_decision(
                screen_description=screen_desc.description,
                task_context=f"当前应用: {screen_desc.current_app}",
                on_thinking=self._on_decision_thinking,
                on_answer=self._on_decision_answer,
            )

            self._update_state(
                decision_result=f"{decision.action}: {decision.target}",
                decision_thinking=decision.reasoning,
                decision_stage=ModelStage.IDLE,
            )
            self._emit_event(
                DualModelEventType.DECISION_RESULT,
                {
                    "decision": decision.to_dict(),
                    "reasoning": decision.reasoning,
                },
                ModelRole.DECISION,
            )

            if self.callbacks.on_decision_result:
                self.callbacks.on_decision_result(decision)

            # 检查是否完成
            if decision.finished:
                return StepResult(
                    step=self.step_count,
                    success=True,
                    finished=True,
                    decision=decision,
                    screen_desc=screen_desc,
                )

            # 2.3 小模型执行
            self._update_state(
                vision_stage=ModelStage.EXECUTING,
                vision_active=True,
                decision_active=False,
            )

            action_dict = {
                "action": decision.action,
                "target": decision.target,
                "content": decision.content,
            }

            self._emit_event(
                DualModelEventType.ACTION_START,
                {"action": action_dict},
                ModelRole.VISION,
            )

            if self.callbacks.on_action_start:
                self.callbacks.on_action_start(action_dict)

            execution = self.vision_model.execute_decision(
                decision=action_dict,
                screenshot_base64=screenshot_base64,
            )

            self._update_state(
                vision_action=f"{execution.action_type}: {execution.target}",
                vision_stage=ModelStage.IDLE,
                vision_active=False,
            )
            self._emit_event(
                DualModelEventType.ACTION_RESULT,
                {
                    "success": execution.success,
                    "action_type": execution.action_type,
                    "target": execution.target,
                    "position": execution.position,
                    "message": execution.message,
                },
                ModelRole.VISION,
            )

            if self.callbacks.on_action_result:
                self.callbacks.on_action_result(execution)

            # 步骤完成事件
            self._emit_event(
                DualModelEventType.STEP_COMPLETE,
                {
                    "step": self.step_count,
                    "success": execution.success,
                    "finished": execution.finished,
                },
            )

            return StepResult(
                step=self.step_count,
                success=execution.success,
                finished=execution.finished,
                decision=decision,
                screen_desc=screen_desc,
                execution=execution,
            )

        except Exception as e:
            logger.exception(f"步骤执行异常: {e}")
            return StepResult(
                step=self.step_count,
                success=False,
                finished=False,
                error=str(e),
            )

    def _update_state(self, **kwargs):
        """更新状态"""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self.state.current_step = self.step_count

    def _on_decision_thinking(self, chunk: str):
        """决策思考回调"""
        self._emit_event(
            DualModelEventType.DECISION_THINKING,
            {"chunk": chunk},
            ModelRole.DECISION,
        )
        if self.callbacks.on_decision_thinking:
            self.callbacks.on_decision_thinking(chunk)

    def _on_decision_answer(self, chunk: str):
        """决策答案回调"""
        pass  # 答案通过 DECISION_RESULT 事件发送

    def abort(self):
        """中止任务"""
        logger.info("中止任务")
        self.stop_event.set()

    def reset(self):
        """重置状态"""
        self.current_task = ""
        self.task_plan = None
        self.step_count = 0
        self.stop_event.clear()
        self.state = DualModelState()
        self.decision_model.reset()

        # 清空事件队列
        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
            except Exception:
                break

        logger.info("双模型协调器已重置")

    def get_state(self) -> dict:
        """获取当前状态"""
        return self.state.to_dict()

    def get_events(self, timeout: float = 0.1) -> list[DualModelEvent]:
        """获取待处理的事件"""
        events = []
        while True:
            try:
                event = self.event_queue.get(timeout=timeout)
                events.append(event)
            except Exception:
                break
        return events
