"""Signal: 平台无关的运维线索

本模块只负责定义"什么样的数据算一条标准化的 Signal"。
不包含:
- 数据采集逻辑(归 Provider)
- 平台判断(归 Adapter)
- 聚合分析(归 Agent)
"""
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SignalCategory(str, Enum):
    """Signal 大类: 用于快速分桶和过滤"""
    HEALTH = "health"
    METRICS = "metrics"
    LOGS = "logs"
    EVENTS = "events"


class Severity(str, Enum):
    """Signal 自身严重程度(不代表最终 Incident 级别)"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Signal(BaseModel):
    """标准化的运维信号

    设计原则:
    - Signal 是"线索",不是"结论"
    - 单个 Signal 不应触发处置,需要聚合成 Incident 后再决策
    - 字段保持平台无关,平台差异通过 payload 携带
    """
    signal_id: str
    signal_type: str
    category: SignalCategory
    severity: Severity
    timestamp: datetime
    source: str
    summary: str
    payload: dict[str, Any] = Field(default_factory=dict)
