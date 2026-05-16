"""Observation: 来自单个 provider 的、未经诊断判断的原始观察

设计原则:
- Observation 只表达"看到了什么",不表达"这意味着什么"
- Observation 的字段应尽量贴近原始事实,而不是贴近诊断结论
- 不同来源的 Observation 使用不同子类承载,避免把所有信息塞进 payload dict
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ObservationKind(str, Enum):
    """观察类型: 描述来自什么来源,不描述诊断结论"""

    CONTAINER_STATE = "container_state"
    CONTAINER_LOG = "container_log"
    HTTP_HEALTHCHECK = "http_healthcheck"
    HOST_METRIC = "host_metric"
    PLATFORM_EVENT = "platform_event"


class BaseObservation(BaseModel):
    """所有 observation 的公共字段"""

    observation_id: str
    kind: ObservationKind
    source: str
    collected_at: datetime
    target_ref: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class ContainerStateObservation(BaseObservation):
    """容器状态快照: 尽量保留 Docker 原始值"""

    kind: Literal[ObservationKind.CONTAINER_STATE] = ObservationKind.CONTAINER_STATE
    container_id: str
    container_name: str
    image: str
    status: str
    health: str | None = None
    restart_count: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None


class ContainerLogObservation(BaseObservation):
    """容器日志片段: 保存原始日志行,不在这里做重要性判断"""

    kind: Literal[ObservationKind.CONTAINER_LOG] = ObservationKind.CONTAINER_LOG
    container_name: str
    lines: list[str] = Field(default_factory=list)
    line_range: tuple[int, int] | None = None
    truncation: str | None = None
    log_source_path: str | None = None


class HttpHealthcheckObservation(BaseObservation):
    """HTTP 健康检查结果"""

    kind: Literal[ObservationKind.HTTP_HEALTHCHECK] = ObservationKind.HTTP_HEALTHCHECK
    url: str
    method: str = "GET"
    status_code: int | None = None
    response_time_ms: int | None = None
    error: str | None = None


class HostMetricObservation(BaseObservation):
    """主机或容器层指标观察"""

    kind: Literal[ObservationKind.HOST_METRIC] = ObservationKind.HOST_METRIC
    metric_name: str
    value: float
    unit: str
    window_seconds: int | None = None
    aggregation: str | None = None


class PlatformEventObservation(BaseObservation):
    """平台业务事件观察"""

    kind: Literal[ObservationKind.PLATFORM_EVENT] = ObservationKind.PLATFORM_EVENT
    event_name: str
    payload: dict[str, Any] = Field(default_factory=dict)


Observation = (
    ContainerStateObservation
    | ContainerLogObservation
    | HttpHealthcheckObservation
    | HostMetricObservation
    | PlatformEventObservation
)
