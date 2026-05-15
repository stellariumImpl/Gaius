from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    session_id: str=Field(...,description="会话ID")
    question: str=Field(...,description="用户问题")
    user_id: str=Field(default="anonymous", description="用户ID")