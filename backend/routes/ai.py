from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from db.postgres import get_db
from db.models import User
from utils.auth_dependency import get_current_user

from services.ai_service import review_resume_service, evaluate_resume_service

from schemas.ai_schema import (
    AIReviewRequest,
    AIReviewResponse,
    AIEvaluationRequest,
    InterviewReport
)

from utils.rate_limiter import limiter

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/review", response_model=AIReviewResponse)
@limiter.limit("10/hour")
def ai_review(
    request: Request,
    data: AIReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return review_resume_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        model_choice=data.model,
        db=db
    )


@router.post("/evaluate", response_model=InterviewReport)
@limiter.limit("10/hour")
def ai_evaluate(
    request: Request,
    data: AIEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return evaluate_resume_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        job_description=data.job_description,
        model_choice=data.model,
        db=db
    )