from pydantic import BaseModel, Field
from typing import List, Literal, Optional


# ── Request ────────────────────────────────────────────────────────────────

class MockInterviewStartRequest(BaseModel):
    resume_id: int
    job_description: Optional[str] = Field(default=None, max_length=3000)
    model: Literal["gemini", "gpt", "gpt5"] = "gemini"
    num_questions: int = Field(default=5, ge=1, le=10)
    interview_type: Literal["technical", "behavioral", "mixed"] = "mixed"


class MockInterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str = Field(min_length=1, max_length=4000)
    model: Literal["gemini", "gpt", "gpt5"] = "gemini"


# ── Internal LLM-generated types (not exposed to client) ───────────────────

class GeneratedQuestion(BaseModel):
    question: str
    type: Literal["technical", "behavioral"]
    ideal_answer: str  # used as rubric during evaluation — never sent to frontend


# ── Response ───────────────────────────────────────────────────────────────

class MockInterviewStartResponse(BaseModel):
    session_id: str
    first_question: str
    question_type: Literal["technical", "behavioral"]
    question_index: int          # always 0
    total_questions: int
    model_used: str
    fallback_warning: Optional[str] = None


class TurnResult(BaseModel):
    """Stored per turn in MockInterviewSession.turns — internal only."""
    question: str
    answer: str
    score: int
    strengths: List[str]
    improvements: List[str]
    ideal_answer_hint: str


class SessionSummary(BaseModel):
    total_score: int       # sum of per-question scores
    max_score: int         # num_questions * 10
    percentage: int
    questions_answered: int
    overall_feedback: str
    top_strength: str
    top_improvement: str
    turns: List[TurnResult]


class QuestionFeedback(BaseModel):
    """Returned after each answer. Contains evaluation + the next question (if any)."""
    score: int           # 0–10
    strengths: List[str]
    improvements: List[str]
    ideal_answer_hint: str  # a hint toward the ideal answer, not a full giveaway

    # Next question (None when is_complete=True)
    next_question: Optional[str] = None
    next_question_type: Optional[Literal["technical", "behavioral"]] = None
    question_index: int           # index of the question just answered
    total_questions: int

    is_complete: bool = False
    session_summary: Optional[SessionSummary] = None

    model_used: str
    fallback_warning: Optional[str] = None
