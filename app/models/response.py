from typing import Any

from pydantic import BaseModel, Field


class ChatResponseData(BaseModel):
    answer: str = Field(..., description="助手回答")


class ApiResponse(BaseModel):
    code: int = Field(..., description="状态码")
    message: str = Field(..., description="状态信息")
    data: Any = Field(..., description="响应数据")
