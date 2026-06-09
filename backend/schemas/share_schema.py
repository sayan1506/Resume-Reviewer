from pydantic import BaseModel
from typing import Literal, Any, Optional
from datetime import datetime


class CreateShareRequest(BaseModel):
    resume_id: int
    report_type: Literal["review", "evaluate"]


class CreateShareResponse(BaseModel):
    token: str
    share_url: str
    expires_at: Optional[datetime] = None


class SharedReportResponse(BaseModel):
    report_type: str
    payload: Any          # raw dict — frontend handles rendering
    created_at: datetime
