from pydantic import BaseModel


class ResumeUploadResponse(BaseModel):
    resume_id: int
    file_url: str
    message: str