from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db.models import User, Resume, ResumeAnalysis
from utils.auth_dependency import get_current_user
from db.postgres import get_db
from services.resumeUpload import upload_resume_service
from utils.file_validator import validate_pdf
from db.supabase_storage import extract_object_path, create_signed_url

router = APIRouter()


@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    validate_pdf(file)   # <-- add this line

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


@router.get("/{resume_id}/history")
def resume_analysis_history(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return every analysis for this resume oldest-first, so the frontend can plot a score trend."""
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    analyses = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.resume_id == resume_id
    ).order_by(ResumeAnalysis.created_at.asc()).all()

    return [
        {
            "id": a.id,
            "score": a.score,
            "strengths": a.strengths,
            "weaknesses": a.weaknesses,
            "suggestions": a.suggestions,
            "created_at": str(a.created_at) if a.created_at else None,
        }
        for a in analyses
    ]


@router.get("/{resume_id}/view")
def view_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return a short-lived signed URL so the owner can view their resume PDF.

    The bucket is private, so this is the only way to reach the file — the link
    expires quickly and is scoped to the authenticated owner.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.file_url:
        raise HTTPException(status_code=404, detail="Resume file is unavailable")

    object_path = extract_object_path(resume.file_url)
    signed_url = create_signed_url(object_path, expires_in=300)

    if not signed_url:
        raise HTTPException(status_code=502, detail="Could not generate a view link")

    return {"url": signed_url, "expires_in": 300}
