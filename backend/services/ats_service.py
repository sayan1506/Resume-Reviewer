import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import Resume
from langchain_core.prompts import ChatPromptTemplate
from ai.router import get_llm
from ai.llm import llm as gemini_llm
from schemas.ai_schema import ATSCheckResponse, ATSCheckItem, ATSKeywordResult


SECTION_PATTERNS = {
    "Experience": r"(work\s+experience|professional\s+experience|employment|experience)",
    "Education": r"education",
    "Skills": r"(technical\s+skills|skills|competencies)",
    "Projects": r"projects",
    "Summary": r"(summary|objective|profile|about)",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s().\-]{7,}\d)")
BULLET_RE = re.compile(r"(^|\n)\s*[•\-\*•●‣⁃]\s+")

# Distinct date styles — mixing several hurts ATS date parsing.
DATE_STYLES = {
    "month_year": re.compile(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}\b",
        re.IGNORECASE,
    ),
    "numeric_slash": re.compile(r"\b\d{1,2}/\d{4}\b"),
    "numeric_dash": re.compile(r"\b\d{1,2}-\d{4}\b"),
    "year_only": re.compile(r"\b(19|20)\d{2}\b"),
}

_KEYWORD_PROMPT = ChatPromptTemplate.from_template(
    """
You are an ATS (Applicant Tracking System) keyword analyzer.

Compare the resume against the job description. Identify the important
skills/keywords from the job description and decide which appear in the resume
(treat close synonyms and obvious variants as matches, e.g. "JS" == "JavaScript").

Return:
- matchedKeywords: important JD keywords that DO appear in the resume
- missingKeywords: important JD keywords that are ABSENT from the resume

Resume:
{resume}

Job Description:
{job_description}
"""
)


def _run_deterministic_checks(text: str) -> tuple[list[ATSCheckItem], int]:
    checks: list[ATSCheckItem] = []
    lower = text.lower()

    # 1. Section detection
    found_sections = [
        name for name, pat in SECTION_PATTERNS.items()
        if re.search(pat, lower)
    ]
    missing_sections = [n for n in SECTION_PATTERNS if n not in found_sections]
    if len(found_sections) >= 4:
        checks.append(ATSCheckItem(
            label="Standard sections",
            status="pass",
            detail=f"Detected: {', '.join(found_sections)}.",
        ))
    elif len(found_sections) >= 2:
        checks.append(ATSCheckItem(
            label="Standard sections",
            status="warn",
            detail=f"Found {', '.join(found_sections)}. Consider adding clear headers for: {', '.join(missing_sections)}.",
        ))
    else:
        checks.append(ATSCheckItem(
            label="Standard sections",
            status="fail",
            detail="Few or no standard section headers detected. ATS relies on headers like Experience, Education, Skills.",
        ))

    # 2. Contact info
    has_email = bool(EMAIL_RE.search(text))
    has_phone = bool(PHONE_RE.search(text))
    if has_email and has_phone:
        checks.append(ATSCheckItem(
            label="Contact information",
            status="pass",
            detail="Both an email address and phone number were found.",
        ))
    elif has_email or has_phone:
        checks.append(ATSCheckItem(
            label="Contact information",
            status="warn",
            detail=f"Only {'email' if has_email else 'phone'} detected. Include both email and phone.",
        ))
    else:
        checks.append(ATSCheckItem(
            label="Contact information",
            status="fail",
            detail="No email or phone number detected. ATS may fail to route your application.",
        ))

    # 3. Date-format consistency
    used_styles = [name for name, pat in DATE_STYLES.items() if pat.search(text)]
    # year_only often co-occurs with month_year; only flag genuinely mixed explicit styles.
    explicit_styles = [s for s in used_styles if s != "year_only"]
    if len(explicit_styles) <= 1:
        checks.append(ATSCheckItem(
            label="Date formatting",
            status="pass",
            detail="Date formats look consistent.",
        ))
    else:
        checks.append(ATSCheckItem(
            label="Date formatting",
            status="warn",
            detail=f"Multiple date formats detected ({', '.join(explicit_styles)}). Pick one style (e.g. 'Jan 2023') throughout.",
        ))

    # 4. Bullet structure
    bullet_count = len(BULLET_RE.findall(text))
    if bullet_count >= 3:
        checks.append(ATSCheckItem(
            label="Bullet structure",
            status="pass",
            detail=f"{bullet_count} bullet points detected — good for parseable, scannable content.",
        ))
    else:
        checks.append(ATSCheckItem(
            label="Bullet structure",
            status="warn",
            detail="Few or no bullet points detected. Use bullets to list achievements for better parsing.",
        ))

    # 5. Length sanity
    word_count = len(text.split())
    if word_count < 200:
        checks.append(ATSCheckItem(
            label="Resume length",
            status="warn",
            detail=f"Only ~{word_count} words. This may be too sparse — aim for 400–800 words.",
        ))
    elif word_count > 1200:
        checks.append(ATSCheckItem(
            label="Resume length",
            status="warn",
            detail=f"~{word_count} words. This is long — consider tightening to 1–2 pages.",
        ))
    else:
        checks.append(ATSCheckItem(
            label="Resume length",
            status="pass",
            detail=f"~{word_count} words — a healthy length.",
        ))

    # Weighted parseability score
    weights = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
    score = round(sum(weights[c.status] for c in checks) / len(checks) * 100)
    return checks, score


def ats_check_service(resume_id: int, user_id: int, job_description, model_choice: str, db: Session) -> ATSCheckResponse:

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume not parsed yet")

    checks, parseability_score = _run_deterministic_checks(resume.parsed_text)

    matched_keywords: list[str] = []
    missing_keywords: list[str] = []
    model_used = None
    fallback_warning = None

    if job_description and job_description.strip():
        llm_result = get_llm(model_choice)
        model_used = llm_result.model_used
        fallback_warning = llm_result.fallback_warning

        chain = _KEYWORD_PROMPT | llm_result.llm.with_structured_output(ATSKeywordResult)
        inputs = {"resume": resume.parsed_text, "job_description": job_description}

        try:
            kw = chain.invoke(inputs)
        except Exception as primary_error:
            if llm_result.model_used not in ("gpt", "gpt5"):
                raise HTTPException(
                    status_code=502,
                    detail="The AI model is currently unavailable. Please try again.",
                )
            chain = _KEYWORD_PROMPT | gemini_llm.with_structured_output(ATSKeywordResult)
            try:
                kw = chain.invoke(inputs)
            except Exception:
                raise HTTPException(
                    status_code=502,
                    detail="The AI model is currently unavailable. Please try again.",
                )
            model_used = "gemini"
            fallback_warning = f"GPT failed during generation ({primary_error}). Fell back to Gemini."

        matched_keywords = kw.matchedKeywords
        missing_keywords = kw.missingKeywords

    return ATSCheckResponse(
        parseabilityScore=parseability_score,
        checks=checks,
        matchedKeywords=matched_keywords,
        missingKeywords=missing_keywords,
        model_used=model_used,
        fallback_warning=fallback_warning,
    )
