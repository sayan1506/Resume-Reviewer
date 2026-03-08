from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .postgres import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    file_url = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class ResumeAnalysis(Base):
    __tablename__ = "resume_analysis"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer)
    score = Column(Integer)
    feedback = Column(String)