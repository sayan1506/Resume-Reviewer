import uuid
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from .postgres import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    avatar_url = Column(Text, nullable=True)
    auth_provider = Column(String(50), default="email")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    resumes = relationship("Resume", back_populates="user")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_url = Column(String)
    parsed_text = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="resumes")
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
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="analysis")


class SharedReport(Base):
    __tablename__ = "shared_reports"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    report_type = Column(String(20), nullable=False)   # "review" | "evaluate"
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    payload = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)


class MockInterviewSession(Base):
    __tablename__ = "mock_interview_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Generated up-front: list of {"question": str, "type": "technical"|"behavioral", "ideal_answer": str}
    questions = Column(JSONB, nullable=False, default=list)

    # Appended per answer: list of {"question", "answer", "score", "strengths", "improvements", "ideal_answer_hint"}
    turns = Column(JSONB, nullable=False, default=list)

    current_index = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="active")  # "active" | "complete"
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Appended per exchange: list of {"role": "user"|"assistant", "content": str}
    turns = Column(JSONB, nullable=False, default=list)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())