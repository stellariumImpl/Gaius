"""Log Provider: 从真实 Docker 容器读取最近日志

职责:
- 只负责采集日志事实
- 不负责诊断
- 不负责 Incident 判断
- 不负责平台特定结论

当前版本:
- 基于 docker logs 读取最近 N 行
- 返回结构化日志快照
"""
from __future__ import annotations

import subprocess
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.domain.observation import ContainerLogObservation


def get_container_logs(container_name: str, tail: int = 100) -> dict[str, Any]:
    """读取单个容器最近日志
    
    返回:
    - container_name
    - tail
    - logs
    - error
    """
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(tail), container_name],
            capture_output=True,
            text=True,
            check=True,
        )
        return {
            "container_name": container_name,
            "tail": tail,
            "logs": result.stdout.strip(),
            "error": None,
        }
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip() if exc.stderr else str(exc)
        return {
            "container_name": container_name,
            "tail": tail,
            "logs": "",
            "error": stderr,
        }


def get_multiple_container_logs(
    container_names: list[str],
    tail: int = 100,
) -> list[dict[str, Any]]:
    """批量读取多个容器最近日志"""
    snapshots: list[dict[str, Any]] = []

    for container_name in container_names:
        snapshots.append(get_container_logs(container_name=container_name, tail=tail))

    return snapshots


def get_container_log_observation(
    container_name: str,
    tail: int = 100,
) -> ContainerLogObservation:
    """读取单个容器日志,并返回 observation 形式

    注意:
    - 保留现有 dict 输出函数不变
    - observation 形式只表达日志事实,不表达诊断结论
    """
    snapshot = get_container_logs(container_name=container_name, tail=tail)
    logs = snapshot.get("logs", "")
    lines = logs.splitlines() if isinstance(logs, str) and logs else []

    tags = ["docker", "container_log"]
    if snapshot.get("error"):
        tags.append("log_read_error")

    return ContainerLogObservation(
        observation_id=f"obs_{uuid4().hex[:12]}",
        source="log_provider",
        collected_at=datetime.now(),
        target_ref={"type": "container", "name": container_name},
        tags=tags,
        container_name=container_name,
        lines=lines,
        truncation=f"tail={tail}",
        log_source_path=f"docker logs {container_name}",
    )


def get_container_log_observations(
    container_names: list[str],
    tail: int = 100,
) -> list[ContainerLogObservation]:
    """批量读取多个容器日志,并返回 observation 列表"""
    observations: list[ContainerLogObservation] = []

    for container_name in container_names:
        observations.append(
            get_container_log_observation(container_name=container_name, tail=tail)
        )

    return observations
