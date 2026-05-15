"""Output Contract: 智能体最终输出结构

本模块只负责定义"一个运维智能体最后应该交付什么结构化信息"。
不包含:
- Incident 生成逻辑
- 文本生成逻辑
- 平台适配逻辑
"""
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class OutputStatus(str, Enum):
    """智能体本次输出状态"""
    SUCCESS = "success"
    PARTIAL = "partial"
    CLARIFICATION_NEEDED = "clarification_needed"
    FAILED = "failed"


class Confidence(str, Enum):
    """当前结论置信度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Evidence(BaseModel):
    """支撑当前判断的证据项"""
    type: Literal["log", "metric", "event", "health_check", "container_status"]
    source: str
    content: str


class AgentOutput(BaseModel):
    """智能体标准输出契约
    
    设计原则:
    - 面向运维决策,而不是面向自由聊天
    - 必须允许"不确定"和"信息不足"
    - 必须能承载证据和建议动作
    """
    status: OutputStatus
    summary: str
    current_situation: str = ""
    impact_scope: str = ""
    suspected_causes: list[str] = Field(default_factory=list)
    investigation_steps: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.LOW
    missing_information: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    related_incident_id: Optional[str] = None
