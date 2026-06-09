import secrets
import os
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from db.models import SharedReport, ResumeAnalysis, Resume


def create_share_token(
    resume_id: int,
    user_id: int,
    report_type: str,
    db: Session
) -> dict:
    """
    Generates a unique share token for the latest analysis of this resume.
    report_type: "review" | "evaluate"

    For "review":  reads from ResumeAnalysis (score, strengths, weaknesses, suggestions).
    For "evaluate": reads from ResumeAnalysis — NOTE: evaluate results are not persisted
                    in the current schema. See Edge Cases section below.

    Returns token and fully-qualified share URL.
    """

    # Verify the resume belongs to the requesting user
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if report_type == "review":
        analysis = db.query(ResumeAnalysis).filter(
            ResumeAnalysis.resume_id == resume_id
        ).order_by(ResumeAnalysis.created_at.desc()).first()

        if not analysis:
            raise HTTPException(
                status_code=400,
                detail="No review found for this resume. Run /ai/review first."
            )

        payload = {
            "score": analysis.score,
            "strengths": analysis.strengths,
            "weaknesses": analysis.weaknesses,
            "suggestions": analysis.suggestions,
        }

    elif report_type == "evaluate":
        # evaluate results are not currently persisted in DB.
        # This route must receive the payload from the frontend directly.
        # See Edge Case 1 below — the request body carries the report payload
        # for evaluate type.
        raise HTTPException(
            status_code=400,
            detail="For evaluate reports, supply the payload directly. See /share/create endpoint."
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid report_type")

    # Check if a share token already exists for this resume+type; reuse it
    existing = db.query(SharedReport).filter(
        SharedReport.resume_id == resume_id,
        SharedReport.report_type == report_type,
        SharedReport.user_id == user_id
    ).first()

    if existing:
        # Overwrite the payload with the latest analysis and return same token
        existing.payload = payload
        existing.created_at = datetime.now(timezone.utc)
        db.commit()
        token = existing.token
    else:
        token = secrets.token_urlsafe(32)
        shared = SharedReport(
            token=token,
            report_type=report_type,
            resume_id=resume_id,
            user_id=user_id,
            payload=payload
        )
        db.add(shared)
        db.commit()

    frontend_base = os.getenv("FRONTEND_BASE_URL", "https://resume-reviewer-navy.vercel.app")
    share_url = f"{frontend_base}/shared/{token}"

    return {"token": token, "share_url": share_url, "expires_at": None}


def create_share_token_with_payload(
    resume_id: int,
    user_id: int,
    report_type: str,
    payload: dict,
    db: Session
) -> dict:
    """
    Used for evaluate reports (not persisted in DB).
    Accepts the full report payload from the frontend/caller.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    existing = db.query(SharedReport).filter(
        SharedReport.resume_id == resume_id,
        SharedReport.report_type == report_type,
        SharedReport.user_id == user_id
    ).first()

    if existing:
        existing.payload = payload
        existing.created_at = datetime.now(timezone.utc)
        db.commit()
        token = existing.token
    else:
        token = secrets.token_urlsafe(32)
        shared = SharedReport(
            token=token,
            report_type=report_type,
            resume_id=resume_id,
            user_id=user_id,
            payload=payload
        )
        db.add(shared)
        db.commit()

    frontend_base = os.getenv("FRONTEND_BASE_URL", "https://resume-reviewer-navy.vercel.app")
    share_url = f"{frontend_base}/shared/{token}"

    return {"token": token, "share_url": share_url, "expires_at": None}


def get_shared_report(token: str, db: Session) -> dict:
    """
    Public — no auth required.
    Returns the report payload for a given token.
    """
    report = db.query(SharedReport).filter(SharedReport.token == token).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found or link has expired")

    return {
        "report_type": report.report_type,
        "payload": report.payload,
        "created_at": report.created_at
    }
