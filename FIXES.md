# Resume Reviewer — AI Agent Fix Guide

> **How to use this guide:** Work through each fix in order. Every fix specifies the exact file(s) to touch, what to change, and the complete replacement code. Do not skip fixes — some later fixes depend on earlier ones. After all fixes are applied, run the backend with `uvicorn main:app --reload` and the frontend with `npm run dev` and verify each section manually.

---

## Fix 1 — Remove Duplicate Database Setup

**Problem:** `backend/db/config.py` creates a second SQLAlchemy engine and `SessionLocal` that duplicates `backend/db/postgres.py`. Only `postgres.py` is used anywhere. `config.py` wastes a connection pool slot and is a maintenance trap.

**Action:** Delete `backend/db/config.py` entirely.

Then open `backend/db/pinecone_db.py` and replace the import at the top:

```python
# BEFORE
from .config import PINECONE_API_KEY, PINECONE_INDEX

# AFTER
import os
from dotenv import load_dotenv
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
```

Open `backend/db/supabase_storage.py` and replace the import:

```python
# BEFORE
from .config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET

# AFTER
import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")
```

---

## Fix 2 — File Double-Read Bug in Resume Upload

**Problem:** `backend/services/resumeUpload.py` reads `file.file` to extract PDF text, which moves the stream cursor to the end. When `upload_pdf` then calls `file.read()` again, it gets 0 bytes — every PDF stored in Supabase is empty.

**Action:** Replace the entire contents of `backend/services/resumeUpload.py`:

```python
from fastapi import HTTPException
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi import UploadFile

from db.supabase_storage import upload_pdf
from db.models import Resume
from utils.pdf_parser import extract_text_from_pdf


def upload_resume_service(file: UploadFile, user_id: int, db: Session):

    # Read once — reuse the bytes for both parsing and uploading
    file_bytes = file.file.read()

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Parse PDF text from bytes
    parsed_text = extract_text_from_pdf(file_bytes)

    filename = f"{uuid4()}.pdf"

    # Pass bytes directly — no re-reading the stream
    file_url = upload_pdf(file_bytes, filename)

    resume = Resume(
        user_id=user_id,
        file_url=file_url,
        parsed_text=parsed_text
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Do NOT return parsed_text — it is large and the client never uses it
    return {
        "resume_id": resume.id,
        "file_url": file_url,
        "message": "Resume uploaded successfully",
    }
```

Then update `backend/db/supabase_storage.py` to accept bytes instead of a file object:

```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_pdf(file_bytes: bytes, filename: str) -> str:
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path=filename,
        file=file_bytes,
        file_options={"content-type": "application/pdf"}
    )

    # Use the SDK's URL builder instead of manual string construction
    file_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)

    return file_url
```

---

## Fix 3 — Actually Call the PDF File Validator

**Problem:** `validate_pdf` is imported in `backend/routes/resume.py` but never invoked. Any non-PDF file passes through.

**Action:** In `backend/routes/resume.py`, add the validator call inside the upload route:

```python
# BEFORE
@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = upload_resume_service(
        file=file,
        user_id=current_user.id,
        db=db
    )
    return result

# AFTER
@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    validate_pdf(file)   # <-- add this line

    result = upload_resume_service(
        file=file,
        user_id=current_user.id,
        db=db
    )
    return result
```

---

## Fix 4 — Fix JWT Secret Being None at Startup

**Problem:** `backend/utils/auth_dependency.py` reads `JWT_SECRET` at module import time with `os.getenv`. If the env var is missing, `SECRET_KEY` is `None` and PyJWT silently accepts any token.

**Action:** Replace the entire contents of `backend/utils/auth_dependency.py`:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import os

from db.postgres import get_db
from db.models import User

ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()


def _get_secret_key() -> str:
    key = os.getenv("JWT_SECRET")
    if not key:
        raise RuntimeError("JWT_SECRET environment variable is not set")
    return key


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    secret = _get_secret_key()

    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
```

Also update `backend/utils/jwt_handler.py` to validate its env vars on first use:

```python
import jwt
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()


def create_access_token(data: dict) -> str:
    secret = os.getenv("JWT_SECRET")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    if not secret:
        raise RuntimeError("JWT_SECRET environment variable is not set")

    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload.update({"exp": expire})

    return jwt.encode(payload, secret, algorithm=algorithm)
```

---

## Fix 5 — Fix Deprecated `datetime.utcnow()` in Models

**Problem:** `backend/db/models.py` uses `datetime.utcnow` as a column default, which is deprecated in Python 3.12+ and will break in future versions.

**Action:** Replace the entire contents of `backend/db/models.py`:

```python
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from .postgres import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    resumes = relationship("Resume", back_populates="user")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_url = Column(String)
    parsed_text = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="resumes")
    analysis = relationship("ResumeAnalysis", back_populates="resume")


class ResumeAnalysis(Base):
    __tablename__ = "resume_analysis"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False
    )
    score = Column(Integer, nullable=False)
    strengths = Column(JSONB, nullable=False)
    weaknesses = Column(JSONB, nullable=False)
    suggestions = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="analysis")
```

---

## Fix 6 — Add `__init__.py` to All Backend Packages

**Problem:** `backend/services/`, `backend/utils/`, `backend/ai/`, and `backend/db/` have no `__init__.py`. This causes fragile implicit namespace package resolution.

**Action:** Create an empty `__init__.py` in each of these directories:

- `backend/services/__init__.py` — empty file
- `backend/utils/__init__.py` — empty file
- `backend/ai/__init__.py` — empty file
- `backend/db/__init__.py` — empty file (if not already present)

---

## Fix 7 — Remove Dead Code and Empty Files

**Problem:** `backend/ai/ChatGpt5.py` is entirely commented out. `backend/utils/embedding.py` is entirely commented out. `backend/routes/chat.py` contains only a comment. These confuse anyone reading the codebase.

**Action:**
- Delete `backend/utils/embedding.py`
- Delete `backend/routes/chat.py`
- Do NOT delete `backend/ai/ChatGpt5.py` — it will be repurposed in Fix 9 (model switcher)

---

## Fix 8 — Fix Text Chunker to Split on Word Boundaries

**Problem:** `backend/utils/text_chunker.py` splits text at fixed character indices, regularly cutting mid-word or mid-sentence, which degrades embedding quality.

**Action:** Replace the entire contents of `backend/utils/text_chunker.py`:

```python
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """
    Splits text into overlapping chunks on word boundaries.
    chunk_size and overlap are measured in characters (approximate).
    """
    words = text.split()
    chunks = []
    current_chars = 0
    current_words: list[str] = []
    overlap_words: list[str] = []

    for word in words:
        current_words.append(word)
        current_chars += len(word) + 1  # +1 for the space

        if current_chars >= chunk_size:
            chunk = " ".join(current_words)
            chunks.append(chunk)

            # Carry over the last `overlap` characters worth of words
            overlap_words = []
            overlap_chars = 0
            for w in reversed(current_words):
                overlap_chars += len(w) + 1
                overlap_words.insert(0, w)
                if overlap_chars >= overlap:
                    break

            current_words = overlap_words[:]
            current_chars = sum(len(w) + 1 for w in current_words)

    # Append any remaining words as the last chunk
    if current_words:
        chunks.append(" ".join(current_words))

    return chunks
```

---

## Fix 9 — Model Switcher (Gemini vs GPT per Request)

**Problem:** The AI model is hardcoded to Gemini. Users want to choose Gemini or GPT per request, with auto-fallback to Gemini (with a warning) if GPT hits its daily limit.

### Step A — Restore and clean `backend/ai/ChatGpt5.py`

Replace the entire contents of `backend/ai/ChatGpt5.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Lazy import so missing azure package doesn't crash the whole app
def get_gpt_client():
    try:
        from azure.ai.inference import ChatCompletionsClient
        from azure.core.credentials import AzureKeyCredential
    except ImportError:
        raise RuntimeError(
            "azure-ai-inference is not installed. "
            "Run: pip install azure-ai-inference"
        )

    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN environment variable is not set")

    return ChatCompletionsClient(
        endpoint="https://models.github.ai/inference",
        credential=AzureKeyCredential(GITHUB_TOKEN),
    )


GPT_MODEL = "openai/gpt-4o"
```

### Step B — Create `backend/ai/router.py` (new file)

This module is the single place that picks the LLM based on the user's choice, with fallback logic:

```python
"""
LLM Router — returns the correct LangChain-compatible LLM based on user's model choice.
Handles GPT rate-limit fallback to Gemini with a warning flag.
"""
import os
from dataclasses import dataclass
from typing import Literal

ModelChoice = Literal["gemini", "gpt"]


@dataclass
class LLMResult:
    llm: object          # LangChain LLM instance
    model_used: str      # "gemini" or "gpt"
    fallback_warning: str | None  # set if GPT was requested but Gemini used


def get_llm(model_choice: ModelChoice) -> LLMResult:
    """
    Returns the appropriate LLM.
    If GPT is chosen but unavailable (missing token, rate limit, import error),
    falls back to Gemini and sets fallback_warning.
    """
    from ai.llm import llm as gemini_llm  # always available

    if model_choice == "gemini":
        return LLMResult(llm=gemini_llm, model_used="gemini", fallback_warning=None)

    # Attempt GPT
    try:
        from langchain_community.chat_models import AzureChatOpenAI
        from ai.ChatGpt5 import get_gpt_client, GPT_MODEL
        import os

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise RuntimeError("GITHUB_TOKEN not set")

        # LangChain wrapper around the Azure inference endpoint
        from langchain_openai import AzureChatOpenAI as LCAzure
        gpt_llm = LCAzure(
            azure_endpoint="https://models.github.ai/inference",
            api_key=github_token,
            azure_deployment=GPT_MODEL,
            api_version="2024-05-01-preview",
            temperature=0.7,
        )
        return LLMResult(llm=gpt_llm, model_used="gpt", fallback_warning=None)

    except Exception as e:
        warning = (
            f"GPT is unavailable ({str(e)}). "
            "Your request was processed using Gemini instead."
        )
        return LLMResult(llm=gemini_llm, model_used="gemini", fallback_warning=warning)
```

### Step C — Update `backend/schemas/ai_schema.py`

Add `model` field to request schemas and `model_used` / `fallback_warning` to responses:

```python
from pydantic import BaseModel
from typing import List, Literal, Optional


# -------------------------
# REQUEST SCHEMAS
# -------------------------

class AIReviewRequest(BaseModel):
    resume_id: int
    model: Literal["gemini", "gpt"] = "gemini"


class AIEvaluationRequest(BaseModel):
    resume_id: int
    job_description: str
    model: Literal["gemini", "gpt"] = "gemini"


# -------------------------
# REVIEW RESPONSE SCHEMA
# -------------------------

class AIReviewResponse(BaseModel):
    score: int
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    model_used: Optional[str] = None
    fallback_warning: Optional[str] = None


# -------------------------
# INTERVIEW QUESTION MODELS
# -------------------------

class TechnicalQuestion(BaseModel):
    question: str
    intention: str
    answer: str


class BehavioralQuestion(BaseModel):
    question: str
    intention: str
    answer: str


# -------------------------
# SKILL GAP MODEL
# -------------------------

class SkillGap(BaseModel):
    skill: str
    severity: Literal["low", "medium", "high"]


# -------------------------
# PREPARATION PLAN
# -------------------------

class PreparationDay(BaseModel):
    day: int
    focus: str
    tasks: List[str]


# -------------------------
# INTERVIEW REPORT RESPONSE
# -------------------------

class InterviewReport(BaseModel):
    matchScore: int
    technicalQuestions: List[TechnicalQuestion]
    behavioralQuestions: List[BehavioralQuestion]
    skillGaps: List[SkillGap]
    preparationPlan: List[PreparationDay]
    title: str
    model_used: Optional[str] = None
    fallback_warning: Optional[str] = None
```

### Step D — Update `backend/services/ai_service.py`

Replace the entire file:

```python
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db.models import Resume, ResumeAnalysis
from langchain_core.prompts import ChatPromptTemplate
from ai.router import get_llm
from services.pinecone_service import store_resume_embeddings
from schemas.ai_schema import AIReviewResponse, InterviewReport
import asyncio


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
- A score from 0–100
- 3–5 strengths (specific)
- 3–5 weaknesses (critical)
- 3–5 suggestions (actionable)

Resume:
{resume}
"""
    )

    # Use only the core schema for structured output (no extra fields)
    class _CoreReview(AIReviewResponse):
        model_used: str | None = None
        fallback_warning: str | None = None

    chain = prompt | llm_result.llm.with_structured_output(AIReviewResponse.__bases__[0]
        if hasattr(AIReviewResponse, '__bases__') else AIReviewResponse)

    # Safer: build a minimal schema class for structured output
    from pydantic import BaseModel
    from typing import List

    class _ReviewOutput(BaseModel):
        score: int
        strengths: List[str]
        weaknesses: List[str]
        suggestions: List[str]

    chain = prompt | llm_result.llm.with_structured_output(_ReviewOutput)

    raw = chain.invoke({"resume": resume.parsed_text})

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

    return AIReviewResponse(
        score=raw.score,
        strengths=raw.strengths,
        weaknesses=raw.weaknesses,
        suggestions=raw.suggestions,
        model_used=llm_result.model_used,
        fallback_warning=llm_result.fallback_warning,
    )


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

    from pydantic import BaseModel
    from typing import List, Literal

    class _SkillGap(BaseModel):
        skill: str
        severity: Literal["low", "medium", "high"]

    class _TQ(BaseModel):
        question: str
        intention: str
        answer: str

    class _BQ(BaseModel):
        question: str
        intention: str
        answer: str

    class _Day(BaseModel):
        day: int
        focus: str
        tasks: List[str]

    class _EvalOutput(BaseModel):
        matchScore: int
        technicalQuestions: List[_TQ]
        behavioralQuestions: List[_BQ]
        skillGaps: List[_SkillGap]
        preparationPlan: List[_Day]
        title: str

    chain = prompt | llm_result.llm.with_structured_output(_EvalOutput)

    raw = chain.invoke({
        "resume": resume.parsed_text,
        "job_description": job_description
    })

    # Store embeddings in background
    tech_q = " ".join([q.question + " " + q.answer for q in raw.technicalQuestions])
    behav_q = " ".join([q.question + " " + q.answer for q in raw.behavioralQuestions])
    skill_gaps = " ".join([s.skill for s in raw.skillGaps])
    prep = " ".join([f"Day {d.day}: {d.focus} " + " ".join(d.tasks) for d in raw.preparationPlan])
    combined_text = f"{raw.title} {tech_q} {behav_q} {skill_gaps} {prep}"
    _fire_and_forget_embeddings(resume.id, combined_text, "evaluate")

    return InterviewReport(
        matchScore=raw.matchScore,
        technicalQuestions=raw.technicalQuestions,
        behavioralQuestions=raw.behavioralQuestions,
        skillGaps=raw.skillGaps,
        preparationPlan=raw.preparationPlan,
        title=raw.title,
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
```

### Step E — Update `backend/routes/ai.py`

Pass `model` from the request to the service:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.postgres import get_db
from db.models import User
from utils.auth_dependency import get_current_user

from services.ai_service import review_resume_service, evaluate_resume_service

from schemas.ai_schema import (
    AIReviewRequest,
    AIReviewResponse,
    AIEvaluationRequest,
    InterviewReport
)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/review", response_model=AIReviewResponse)
def ai_review(
    data: AIReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return review_resume_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        model_choice=data.model,
        db=db
    )


@router.post("/evaluate", response_model=InterviewReport)
def ai_evaluate(
    data: AIEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return evaluate_resume_service(
        resume_id=data.resume_id,
        user_id=current_user.id,
        job_description=data.job_description,
        model_choice=data.model,
        db=db
    )
```

### Step F — Add model selector to `frontend/src/pages/ReviewResults.jsx`

Add a model toggle at the top of the page. Replace the state declarations and add the selector UI:

```jsx
// Add to existing state declarations:
const [selectedModel, setSelectedModel] = useState('gemini');
const [fallbackWarning, setFallbackWarning] = useState('');

// Replace the useEffect fetch call body:
const fetchReview = async () => {
  try {
    const response = await api.post('/ai/review', {
      resume_id: parseInt(resumeId),
      model: selectedModel,
    });
    setResult(response.data);
    setFallbackWarning(response.data.fallback_warning || '');
  } catch (err) {
    setError(err.response?.data?.detail || 'Failed to fetch review');
  } finally {
    setLoading(false);
  }
};
```

Add this JSX block just before the loading spinner, after the results-header div:

```jsx
{/* Model Selector */}
<div className="model-selector">
  <label>AI Model:</label>
  <div className="model-toggle">
    <button
      className={`model-btn ${selectedModel === 'gemini' ? 'active' : ''}`}
      onClick={() => setSelectedModel('gemini')}
      type="button"
    >
      Gemini
    </button>
    <button
      className={`model-btn ${selectedModel === 'gpt' ? 'active' : ''}`}
      onClick={() => setSelectedModel('gpt')}
      type="button"
    >
      GPT-4o
    </button>
  </div>
  <button
    className="btn-action btn-review"
    onClick={() => { setLoading(true); setResult(null); setError(''); fetchReview(); }}
    type="button"
    disabled={loading}
  >
    {result ? 'Re-Review' : 'Run Review'}
  </button>
</div>

{fallbackWarning && (
  <div className="fallback-warning">
    ⚠️ {fallbackWarning}
  </div>
)}
```

**Important:** Remove the `useEffect` auto-fetch on mount. The user should click "Run Review" explicitly. Change the `useEffect` to only set `loading(false)` without fetching:

```jsx
// REMOVE the auto-fetch useEffect entirely.
// The page now starts empty and waits for the user to click "Run Review".
// Initialize loading as false:
const [loading, setLoading] = useState(false);
```

### Step G — Add model selector to `frontend/src/pages/Evaluate.jsx`

Add the same model toggle. In the existing state declarations add:

```jsx
const [selectedModel, setSelectedModel] = useState('gemini');
const [fallbackWarning, setFallbackWarning] = useState('');
```

In `handleSubmit`, update the API call:

```jsx
const response = await api.post('/ai/evaluate', {
  resume_id: parseInt(resumeId),
  job_description: jobDescription,
  model: selectedModel,        // <-- add this line
});
setResult(response.data);
setFallbackWarning(response.data.fallback_warning || '');
```

Add the same model toggle UI and fallback warning display as in Step F, inside the form section, before the submit button.

### Step H — Add CSS for new model selector UI

Add these classes to `frontend/src/index.css`:

```css
.model-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.model-toggle {
  display: flex;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border);
}

.model-btn {
  padding: 0.4rem 1rem;
  border: none;
  background: var(--surface);
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.875rem;
  transition: background 0.2s, color 0.2s;
}

.model-btn.active {
  background: var(--accent-start, #6366f1);
  color: #fff;
}

.fallback-warning {
  background: rgba(234, 179, 8, 0.1);
  border: 1px solid rgba(234, 179,8, 0.4);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #ca8a04;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}
```

---

## Fix 10 — Per-User Rate Limiting on AI Endpoints

**Problem:** `/ai/review` and `/ai/evaluate` have no throttle. A single user can spam expensive LLM calls.

### Step A — Install slowapi

Add to `backend/requirements.txt`:
```
slowapi==0.1.9
```

### Step B — Configure rate limiter in `backend/main.py`

Replace the entire contents of `backend/main.py`:

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routes import resume, auth
from routes import ai
import os

# Use user_id from JWT if available, else fall back to IP
def get_user_identifier(request: Request) -> str:
    # Try to extract user_id from the Authorization header without full DB lookup
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt
            token = auth_header.split(" ")[1]
            secret = os.getenv("JWT_SECRET", "")
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            return f"user:{payload.get('user_id', 'unknown')}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_identifier)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,https://resume-reviewer-navy.vercel.app"
    ).split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(resume.router, prefix="/resume", tags=["Resume"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(ai.router, prefix="", tags=["AI"])


@app.get("/")
def root():
    return {"status": "running"}
```

### Step C — Apply rate limit decorators in `backend/routes/ai.py`

Add to the existing route file (after imports):

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

# Import the limiter from main — or reuse the same instance
# Simpler: re-declare here and attach via app state in main.py
```

Add `@limiter.limit("10/hour")` decorator to both routes:

```python
# Add this import at the top of routes/ai.py
from main import limiter
from fastapi import Request

# Add Request parameter and decorator to each route:
@router.post("/review", response_model=AIReviewResponse)
@limiter.limit("10/hour")
def ai_review(
    request: Request,          # <-- required by slowapi
    data: AIReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ...

@router.post("/evaluate", response_model=InterviewReport)
@limiter.limit("10/hour")
def ai_evaluate(
    request: Request,          # <-- required by slowapi
    data: AIEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ...
```

---

## Fix 11 — Fix `pinecone_service.py` Shadowing Built-in `filter`

**Problem:** Variable named `filter` shadows Python's built-in in `backend/services/pinecone_service.py`.

**Action:** In `query_resume_embeddings`, rename the variable:

```python
# BEFORE
filter = {"resume_id": {"$eq": resume_id}}
if type:
    filter["type"] = {"$eq": type}
results = index.query(vector=query_vector, top_k=top_k, include_metadata=True, filter=filter)

# AFTER
query_filter = {"resume_id": {"$eq": resume_id}}
if type:
    query_filter["type"] = {"$eq": type}
results = index.query(vector=query_vector, top_k=top_k, include_metadata=True, filter=query_filter)
```

---

## Fix 12 — Remove Unused Import in `ai_service.py`

**Problem:** `from routes import resume` is at the top of `backend/services/ai_service.py` but never used. It also creates a circular import risk (service → route).

**Action:** Delete that import line from `backend/services/ai_service.py`.

---

## Fix 13 — Frontend Environment Variable for API Base URL

**Problem:** The backend URL is hardcoded in `frontend/src/api/axios.js`. Local dev always hits production.

### Step A — Update `frontend/src/api/axios.js`

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

// Attach JWT token for every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (!(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Show session-expired message then redirect on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.setItem(
        'session_expired',
        'Your session has expired. Please sign in again.'
      );
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Step B — Create `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
```

### Step C — Create `frontend/.env.production`

```env
VITE_API_URL=https://resume-reviewer-yqdp.onrender.com
```

### Step D — Add `.env` to `frontend/.gitignore`

Open `frontend/.gitignore` and add:
```
.env
.env.local
```

---

## Fix 14 — Show "Session Expired" Message on Login Page

**Problem:** When a 401 causes auto-logout, the user is just silently redirected to `/login` with no explanation.

**Action:** Update `frontend/src/pages/Login.jsx`. Add this block just after the existing state declarations and before `handleSubmit`:

```jsx
// Check for session expiry message set by axios interceptor
useEffect(() => {
  const msg = localStorage.getItem('session_expired');
  if (msg) {
    setError(msg);   // reuse the existing error state
    localStorage.removeItem('session_expired');
  }
}, []);
```

Add the import at the top:

```jsx
import { useState, useEffect } from 'react';
```

No other changes needed — the existing `{error && <div className="error-message">{error}</div>}` block already renders it.

---

## Fix 15 — Fix CORS Origins to Use Environment Variable

**Problem:** CORS allowed origins are hardcoded in `main.py`. Already fixed as part of Fix 10 — the `ALLOWED_ORIGINS` env var approach is in the new `main.py`.

**Action:** Add to `backend/.env` (and `.env.example`):

```env
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,https://resume-reviewer-navy.vercel.app
```

---

## Final Checklist

After applying all fixes, verify the following:

- [ ] `backend/db/config.py` is deleted
- [ ] `backend/utils/embedding.py` is deleted
- [ ] `backend/routes/chat.py` is deleted
- [ ] Empty `__init__.py` exists in `backend/services/`, `backend/utils/`, `backend/ai/`, `backend/db/`
- [ ] Upload a PDF → file in Supabase is not 0 bytes
- [ ] Upload a non-PDF → get 400 error
- [ ] Navigate to `/review/:id` → page does NOT auto-trigger LLM; user must click "Run Review"
- [ ] Select "GPT-4o" model → if `GITHUB_TOKEN` is missing, fallback warning appears
- [ ] Select "Gemini" model → review works normally
- [ ] Make 11 review requests in an hour → 11th gets a 429 rate limit error
- [ ] Let JWT expire → get redirected to login with "Your session has expired" message
- [ ] Local dev with `.env` uses `http://localhost:8000` not the production URL
- [ ] `datetime.utcnow` deprecation warning is gone from server logs

---

## Dependencies to Add to `backend/requirements.txt`

```
slowapi==0.1.9
langchain-openai>=0.1.0
```

## Dependencies to Add to `frontend/package.json` (none required)

All frontend changes use existing dependencies.
