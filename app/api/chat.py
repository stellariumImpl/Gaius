from fastapi import APIRouter

from app.models.request import ChatRequest
from app.models.response import ApiResponse, ChatResponseData
from app.services.chat_service import chat_service

router = APIRouter()


@router.post("/chat", response_model=ApiResponse)
async def chat(request: ChatRequest) -> ApiResponse:
    answer = await chat_service.chat(
        question=request.question,
        session_id=request.session_id,
        user_id=request.user_id,
    )

    return ApiResponse(
        code=200,
        message="success",
        data=ChatResponseData(answer=answer),
    )
