"""Log Context Builder: 从原始日志中抽取高价值上下文"""

from __future__ import annotations

from typing import Any


KEYWORDS = [
    "FTL",
    "ERR",
    "WRN",
    "error",
    "failed",
    "exception",
    "shutdown",
    "authentication failed",
    "password authentication failed",
    "received fast shutdown request",
]


def build_log_context(log_snapshots: list[dict[str, Any]], max_lines_per_container: int = 8) -> list[dict[str, Any]]:
    """从原始日志快照中提取更适合 LLM 使用的上下文片段"""
    contexts: list[dict[str, Any]] = []

    for snapshot in log_snapshots:
        container_name = snapshot.get("container_name", "unknown")
        error = snapshot.get("error")
        logs = snapshot.get("logs", "")

        if error:
            contexts.append(
                {
                    "container_name": container_name,
                    "error": error,
                    "selected_lines": [],
                }
            )
            continue

        selected_lines = _select_relevant_lines(logs, max_lines=max_lines_per_container)

        contexts.append(
            {
                "container_name": container_name,
                "error": None,
                "selected_lines": selected_lines,
            }
        )

    return contexts


def _select_relevant_lines(log_text: str, max_lines: int) -> list[str]:
    if not isinstance(log_text, str) or not log_text.strip():
        return []

    lines = [line.strip() for line in log_text.splitlines() if line.strip()]

    matched: list[str] = []
    for line in lines:
        lowered = line.lower()
        if any(keyword.lower() in lowered for keyword in KEYWORDS):
            matched.append(line)

    if matched:
        return matched[:max_lines]

    # 如果没有命中关键词，就保留最后几行，避免完全丢失上下文
    return lines[-max_lines:]
