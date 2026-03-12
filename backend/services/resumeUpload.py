from fastapi import HTTPException
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi import UploadFile

from db.supabase_storage import upload_pdf
from db.models import Resume
from utils.pdf_parser import extract_text_from_pdf
from services.pinecone_service import store_resume_embeddings



def upload_resume_service(file: UploadFile, user_id: int, db: Session):

    file_bytes = file.file.read()

    # Parse PDF
    parsed_text = extract_text_from_pdf(file_bytes)

    filename = f"{uuid4()}.pdf"

    file_url = upload_pdf(file.file, filename)

    resume = Resume(
        user_id=user_id,
        file_url=file_url
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    # store embeddings
    store_resume_embeddings(resume.id, parsed_text)

    return {
        "resume_id": resume.id,
        "file_url": file_url,
        "message": "Resume uploaded successfully",
        "parsed_text": parsed_text
    }