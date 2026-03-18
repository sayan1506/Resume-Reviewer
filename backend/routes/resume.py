from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from typing import List

from db.models import User, Resume, ResumeAnalysis
from utils.auth_dependency import get_current_user
from db.postgres import get_db
from services.resumeUpload import upload_resume_service
from utils.file_validator import validate_pdf

router = APIRouter()


@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    result = upload_resume_service(
        file=file,
        user_id=current_user.id,
        db=db
    )

    return result


@router.get("/list")
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resumes = db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.uploaded_at.desc()).all()

    result = []
    for r in resumes:
        # Get latest analysis if exists
        analysis = db.query(ResumeAnalysis).filter(
            ResumeAnalysis.resume_id == r.id
        ).order_by(ResumeAnalysis.created_at.desc()).first()

        result.append({
            "id": r.id,
            "file_url": r.file_url,
            "uploaded_at": str(r.uploaded_at) if r.uploaded_at else None,
            "has_analysis": analysis is not None,
            "score": analysis.score if analysis else None,
            "strengths": analysis.strengths if analysis else None,
            "weaknesses": analysis.weaknesses if analysis else None,
            "suggestions": analysis.suggestions if analysis else None,
        })

    return result
