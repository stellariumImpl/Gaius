"""Diagnosis API: 真实环境诊断接口"""
from fastapi import APIRouter

from app.models.diagnosis import DiagnosisRequest
from app.services.diagnosis_service import diagnosis_service

router = APIRouter()


@router.post("/diagnosis")
async def diagnose(request: DiagnosisRequest):
    output = diagnosis_service.diagnose(platform_id=request.platform_id)
    return output.model_dump(mode="json")
