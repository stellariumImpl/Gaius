"""LLM Reasoner: 基于标准 Signal 的推理层

职责:
- 接收标准化 Signal 列表
- 生成结构化运维上下文
- 调用 LLM 进行分析
- 输出标准 AgentOutput

注意:
- 不直接依赖平台特定原始数据
- 不直接返回自由文本
- 所有输出必须回到 AgentOutput
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.core.llm import get_chat_model
from app.domain.output import AgentOutput
from app.domain.signal import Signal


def reason_with_llm(signals: list[Signal]) -> AgentOutput:
    """基于标准 Signal 列表进行 LLM 推理"""
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
    prompt = _build_prompt(signals)

    response = llm.invoke(prompt)
    text = _extract_text(response)

    try:
        payload = _extract_json_object(text)
        return AgentOutput.model_validate(payload)
    except Exception:
        # 如果模型没严格按 JSON 返回，兜底成一个 partial 输出
        return AgentOutput(
            status="partial",
            summary="模型已完成分析，但输出未完全符合结构化要求",
            current_situation=text[:1000],
            impact_scope="待人工确认",
            confidence="low",
            missing_information=["需要重新约束模型输出为合法 JSON"],
        )


def _build_prompt(signals: list[Signal]) -> str:
    """构造给模型的结构化推理提示"""
    signal_blocks = [_format_signal(signal) for signal in signals]
    signal_text = "\n".join(signal_blocks)

    return f"""
你是一个面向 CTF 比赛平台运维场景的 AI 智能体。

你的任务不是闲聊，而是根据给定的运维信号，判断当前是否存在异常、异常可能意味着什么、影响范围如何、下一步应如何排查。

你必须遵守以下要求：
1. 只基于输入信号做判断，不要编造不存在的日志、指标或事件。
2. 如果当前信息不足，请明确指出缺少哪些信息。
3. 输出必须是一个合法 JSON 对象，且字段必须严格符合下面这个结构：
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

请直接输出 JSON，不要输出 markdown，不要输出代码块，不要输出额外解释。
""".strip()


def _format_signal(signal: Signal) -> str:
    """把单条 Signal 压缩成可读上下文"""
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


def _extract_text(response: Any) -> str:
    """从模型响应对象中提取文本"""
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
    """从模型输出中提取 JSON 对象
    
    兼容:
    - 纯 JSON
    - ```json ... ``` 包裹
    """
    text = text.strip()

    # 去掉 fenced code block
    fenced_match = re.search(r"```json\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced_match:
        text = fenced_match.group(1).strip()

    return json.loads(text)
