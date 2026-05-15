"""Diagnosis API 模型"""
from pydantic import BaseModel, Field


class DiagnosisRequest(BaseModel):
    """诊断请求
    
    第一版只保留 platform_id，后面再扩展更多上下文。
    """
    platform_id: str = Field(
        default="platform_default",
        description="平台实例 ID",
    )
