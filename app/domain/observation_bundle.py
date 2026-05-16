"""ObservationBundle: 一次完整诊断采集的统一输入包

它的职责是回答:
- 当前平台是谁
- 当前采集看到了哪些 observation
- 哪些 provider 成功了
- 哪些 provider 失败了

它不负责回答:
- 这是不是故障
- 哪种 observation 更重要
- 当前应该输出什么结论
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.observation import Observation


class PlatformMetadata(BaseModel):
    """平台元信息: 描述正在观察什么平台,不描述诊断结果"""

    platform_id: str
    platform_type: str
    platform_version: str | None = None
    deployment_mode: str | None = None
    expected_components: list[str] = Field(default_factory=list)
    is_competition_active: bool | None = None
    active_competition_id: str | None = None
    extra: dict = Field(default_factory=dict)


class ProviderAttempt(BaseModel):
    """单个 provider 的采集结果"""

    provider_name: str
    success: bool
    duration_ms: int
    observations_count: int = 0
    error: str | None = None


class CollectionReport(BaseModel):
    """采集过程元信息: 让下游知道"没看到"和"没采到"的区别"""

    collected_at: datetime
    duration_ms: int
    providers_attempted: list[ProviderAttempt] = Field(default_factory=list)

    @property
    def successful_providers(self) -> list[str]:
        return [item.provider_name for item in self.providers_attempted if item.success]

    @property
    def failed_providers(self) -> list[ProviderAttempt]:
        return [item for item in self.providers_attempted if not item.success]

    @property
    def has_collection_failures(self) -> bool:
        return any(not item.success for item in self.providers_attempted)


class ObservationBundle(BaseModel):
    """一次完整诊断采集的观察包"""

    bundle_id: str
    platform: PlatformMetadata
    observations: list[Observation] = Field(default_factory=list)
    collection_report: CollectionReport

    def by_kind(self, kind: str) -> list[Observation]:
        return [item for item in self.observations if item.kind == kind]

    def by_source(self, source: str) -> list[Observation]:
        return [item for item in self.observations if item.source == source]

    def by_target(self, target_type: str, target_name: str) -> list[Observation]:
        return [
            item
            for item in self.observations
            if item.target_ref.get("type") == target_type
            and item.target_ref.get("name") == target_name
        ]

    def summary_stats(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for item in self.observations:
            key = item.kind.value if hasattr(item.kind, "value") else str(item.kind)
            stats[key] = stats.get(key, 0) + 1
        return stats
