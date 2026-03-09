from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from db.postgres import get_db
from services.resumeUpload import upload_resume_service
from utils.file_validator import validate_pdf

router = APIRouter()


@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    validate_pdf(file)

    return upload_resume_service(file, db)