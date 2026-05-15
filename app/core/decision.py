from typing import Literal

from pydantic import BaseModel, Field


DecisionType = Literal["respond", "tool_call", "clarify", "handoff"]


class Decision(BaseModel):
    type: DecisionType = Field(..., description="决策类型")
    content: str = Field(default="", description="决策内容")
