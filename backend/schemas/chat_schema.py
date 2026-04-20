from pydantic import BaseModel, Field
from typing import Literal, Optional


class ChatRequest(BaseModel):
    resume_id: int
    message: str = Field(min_length=1, max_length=2000)
    model: Literal["gemini", "gpt"] = "gemini"


class ChatResponse(BaseModel):
    answer: str
    model_used: str
    fallback_warning: Optional[str] = None