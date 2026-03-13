from pydantic import BaseModel
from typing import List, Literal


# -------------------------
# REQUEST SCHEMAS
# -------------------------

class AIReviewRequest(BaseModel):
    resume_id: int


class AIEvaluationRequest(BaseModel):
    resume_id: int
    job_description: str


# -------------------------
# REVIEW RESPONSE SCHEMA
# -------------------------

class AIReviewResponse(BaseModel):
    score: int
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


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