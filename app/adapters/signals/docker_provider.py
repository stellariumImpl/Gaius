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
from typing import Any


def get_container_snapshots() -> list[dict[str, Any]]:
    """获取当前 Docker 容器快照
    
    返回字段:
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

    # Docker inspect 的 Name 通常带前导 /
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
