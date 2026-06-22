from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from db.postgres import get_db
from db.models import User
from utils.auth_dependency import get_current_user

from services.ai_service import review_resume_service, evaluate_resume_service, cover_letter_service
from services.ats_service import ats_check_service
from services.rewrite_service import rewrite_resume_service
from services.job_match_service import job_match_service
from services.chat_service import chat_with_resume_service
from schemas.chat_schema import ChatRequest, ChatResponse


from schemas.ai_schema import (
    AIReviewRequest,
    AIReviewResponse,
    AIEvaluationRequest,
    InterviewReport,
    CoverLetterRequest,
    CoverLetterResponse,
    ATSCheckRequest,
    ATSCheckResponse,
    RewriteRequest,
    RewriteResponse,
    JobMatchRequest,
    JobMatchResponse,
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



@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/hour")
def ai_chat(
    request: Request,
    data: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return chat_with_resume_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        message=data.message,
        model_choice=data.model,
        session_id=data.session_id,
        db=db
    )


@router.post("/cover-letter", response_model=CoverLetterResponse)
@limiter.limit("10/hour")
def ai_cover_letter(
    request: Request,
    data: CoverLetterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return cover_letter_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        job_description=data.job_description,
        tone=data.tone,
        model_choice=data.model,
        db=db
    )


@router.post("/ats-check", response_model=ATSCheckResponse)
@limiter.limit("10/hour")
def ai_ats_check(
    request: Request,
    data: ATSCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return ats_check_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        job_description=data.job_description,
        model_choice=data.model,
        db=db
    )


@router.post("/rewrite", response_model=RewriteResponse)
@limiter.limit("10/hour")
def ai_rewrite(
    request: Request,
    data: RewriteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return rewrite_resume_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        job_description=data.job_description,
        model_choice=data.model,
        db=db
    )


@router.post("/job-match", response_model=JobMatchResponse)
@limiter.limit("10/hour")
def ai_job_match(
    request: Request,
    data: JobMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return job_match_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        query=data.query,
        model_choice=data.model,
        db=db
    )