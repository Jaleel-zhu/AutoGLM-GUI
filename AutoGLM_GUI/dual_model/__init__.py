"""
双模型协作模块

大模型(GLM-4.7): 负责任务分析、决策制定、内容生成
小模型(autoglm-phone): 负责屏幕识别、动作执行
"""

from .decision_model import DecisionModel, Decision, TaskPlan
from .vision_model import VisionModel, ScreenDescription, ExecutionResult
from .dual_agent import DualModelAgent, DualModelCallbacks
from .protocols import (
    DualModelConfig,
    DecisionModelConfig,
    DualModelState,
    DualModelEvent,
    DualModelEventType,
    ModelRole,
    ModelStage,
    DECISION_SYSTEM_PROMPT,
    VISION_DESCRIBE_PROMPT,
)

__all__ = [
    "DecisionModel",
    "Decision",
    "TaskPlan",
    "VisionModel",
    "ScreenDescription",
    "ExecutionResult",
    "DualModelAgent",
    "DualModelCallbacks",
    "DualModelConfig",
    "DecisionModelConfig",
    "DualModelState",
    "DualModelEvent",
    "DualModelEventType",
    "ModelRole",
    "ModelStage",
    "DECISION_SYSTEM_PROMPT",
    "VISION_DESCRIBE_PROMPT",
]
