# ResumeAI — AI-Powered Resume Reviewer

An intelligent resume analysis platform that gives you deep feedback, an ATS compatibility check, STAR-method bullet rewriting, job-description fit + interview prep, real job matching, tailored cover letters, a conversational AI assistant grounded in your resume review, turn-based mock interviews, and shareable public reports.

**Live Demo:** [resume-reviewer-navy.vercel.app](https://resume-reviewer-navy.vercel.app)

This is a monorepo. For component-level detail see:
- **Backend:** [`backend/README.md`](backend/README.md) — FastAPI service, API reference, DB schema, AI/RAG pipeline
- **Frontend:** [`frontend/README.md`](frontend/README.md) — React + Vite client, routing, pages, styling

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [API Routes](#api-routes)
- [AI Model Selection & Fallback](#ai-model-selection--fallback)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Deployment](#deployment)
- [How the Chat Works](#how-the-chat-works)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Development Notes](#development-notes)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Features

### Core Functionality

- **AI-Powered Resume Analysis** — Upload a PDF resume and receive:
  - Numerical score (0–100) evaluating overall quality
  - Detailed strengths highlighting what works well
  - Specific weaknesses identifying areas for improvement
  - Actionable suggestions for enhancement
  - Each review is saved as a new row, so score history is preserved over time

- **ATS Compatibility Check** — Score how well your resume parses through Applicant Tracking Systems:
  - A weighted parseability score (0–100) from deterministic checks
  - Standard-section detection (Experience, Education, Skills, Projects, Summary)
  - Contact-info, date-format consistency, bullet-structure, and length checks
  - Optional job-description keyword pass: matched vs. missing keywords (synonym-aware)

- **Bullet Point Rewriting** — Turn weak bullets into strong ones:
  - Identifies the 5–8 highest-impact bullets (vague, passive, or unquantified)
  - Rewrites each using the STAR method (Situation/Task, Action, Result)
  - Provides a short rationale explaining what the rewrite fixes
  - Optionally tailors rewrites toward a target job description

- **Job Description Fit & Interview Prep** — Paste any job description to get:
  - Match percentage showing alignment with the role
  - Technical interview questions tailored to the position
  - Behavioral interview questions for preparation
  - Skill gap analysis with severity ratings
  - Day-by-day preparation plan for interview success

- **Job Matching** — Discover real open roles that fit your resume:
  - Pulls live listings from public job boards (Remotive + Arbeitnow)
  - Ranks the pool against your resume using embedding cosine similarity
  - Returns the top matches with a per-job fit percentage, a "why it fits" note, and skill gaps
  - One failing source never sinks the request; results are de-duplicated by URL

- **Cover Letter Generation** — Produce a tailored cover letter:
  - Grounded strictly in your actual resume — no invented experience
  - Three selectable tones: professional, enthusiastic, or concise
  - Addresses the role from the job description (generic salutation if no company is named)

- **Conversational Resume Assistant** — Chat with an AI that:
  - Answers questions about your resume analysis
  - Uses semantic search (RAG) over your review data
  - Provides context-aware responses grounded in your specific analysis
  - Maintains multi-turn conversation history on the backend so follow-up questions resolve against earlier messages

- **Turn-Based Mock Interview** — Practice with an AI interviewer that:
  - Generates 1–10 questions from your resume (and optional job description)
  - Supports technical, behavioral, or mixed question types
  - Scores each answer 0–10 with specific strengths and improvements
  - Delivers a full end-of-session scorecard with overall feedback
  - Persists each session server-side so progress is tracked turn by turn

- **Shareable Reports** — Publish a read-only report:
  - Generates an unguessable public link (no login required to view)
  - Works for both review and evaluate reports
  - Export any report to PDF directly from the browser

### Technical Features

- **Triple AI Models with Automatic Fallback** — Choose between:
  - GPT-4o (default, via GitHub Models / Azure Inference)
  - Gemini 2.5 Flash (via Google AI)
  - GPT-5 (reasoning model, via GitHub Models)
  - The selected model is always tried first; on failure the request cascades through the others so every request gets full coverage

- **Secure Authentication** — Multiple auth options:
  - Email/password registration with JWT tokens
  - Google OAuth 2.0 (authorization code flow)
  - Automatic account linking for existing email users
  - Password reset request (with OAuth-only protection)

- **Smart Rate Limiting** — Protection against abuse:
  - User-based limits (not IP-based)
  - Clear error messages with `Retry-After` timing
  - Different limits for different endpoints

- **Vector-Powered Chat** — Advanced semantic search:
  - Embeddings stored in Pinecone (`gemini-embedding-001`)
  - RAG (Retrieval-Augmented Generation) for accurate responses
  - Background processing doesn't block API responses

---

## Quick Start

### Prerequisites Checklist

Before starting, ensure you have:
- [ ] Python 3.11 or higher
- [ ] Node.js 18 or higher
- [ ] A Supabase project (for PostgreSQL + Storage)
- [ ] A Pinecone account with an index created
- [ ] Google AI API key (for Gemini + embeddings)
- [ ] A GitHub Models token (for GPT-4o / GPT-5)
- [ ] Optional: Google OAuth credentials (for Google Sign-In)

### 5-Minute Setup

```bash
# 1. Clone the repo
git clone https://github.com/sayan1506/Resume-Reviewer.git
cd Resume-Reviewer

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
alembic upgrade head
uvicorn main:app --reload --port 8000 &

# 3. Frontend setup (in new terminal)
cd ../frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

Open `http://localhost:5173` and start analyzing resumes!

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL via Supabase (SQLAlchemy ORM) |
| Migrations | Alembic |
| File Storage | Supabase Storage |
| Vector Search | Pinecone |
| LLM Orchestration | LangChain (structured output + fallback chain) |
| Default LLM | GPT-4o via GitHub Models / Azure Inference |
| Alternate LLMs | Gemini 2.5 Flash (Google AI) · GPT-5 (GitHub Models) |
| Embeddings | `models/gemini-embedding-001` |
| Job Sources | Remotive + Arbeitnow public APIs |
| Ranking | NumPy cosine similarity over embeddings |
| PDF Parsing | PyMuPDF |
| Auth | PyJWT (HS256), Google OAuth 2.0 |
| Rate Limiting | slowapi (per-user) |
| Testing | pytest + Hypothesis (Property-Based Testing) |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 19 + Vite 8 |
| Routing | React Router DOM v7 |
| HTTP Client | Axios (with JWT interceptor) |
| File Upload | react-dropzone |
| OAuth | @react-oauth/google |
| PDF Export | jspdf + html2canvas |
| Icons | react-icons |
| Styling | Tailwind CSS v3 (Material Design 3 token theme) |
| Testing | Vitest + React Testing Library + jsdom |
| Deployment | Vercel |

---

## Architecture

```
Frontend (Vercel)
      │
      │  REST API (JWT Auth)
      ▼
FastAPI Backend
      │
      ├── PostgreSQL (Supabase)     ← source of truth: users, resumes, analysis,
      │                               shared reports, interview sessions, chat sessions
      ├── Supabase Storage          ← raw PDF files
      ├── Pinecone                  ← vector embeddings for chat + job ranking
      └── Job Boards (Remotive,     ← live listings for job matching
          Arbeitnow)

AI Pipeline:
  PDF Upload → PyMuPDF parse → stored in Postgres
  /ai/review        → LLM structured output → saved to ResumeAnalysis → embeddings → Pinecone (background)
  /ai/evaluate      → LLM structured output → embeddings → Pinecone (report not persisted in DB)
  /ai/ats-check     → deterministic checks (+ optional LLM JD keyword pass)
  /ai/rewrite       → LLM STAR-method bullet rewrites (optionally JD-tailored)
  /ai/job-match     → fetch job boards → embed + cosine rank → LLM per-job fit analysis
  /ai/cover-letter  → LLM cover letter grounded in resume (tone-controlled)
  /ai/chat          → embed question → query Pinecone → RAG prompt + history → LLM answer
  /ai/mock-interview/* → generate questions → persist session → score each answer → final summary
  /share/create     → snapshot report payload → public token → /shared/{token}
```

---

## API Routes

### Auth
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| POST | `/signup` | — | Register new user, returns JWT |
| POST | `/login` | — | Login, returns JWT |
| POST | `/google` | 5/min | Exchange Google auth code for JWT |
| POST | `/password-reset` | — | Request password reset (rejects OAuth-only accounts) |

### Resume
| Method | Endpoint | Description |
|---|---|---|
| POST | `/resume/upload` | Upload PDF, parse and store |
| GET | `/resume/list` | List all resumes with latest analysis |

### AI
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| POST | `/ai/review` | 10/hour | Score + strengths + weaknesses + suggestions |
| POST | `/ai/evaluate` | 10/hour | Job-description fit score + interview prep report |
| POST | `/ai/ats-check` | 10/hour | ATS parseability score + checks (+ optional JD keyword match) |
| POST | `/ai/rewrite` | 10/hour | STAR-method rewrites of weak bullets (optional JD tailoring) |
| POST | `/ai/job-match` | 10/hour | Rank live job listings against the resume with per-job fit analysis |
| POST | `/ai/cover-letter` | 10/hour | Tone-controlled cover letter grounded in the resume |
| POST | `/ai/chat` | 20/hour | Conversational Q&A over resume analysis (stateful) |

### Mock Interview
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| POST | `/ai/mock-interview/start` | 5/hour | Generate questions, create session, return first question |
| POST | `/ai/mock-interview/answer` | 30/hour | Score answer, return feedback + next question (or summary) |

### Share
| Method | Endpoint | Auth | Rate Limit | Description |
|---|---|---|---|---|
| POST | `/share/create` | required | 20/hour | Create/refresh a public link for a review or evaluate report |
| GET | `/share/{token}` | public | — | Fetch a shared report payload (no login) |

> Every AI endpoint accepts an optional `model` field (`"gpt"` · `"gemini"` · `"gpt5"`), defaulting to `"gpt"`. See below.

---

## AI Model Selection & Fallback

Every AI request may specify a `model`. The selected model is always tried **first**, then the request cascades through the remaining models in a fixed order so every request gets full coverage:

| Selected | Attempt order |
|---|---|
| `gpt` (default) | GPT-4o → Gemini → GPT-5 |
| `gemini` | Gemini → GPT-4o → GPT-5 |
| `gpt5` | GPT-5 → GPT-4o → Gemini |

| Key | Model | Provider / Endpoint | Auth |
|---|---|---|---|
| `gpt` | `gpt-4o` | GitHub Models (Azure Inference) | `GITHUB_TOKEN` |
| `gpt5` | `openai/gpt-5` | GitHub Models Inference | `GITHUB_TOKEN` |
| `gemini` | `gemini-2.5-flash` | Google AI | `GOOGLE_API_KEY` |

When a fallback occurs, the successful response includes a `fallback_warning` explaining which model was unavailable and which one served the request. If every model in the chain fails, the API returns `502`.

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Supabase project (PostgreSQL + Storage)
- A Pinecone account with an index created
- Google AI API key (Gemini + embeddings)
- GitHub Models token (for GPT-4o / GPT-5)

### Backend Setup

```bash
# 1. Clone and navigate to backend
git clone https://github.com/sayan1506/Resume-Reviewer.git
cd Resume-Reviewer/backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Fill in all values in .env (see Environment Variables section below)

# 5. Run database migrations (using Alembic)
alembic upgrade head

# Alternative: Create tables directly if migrations aren't set up
# python -c "from db.postgres import engine; from db.models import Base; Base.metadata.create_all(engine)"

# 6. Start the server
uvicorn main:app --reload --port 8000
```

Backend will be live at `http://localhost:8000`  
Swagger docs at `http://localhost:8000/docs`

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment
# Create .env file in the frontend root:
echo "VITE_API_URL=http://localhost:8000" > .env
echo "VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id" >> .env

# 4. Start dev server
npm run dev
```

Frontend will be live at `http://localhost:5173`

> **Important:** Always start the backend before the frontend. The frontend has no mock layer — all API calls go to the real backend.

---

## Environment Variables

### Backend (`.env`)

```env
# PostgreSQL (Note: use POSTGRES_URL, not DATABASE_URL)
POSTGRES_URL=postgresql+psycopg2://user:password@host:5432/dbname

# JWT Auth
JWT_SECRET=your_secure_random_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=resume-index

# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_BUCKET=resumes

# Google Generative AI (Gemini + embeddings)
GOOGLE_API_KEY=your_google_genai_api_key

# GitHub Models (GPT-4o and GPT-5)
GITHUB_TOKEN=your_github_models_token

# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback

# CORS (comma-separated list of allowed origins)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,https://resume-reviewer-navy.vercel.app

# Frontend base URL (used to build shareable report links)
FRONTEND_BASE_URL=https://resume-reviewer-navy.vercel.app
```

> **Note:** `GITHUB_TOKEN` powers both GPT-4o and GPT-5. If it is missing, those models are skipped and requests fall back to Gemini (which needs `GOOGLE_API_KEY`).

### Frontend (`.env` for development)

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id
```

### Frontend (`.env.production` for deployment)

```env
VITE_API_URL=https://your-deployed-backend-url.com
```

> **Note:** The frontend does not need `VITE_GOOGLE_CLIENT_ID` in production if it's already set in the main `.env` file.

---

## Testing

### Backend Testing

The backend includes tests using pytest and Hypothesis for property-based testing:

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_oauth_service.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run property-based tests (Hypothesis)
pytest tests/test_property_*.py
```

Test coverage includes:
- **OAuth Flow Tests**: Google OAuth code exchange, account linking, user creation
- **Property-Based Tests**: Account linking properties, duplicate Google ID handling, password reset prevention
- **Integration Tests**: End-to-end OAuth flow testing
- **Mock Interview Tests**: Session lifecycle and scoring
- **Unit Tests**: Auth service, config validation, incomplete profile rejection

### Frontend Testing

The frontend uses Vitest with React Testing Library:

```bash
cd frontend

# Run tests (single run)
npm run test

# Run tests with UI
npm run test -- --ui
```

---

## Deployment

### Backend

Deploy to any platform that supports Python (Railway, Render, Fly.io, etc.).

**Important Configuration:**
- Set environment variable as `POSTGRES_URL` (not `DATABASE_URL`)
- Make sure `ALLOWED_ORIGINS` includes your Vercel frontend URL
- Update `GOOGLE_REDIRECT_URI` to match your production frontend URL

**Example Environment Variables for Production:**
```env
POSTGRES_URL=postgresql+psycopg2://user:password@host:5432/dbname
ALLOWED_ORIGINS=https://resume-reviewer-navy.vercel.app
GOOGLE_REDIRECT_URI=https://resume-reviewer-navy.vercel.app/auth/google/callback
```

**Deployment Steps:**
1. Push backend code to GitHub
2. Create new project on your hosting platform (e.g., Render)
3. Connect the GitHub repository
4. Set all environment variables from the `.env.example` file
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Deploy

### Frontend (Vercel)

1. Push frontend to GitHub
2. Import the repo in Vercel
3. Set root directory to `frontend` (if deploying from monorepo)
4. Add environment variables in Vercel dashboard:
   ```
   VITE_API_URL=https://your-deployed-backend-url.com
   ```
   > **Note:** `VITE_GOOGLE_CLIENT_ID` should already be in your `.env` file, so it's not needed in Vercel unless you want to override it
5. Deploy — Vercel handles the rest

**Current Deployment:**
- Frontend: Vercel at [resume-reviewer-navy.vercel.app](https://resume-reviewer-navy.vercel.app)
- Backend: Render (API endpoint not publicly exposed). The frontend pings `/health` on load to mitigate cold starts.

---

## How the Chat Works

The chat feature uses **Retrieval-Augmented Generation (RAG)**:

1. When you run `/ai/review` or `/ai/evaluate`, the analysis text is chunked and embedded using `gemini-embedding-001`
2. Embeddings are stored in Pinecone in a background thread — this does not block the API response
3. When you send a chat message, it is embedded and used to query Pinecone for the top 5 most relevant chunks
4. Those chunks are injected into a prompt as context, and the LLM answers grounded in your specific analysis
5. Conversation is stateful on the backend — each exchange is persisted to a `ChatSession` (turns stored as JSONB), and the most recent turns (`MAX_HISTORY_TURNS = 10`) are replayed into the prompt so follow-up questions like "what about the second one?" resolve against earlier messages. Pass the returned `session_id` back on the next request to continue a conversation; omitting it (or passing a stale/mismatched id) starts a fresh session

> **Note:** Chat only works after running at least one `/ai/review` or `/ai/evaluate` on a resume. The Chat button on the dashboard is disabled until analysis exists.

### Mock Interview (stateful)

Unlike a stateless request, the mock interview is **stateful on the backend**. `/ai/mock-interview/start` generates the full question set, stores it in `mock_interview_sessions` (including a private `ideal_answer` rubric per question that is never sent to the client), and returns the first question. Each `/ai/mock-interview/answer` call scores the answer against the rubric, appends the turn, advances the session, and — on the last question — returns a full scorecard summary.

---

## Project Structure

```
backend/
├── main.py                   # FastAPI app, CORS, router mounting, /health
├── ai/
│   ├── llm.py                # Gemini 2.5 Flash client
│   ├── router.py             # Model selection + fallback chain (gpt/gemini/gpt5)
│   └── ChatGpt5.py           # Azure inference client (legacy, unused in active pipeline)
├── db/
│   ├── models.py             # SQLAlchemy models: User, Resume, ResumeAnalysis,
│   │                         #   SharedReport, MockInterviewSession, ChatSession
│   ├── postgres.py           # DB engine + session factory
│   ├── pinecone_db.py        # Pinecone index client
│   └── supabase_storage.py   # Supabase Storage client
├── routes/
│   ├── auth.py               # /signup, /login, /google, /password-reset
│   ├── resume.py             # /resume/upload, /resume/list
│   ├── ai.py                 # /ai/review, /evaluate, /ats-check, /rewrite,
│   │                         #   /job-match, /cover-letter, /chat
│   ├── mock_interview.py     # /ai/mock-interview/start, /answer
│   └── share.py              # /share/create, /share/{token}
├── services/
│   ├── auth_service.py            # Signup/login/password-reset business logic
│   ├── oauth_service.py           # Google OAuth code exchange + user linking
│   ├── resumeUpload.py            # PDF upload + parse pipeline
│   ├── pdf_parser_service.py      # PDF text extraction helpers
│   ├── ai_service.py              # Review + evaluate + cover-letter orchestration
│   ├── ats_service.py             # Deterministic ATS checks + JD keyword pass
│   ├── rewrite_service.py         # STAR-method bullet rewriting
│   ├── job_match_service.py       # Job-board fetch + cosine ranking + fit analysis
│   ├── chat_service.py            # Stateful RAG chat logic
│   ├── mock_interview_service.py  # Question generation + answer scoring + summary
│   ├── share_service.py           # Public share token + report retrieval
│   └── pinecone_service.py        # Embedding store + query + batch embed
├── schemas/
│   ├── auth_schema.py
│   ├── resume_schema.py
│   ├── ai_schema.py               # Review, evaluate, cover-letter, ATS, rewrite, job-match models
│   ├── chat_schema.py             # Chat request/response models
│   ├── mock_interview_schema.py   # Mock interview request/response models
│   └── share_schema.py            # Share request/response models
├── migrations/versions/           # 001 oauth cols · 002 mock sessions · 003 chat sessions
└── utils/
    ├── auth_dependency.py    # JWT bearer dependency
    ├── jwt_handler.py        # Token creation
    ├── oauth_config.py       # Google OAuth configuration + startup validation
    ├── rate_limiter.py       # slowapi config (rate by user_id)
    ├── security.py           # Password hashing (pbkdf2_sha256)
    ├── text_chunker.py       # Word-boundary chunking for embeddings
    ├── pdf_parser.py         # PDF parsing helpers
    └── file_validator.py     # PDF MIME type validation

frontend/
├── src/
│   ├── api/axios.js          # Axios instance + JWT + 401 interceptors
│   ├── context/AuthContext.jsx
│   ├── App.jsx               # Routes
│   ├── components/
│   │   ├── Navbar.jsx
│   │   ├── ProtectedRoute.jsx
│   │   ├── ShareModal.jsx          # Public share-link dialog
│   │   ├── ScoreTrend.jsx          # Score history trend visualization
│   │   ├── InterviewScoreCard.jsx  # Per-answer mock interview feedback
│   │   └── InterviewSummary.jsx    # End-of-interview scorecard
│   ├── pages/
│   │   ├── LandingPage.jsx
│   │   ├── Login.jsx
│   │   ├── Signup.jsx
│   │   ├── Dashboard.jsx           # Upload + resume list + analysis preview
│   │   ├── ReviewResults.jsx       # AI review output
│   │   ├── Evaluate.jsx            # JD fit + interview prep + share + PDF export
│   │   ├── ATSCheck.jsx            # ATS compatibility report
│   │   ├── Rewrite.jsx             # Bullet rewriting
│   │   ├── JobMatch.jsx            # Job matching results
│   │   ├── CoverLetter.jsx         # Cover letter generator
│   │   ├── ChatPage.jsx            # Conversational chat + mock interview
│   │   └── SharedReportPage.jsx    # Public, no-auth shared report view
│   ├── utils/exportPDF.js          # html2canvas + jsPDF export
│   └── index.css                   # Tailwind layers + custom component styles
└── tailwind.config.js              # Material Design 3 token theme
```

---

## Database Schema

```sql
users
  id            SERIAL PRIMARY KEY
  email         VARCHAR UNIQUE
  password      VARCHAR NULL         -- pbkdf2_sha256 hashed (NULL for OAuth-only users)
  google_id     VARCHAR(255) UNIQUE NULL  -- Google sub ID for OAuth linking (indexed)
  avatar_url    TEXT NULL            -- Google profile picture URL
  auth_provider VARCHAR(50) DEFAULT 'email'  -- 'email' or 'google'
  created_at    TIMESTAMPTZ

resumes
  id          SERIAL PRIMARY KEY
  user_id     INTEGER REFERENCES users(id)
  file_url    VARCHAR              -- Supabase Storage public URL
  parsed_text TEXT                 -- extracted by PyMuPDF
  uploaded_at TIMESTAMPTZ

resume_analysis
  id          SERIAL PRIMARY KEY
  resume_id   INTEGER REFERENCES resumes(id) ON DELETE CASCADE
  score       INTEGER
  strengths   JSONB
  weaknesses  JSONB
  suggestions JSONB
  created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()  -- new row per review (score history)

shared_reports
  id          SERIAL PRIMARY KEY
  token       VARCHAR(64) UNIQUE       -- secrets.token_urlsafe(32), indexed
  report_type VARCHAR(20)              -- 'review' | 'evaluate'
  resume_id   INTEGER REFERENCES resumes(id) ON DELETE CASCADE
  user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE
  payload     JSONB                    -- frozen report snapshot rendered on the public page
  created_at  TIMESTAMPTZ DEFAULT NOW()
  expires_at  TIMESTAMPTZ NULL

mock_interview_sessions
  id            VARCHAR(36) PRIMARY KEY  -- uuid4
  resume_id     INTEGER REFERENCES resumes(id) ON DELETE CASCADE
  user_id       INTEGER REFERENCES users(id) ON DELETE CASCADE
  questions     JSONB                    -- [{question, type, ideal_answer}] (ideal_answer never sent to client)
  turns         JSONB                    -- appended per answer: {question, answer, score, strengths, improvements, ideal_answer_hint}
  current_index INTEGER DEFAULT 0
  status        VARCHAR(20) DEFAULT 'active'  -- 'active' | 'complete'
  created_at    TIMESTAMPTZ DEFAULT NOW()

chat_sessions
  id          VARCHAR(36) PRIMARY KEY  -- uuid4
  resume_id   INTEGER REFERENCES resumes(id) ON DELETE CASCADE
  user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE
  turns       JSONB                    -- [{role: 'user'|'assistant', content: str}]
  created_at  TIMESTAMPTZ DEFAULT NOW()
```

---

## Development Notes

### Database Migrations with Alembic

This project uses Alembic for database schema migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

Existing migrations: `001` OAuth columns on users · `002` mock interview sessions · `003` chat sessions.

### Rate Limiting

The API implements user-based rate limiting using slowapi:
- `/ai/review`, `/ai/evaluate`, `/ai/ats-check`, `/ai/rewrite`, `/ai/job-match`, `/ai/cover-letter`: 10 requests per hour per user
- `/ai/chat`: 20 requests per hour per user
- `/ai/mock-interview/start`: 5 requests per hour per user
- `/ai/mock-interview/answer`: 30 requests per hour per user
- `/share/create`: 20 requests per hour per user
- `/google` (OAuth): 5 requests per minute (to prevent abuse)

Rate limit responses include a `Retry-After` header (60 seconds).

### File Validation

PDF uploads are validated using:
- MIME type checking (`application/pdf`)
- File extension validation
- Handled by `utils/file_validator.py`

### OAuth Flow

1. Frontend initiates OAuth with Google
2. Google redirects back with authorization code
3. Frontend sends code to `/google`
4. Backend exchanges code for user info
5. Backend finds or creates user (with account linking)
6. Backend returns JWT token
7. Frontend stores token and redirects to dashboard

---

## Known Limitations

- Chat history is capped at the most recent `MAX_HISTORY_TURNS = 10` turns per session; older turns are dropped from the prompt (though still persisted).
- PDF parsing is text-only. Scanned PDFs or image-heavy resumes may parse poorly.
- GPT-4o / GPT-5 availability depends on GitHub Models rate limits. Gemini is always in the fallback chain.
- Job matching depends on external job-board APIs (Remotive, Arbeitnow). If both sources are down, the endpoint returns `503`.
- `/ai/evaluate` results are not persisted server-side, so sharing an evaluate report sends the rendered payload from the client.
- Google OAuth account linking is one-way — once linked, there's no UI to unlink a Google account.
- Password reset for OAuth-only users (no password set) is rejected with a clear error message.

---

## Troubleshooting

### Common Issues

**Backend won't start / Database connection errors**
- Verify `POSTGRES_URL` is set correctly (not `DATABASE_URL`)
- Ensure PostgreSQL is running and accessible
- Check that database exists and credentials are correct

**Frontend can't connect to backend**
- Verify backend is running on `http://localhost:8000`
- Check `VITE_API_URL` in frontend `.env` file
- Verify CORS settings in backend allow your frontend origin

**AI requests failing / unexpected model used**
- Ensure `GITHUB_TOKEN` (for GPT-4o/GPT-5) and `GOOGLE_API_KEY` (for Gemini) are set
- A `fallback_warning` in the response means the preferred model was unavailable and a fallback served the request
- A `502` means every model in the chain failed — check API keys and provider status

**Google OAuth not working**
- Ensure `GOOGLE_CLIENT_ID` matches in both frontend `.env` and backend `.env`
- Verify `GOOGLE_REDIRECT_URI` is correctly configured in Google Cloud Console
- Check that OAuth consent screen is properly configured

**Rate limit errors**
- Wait for the time specified in the `Retry-After` header (60 seconds)
- Rate limits are per-user, not global

**PDF upload fails**
- Verify file is a valid PDF (not scanned image)
- Check file size (large files may timeout)
- Ensure Supabase Storage bucket exists and is accessible

**Pinecone/Vector search not working**
- Verify `PINECONE_API_KEY` and `PINECONE_INDEX` are correct
- Ensure Pinecone index has correct dimensions (matches embedding model)
- Check that embeddings are being stored (background thread may have failed)

**Job matching returns 503**
- Both Remotive and Arbeitnow were unreachable; retry shortly

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure nothing broke
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Backend: Follow PEP 8 guidelines
- Frontend: Follow the existing ESLint configuration
- Write tests for new features
- Update documentation as needed

---

## License

This project is open source and available under the MIT License.

---

## Contact

**Author:** Sayan Mondal  
**GitHub:** [@sayan1506](https://github.com/sayan1506)  
**Live Demo:** [resume-reviewer-navy.vercel.app](https://resume-reviewer-navy.vercel.app)
