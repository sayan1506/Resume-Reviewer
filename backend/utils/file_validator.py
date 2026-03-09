from fastapi import UploadFile, HTTPException


def validate_pdf(file: UploadFile):

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files allowed")