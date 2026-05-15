"""LLM Reasoner: 基于标准 Signal 的推理层"""

from __future__ import annotations

import json
import re
from typing import Any

from app.core.llm import get_chat_model
from app.domain.output import AgentOutput
from app.domain.signal import Signal


def _build_evidence_candidates(
    signals: list[Signal],
    log_contexts: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """从 signals 和日志上下文中预构建证据候选
    
    注意:
    - 这里只做证据整理，不做诊断判断
    - 输出给 LLM 的是“可引用证据池”
    """
    evidence: list[dict[str, str]] = []

    # 1. 从 Signal 提取基础容器状态证据
    for signal in signals:
        container_name = signal.payload.get("container_name", "unknown")
        status = signal.payload.get("status")
        health = signal.payload.get("health")
        restart_count = signal.payload.get("restart_count")

        if signal.signal_type == "container_restarted":
            evidence.append(
                {
                    "type": "event",
                    "source": signal.source,
                    "content": (
                        f"容器 {container_name} 发生过重启，"
                        f"次数为 {restart_count}，当前状态 {status}，health {health}"
                    ),
                }
            )

        elif signal.signal_type == "container_unhealthy":
            evidence.append(
                {
                    "type": "health_check",
                    "source": signal.source,
                    "content": f"容器 {container_name} 健康检查失败，当前状态 {status}",
                }
            )

        elif signal.signal_type == "container_not_running":
            evidence.append(
                {
                    "type": "container_status",
                    "source": signal.source,
                    "content": f"容器 {container_name} 当前未运行，状态为 {status}",
                }
            )

    # 2. 从日志上下文提取日志证据
    for ctx in log_contexts:
        container_name = ctx.get("container_name", "unknown")
        selected_lines = ctx.get("selected_lines", [])
        error = ctx.get("error")

        if error:
            evidence.append(
                {
                    "type": "log",
                    "source": container_name,
                    "content": f"日志读取失败: {error}",
                }
            )
            continue

        for line in selected_lines:
            evidence.append(
                {
                    "type": "log",
                    "source": container_name,
                    "content": line,
                }
            )

    return evidence



def reason_with_llm(
    signals: list[Signal],
    log_contexts: list[dict[str, Any]] | None = None,
) -> AgentOutput:
    """基于标准 Signal 列表和日志上下文进行 LLM 推理"""
    if not signals:
        return AgentOutput(
            status="failed",
            summary="当前没有可用于分析的运维信号",
            current_situation="未采集到有效 Signal",
            impact_scope="未知",
            confidence="low",
            missing_information=["需要至少一种真实环境信号来源"],
        )

    llm = get_chat_model()

    log_contexts = log_contexts or []
    evidence_candidates = _build_evidence_candidates(signals, log_contexts)
    prompt = _build_prompt(signals, log_contexts, evidence_candidates)


    response = llm.invoke(prompt)
    text = _extract_text(response)

    try:
        payload = _extract_json_object(text)
        payload = _normalize_output_payload(payload, evidence_candidates)
        return AgentOutput.model_validate(payload)
    except Exception:
        return AgentOutput(
            status="partial",
            summary="模型已完成分析，但输出未完全符合结构化要求",
            current_situation=text[:1000],
            impact_scope="待人工确认",
            confidence="low",
            missing_information=["需要重新约束模型输出为合法 JSON"],
        )


def _build_prompt(
    signals: list[Signal],
    log_contexts: list[dict[str, Any]],
    evidence_candidates: list[dict[str, str]],
) -> str:
    signal_blocks = [_format_signal(signal) for signal in signals]
    signal_text = "\n".join(signal_blocks)
    
    log_text = _format_log_contexts(log_contexts)

    evidence_text = json.dumps(evidence_candidates, ensure_ascii=False, indent=2)

    return f"""
你是一个面向 CTF 比赛平台运维场景的 AI 智能体。

你的任务不是闲聊，而是根据给定的运维信号、日志上下文和证据候选，判断当前是否存在异常、异常可能意味着什么、影响范围如何、下一步应如何排查。

你必须严格遵守以下要求：

1. 只基于输入信号、日志上下文和证据候选做判断。
2. 不要编造不存在的日志、指标、事件、重启原因或平台行为。
3. 如果证据不足，请明确输出 partial 或 clarification_needed。
4. 只有在日志或信号明确支持时，才能给出较强结论。
5. 如果某个字段未知，例如 health 为 null，不要把它直接说成确定故障，只能说“未知”或“待确认”。
6. evidence 字段必须尽量从提供的 evidence candidates 中选取，不要自由编造新的证据文本。

输出必须是一个合法 JSON 对象，且字段必须严格符合下面这个结构：
{{
  "status": "success | partial | clarification_needed | failed",
  "summary": "一句话总结",
  "current_situation": "当前现象描述",
  "impact_scope": "影响范围描述",
  "suspected_causes": ["可能原因1", "可能原因2"],
  "investigation_steps": ["排查步骤1", "排查步骤2"],
  "suggested_actions": ["建议动作1", "建议动作2"],
  "confidence": "low | medium | high",
  "missing_information": ["缺失信息1", "缺失信息2"],
  "evidence": [
    {{
      "type": "log | metric | event | health_check | container_status",
      "source": "证据来源",
      "content": "证据内容"
    }}
  ],
  "related_incident_id": null
}}

下面是当前收到的标准化运维信号：

{signal_text}

下面是压缩后的日志上下文：

{log_text}

下面是程序预先整理的证据候选：

{evidence_text}

请直接输出 JSON，不要输出 markdown，不要输出代码块，不要输出额外解释。
""".strip()

def _normalize_output_payload(
    payload: dict[str, Any],
    evidence_candidates: list[dict[str, str]],
) -> dict[str, Any]:
    """对模型输出做轻量收敛
    
    当前只做:
    - 如果 evidence 缺失或为空，补一个空列表
    - 如果 evidence 数量过多，截断
    """
    if "evidence" not in payload or not isinstance(payload["evidence"], list):
        payload["evidence"] = []

    payload["evidence"] = payload["evidence"][:8]

    return payload


def _format_signal(signal: Signal) -> str:
    payload_text = json.dumps(signal.payload, ensure_ascii=False)
    return (
        f"- signal_id: {signal.signal_id}\n"
        f"  signal_type: {signal.signal_type}\n"
        f"  category: {signal.category.value}\n"
        f"  severity: {signal.severity.value}\n"
        f"  source: {signal.source}\n"
        f"  summary: {signal.summary}\n"
        f"  payload: {payload_text}"
    )


def _format_log_contexts(log_contexts: list[dict[str, Any]]) -> str:
    if not log_contexts:
        return "无附加日志上下文"

    blocks: list[str] = []
    for ctx in log_contexts:
        container_name = ctx.get("container_name", "unknown")
        error = ctx.get("error")
        selected_lines = ctx.get("selected_lines", [])

        if error:
            blocks.append(
                f"- container: {container_name}\n"
                f"  error: {error}"
            )
            continue

        if not selected_lines:
            blocks.append(
                f"- container: {container_name}\n"
                f"  selected_lines: (无高价值日志片段)"
            )
            continue

        joined_lines = "\n".join(selected_lines)
        blocks.append(
            f"- container: {container_name}\n"
            f"  selected_lines:\n{joined_lines}"
        )

    return "\n\n".join(blocks)


def _extract_text(response: Any) -> str:
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    text_parts.append(text)
        return "\n".join(text_parts).strip()

    return str(content).strip()


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()

    fenced_match = re.search(r"```json\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced_match:
        text = fenced_match.group(1).strip()

    return json.loads(text)
