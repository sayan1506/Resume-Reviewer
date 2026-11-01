from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from db.models import Resume, ResumeAnalysis
from langchain_core.prompts import ChatPromptTemplate
from ai.router import invoke_with_fallback
from ai.context import UserContext, build_prompt_context, wrap_untrusted
from services.pinecone_service import store_resume_embeddings
from schemas.ai_schema import AIReviewResponse, InterviewReport, CoverLetterResponse


def review_resume_service(
    resume_id: int,
    user_id: int,
    model_choice: str,
    db: Session,
    user_ctx: UserContext | None = None,
    target_role: str | None = None,
    seniority: str | None = None,
):

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume not parsed yet")

    # Look this up before inserting the new row, so it really is the previous review.
    previous = _previous_review(db, resume.id, target_role, seniority)

    prompt = ChatPromptTemplate.from_template(
        """
{context}

You are an expert resume reviewer.

Evaluate the resume rigorously.
{target_clause}{seniority_clause}{consistency_clause}
Return:
- A score from 0-100
- 3-5 strengths (specific)
- 3-5 weaknesses (critical)
- 3-5 suggestions (actionable)

Resume:
{resume}
"""
    )

    invoke_result = invoke_with_fallback(
        model_choice,
        lambda llm: prompt | llm.with_structured_output(AIReviewResponse),
        {
            "resume": wrap_untrusted("resume", resume.parsed_text),
            "context": build_prompt_context(user_ctx, resume_text=resume.parsed_text),
            "target_clause": _target_role_clause(target_role),
            "seniority_clause": _seniority_clause(seniority),
            "consistency_clause": _consistency_clause(previous),
        },
    )
    raw = invoke_result.result

    # Keep prior analyses as version history — each review inserts a new row.
    # Latest analysis is always selected via order_by(created_at.desc()) elsewhere.
    analysis = ResumeAnalysis(
        resume_id=resume.id,
        score=raw.score,
        strengths=raw.strengths,
        weaknesses=raw.weaknesses,
        suggestions=raw.suggestions,
        target_role=target_role,
        seniority=seniority,
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Store embeddings in background — don't block the response
    combined_text = " ".join(raw.strengths + raw.weaknesses + raw.suggestions)
    _fire_and_forget_embeddings(resume.id, combined_text, "review")

    raw.model_used = invoke_result.model_used
    raw.fallback_warning = invoke_result.fallback_warning
    raw.target_role = target_role
    raw.seniority = seniority
    raw.previous_score = previous.score if previous else None

    return raw


def _previous_review(db: Session, resume_id: int, target_role: str | None, seniority: str | None):
    """Latest earlier review of this resume judged against the same role and level."""
    query = db.query(ResumeAnalysis).filter(ResumeAnalysis.resume_id == resume_id)
    if target_role:
        query = query.filter(func.lower(ResumeAnalysis.target_role) == target_role.lower())
    else:
        query = query.filter(ResumeAnalysis.target_role.is_(None))
    if seniority:
        query = query.filter(ResumeAnalysis.seniority == seniority)
    else:
        query = query.filter(ResumeAnalysis.seniority.is_(None))
    return query.order_by(ResumeAnalysis.created_at.desc()).first()


def _consistency_clause(previous) -> str:
    # A resume's text never changes after upload (a new upload is a new resume),
    # so a big score swing on a re-review is model noise, not a real difference.
    if not previous:
        return ""
    when = previous.created_at.strftime("%d %B %Y") if previous.created_at else "an earlier date"
    return (
        f"\nThis exact resume was reviewed before for the same target role and level, on {when}, "
        f"and scored {previous.score}/100. The resume text has not changed since. Keep the score "
        f"consistent: stay within about 5 points of {previous.score} unless you find a specific, "
        f"concrete reason the earlier score was wrong, and if you move it further, state that reason "
        f"in your feedback. Still judge the resume on its own merits and do not copy earlier feedback.\n"
    )


def _target_role_clause(target_role: str | None) -> str:
    if not target_role:
        return (
            "\nNo target role was given. Judge the resume for the kind of role its own "
            "experience and skills point to, and name that role in your feedback.\n"
        )
    return f"""
The candidate is targeting this role:
{wrap_untrusted("target_role", target_role)}
Score the resume for how well it positions the candidate for that role. Strengths and
weaknesses must be about fit for this role (relevant skills, experience, projects and
keywords that are present or missing), and suggestions must say what to add, cut or
reword to compete for it. If the role is far from the candidate's background, say so
plainly in the weaknesses rather than inflating the score.
"""


SENIORITY_GUIDANCE = {
    "fresher": (
        "a fresher (student or new graduate, under 1 year of work experience)",
        "Weigh education, internships, academic and personal projects, skills and "
        "certifications most. Do not penalise little or no full-time experience, a short "
        "resume, or listing CGPA and coursework. Expect a clear 1-page resume.",
    ),
    "junior": (
        "a junior professional (about 1-3 years of experience)",
        "Expect some real work experience with concrete contributions and early measurable "
        "results. Education and projects still count but should support the work history.",
    ),
    "mid": (
        "a mid-level professional (about 3-7 years of experience)",
        "Expect ownership of features or projects, quantified impact, depth in a core skill "
        "set and some collaboration or mentoring. Academic details should be brief.",
    ),
    "senior": (
        "a senior professional (7+ years of experience)",
        "Expect leadership, scope and strategic impact: owning systems or teams, cross-team "
        "influence, mentoring and business outcomes. Penalise a resume that reads like a list "
        "of tasks, or that gives early-career and academic details too much space.",
    ),
}


def _seniority_clause(seniority: str | None) -> str:
    if seniority not in SENIORITY_GUIDANCE:
        return (
            "\nNo seniority level was given. Infer it from the total work experience "
            "computed above (or from the resume if no total is listed), state the level you "
            "assumed in your feedback, and judge the resume against that level's expectations.\n"
        )
    who, expectations = SENIORITY_GUIDANCE[seniority]
    return (
        f"\nThe candidate describes themselves as {who}. Score the resume against what is "
        f"expected at that level, not against a more senior or more junior standard. "
        f"{expectations} If the resume clearly doesn't match this level, mention it as "
        f"feedback rather than changing the standard.\n"
    )


def evaluate_resume_service(resume_id: int, user_id: int, job_description: str, model_choice: str, db: Session, user_ctx: UserContext | None = None):

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume not parsed yet")

    prompt = ChatPromptTemplate.from_template(
        """
{context}

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

    invoke_result = invoke_with_fallback(
        model_choice,
        lambda llm: prompt | llm.with_structured_output(InterviewReport),
        {"resume": wrap_untrusted("resume", resume.parsed_text), "job_description": wrap_untrusted("job_description", job_description), "context": build_prompt_context(user_ctx, resume_text=resume.parsed_text)},
    )
    raw = invoke_result.result

    tech_q = " ".join([q.question + " " + q.answer for q in raw.technicalQuestions])
    behav_q = " ".join([q.question + " " + q.answer for q in raw.behavioralQuestions])
    skill_gaps = " ".join([s.skill for s in raw.skillGaps])
    prep = " ".join([f"Day {d.day}: {d.focus} " + " ".join(d.tasks) for d in raw.preparationPlan])
    combined_text = f"{raw.title} {tech_q} {behav_q} {skill_gaps} {prep}"
    _fire_and_forget_embeddings(resume.id, combined_text, "evaluate")

    raw.model_used = invoke_result.model_used
    raw.fallback_warning = invoke_result.fallback_warning

    return raw


TONE_GUIDANCE = {
    "professional": "Maintain a polished, formal, confident tone.",
    "enthusiastic": "Convey genuine excitement and energy while staying credible.",
    "concise": "Be tight and direct — short paragraphs, no filler.",
}


_COVER_LETTER_PROMPT = ChatPromptTemplate.from_template(
    """
{context}

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
    user_ctx: UserContext | None = None,
) -> CoverLetterResponse:

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=400, detail="Resume not parsed yet")

    inputs = {
        "tone_guidance": TONE_GUIDANCE.get(tone, TONE_GUIDANCE["professional"]),
        "resume": wrap_untrusted("resume", resume.parsed_text),
        "job_description": wrap_untrusted("job_description", job_description),
        "context": build_prompt_context(user_ctx, resume_text=resume.parsed_text),
    }

    invoke_result = invoke_with_fallback(
        model_choice,
        lambda llm: _COVER_LETTER_PROMPT | llm,
        inputs,
    )

    return CoverLetterResponse(
        cover_letter=invoke_result.result.content,
        model_used=invoke_result.model_used,
        fallback_warning=invoke_result.fallback_warning,
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