from fastapi import APIRouter

from app.models.request import ChatRequest
from app.models.response import ApiResponse, ChatResponseData
from app.services.aiops_service import aiops_service

router = APIRouter()


@router.post("/aiops", response_model=ApiResponse)
async def aiops(request: ChatRequest) -> ApiResponse:
    answer = await aiops_service.diagnose(
        question=request.question,
        session_id=request.session_id,
        user_id=request.user_id,
    )

    return ApiResponse(
        code=200,
        message="success",
        data=ChatResponseData(answer=answer),
    )
