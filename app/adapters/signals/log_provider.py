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
from typing import Any


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
