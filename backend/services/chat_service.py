import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.models import Resume, ChatSession
from services.pinecone_service import query_resume_embeddings
from ai.router import invoke_with_fallback
from schemas.chat_schema import ChatResponse


# Number of most recent turn entries (user/assistant lines) fed back into the prompt.
# Caps prompt size / LLM cost while preserving recent conversational context.
MAX_HISTORY_TURNS = 10


SYSTEM_PROMPT = """You are a helpful resume and career advisor assistant.

You have been given excerpts from an AI-generated resume analysis including strengths, weaknesses, suggestions, and interview preparation details.

Answer the user's question using the context as your primary source. However:
- If the user asks you to extend, expand, or build on something in the context (like extending a 7-day plan to 14 days), you SHOULD do it using your own knowledge as a career advisor.
- If the user asks general career advice related to their resume situation, answer helpfully.
- Use the conversation history to resolve follow-up questions (e.g. "what about the second one?") that refer to earlier messages.
- Only say you don't have enough information if the question is completely unrelated to resumes or career development.

Be concise, specific, and actionable."""


def chat_with_resume_service(
    resume_id: int,
    user_id: int,
    message: str,
    model_choice: str,
    db: Session,
    session_id: Optional[str] = None,
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

    # 3. Load existing session (scoped to this user + resume) or start a new one.
    #    A stale/mismatched session_id silently starts a fresh session.
    session = None
    if session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
            ChatSession.resume_id == resume_id,
        ).first()

    is_new_session = session is None
    if is_new_session:
        session = ChatSession(
            id=str(uuid.uuid4()),
            resume_id=resume_id,
            user_id=user_id,
            turns=[],
        )

    # 4. Build RAG context + recent conversation history
    context = "\n\n---\n\n".join(chunks)

    recent_turns = list(session.turns)[-MAX_HISTORY_TURNS:]
    if recent_turns:
        history_lines = [
            f"{'User' if t.get('role') == 'user' else 'Assistant'}: {t.get('content', '')}"
            for t in recent_turns
        ]
        history_block = "\n".join(history_lines)
        history_section = f"\n--- CONVERSATION HISTORY ---\n{history_block}\n--- END HISTORY ---\n"
    else:
        history_section = ""

    full_prompt = f"""{SYSTEM_PROMPT}

--- CONTEXT START ---
{context}
--- CONTEXT END ---
{history_section}
User question: {message}"""

    # 5. Call LLM
    invoke_result = invoke_with_fallback(model_choice, lambda llm: llm, full_prompt)
    answer = invoke_result.result.content

    # 6. Persist the exchange. Reassign turns (do not mutate) so SQLAlchemy
    #    detects the JSONB change. Only commit after a successful LLM answer,
    #    so a failed call never leaves an empty session behind.
    session.turns = list(session.turns) + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]
    if is_new_session:
        db.add(session)
    db.commit()

    return ChatResponse(
        answer=answer,
        session_id=session.id,
        model_used=invoke_result.model_used,
        fallback_warning=invoke_result.fallback_warning
    )
