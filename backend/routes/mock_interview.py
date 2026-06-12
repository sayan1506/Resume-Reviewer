from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from db.postgres import get_db
from db.models import User
from utils.auth_dependency import get_current_user
from utils.rate_limiter import limiter

from schemas.mock_interview_schema import (
    MockInterviewStartRequest,
    MockInterviewAnswerRequest,
    MockInterviewStartResponse,
    QuestionFeedback,
)
from services.mock_interview_service import (
    start_mock_interview_service,
    answer_mock_question_service,
)

router = APIRouter(prefix="/ai/mock-interview", tags=["Mock Interview"])


@router.post("/start", response_model=MockInterviewStartResponse)
@limiter.limit("5/hour")           # question generation is expensive
def start_interview(
    request: Request,
    data: MockInterviewStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return start_mock_interview_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        job_description=data.job_description,
        model_choice=data.model,
        num_questions=data.num_questions,
        interview_type=data.interview_type,
        db=db,
    )


@router.post("/answer", response_model=QuestionFeedback)
@limiter.limit("30/hour")
def answer_question(
    request: Request,
    data: MockInterviewAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return answer_mock_question_service(
        session_id=data.session_id,
        user_id=current_user.id,
        answer=data.answer,
        model_choice=data.model,
        db=db,
    )
