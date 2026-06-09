from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional

from db.postgres import get_db
from db.models import User
from utils.auth_dependency import get_current_user
from services.share_service import (
    create_share_token,
    create_share_token_with_payload,
    get_shared_report
)
from schemas.share_schema import CreateShareResponse, SharedReportResponse
from utils.rate_limiter import limiter


router = APIRouter(prefix="/share", tags=["Share"])


@router.post("/create", response_model=CreateShareResponse)
@limiter.limit("20/hour")
def create_share(
    request: Request,
    resume_id: int,
    report_type: str,                # "review" | "evaluate"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payload: Optional[dict] = None   # required when report_type == "evaluate"
):
    """
    Creates or refreshes a public share link for a report.
    - For "review": reads from DB (ResumeAnalysis), payload not needed.
    - For "evaluate": payload must be provided in request body since
      evaluate results are not persisted server-side.
    """
    if report_type == "evaluate":
        if not payload:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail="payload is required for evaluate report_type"
            )
        return create_share_token_with_payload(
            resume_id=resume_id,
            user_id=current_user.id,
            report_type=report_type,
            payload=payload,
            db=db
        )
    else:
        return create_share_token(
            resume_id=resume_id,
            user_id=current_user.id,
            report_type=report_type,
            db=db
        )


@router.get("/{token}", response_model=SharedReportResponse)
def view_shared_report(token: str, db: Session = Depends(get_db)):
    """
    Public endpoint — no auth.
    Returns the stored report payload for rendering on the public share page.
    """
    return get_shared_report(token, db)
