"""
通信协议定义

定义大小模型之间的通信协议和数据结构
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel


class DecisionModelConfig(BaseModel):
    """决策大模型配置"""
    base_url: str = "https://api-inference.modelscope.cn/v1"
    api_key: str = ""
    model_name: str = "ZhipuAI/GLM-4.7"
    max_tokens: int = 4096
    temperature: float = 0.7


class DualModelConfig(BaseModel):
    """双模型协作配置"""
    enabled: bool = False
    decision_model: DecisionModelConfig = DecisionModelConfig()


class ModelRole(str, Enum):
    """模型角色"""
    DECISION = "decision"  # 决策大模型
    VISION = "vision"      # 视觉小模型


class ModelStage(str, Enum):
    """模型当前阶段"""
    IDLE = "idle"
    ANALYZING = "analyzing"       # 分析任务
    DECIDING = "deciding"         # 做决策
    GENERATING = "generating"     # 生成内容
    CAPTURING = "capturing"       # 截图
    RECOGNIZING = "recognizing"   # 识别屏幕
    EXECUTING = "executing"       # 执行动作
    WAITING = "waiting"           # 等待


@dataclass
class DualModelState:
    """双模型状态"""
    # 大模型状态
    decision_active: bool = False
    decision_stage: ModelStage = ModelStage.IDLE
    decision_thinking: str = ""
    decision_result: str = ""

    # 小模型状态
    vision_active: bool = False
    vision_stage: ModelStage = ModelStage.IDLE
    vision_description: str = ""
    vision_action: str = ""

    # 整体状态
    current_step: int = 0
    total_steps: int = 0
    task_plan: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "decision": {
                "active": self.decision_active,
                "stage": self.decision_stage.value,
                "thinking": self.decision_thinking,
                "result": self.decision_result,
            },
            "vision": {
                "active": self.vision_active,
                "stage": self.vision_stage.value,
                "description": self.vision_description,
                "action": self.vision_action,
            },
            "progress": {
                "current_step": self.current_step,
                "total_steps": self.total_steps,
                "task_plan": self.task_plan,
            }
        }


class DualModelEventType(str, Enum):
    """双模型事件类型"""
    # 大模型事件
    DECISION_START = "decision_start"
    DECISION_THINKING = "decision_thinking"
    DECISION_RESULT = "decision_result"
    CONTENT_GENERATION = "content_generation"
    TASK_PLAN = "task_plan"

    # 小模型事件
    VISION_START = "vision_start"
    VISION_RECOGNITION = "vision_recognition"
    ACTION_START = "action_start"
    ACTION_RESULT = "action_result"

    # 整体事件
    STEP_COMPLETE = "step_complete"
    TASK_COMPLETE = "task_complete"
    ERROR = "error"
    ABORTED = "aborted"


@dataclass
class DualModelEvent:
    """双模型事件"""
    type: DualModelEventType
    data: dict
    model: Optional[ModelRole] = None
    step: int = 0
    timestamp: float = 0.0

    def to_sse(self) -> str:
        """转换为SSE格式"""
        import json
        import time

        event_data = {
            "type": self.type.value,
            "model": self.model.value if self.model else None,
            "step": self.step,
            "timestamp": self.timestamp or time.time(),
            **self.data
        }
        return f"event: {self.type.value}\ndata: {json.dumps(event_data, ensure_ascii=False)}\n\n"


# 系统提示词
DECISION_SYSTEM_PROMPT = """你是一个智能手机操作决策专家。你的任务是根据用户需求和当前屏幕状态，做出精确的操作决策。

## 你的能力
- 分析用户任务，制定执行计划
- 根据屏幕描述，决定下一步操作
- 生成需要输入的内容（如帖子、回复、消息等）

## 响应格式
你必须以JSON格式响应，包含以下字段：

### 任务分析响应
```json
{
    "type": "plan",
    "summary": "任务简述",
    "steps": ["步骤1", "步骤2", ...],
    "estimated_actions": 5
}
```

### 决策响应
```json
{
    "type": "decision",
    "reasoning": "决策理由",
    "action": "tap|swipe|type|scroll|back|home|launch",
    "target": "目标元素描述",
    "content": "如果是type操作，这里是要输入的内容",
    "finished": false
}
```

### 任务完成响应
```json
{
    "type": "finish",
    "message": "任务完成说明",
    "success": true
}
```

## 注意事项
1. 你看不到屏幕，只能根据小模型提供的屏幕描述来决策
2. 每次只做一个决策，等待小模型执行后再继续
3. 如果屏幕描述不清楚，可以要求重新识别
4. 遇到需要登录、验证码等情况，请求用户介入
"""

VISION_DESCRIBE_PROMPT = """请详细描述当前屏幕内容，包括：

1. 当前所在的应用/页面
2. 屏幕上可见的主要元素（按钮、文本、图标等）
3. 各元素的大致位置（上/中/下，左/中/右）
4. 任何输入框、可点击区域
5. 当前页面的状态（是否有弹窗、是否在加载等）

请用简洁清晰的中文描述，让决策模型能理解当前屏幕状态。
"""
