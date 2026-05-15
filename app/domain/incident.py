"""Incident: 对多个 Signal 的归纳结果

本模块只负责定义"什么样的数据算一个 Incident"。
不包含:
- Signal 聚合逻辑(归 Agent / Incident Engine)
- 平台特定规则(归 Adapter / Mapper)
- 最终对外回答格式(归 Output Contract)
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.domain.signal import Severity


class IncidentStatus(str, Enum):
    """Incident 生命周期状态"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(BaseModel):
    """标准化的问题对象
    
    设计原则:
    - Incident 是"问题表达",不是原始线索
    - Incident 通常由一个或多个 Signal 聚合而来
    - Incident 应该足够稳定,便于后续生成输出、匹配 Runbook
    """
    incident_id: str
    incident_type: str
    title: str
    severity: Severity
    status: IncidentStatus = IncidentStatus.OPEN
    timestamp: datetime
    summary: str
    related_signal_ids: list[str] = Field(default_factory=list)
