"""
决策大模型客户端

调用 GLM-4.7 进行任务分析和决策
"""

import json
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

from openai import OpenAI

from AutoGLM_GUI.logger import logger
from .protocols import (
    DecisionModelConfig,
    DECISION_SYSTEM_PROMPT,
    ModelStage,
)


@dataclass
class TaskPlan:
    """任务计划"""
    summary: str
    steps: list[str]
    estimated_actions: int
    raw_response: str = ""

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "steps": self.steps,
            "estimated_actions": self.estimated_actions,
        }


@dataclass
class Decision:
    """决策结果"""
    action: str           # tap, swipe, type, scroll, back, home, launch
    target: str           # 目标描述
    reasoning: str        # 决策理由
    content: Optional[str] = None  # 输入内容(type操作时使用)
    finished: bool = False
    raw_response: str = ""

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "target": self.target,
            "reasoning": self.reasoning,
            "content": self.content,
            "finished": self.finished,
        }


class DecisionModel:
    """
    决策大模型 - 负责任务分析和决策制定

    使用 GLM-4.7 或其他高智商模型，通过文本理解屏幕状态，
    制定操作决策并指导小模型执行。
    """

    def __init__(self, config: DecisionModelConfig):
        self.config = config
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )
        self.model_name = config.model_name
        self.conversation_history: list[dict] = []

        logger.info(f"决策大模型初始化: {config.model_name}")

    def _stream_completion(
        self,
        messages: list[dict],
        on_thinking: Optional[Callable[[str], None]] = None,
        on_answer: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        流式调用大模型

        GLM-4.7 支持 reasoning_content 字段，可以分离思考过程和最终答案
        """
        logger.debug(f"调用决策大模型，消息数: {len(messages)}")

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stream=True,
            )

            full_reasoning = ""
            full_answer = ""
            done_reasoning = False

            for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta

                    # 处理思考过程 (reasoning_content)
                    reasoning_chunk = getattr(delta, 'reasoning_content', None) or ""
                    if reasoning_chunk:
                        full_reasoning += reasoning_chunk
                        if on_thinking:
                            on_thinking(reasoning_chunk)

                    # 处理最终答案 (content)
                    answer_chunk = delta.content or ""
                    if answer_chunk:
                        if not done_reasoning and full_reasoning:
                            done_reasoning = True
                            logger.debug("思考阶段结束，开始输出答案")

                        full_answer += answer_chunk
                        if on_answer:
                            on_answer(answer_chunk)

            # 如果模型不支持 reasoning_content，整个响应都在 content 中
            if not full_answer and full_reasoning:
                full_answer = full_reasoning
                full_reasoning = ""

            logger.debug(f"大模型响应完成，答案长度: {len(full_answer)}")
            return full_answer

        except Exception as e:
            logger.error(f"决策大模型调用失败: {e}")
            raise

    def analyze_task(
        self,
        task: str,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_answer: Optional[Callable[[str], None]] = None,
    ) -> TaskPlan:
        """
        分析用户任务，制定执行计划

        Args:
            task: 用户任务描述
            on_thinking: 思考过程回调
            on_answer: 答案输出回调

        Returns:
            TaskPlan: 任务执行计划
        """
        logger.info(f"分析任务: {task[:50]}...")

        # 构建消息
        messages = [
            {"role": "system", "content": DECISION_SYSTEM_PROMPT},
            {"role": "user", "content": f"""请分析以下任务，并制定执行计划：

任务: {task}

请以JSON格式返回任务计划。"""}
        ]

        # 调用模型
        response = self._stream_completion(messages, on_thinking, on_answer)

        # 解析响应
        try:
            # 尝试提取JSON
            plan_data = self._extract_json(response)

            if plan_data.get("type") == "plan":
                plan = TaskPlan(
                    summary=plan_data.get("summary", task),
                    steps=plan_data.get("steps", []),
                    estimated_actions=plan_data.get("estimated_actions", 5),
                    raw_response=response,
                )
            else:
                # 回退处理
                plan = TaskPlan(
                    summary=task,
                    steps=[task],
                    estimated_actions=5,
                    raw_response=response,
                )
        except Exception as e:
            logger.warning(f"解析任务计划失败: {e}")
            plan = TaskPlan(
                summary=task,
                steps=[task],
                estimated_actions=5,
                raw_response=response,
            )

        # 初始化对话历史
        self.conversation_history = [
            {"role": "system", "content": DECISION_SYSTEM_PROMPT},
            {"role": "user", "content": f"任务: {task}"},
            {"role": "assistant", "content": response},
        ]

        logger.info(f"任务计划: {plan.summary}, 预计 {plan.estimated_actions} 步")
        return plan

    def make_decision(
        self,
        screen_description: str,
        task_context: Optional[str] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_answer: Optional[Callable[[str], None]] = None,
    ) -> Decision:
        """
        根据屏幕描述做出决策

        Args:
            screen_description: 小模型提供的屏幕描述
            task_context: 额外的任务上下文
            on_thinking: 思考过程回调
            on_answer: 答案输出回调

        Returns:
            Decision: 决策结果
        """
        logger.info("正在做决策...")

        # 构建消息
        user_message = f"""当前屏幕状态：
{screen_description}

{f"补充信息: {task_context}" if task_context else ""}

请根据屏幕状态，决定下一步操作。以JSON格式返回决策。"""

        self.conversation_history.append({"role": "user", "content": user_message})

        # 调用模型
        response = self._stream_completion(
            self.conversation_history,
            on_thinking,
            on_answer,
        )

        # 保存助手响应
        self.conversation_history.append({"role": "assistant", "content": response})

        # 解析决策
        try:
            decision_data = self._extract_json(response)

            if decision_data.get("type") == "finish":
                decision = Decision(
                    action="finish",
                    target="",
                    reasoning=decision_data.get("message", "任务完成"),
                    finished=True,
                    raw_response=response,
                )
            elif decision_data.get("type") == "decision":
                decision = Decision(
                    action=decision_data.get("action", "tap"),
                    target=decision_data.get("target", ""),
                    reasoning=decision_data.get("reasoning", ""),
                    content=decision_data.get("content"),
                    finished=decision_data.get("finished", False),
                    raw_response=response,
                )
            else:
                # 尝试直接解析为决策
                decision = Decision(
                    action=decision_data.get("action", "tap"),
                    target=decision_data.get("target", "未知目标"),
                    reasoning=decision_data.get("reasoning", response),
                    content=decision_data.get("content"),
                    finished=decision_data.get("finished", False),
                    raw_response=response,
                )
        except Exception as e:
            logger.warning(f"解析决策失败: {e}")
            # 回退：将整个响应作为reasoning
            decision = Decision(
                action="unknown",
                target="",
                reasoning=response,
                raw_response=response,
            )

        logger.info(f"决策: {decision.action} -> {decision.target}")
        return decision

    def generate_content(
        self,
        content_type: str,
        context: str,
        requirements: Optional[str] = None,
        on_thinking: Optional[Callable[[str], None]] = None,
        on_answer: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        生成需要输入的内容（帖子、回复、消息等）

        Args:
            content_type: 内容类型（post, reply, message等）
            context: 上下文信息
            requirements: 具体要求
            on_thinking: 思考过程回调
            on_answer: 答案输出回调

        Returns:
            str: 生成的内容
        """
        logger.info(f"生成内容: {content_type}")

        prompt = f"""请为以下场景生成内容：

内容类型: {content_type}
上下文: {context}
{f"具体要求: {requirements}" if requirements else ""}

请直接返回生成的内容文本，不需要JSON格式，不需要额外解释。"""

        messages = [
            {"role": "system", "content": "你是一个内容创作助手，擅长生成各类社交媒体内容。请直接返回内容，不要添加任何解释或格式标记。"},
            {"role": "user", "content": prompt},
        ]

        content = self._stream_completion(messages, on_thinking, on_answer)

        # 清理内容（移除可能的引号和格式标记）
        content = content.strip()
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1]
        if content.startswith("```") and content.endswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        logger.info(f"生成内容完成，长度: {len(content)}")
        return content

    def _extract_json(self, text: str) -> dict:
        """从文本中提取JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 代码块
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取 { ... }
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法从文本中提取JSON: {text[:100]}...")

    def reset(self):
        """重置对话历史"""
        self.conversation_history = []
        logger.info("决策大模型对话历史已重置")
