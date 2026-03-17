from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .postgres import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="user")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    file_url = Column(String)
    parsed_text = Column(Text)

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resumes")

    # 🔥 REQUIRED FIX
    analysis = relationship("ResumeAnalysis", back_populates="resume")


class ResumeAnalysis(Base):
    __tablename__ = "resume_analysis"

    id = Column(Integer, primary_key=True, index=True)

    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False
    )

    score = Column(Integer, nullable=False)

    strengths = Column(JSONB, nullable=False)
    weaknesses = Column(JSONB, nullable=False)
    suggestions = Column(JSONB, nullable=False)

    created_at = Column(TIMESTAMP, server_default=func.now())

    resume = relationship("Resume", back_populates="analysis")