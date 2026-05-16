"""ObservationBuilder: 编排多个 provider,产出 ObservationBundle

当前版本特意保持为同步实现:
- 兼容当前同步 provider
- 先让 observation-first 主线骨架立住
- 暂不替换现有 diagnosis_service 主线
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, UTC
from typing import Callable

from app.domain.observation import Observation
from app.domain.observation_bundle import (
    CollectionReport,
    ObservationBundle,
    PlatformMetadata,
    ProviderAttempt,
)


ProviderFn = Callable[[], list[Observation]]


class ObservationBuilder:
    """把多个 provider 的输出组织为一次完整 ObservationBundle"""

    def __init__(self, platform: PlatformMetadata) -> None:
        self._platform = platform
        self._providers: list[tuple[str, ProviderFn]] = []

    def register(self, name: str, fn: ProviderFn) -> "ObservationBuilder":
        """注册一个同步 provider 函数"""
        self._providers.append((name, fn))
        return self

    def build(self) -> ObservationBundle:
        """执行所有已注册 provider,构建 ObservationBundle"""
        bundle_id = f"obs_{uuid.uuid4().hex[:12]}"
        started = time.monotonic()
        collected_at = datetime.now(UTC)

        observations: list[Observation] = []
        attempts: list[ProviderAttempt] = []

        for name, fn in self._providers:
            provider_observations, attempt = self._run_provider(name, fn)
            observations.extend(provider_observations)
            attempts.append(attempt)

        duration_ms = int((time.monotonic() - started) * 1000)

        return ObservationBundle(
            bundle_id=bundle_id,
            platform=self._platform,
            observations=observations,
            collection_report=CollectionReport(
                collected_at=collected_at,
                duration_ms=duration_ms,
                providers_attempted=attempts,
            ),
        )

    def _run_provider(
        self,
        name: str,
        fn: ProviderFn,
    ) -> tuple[list[Observation], ProviderAttempt]:
        """执行单个 provider,并把失败显式记录到 collection_report 里"""
        provider_started = time.monotonic()

        try:
            observations = fn()
            duration_ms = int((time.monotonic() - provider_started) * 1000)
            return observations, ProviderAttempt(
                provider_name=name,
                success=True,
                duration_ms=duration_ms,
                observations_count=len(observations),
            )
        except Exception as exc:
            duration_ms = int((time.monotonic() - provider_started) * 1000)
            return [], ProviderAttempt(
                provider_name=name,
                success=False,
                duration_ms=duration_ms,
                observations_count=0,
                error=f"{type(exc).__name__}: {exc}",
            )
