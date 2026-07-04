import uuid
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from db.models import Resume, MockInterviewSession
from ai.router import invoke_with_fallback
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

    inputs = {
        "num_questions": num_questions,
        "interview_type": interview_type,
        "resume_text": resume.parsed_text,
        "job_description": job_description or "Not specified — base questions on the resume alone.",
    }

    invoke_result = invoke_with_fallback(
        model_choice,
        lambda llm: QUESTION_GENERATION_PROMPT | llm.with_structured_output(QuestionList),
        inputs,
    )
    questions: List[GeneratedQuestion] = invoke_result.result.questions[:num_questions]

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
        model_used=invoke_result.model_used,
        fallback_warning=invoke_result.fallback_warning,
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

    # Evaluate the answer
    invoke_result = invoke_with_fallback(
        model_choice,
        lambda llm: ANSWER_EVALUATION_PROMPT | llm.with_structured_output(AnswerEvaluation),
        {
            "question": current_q["question"],
            "ideal_answer": current_q["ideal_answer"],
            "candidate_answer": answer,
        },
    )
    eval_result = invoke_result.result

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
        summary = _build_summary(new_turns, total, model_choice)

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
        model_used=invoke_result.model_used,
        fallback_warning=invoke_result.fallback_warning,
    )


def _build_summary(turns: list, num_questions: int, model_choice: str) -> SessionSummary:
    total_score = sum(t["score"] for t in turns)
    percentage = round((total_score / (num_questions * 10)) * 100)

    turns_summary = "\n\n".join(
        f"Q{i+1}: {t['question']}\nScore: {t['score']}/10\n"
        f"Strengths: {', '.join(t['strengths'])}\n"
        f"Improvements: {', '.join(t['improvements'])}"
        for i, t in enumerate(turns)
    )

    text_result = invoke_with_fallback(
        model_choice,
        lambda llm: SUMMARY_PROMPT | llm.with_structured_output(SummaryText),
        {"num_questions": num_questions, "turns_json": turns_summary},
    ).result

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
