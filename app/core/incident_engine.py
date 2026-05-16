"""Incident Engine: 将 Signal 聚合成 Incident

STATUS: FROZEN

职责:
- 只负责把标准化 Signal 归纳为 Incident
- 不负责采集数据
- 不负责生成最终对外回答
- 不负责平台特定适配

说明:
- 这是第一版规则聚合实现,用于验证 Signal -> Incident 主线
- 当前不再作为未来主线继续扩展
- 后续应逐步降级为 fallback / 对照实现
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.domain.incident import Incident, IncidentStatus
from app.domain.signal import Severity, Signal


def build_incidents(signals: list[Signal]) -> list[Incident]:
    """根据一组 Signal 构建 Incident 列表"""
    incidents: list[Incident] = []

    unhealthy_signals = [s for s in signals if s.signal_type == "container_unhealthy"]
    not_running_signals = [s for s in signals if s.signal_type == "container_not_running"]
    restarted_signals = [s for s in signals if s.signal_type == "container_restarted"]

    if unhealthy_signals:
        incidents.append(_build_health_degradation_incident(unhealthy_signals))

    if not_running_signals:
        incidents.append(_build_service_unavailable_incident(not_running_signals))

    if restarted_signals and not unhealthy_signals and not not_running_signals:
        incidents.append(_build_restart_detected_incident(restarted_signals))

    return incidents


def _build_health_degradation_incident(signals: list[Signal]) -> Incident:
    container_names = _extract_container_names(signals)

    return Incident(
        incident_id=_new_incident_id(),
        incident_type="service_health_degradation",
        title="服务健康状态异常",
        severity=Severity.HIGH,
        status=IncidentStatus.OPEN,
        timestamp=datetime.now(),
        summary=f"检测到容器健康检查失败: {', '.join(container_names)}",
        related_signal_ids=[s.signal_id for s in signals],
    )


def _build_service_unavailable_incident(signals: list[Signal]) -> Incident:
    container_names = _extract_container_names(signals)

    return Incident(
        incident_id=_new_incident_id(),
        incident_type="service_unavailable",
        title="服务不可用",
        severity=Severity.HIGH,
        status=IncidentStatus.OPEN,
        timestamp=datetime.now(),
        summary=f"检测到容器未运行: {', '.join(container_names)}",
        related_signal_ids=[s.signal_id for s in signals],
    )


def _build_restart_detected_incident(signals: list[Signal]) -> Incident:
    container_names = _extract_container_names(signals)

    return Incident(
        incident_id=_new_incident_id(),
        incident_type="container_restart_detected",
        title="检测到容器发生重启",
        severity=Severity.MEDIUM,
        status=IncidentStatus.OPEN,
        timestamp=datetime.now(),
        summary=f"检测到容器发生过重启: {', '.join(container_names)}",
        related_signal_ids=[s.signal_id for s in signals],
    )


def _extract_container_names(signals: list[Signal]) -> list[str]:
    names: list[str] = []

    for signal in signals:
        container_name = signal.payload.get("container_name")
        if isinstance(container_name, str) and container_name not in names:
            names.append(container_name)

    return names


def _new_incident_id() -> str:
    return f"inc_{uuid4().hex[:12]}"
