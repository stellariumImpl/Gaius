"""Docker Provider: 从真实 Docker 环境采集容器快照

职责:
- 只负责采集容器事实
- 不负责诊断
- 不负责 Incident 判断
- 不负责平台特定逻辑

当前返回的是原始容器快照列表，后续再交给 mapper 转成 Signal。
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.domain.observation import ContainerStateObservation


def get_container_snapshots() -> list[dict[str, Any]]:
    """获取当前 Docker 容器快照

    返回字段:
    - container_id: 容器 ID
    - container_name: 容器名
    - image: 镜像名
    - status: 运行状态(running / exited / restarting ...)
    - health: 健康状态(healthy / unhealthy / None)
    - restart_count: 重启次数
    """
    container_ids = _list_container_ids()
    snapshots: list[dict[str, Any]] = []

    for container_id in container_ids:
        inspect_data = _inspect_container(container_id)
        if not inspect_data:
            continue

        snapshot = _extract_snapshot(inspect_data)
        snapshots.append(snapshot)

    return snapshots


def get_container_state_observations() -> list[ContainerStateObservation]:
    """获取当前 Docker 容器状态 observations

    这是 observation-first 主线的旁路输出:
    - 保留旧的 snapshot 输出函数不变
    - 新增更中立的 Observation 输出函数
    """
    container_ids = _list_container_ids()
    observations: list[ContainerStateObservation] = []

    for container_id in container_ids:
        inspect_data = _inspect_container(container_id)
        if not inspect_data:
            continue

        observations.append(_extract_container_state_observation(inspect_data))

    return observations


def _list_container_ids() -> list[str]:
    """列出当前所有容器 ID（包括已退出容器）"""
    result = subprocess.run(
        ["docker", "ps", "-a", "-q"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout.strip()
    if not output:
        return []
    return output.splitlines()


def _inspect_container(container_id: str) -> dict[str, Any] | None:
    """获取单个容器的 inspect JSON"""
    result = subprocess.run(
        ["docker", "inspect", container_id],
        capture_output=True,
        text=True,
        check=True,
    )
    raw = result.stdout.strip()
    if not raw:
        return None

    parsed = json.loads(raw)
    if not parsed or not isinstance(parsed, list):
        return None

    first = parsed[0]
    if not isinstance(first, dict):
        return None

    return first


def _extract_snapshot(inspect_data: dict[str, Any]) -> dict[str, Any]:
    """从 inspect JSON 中提取我们关心的字段"""
    state = inspect_data.get("State", {}) or {}
    config = inspect_data.get("Config", {}) or {}

    raw_name = inspect_data.get("Name", "") or ""
    container_name = raw_name.lstrip("/") if isinstance(raw_name, str) else "unknown"

    image = config.get("Image", "unknown")
    status = state.get("Status", "unknown")
    restart_count = inspect_data.get("RestartCount", 0)

    health_info = state.get("Health")
    health: str | None = None
    if isinstance(health_info, dict):
        maybe_health = health_info.get("Status")
        if isinstance(maybe_health, str):
            health = maybe_health

    return {
        "container_id": inspect_data.get("Id", ""),
        "container_name": container_name,
        "image": image,
        "status": status,
        "health": health,
        "restart_count": restart_count,
    }


def _extract_container_state_observation(
    inspect_data: dict[str, Any],
) -> ContainerStateObservation:
    """从 inspect JSON 中提取更中立的容器状态 observation"""
    state = inspect_data.get("State", {}) or {}
    config = inspect_data.get("Config", {}) or {}

    raw_name = inspect_data.get("Name", "") or ""
    container_name = raw_name.lstrip("/") if isinstance(raw_name, str) else "unknown"

    image = config.get("Image", "unknown")
    status = state.get("Status", "unknown")
    restart_count = inspect_data.get("RestartCount", 0)
    exit_code = state.get("ExitCode")

    health_info = state.get("Health")
    health: str | None = None
    if isinstance(health_info, dict):
        maybe_health = health_info.get("Status")
        if isinstance(maybe_health, str):
            health = maybe_health

    return ContainerStateObservation(
        observation_id=f"obs_{uuid4().hex[:12]}",
        source="docker_provider",
        collected_at=datetime.now(),
        target_ref={"type": "container", "name": container_name},
        tags=["docker", "container_state"],
        container_id=inspect_data.get("Id", ""),
        container_name=container_name,
        image=image,
        status=status,
        health=health,
        restart_count=restart_count if isinstance(restart_count, int) else 0,
        started_at=_parse_docker_datetime(state.get("StartedAt")),
        finished_at=_parse_docker_datetime(state.get("FinishedAt")),
        exit_code=exit_code if isinstance(exit_code, int) else None,
    )


def _parse_docker_datetime(value: Any) -> datetime | None:
    """解析 Docker inspect 返回的时间字符串"""
    if not isinstance(value, str) or not value:
        return None

    # Docker 常见零值: 0001-01-01T00:00:00Z
    if value.startswith("0001-01-01"):
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None
