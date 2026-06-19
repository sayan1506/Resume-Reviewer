from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models import Resume, ResumeAnalysis
from langchain_core.prompts import ChatPromptTemplate
from ai.router import get_llm
from services.pinecone_service import store_resume_embeddings
from schemas.ai_schema import AIReviewResponse, InterviewReport, CoverLetterResponse

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
    except Exception as primary_error:
        if llm_result.model_used != "gpt":
            raise HTTPException(
                status_code=502,
                detail="The AI model is currently unavailable. Please try again.",
            )
        chain = prompt | gemini_llm.with_structured_output(AIReviewResponse)
        try:
            raw = chain.invoke({"resume": resume.parsed_text})
        except Exception:
            raise HTTPException(
                status_code=502,
                detail="The AI model is currently unavailable. Please try again.",
            )
        llm_result.model_used = "gemini"
        llm_result.fallback_warning = f"GPT failed during generation ({primary_error}). Fell back to Gemini."

    # Keep prior analyses as version history — each review inserts a new row.
    # Latest analysis is always selected via order_by(created_at.desc()) elsewhere.
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
    except Exception as primary_error:
        if llm_result.model_used != "gpt":
            raise HTTPException(
                status_code=502,
                detail="The AI model is currently unavailable. Please try again.",
            )
        chain = prompt | gemini_llm.with_structured_output(InterviewReport)
        try:
            raw = chain.invoke({
                "resume": resume.parsed_text,
                "job_description": job_description
            })
        except Exception:
            raise HTTPException(
                status_code=502,
                detail="The AI model is currently unavailable. Please try again.",
            )
        llm_result.model_used = "gemini"
        llm_result.fallback_warning = f"GPT failed during generation ({primary_error}). Fell back to Gemini."

    tech_q = " ".join([q.question + " " + q.answer for q in raw.technicalQuestions])
    behav_q = " ".join([q.question + " " + q.answer for q in raw.behavioralQuestions])
    skill_gaps = " ".join([s.skill for s in raw.skillGaps])
    prep = " ".join([f"Day {d.day}: {d.focus} " + " ".join(d.tasks) for d in raw.preparationPlan])
    combined_text = f"{raw.title} {tech_q} {behav_q} {skill_gaps} {prep}"
    _fire_and_forget_embeddings(resume.id, combined_text, "evaluate")

    raw.model_used = llm_result.model_used
    raw.fallback_warning = llm_result.fallback_warning

    return raw


TONE_GUIDANCE = {
    "professional": "Maintain a polished, formal, confident tone.",
    "enthusiastic": "Convey genuine excitement and energy while staying credible.",
    "concise": "Be tight and direct — short paragraphs, no filler.",
}


_COVER_LETTER_PROMPT = ChatPromptTemplate.from_template(
    """
You are an expert career writer. Write a tailored cover letter for this candidate
applying to the role described in the job description.

Tone: {tone_guidance}

Rules:
- Ground every claim in the candidate's actual resume — never invent experience.
- Map the candidate's real strengths to the role's requirements.
- 3-4 short paragraphs: a hook, a body connecting experience to the role, and a closing call to action.
- Do NOT fabricate the company name, hiring manager, dates, or contact details. If the
  job description does not name the company, address it generically (e.g. "Dear Hiring Manager,").
- Output ONLY the cover letter body text. No preamble, no markdown, no placeholders like "[Your Name]"
  beyond a closing signature line.

Resume:
{resume}

Job Description:
{job_description}
"""
)


def cover_letter_service(
    resume_id: int,
    user_id: int,
    job_description: str,
    tone: str,
    model_choice: str,
    db: Session,
) -> CoverLetterResponse:

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume not parsed yet")

    llm_result = get_llm(model_choice)

    inputs = {
        "tone_guidance": TONE_GUIDANCE.get(tone, TONE_GUIDANCE["professional"]),
        "resume": resume.parsed_text,
        "job_description": job_description,
    }

    chain = _COVER_LETTER_PROMPT | llm_result.llm
    try:
        response = chain.invoke(inputs)
    except Exception as primary_error:
        if llm_result.model_used != "gpt":
            raise HTTPException(
                status_code=502,
                detail="The AI model is currently unavailable. Please try again.",
            )
        try:
            response = (_COVER_LETTER_PROMPT | gemini_llm).invoke(inputs)
        except Exception:
            raise HTTPException(
                status_code=502,
                detail="The AI model is currently unavailable. Please try again.",
            )
        llm_result.model_used = "gemini"
        llm_result.fallback_warning = f"GPT failed during generation ({primary_error}). Fell back to Gemini."

    return CoverLetterResponse(
        cover_letter=response.content,
        model_used=llm_result.model_used,
        fallback_warning=llm_result.fallback_warning,
    )


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