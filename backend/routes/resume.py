from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from db.models import User
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

