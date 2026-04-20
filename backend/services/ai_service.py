from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models import Resume, ResumeAnalysis
from langchain_core.prompts import ChatPromptTemplate
from ai.router import get_llm
from services.pinecone_service import store_resume_embeddings
from schemas.ai_schema import AIReviewResponse, InterviewReport

from ai.llm import llm as gemini_llm


def review_resume_service(resume_id: int, user_id: int, model_choice: str, db: Session):

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume not parsed yet")

    llm_result = get_llm(model_choice)

    prompt = ChatPromptTemplate.from_template(
        """
You are an expert resume reviewer.

Evaluate the resume rigorously.

Return:
- A score from 0-100
- 3-5 strengths (specific)
- 3-5 weaknesses (critical)
- 3-5 suggestions (actionable)

Resume:
{resume}
"""
    )

    chain = prompt | llm_result.llm.with_structured_output(AIReviewResponse)

    try:
        raw = chain.invoke({"resume": resume.parsed_text})
    except Exception as e:
        fallback_warning = f"GPT failed during generation ({str(e)}). Fell back to Gemini."
        chain = prompt | gemini_llm.with_structured_output(AIReviewResponse)
        raw = chain.invoke({"resume": resume.parsed_text})
        llm_result.model_used = "gemini"
        llm_result.fallback_warning = fallback_warning

    # Delete existing analysis for this resume to avoid duplicates
    db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume.id).delete()

    analysis = ResumeAnalysis(
        resume_id=resume.id,
        score=raw.score,
        strengths=raw.strengths,
        weaknesses=raw.weaknesses,
        suggestions=raw.suggestions
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Store embeddings in background — don't block the response
    combined_text = " ".join(raw.strengths + raw.weaknesses + raw.suggestions)
    _fire_and_forget_embeddings(resume.id, combined_text, "review")

    raw.model_used = llm_result.model_used
    raw.fallback_warning = llm_result.fallback_warning

    return raw


def evaluate_resume_service(resume_id: int, user_id: int, job_description: str, model_choice: str, db: Session):

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume not parsed yet")

    llm_result = get_llm(model_choice)

    prompt = ChatPromptTemplate.from_template(
        """
You are an interview preparation assistant.

Analyze the candidate resume and the job description.

Generate a structured interview preparation report including:
- Key focus areas
- Likely interview questions
- Weak areas to prepare
- Suggested answers/topics

Resume:
{resume}

Job Description:
{job_description}
"""
    )

    chain = prompt | llm_result.llm.with_structured_output(InterviewReport)

    try:
        raw = chain.invoke({
            "resume": resume.parsed_text,
            "job_description": job_description
        })
    except Exception as e:
        from ai.llm import llm as gemini_llm
        fallback_warning = f"GPT failed during generation ({str(e)}). Fell back to Gemini."
        chain = prompt | gemini_llm.with_structured_output(InterviewReport)
        raw = chain.invoke({
            "resume": resume.parsed_text,
            "job_description": job_description
        })
        llm_result.model_used = "gemini"
        llm_result.fallback_warning = fallback_warning

    tech_q = " ".join([q.question + " " + q.answer for q in raw.technicalQuestions])
    behav_q = " ".join([q.question + " " + q.answer for q in raw.behavioralQuestions])
    skill_gaps = " ".join([s.skill for s in raw.skillGaps])
    prep = " ".join([f"Day {d.day}: {d.focus} " + " ".join(d.tasks) for d in raw.preparationPlan])
    combined_text = f"{raw.title} {tech_q} {behav_q} {skill_gaps} {prep}"
    _fire_and_forget_embeddings(resume.id, combined_text, "evaluate")

    raw.model_used = llm_result.model_used
    raw.fallback_warning = llm_result.fallback_warning

    return raw


def _fire_and_forget_embeddings(resume_id: int, text: str, embed_type: str):
    """
    Stores embeddings in Pinecone in a background thread.
    DB is already committed before this runs — eventual consistency.
    If Pinecone fails, the DB row is kept and the error is logged.
    """
    import threading

    def _store():
        try:
            store_resume_embeddings(resume_id, text, type=embed_type)
        except Exception as e:
            # Log the error but do not crash the request
            print(f"[WARNING] Pinecone embedding failed for resume {resume_id}: {e}")

    thread = threading.Thread(target=_store, daemon=True)
    thread.start()