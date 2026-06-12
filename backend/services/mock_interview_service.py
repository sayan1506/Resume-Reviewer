import uuid
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from db.models import Resume, MockInterviewSession
from ai.router import get_llm
from ai.llm import llm as gemini_llm
from schemas.mock_interview_schema import (
    GeneratedQuestion,
    MockInterviewStartResponse,
    QuestionFeedback,
    SessionSummary,
    TurnResult,
)


# ── LLM output schemas (for structured output calls) ──────────────────────

class QuestionList(BaseModel):
    questions: List[GeneratedQuestion]


class AnswerEvaluation(BaseModel):
    score: int               # 0–10
    strengths: List[str]
    improvements: List[str]
    ideal_answer_hint: str


class SummaryText(BaseModel):
    overall_feedback: str
    top_strength: str
    top_improvement: str


# ── Prompts ───────────────────────────────────────────────────────────────

QUESTION_GENERATION_PROMPT = ChatPromptTemplate.from_template("""
You are an experienced technical recruiter preparing for a candidate interview.

Based on the candidate's resume and the target role, generate exactly {num_questions} interview
questions. Follow the type distribution: {interview_type}.

Rules:
- For "technical"   -> all questions must test technical skills, tools, or project depth.
- For "behavioral"  -> all questions must use STAR-style situations/scenarios.
- For "mixed"       -> roughly half technical, half behavioral.
- Each question should be realistic and specific to THIS candidate's background.
- The ideal_answer should be a concise rubric (2-4 sentences), never a full essay.
- Do not generate generic questions like "Tell me about yourself."

Resume:
{resume_text}

Job Description (if provided):
{job_description}
""")


ANSWER_EVALUATION_PROMPT = ChatPromptTemplate.from_template("""
You are a strict but fair interview coach evaluating a candidate's answer.

Question:
{question}

Ideal answer rubric (use this as your scoring benchmark, do NOT reveal it verbatim):
{ideal_answer}

Candidate's answer:
{candidate_answer}

Evaluate using these criteria:
- Relevance: does the answer address the question?
- Depth: are specifics, examples, or reasoning provided?
- Clarity: is the answer well-structured?
- Accuracy: is the content correct / credible?

Return:
- score: integer 0-10 (0 = completely off-topic, 10 = perfect)
- strengths: 1-3 specific things the candidate did well
- improvements: 1-3 specific, actionable ways to improve the answer
- ideal_answer_hint: 1-2 sentence hint toward what a great answer would include
  (DO NOT copy the rubric verbatim — rephrase into coaching language)
""")


SUMMARY_PROMPT = ChatPromptTemplate.from_template("""
You are an interview coach summarising a completed mock interview session.

The candidate answered {num_questions} questions. Here are their scores and feedback:
{turns_json}

Write:
- overall_feedback: 2-3 sentences of honest, constructive overall assessment.
- top_strength: the single most impressive thing across all answers.
- top_improvement: the single most impactful improvement to make.

Be specific, not generic.
""")


# ── Internal helpers ───────────────────────────────────────────────────────

def _get_resume(resume_id: int, user_id: int, db: Session) -> Resume:
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume has not been parsed yet. Please re-upload.")
    return resume


def _call_with_fallback(chain, gemini_chain, inputs: dict):
    """Try primary chain; fall back to Gemini on failure. Returns (result, fallback_warning)."""
    try:
        return chain.invoke(inputs), None
    except Exception as e:
        warning = f"Primary model failed ({e}). Fell back to Gemini."
        return gemini_chain.invoke(inputs), warning


# ── Public service functions ───────────────────────────────────────────────

def start_mock_interview_service(
    resume_id: int,
    user_id: int,
    job_description: str | None,
    model_choice: str,
    num_questions: int,
    interview_type: str,
    db: Session,
) -> MockInterviewStartResponse:

    resume = _get_resume(resume_id, user_id, db)
    llm_result = get_llm(model_choice)

    # Build chains
    primary_chain = QUESTION_GENERATION_PROMPT | llm_result.llm.with_structured_output(QuestionList)
    fallback_chain = QUESTION_GENERATION_PROMPT | gemini_llm.with_structured_output(QuestionList)

    inputs = {
        "num_questions": num_questions,
        "interview_type": interview_type,
        "resume_text": resume.parsed_text,
        "job_description": job_description or "Not specified — base questions on the resume alone.",
    }

    result, fallback_warning = _call_with_fallback(primary_chain, fallback_chain, inputs)
    questions: List[GeneratedQuestion] = result.questions[:num_questions]

    if not questions:
        raise HTTPException(status_code=500, detail="LLM returned no questions. Please try again.")

    # Persist session
    session = MockInterviewSession(
        id=str(uuid.uuid4()),
        resume_id=resume_id,
        user_id=user_id,
        questions=[q.model_dump() for q in questions],
        turns=[],
        current_index=0,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    first_q = questions[0]

    return MockInterviewStartResponse(
        session_id=session.id,
        first_question=first_q.question,
        question_type=first_q.type,
        question_index=0,
        total_questions=len(questions),
        model_used=llm_result.model_used,
        fallback_warning=fallback_warning or llm_result.fallback_warning,
    )


def answer_mock_question_service(
    session_id: str,
    user_id: int,
    answer: str,
    model_choice: str,
    db: Session,
) -> QuestionFeedback:

    # Load + validate ownership
    session = db.query(MockInterviewSession).filter(
        MockInterviewSession.id == session_id,
        MockInterviewSession.user_id == user_id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found")
    if session.status == "complete":
        raise HTTPException(status_code=400, detail="This interview session is already complete")

    idx = session.current_index
    questions = session.questions  # list of dicts
    total = len(questions)

    if idx >= total:
        raise HTTPException(status_code=400, detail="No more questions in this session")

    current_q = questions[idx]
    llm_result = get_llm(model_choice)

    # Evaluate the answer
    eval_primary = ANSWER_EVALUATION_PROMPT | llm_result.llm.with_structured_output(AnswerEvaluation)
    eval_fallback = ANSWER_EVALUATION_PROMPT | gemini_llm.with_structured_output(AnswerEvaluation)

    eval_result, fallback_warning = _call_with_fallback(eval_primary, eval_fallback, {
        "question": current_q["question"],
        "ideal_answer": current_q["ideal_answer"],
        "candidate_answer": answer,
    })

    # Persist the turn
    turn = TurnResult(
        question=current_q["question"],
        answer=answer,
        score=eval_result.score,
        strengths=eval_result.strengths,
        improvements=eval_result.improvements,
        ideal_answer_hint=eval_result.ideal_answer_hint,
    )

    new_turns = list(session.turns) + [turn.model_dump()]
    new_index = idx + 1
    is_last = (new_index >= total)

    session.turns = new_turns
    session.current_index = new_index
    if is_last:
        session.status = "complete"

    db.commit()

    # Build response
    summary = None
    if is_last:
        summary = _build_summary(new_turns, total, llm_result)

    next_q = questions[new_index] if not is_last else None
    next_type = next_q["type"] if next_q else None

    return QuestionFeedback(
        score=eval_result.score,
        strengths=eval_result.strengths,
        improvements=eval_result.improvements,
        ideal_answer_hint=eval_result.ideal_answer_hint,
        next_question=next_q["question"] if next_q else None,
        next_question_type=next_type,
        question_index=idx,
        total_questions=total,
        is_complete=is_last,
        session_summary=summary,
        model_used=llm_result.model_used,
        fallback_warning=fallback_warning or llm_result.fallback_warning,
    )


def _build_summary(turns: list, num_questions: int, llm_result) -> SessionSummary:
    total_score = sum(t["score"] for t in turns)
    percentage = round((total_score / (num_questions * 10)) * 100)

    sum_primary = SUMMARY_PROMPT | llm_result.llm.with_structured_output(SummaryText)
    sum_fallback = SUMMARY_PROMPT | gemini_llm.with_structured_output(SummaryText)

    turns_summary = "\n\n".join(
        f"Q{i+1}: {t['question']}\nScore: {t['score']}/10\n"
        f"Strengths: {', '.join(t['strengths'])}\n"
        f"Improvements: {', '.join(t['improvements'])}"
        for i, t in enumerate(turns)
    )

    try:
        text_result = sum_primary.invoke({"num_questions": num_questions, "turns_json": turns_summary})
    except Exception:
        text_result = sum_fallback.invoke({"num_questions": num_questions, "turns_json": turns_summary})

    return SessionSummary(
        total_score=total_score,
        max_score=num_questions * 10,
        percentage=percentage,
        questions_answered=len(turns),
        overall_feedback=text_result.overall_feedback,
        top_strength=text_result.top_strength,
        top_improvement=text_result.top_improvement,
        turns=[TurnResult(**t) for t in turns],
    )
