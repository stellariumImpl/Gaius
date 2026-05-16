"""Signal Mapper: 将原始容器快照映射为标准化 Signal

STATUS: FROZEN

说明:
- 这是第一版规则化映射实现,用于打通早期诊断链路
- 当前不再作为未来主线继续扩展
- 后续主线应逐步迁移到 observation-driven 输入组织
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from app.domain.signal import Severity, Signal, SignalCategory


def map_container_snapshots_to_signals(
    snapshots: list[dict[str, Any]],
    platform_id: str = "platform_default",
) -> list[Signal]:
    """将容器快照列表映射成 Signal 列表"""
    signals: list[Signal] = []

    for snapshot in snapshots:
        signals.extend(_map_single_snapshot(snapshot, platform_id=platform_id))

    return signals


def _map_single_snapshot(
    snapshot: dict[str, Any],
    platform_id: str,
) -> list[Signal]:
    """将单个容器快照映射成 0~N 条 Signal"""
    signals: list[Signal] = []

    container_name = snapshot.get("container_name", "unknown")
    status = snapshot.get("status", "unknown")
    health = snapshot.get("health")
    restart_count = snapshot.get("restart_count", 0)

    # 1. 容器不在运行
    if status != "running":
        signals.append(
            Signal(
                signal_id=_new_signal_id(),
                signal_type="container_not_running",
                category=SignalCategory.HEALTH,
                severity=Severity.HIGH,
                timestamp=datetime.now(),
                source="docker_provider",
                summary=f"容器 {container_name} 当前未运行，状态为 {status}",
                payload={
                    "container_name": container_name,
                    "status": status,
                    "restart_count": restart_count,
                },
            )
        )

    # 2. 容器健康检查失败
    if health == "unhealthy":
        signals.append(
            Signal(
                signal_id=_new_signal_id(),
                signal_type="container_unhealthy",
                category=SignalCategory.HEALTH,
                severity=Severity.HIGH,
                timestamp=datetime.now(),
                source="docker_provider",
                summary=f"容器 {container_name} 健康检查失败",
                payload={
                    "container_name": container_name,
                    "status": status,
                    "health": health,
                    "restart_count": restart_count,
                },
            )
        )

    # 3. 容器发生过重启
    if isinstance(restart_count, int) and restart_count > 0:
        signals.append(
            Signal(
                signal_id=_new_signal_id(),
                signal_type="container_restarted",
                category=SignalCategory.EVENTS,
                severity=Severity.MEDIUM,
                timestamp=datetime.now(),
                source="docker_provider",
                summary=f"容器 {container_name} 发生过重启，次数为 {restart_count}",
                payload={
                    "container_name": container_name,
                    "status": status,
                    "health": health,
                    "restart_count": restart_count,
                },
            )
        )

    return signals


def _new_signal_id() -> str:
    """生成 Signal ID"""
    return f"sig_{uuid4().hex[:12]}"
