"""Diagnosis Service: 真实运维诊断入口"""
from __future__ import annotations

import logging

from app.adapters.mapping.signal_mapper import map_container_snapshots_to_signals
from app.adapters.signals.docker_provider import (
    get_container_snapshots,
    get_container_state_observations,
)
from app.adapters.signals.log_provider import (
    get_container_log_observations,
    get_multiple_container_logs,
)
from app.core.observation_builder import ObservationBuilder
from app.core.llm_reasoner import reason_with_llm
from app.core.log_context_builder import build_log_context
from app.domain.observation_bundle import ObservationBundle, PlatformMetadata
from app.domain.output import AgentOutput

logger = logging.getLogger(__name__)


class DiagnosisService:
    """第一版真实诊断服务入口"""

    def diagnose(self, platform_id: str = "platform_default") -> AgentOutput:
        """执行一次真实环境诊断"""
        snapshots = get_container_snapshots()
        self._build_observation_bundle_shadow(
            platform_id=platform_id,
            snapshots=snapshots,
        )

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

    def _build_observation_bundle_shadow(
        self,
        platform_id: str,
        snapshots: list[dict],
    ) -> ObservationBundle | None:
        """并行构建 ObservationBundle,但不影响当前主线返回

        这是 observation-first 主线的影子运行:
        - 成功时记录 bundle 统计
        - 失败时只记日志,不打断现有 diagnosis 流程
        """
        try:
            container_names = self._extract_relevant_container_names(snapshots)
            platform = self._build_platform_metadata(platform_id=platform_id)

            builder = ObservationBuilder(platform)
            builder.register("docker_provider", get_container_state_observations)
            builder.register(
                "log_provider",
                lambda: get_container_log_observations(container_names, tail=50),
            )

            bundle = builder.build()
            self._log_bundle_summary(bundle)
            return bundle
        except Exception as exc:
            logger.warning(
                "Observation bundle shadow build failed: %s: %s",
                type(exc).__name__,
                exc,
            )
            return None

    @staticmethod
    def _build_platform_metadata(platform_id: str) -> PlatformMetadata:
        """构造第一版平台元信息

        当前保持保守:
        - 只提供最基础的平台上下文
        - 不在这里做平台状态判断
        """
        return PlatformMetadata(
            platform_id=platform_id,
            platform_type="ctf_platform",
            deployment_mode="docker",
        )

    @staticmethod
    def _log_bundle_summary(bundle: ObservationBundle) -> None:
        """记录 ObservationBundle 的影子运行摘要"""
        logger.info(
            "Observation bundle built: bundle_id=%s observations=%s stats=%s providers_ok=%s providers_failed=%s",
            bundle.bundle_id,
            len(bundle.observations),
            bundle.summary_stats(),
            bundle.collection_report.successful_providers,
            [item.provider_name for item in bundle.collection_report.failed_providers],
        )

    @staticmethod
    def _extract_relevant_container_names(snapshots: list[dict]) -> list[str]:
        names: list[str] = []

        for snapshot in snapshots:
            container_name = snapshot.get("container_name")
            if isinstance(container_name, str) and container_name not in names:
                names.append(container_name)

        return names


diagnosis_service = DiagnosisService()
