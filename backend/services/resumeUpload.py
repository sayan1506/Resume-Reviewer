from fastapi import HTTPException
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi import UploadFile

from db.supabase_storage import upload_pdf
from db.models import Resume
from utils.pdf_parser import extract_text_from_pdf


def upload_resume_service(file: UploadFile, user_id: int, db: Session):

    # Read once — reuse the bytes for both parsing and uploading
    file_bytes = file.file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Parse PDF text from bytes
    parsed_text = extract_text_from_pdf(file_bytes)

    filename = f"{uuid4()}.pdf"

    # Pass bytes directly — no re-reading the stream
    file_url = upload_pdf(file_bytes, filename)

    resume = Resume(
        user_id=user_id,
        file_url=file_url,
        parsed_text=parsed_text
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Do NOT return parsed_text — it is large and the client never uses it
    return {
        "resume_id": resume.id,
        "file_url": file_url,
        "message": "Resume uploaded successfully",
    }