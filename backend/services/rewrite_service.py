from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import Resume
from langchain_core.prompts import ChatPromptTemplate
from ai.router import get_llm
from ai.llm import llm as gemini_llm
from schemas.ai_schema import RewriteResponse, RewriteResult


_REWRITE_PROMPT = ChatPromptTemplate.from_template(
    """
You are an expert resume editor. Identify the weak bullet points in this resume
and rewrite them into stronger versions.

For each weak bullet you find:
- "original": the exact original bullet text from the resume.
- "improved": a rewritten version following the STAR method (Situation/Task,
  Action, Result) with concrete, quantified impact where plausible. Do NOT
  fabricate specific numbers the candidate could not have — if a metric is
  unknown, phrase it so the candidate can fill it in (e.g. "by X%").
- "rationale": one short sentence explaining what made the original weak and
  what the rewrite fixes.

Focus on the 5-8 highest-impact bullets (vague, passive, or unquantified).
Use strong action verbs. Keep each improved bullet to one or two lines.
{jd_clause}

Resume:
{resume}
"""
)


def rewrite_resume_service(resume_id: int, user_id: int, job_description, model_choice: str, db: Session) -> RewriteResponse:

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume not parsed yet")

    llm_result = get_llm(model_choice)

    if job_description and job_description.strip():
        jd_clause = (
            "Tailor the rewrites toward the following target job description, "
            f"emphasizing the most relevant skills:\n\n{job_description}"
        )
    else:
        jd_clause = ""

    inputs = {"resume": resume.parsed_text, "jd_clause": jd_clause}

    chain = _REWRITE_PROMPT | llm_result.llm.with_structured_output(RewriteResult)

    try:
        raw = chain.invoke(inputs)
    except Exception as primary_error:
        if llm_result.model_used not in ("gpt", "gpt5"):
            raise HTTPException(
                status_code=502,
                detail="The AI model is currently unavailable. Please try again.",
            )
        chain = _REWRITE_PROMPT | gemini_llm.with_structured_output(RewriteResult)
        try:
            raw = chain.invoke(inputs)
        except Exception:
            raise HTTPException(
                status_code=502,
                detail="The AI model is currently unavailable. Please try again.",
            )
        llm_result.model_used = "gemini"
        llm_result.fallback_warning = f"GPT failed during generation ({primary_error}). Fell back to Gemini."

    return RewriteResponse(
        bullets=raw.bullets,
        model_used=llm_result.model_used,
        fallback_warning=llm_result.fallback_warning,
    )
