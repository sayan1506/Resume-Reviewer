from fastapi import APIRouter, Depends
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

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/review", response_model=AIReviewResponse)
def ai_review(
    data: AIReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    result = review_resume_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        db=db
    )

    return result


@router.post("/evaluate", response_model=InterviewReport)
def ai_evaluate(
    data: AIEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    result = evaluate_resume_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        job_description=data.job_description,
        db=db
    )

    return result