from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models import Resume, ResumeAnalysis
from langchain_core.prompts import ChatPromptTemplate
from ai.llm import llm
from ai.ChatGpt5 import generate_ai_response
from schemas.ai_schema import AIReviewResponse, InterviewReport
import json


def review_resume_service(resume_id: int, user_id: int, db: Session):

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
You are an expert resume reviewer.

Evaluate the resume rigorously.

Return:
- A score from 0–100
- 3–5 strengths (specific)
- 3–5 weaknesses (critical)
- 3–5 suggestions (actionable)

Resume:
{resume}
"""
    )

    chain = prompt | llm.with_structured_output(AIReviewResponse)

    result = chain.invoke({
        "resume": resume.parsed_text
    })

    analysis = ResumeAnalysis(
        resume_id=resume.id,
        score=result.score,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        suggestions=result.suggestions
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return result


def evaluate_resume_service(resume_id: int, user_id: int, job_description: str, db: Session):

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

    chain = prompt | llm.with_structured_output(InterviewReport)

    result = chain.invoke({
        "resume": resume.parsed_text,
        "job_description": job_description
    })

    return result


#---Code for direct LLM call without langchain structured output---


# def evaluate_resume_service(
#     resume_id: int,
#     user_id: int,
#     job_description: str,
#     db: Session
# ):

#     resume = db.query(Resume).filter(
#         Resume.id == resume_id,
#         Resume.user_id == user_id
#     ).first()

#     if not resume:
#         raise HTTPException(
#             status_code=404,
#             detail="Resume not found"
#         )

#     if not resume.parsed_text:
#         raise HTTPException(
#             status_code=400,
#             detail="Resume text not parsed yet"
#         )

#     prompt = f"""
# You are an interview preparation assistant.

# Analyze the candidate resume and job description.

# Return ONLY valid JSON matching this schema:

# {InterviewReport.model_json_schema()}

# Resume:
# {resume.parsed_text}

# Job Description:
# {job_description}
# """

#     response = generate_ai_response(prompt)

#     try:
#         parsed = json.loads(response)
#     except json.JSONDecodeError:
#         raise HTTPException(
#             status_code=500,
#             detail="Model returned invalid JSON"
#         )

#     return parsed