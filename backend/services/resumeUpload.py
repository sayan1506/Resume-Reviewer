from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi import UploadFile

from db.supabase_storage import upload_pdf
from db.models import Resume


def upload_resume_service(file: UploadFile, db: Session):

    filename = f"{uuid4()}.pdf"

    file_url = upload_pdf(file.file, filename)

    resume = Resume(
        user_id=uuid4(),  # Replace with actual user ID from auth context
        file_url=file_url
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "resume_id": resume.id,
        "file_url": file_url,
        "message": "Resume uploaded successfully"
    }