from pydantic import BaseModel, field_validator
from typing import List, Literal, Optional


# -------------------------
# REQUEST SCHEMAS
# -------------------------

class AIReviewRequest(BaseModel):
    resume_id: int
    model: Literal["gemini", "gpt"] = "gemini"

    @field_validator("model", mode="before")
    @classmethod
    def default_empty_model(cls, v):
        if not v or v.strip() == "":
            return "gemini"
        return v


class AIEvaluationRequest(BaseModel):
    resume_id: int
    job_description: str
    model: Literal["gemini", "gpt"] = "gemini"

    @field_validator("model", mode="before")
    @classmethod
    def default_empty_model(cls, v):
        if not v or v.strip() == "":
            return "gemini"
        return v


class CoverLetterRequest(BaseModel):
    resume_id: int
    job_description: str
    tone: Literal["professional", "enthusiastic", "concise"] = "professional"
    model: Literal["gemini", "gpt"] = "gemini"

    @field_validator("model", mode="before")
    @classmethod
    def default_empty_model(cls, v):
        if not v or v.strip() == "":
            return "gemini"
        return v

    @field_validator("tone", mode="before")
    @classmethod
    def default_empty_tone(cls, v):
        if not v or (isinstance(v, str) and v.strip() == ""):
            return "professional"
        return v


class CoverLetterResponse(BaseModel):
    cover_letter: str
    model_used: Optional[str] = None
    fallback_warning: Optional[str] = None


# -------------------------
# REVIEW RESPONSE SCHEMA
# -------------------------

class AIReviewResponse(BaseModel):
    score: int
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    model_used: Optional[str] = None
    fallback_warning: Optional[str] = None


# -------------------------
# INTERVIEW QUESTION MODELS
# -------------------------

class TechnicalQuestion(BaseModel):
    question: str
    intention: str
    answer: str


class BehavioralQuestion(BaseModel):
    question: str
    intention: str
    answer: str


# -------------------------
# SKILL GAP MODEL
# -------------------------

class SkillGap(BaseModel):
    skill: str
    severity: Literal["low", "medium", "high"]


# -------------------------
# PREPARATION PLAN
# -------------------------

class PreparationDay(BaseModel):
    day: int
    focus: str
    tasks: List[str]


# -------------------------
# INTERVIEW REPORT RESPONSE
# -------------------------

class InterviewReport(BaseModel):
    matchScore: int
    technicalQuestions: List[TechnicalQuestion]
    behavioralQuestions: List[BehavioralQuestion]
    skillGaps: List[SkillGap]
    preparationPlan: List[PreparationDay]
    title: str
    model_used: Optional[str] = None
    fallback_warning: Optional[str] = None