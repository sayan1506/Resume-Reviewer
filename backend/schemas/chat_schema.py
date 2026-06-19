from pydantic import BaseModel, Field
from typing import Literal, Optional


class ChatRequest(BaseModel):
    resume_id: int
    message: str = Field(min_length=1, max_length=2000)
    model: Literal["gemini", "gpt"] = "gemini"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: Optional[str] = None
    model_used: str
    fallback_warning: Optional[str] = None