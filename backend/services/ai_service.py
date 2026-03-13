from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models import Resume
from langchain_core.prompts import ChatPromptTemplate
from ai.llm import llm
from schemas.ai_schema import AIReviewResponse, InterviewReport


def review_resume_service(resume_id: int, user_id: int, db: Session):

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_text = resume.parsed_text

    prompt = ChatPromptTemplate.from_template(
        """
You are an expert resume reviewer.

Analyze the following resume and provide structured feedback.

Resume:
{resume}
"""
    )

    chain = prompt | llm.with_structured_output(AIReviewResponse)

    result = chain.invoke({
        "resume": resume_text
    })

    return result



def evaluate_resume_service(resume_id: int, user_id: int, job_description: str, db: Session):

    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    if not resume.parsed_text:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_text = resume.parsed_text

    prompt = ChatPromptTemplate.from_template(
        """
You are an interview preparation assistant.

Analyze the candidate resume and the job description.

Generate a detailed interview preparation report.

Resume:
{resume}

Job Description:
{job_description}
"""
    )

    chain = prompt | llm.with_structured_output(InterviewReport)

    result = chain.invoke({
        "resume": resume_text,
        "job_description": job_description
    })

    return result