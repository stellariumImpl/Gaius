"""Diagnosis Service: 真实运维诊断入口"""
from __future__ import annotations

from app.adapters.mapping.signal_mapper import map_container_snapshots_to_signals
from app.adapters.signals.docker_provider import get_container_snapshots
from app.adapters.signals.log_provider import get_multiple_container_logs
from app.core.llm_reasoner import reason_with_llm
from app.core.log_context_builder import build_log_context
from app.domain.output import AgentOutput


class DiagnosisService:
    """第一版真实诊断服务入口"""

    def diagnose(self, platform_id: str = "platform_default") -> AgentOutput:
        """执行一次真实环境诊断"""
        snapshots = get_container_snapshots()

        signals = map_container_snapshots_to_signals(
            snapshots,
            platform_id=platform_id,
        )

        container_names = self._extract_relevant_container_names(snapshots)
        log_snapshots = get_multiple_container_logs(container_names, tail=50)
        log_contexts = build_log_context(log_snapshots)

        output = reason_with_llm(
            signals=signals,
            log_contexts=log_contexts,
        )
        return output

    @staticmethod
    def _extract_relevant_container_names(snapshots: list[dict]) -> list[str]:
        names: list[str] = []

        for snapshot in snapshots:
            container_name = snapshot.get("container_name")
            if isinstance(container_name, str) and container_name not in names:
                names.append(container_name)

        return names


diagnosis_service = DiagnosisService()
