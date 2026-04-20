from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import Resume
from services.pinecone_service import query_resume_embeddings
from ai.router import get_llm
from ai.llm import llm as gemini_llm
from schemas.chat_schema import ChatResponse


SYSTEM_PROMPT = """You are a helpful resume and career advisor assistant.

You have been given excerpts from an AI-generated resume analysis including strengths, weaknesses, suggestions, and interview preparation details.

Answer the user's question using the context as your primary source. However:
- If the user asks you to extend, expand, or build on something in the context (like extending a 7-day plan to 14 days), you SHOULD do it using your own knowledge as a career advisor.
- If the user asks general career advice related to their resume situation, answer helpfully.
- Only say you don't have enough information if the question is completely unrelated to resumes or career development.

Be concise, specific, and actionable."""


def chat_with_resume_service(
    resume_id: int,
    user_id: int,
    message: str,
    model_choice: str,
    db: Session
) -> ChatResponse:

    # 1. Verify the resume belongs to this user
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # 2. Pull relevant chunks from Pinecone
    #    query without type filter — searches across both review + evaluate chunks
    chunks = query_resume_embeddings(
        resume_id=resume_id,
        query=message,
        top_k=5
    )

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No analysis found for this resume. Please run /ai/review or /ai/evaluate first."
        )

    # 3. Build RAG context
    context = "\n\n---\n\n".join(chunks)

    full_prompt = f"""{SYSTEM_PROMPT}

--- CONTEXT START ---
{context}
--- CONTEXT END ---

User question: {message}"""

    # 4. Call LLM
    llm_result = get_llm(model_choice)

    try:
        response = llm_result.llm.invoke(full_prompt)
        answer = response.content
    except Exception as e:
        fallback_warning = f"GPT failed ({str(e)}). Fell back to Gemini."
        response = gemini_llm.invoke(full_prompt)
        answer = response.content
        llm_result.model_used = "gemini"
        llm_result.fallback_warning = fallback_warning

    return ChatResponse(
        answer=answer,
        model_used=llm_result.model_used,
        fallback_warning=llm_result.fallback_warning
    )