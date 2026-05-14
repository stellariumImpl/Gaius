from fastapi import APIRouter
from pydantic import BaseModel,Field

from app.services.chat_service import chat_service

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Session ID")
    question: str = Field(..., description="User question")

@router.post("/chat")
async def chat(request: ChatRequest):
    answer = await chat_service.chat(
        question=request.question,
        session_id=request.session_id,
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "answer": answer,
        },
    }