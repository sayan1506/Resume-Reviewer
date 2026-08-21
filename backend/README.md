# ResumeAI — Backend

FastAPI service that powers the ResumeAI platform: PDF resume parsing, LLM-driven resume review and job-match evaluation, a RAG chat assistant, turn-based mock interviews, public report sharing, and JWT/Google OAuth authentication.

> Part of the [ResumeAI monorepo](../README.md). For the React client, see [`../frontend/README.md`](../frontend/README.md).

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [AI Pipeline & RAG](#ai-pipeline--rag)
- [Mock Interview](#mock-interview)
- [Report Sharing](#report-sharing)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn / Gunicorn |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL (via Supabase) |
| Migrations | Alembic |
| File Storage | Supabase Storage |
| Vector Search | Pinecone |
| Primary LLM | Gemini 2.5 Flash (`langchain-google-genai`) |
| Secondary LLM | GPT-4o via GitHub Models / Azure Inference (`langchain-openai`) |
| Embeddings | `models/gemini-embedding-001` |
| PDF Parsing | PyMuPDF |
| Auth | PyJWT (HS256), Google OAuth 2.0 (authorization code flow) |
| Rate Limiting | slowapi (keyed per authenticated user) |
| Testing | pytest + Hypothesis (property-based testing) |

---

## Quick Start

```bash
cd backend

# 1. Virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Dependencies
pip install -r requirements.txt

# 3. Environment
cp .env.example .env
# Fill in every value (see Environment Variables below)

# 4. Apply migrations
alembic upgrade head

# 5. Run the server
uvicorn main:app --reload --port 8000
```

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `GET /health` → `{"status": "ok"}`

OAuth configuration is validated at startup via `validate_oauth_config()` — the app will surface a clear error if the Google OAuth env vars are misconfigured.

---

## Environment Variables

Defined in `.env` (template in `.env.example`):

```env
# Database — NOTE: the variable is POSTGRES_URL, not DATABASE_URL
POSTGRES_URL=postgresql+psycopg2://user:password@host:5432/dbname

# JWT Auth
JWT_SECRET=replace_with_secure_random_value
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=resume-index

# Supabase Storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_BUCKET=resumes

# GitHub Models (GPT-4o via Azure Inference) — optional; falls back to Gemini if missing
GITHUB_TOKEN=your_github_models_token

# Google Generative AI (Gemini)
GOOGLE_API_KEY=your_google_genai_api_key

# Google OAuth (validated at startup)
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback

# CORS — comma-separated list of allowed origins
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,https://resume-reviewer-navy.vercel.app

# Frontend base URL — used to build shareable report links
FRONTEND_BASE_URL=https://resume-reviewer-navy.vercel.app
```

---

## Project Structure

```
backend/
├── main.py                       # FastAPI app, CORS, router mounting, rate-limit handler
├── alembic.ini                   # Alembic config
├── requirements.txt
├── ai/
│   ├── llm.py                    # Gemini 2.5 Flash client
│   ├── router.py                 # get_llm() — model selection + GPT→Gemini fallback
│   └── ChatGpt5.py               # Azure inference client (not in the active pipeline)
├── db/
│   ├── models.py                 # User, Resume, ResumeAnalysis, SharedReport, MockInterviewSession
│   ├── postgres.py               # Engine, session factory, Base, get_db dependency
│   ├── pinecone_db.py            # Pinecone index client
│   └── supabase_storage.py       # Supabase Storage client
├── routes/
│   ├── auth.py                   # /signup, /login, /google, /password-reset
│   ├── resume.py                 # /upload, /list
│   ├── ai.py                     # /ai/review, /ai/evaluate, /ai/chat
│   ├── mock_interview.py         # /ai/mock-interview/start, /answer
│   └── share.py                  # /share/create, /share/{token}
├── services/
│   ├── auth_service.py           # Signup / login / password-reset logic
│   ├── oauth_service.py          # Google code exchange + find-or-create + account linking
│   ├── resumeUpload.py           # PDF upload → Supabase Storage → PyMuPDF parse → DB
│   ├── ai_service.py             # Review + evaluate orchestration, background embedding
│   ├── chat_service.py           # RAG chat (Pinecone retrieval + LLM)
│   ├── mock_interview_service.py # Question generation, per-answer scoring, summary
│   ├── share_service.py          # Token creation + public report retrieval
│   ├── pinecone_service.py       # Embed, upsert, query
│   └── pdf_parser_service.py     # PDF text extraction helpers
├── schemas/                      # Pydantic request/response models per domain
├── utils/
│   ├── auth_dependency.py        # get_current_user (JWT bearer)
│   ├── jwt_handler.py            # Token creation
│   ├── oauth_config.py           # Google OAuth config + startup validation
│   ├── rate_limiter.py           # slowapi limiter keyed by user_id
│   ├── security.py               # Password hashing (pbkdf2_sha256)
│   ├── text_chunker.py           # Word-boundary chunking for embeddings
│   └── file_validator.py         # PDF magic-byte validation (not MIME-based)
├── migrations/                   # Alembic environment + versioned migrations
└── tests/                        # pytest + Hypothesis suites (OAuth, mock interview, etc.)
```

---

## API Reference

All `POST`/`GET` routes except `/`, `/health`, `/auth/*`, and `GET /share/{token}` require a
`Authorization: Bearer <jwt>` header.

### Auth (`/auth`)

| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| POST | `/auth/signup` | — | Register with email + password, returns JWT |
| POST | `/auth/login` | — | Log in, returns JWT |
| POST | `/auth/google` | 5/min | Exchange a Google authorization code for a JWT |
| POST | `/auth/password-reset` | — | Request reset; rejects OAuth-only accounts with HTTP 400 |

### Resume (`/resume`)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/resume/upload` | Validate + upload a PDF, store the file and parsed text |
| GET | `/resume/list` | List the user's resumes with their latest analysis (if any) |

### AI (`/ai`)

| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| POST | `/ai/review` | 10/hour | Score (0–100) + strengths + weaknesses + suggestions |
| POST | `/ai/evaluate` | 10/hour | Job-match score + interview-prep report |
| POST | `/ai/chat` | 20/hour | RAG Q&A grounded in the resume's analysis |

### Mock Interview (`/ai/mock-interview`)

| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| POST | `/ai/mock-interview/start` | 5/hour | Generate questions, create a session, return the first question |
| POST | `/ai/mock-interview/answer` | 30/hour | Score the answer, return feedback + next question (or final summary) |

### Share (`/share`)

| Method | Endpoint | Auth | Rate Limit | Description |
|---|---|---|---|---|
| POST | `/share/create` | required | 20/hour | Create/refresh a public link for a `review` or `evaluate` report |
| GET | `/share/{token}` | public | — | Fetch a shared report payload for the public view page |

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | `{"status": "running"}` |
| GET | `/health` | `{"status": "ok"}` — used by the frontend warm-up ping |

Rate-limit responses return HTTP 429 with a `Retry-After: 60` header.

---

## Database Schema

```sql
users
  id            SERIAL PRIMARY KEY
  email         VARCHAR UNIQUE
  password      VARCHAR NULL              -- pbkdf2_sha256 (NULL for OAuth-only users)
  google_id     VARCHAR(255) UNIQUE NULL  -- Google "sub" id (indexed)
  avatar_url    TEXT NULL                 -- Google profile picture URL
  auth_provider VARCHAR(50) DEFAULT 'email'   -- 'email' | 'google'
  created_at    TIMESTAMPTZ

resumes
  id          SERIAL PRIMARY KEY
  user_id     INTEGER REFERENCES users(id)
  file_url    VARCHAR                    -- Supabase Storage URL
  parsed_text TEXT                       -- extracted by PyMuPDF
  uploaded_at TIMESTAMPTZ

resume_analysis
  id          SERIAL PRIMARY KEY
  resume_id   INTEGER REFERENCES resumes(id) ON DELETE CASCADE
  score       INTEGER NOT NULL
  strengths   JSONB NOT NULL
  weaknesses  JSONB NOT NULL
  suggestions JSONB NOT NULL
  created_at  TIMESTAMPTZ DEFAULT NOW()

shared_reports
  id          SERIAL PRIMARY KEY
  token       VARCHAR(64) UNIQUE NOT NULL  -- secrets.token_urlsafe(32), indexed
  report_type VARCHAR(20) NOT NULL         -- 'review' | 'evaluate'
  resume_id   INTEGER REFERENCES resumes(id) ON DELETE CASCADE
  user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE
  payload     JSONB NOT NULL               -- frozen snapshot rendered on the public page
  created_at  TIMESTAMPTZ DEFAULT NOW()
  expires_at  TIMESTAMPTZ NULL

mock_interview_sessions
  id            VARCHAR(36) PRIMARY KEY     -- uuid4
  resume_id     INTEGER REFERENCES resumes(id) ON DELETE CASCADE
  user_id       INTEGER REFERENCES users(id) ON DELETE CASCADE
  questions     JSONB NOT NULL              -- [{question, type, ideal_answer}] (ideal_answer never sent to client)
  turns         JSONB NOT NULL              -- appended per answer: {question, answer, score, strengths, improvements, ideal_answer_hint}
  current_index INTEGER NOT NULL DEFAULT 0
  status        VARCHAR(20) NOT NULL DEFAULT 'active'   -- 'active' | 'complete'
  created_at    TIMESTAMPTZ DEFAULT NOW()
```

---

## AI Pipeline & RAG

The platform supports two models through `ai/router.py:get_llm()`:

- **Gemini 2.5 Flash** — primary, always available.
- **GPT-4o** — secondary, via GitHub Models / Azure Inference. Requires `GITHUB_TOKEN`. If it is
  unset or the call fails, the request transparently **falls back to Gemini** and the response
  carries a `fallback_warning`.

**Review / Evaluate → embeddings (RAG store):**

1. `/ai/review` and `/ai/evaluate` call the LLM with `with_structured_output(...)` so the response
   is validated against the Pydantic schema.
2. Review results are persisted to `resume_analysis` (existing rows for that resume are deleted
   first to avoid duplicates). Evaluate results are **not** persisted server-side.
3. The combined analysis text is chunked (`utils/text_chunker.py`), embedded with
   `gemini-embedding-001`, and upserted into Pinecone in a **background daemon thread** so the API
   response is not blocked. Vectors are namespaced by `{resume_id}_{type}_{i}` with metadata
   `{resume_id, type, text}`.

**Chat (`/ai/chat`):**

1. The question is embedded and used to query Pinecone for the top 5 chunks for that `resume_id`.
2. Those chunks form the RAG context injected into the system prompt; the LLM answers grounded in
   the user's specific analysis.
3. Chat is **stateful on the backend** — each exchange is persisted to a `ChatSession` (turns stored
   as JSONB), and the most recent turns (`MAX_HISTORY_TURNS = 10`) are replayed into the prompt so
   follow-up questions resolve against earlier messages. Pass the returned `session_id` back on the
   next request to continue a conversation; omitting it starts a fresh session.

> Chat requires at least one prior `/ai/review` or `/ai/evaluate` so that embeddings exist; the
> request returns HTTP 400 otherwise.

---

## Mock Interview

A stateful, turn-based flow backed by `mock_interview_sessions` (`services/mock_interview_service.py`):

1. **Start** (`/ai/mock-interview/start`) — generates `num_questions` (1–10) of the chosen
   `interview_type` (`technical` | `behavioral` | `mixed`) from the resume (and optional job
   description), persists the session, and returns the first question. Each generated question
   carries an `ideal_answer` rubric that is stored server-side and **never sent to the client**.
2. **Answer** (`/ai/mock-interview/answer`) — scores the answer 0–10 against the rubric, records
   the turn, and returns per-question feedback (strengths, improvements, a coaching hint) plus the
   next question. On the final answer it also returns a `session_summary` (total score, percentage,
   overall feedback, top strength/improvement, and all turns).

Both calls use the same primary-model + Gemini-fallback wrapper as the rest of the AI pipeline.

---

## Report Sharing

`services/share_service.py` issues a public, unguessable token (`secrets.token_urlsafe(32)`) and
stores a frozen snapshot of the report `payload`:

- **`review`** — the payload is read from the latest `resume_analysis` row. Calling create again for
  the same resume + type refreshes the snapshot and reuses the existing token.
- **`evaluate`** — because evaluate results are not persisted, the frontend must pass the report
  `payload` in the request body. `POST /share/create` returns HTTP 422 if `report_type=evaluate` and
  no payload is supplied.

`GET /share/{token}` is public (no auth) and returns the stored payload for the share page. The
share URL is built from `FRONTEND_BASE_URL` as `{FRONTEND_BASE_URL}/shared/{token}`.

---

## Authentication

- **Email/password** — `pbkdf2_sha256` hashing (`utils/security.py`), JWT (HS256) issued on
  signup/login.
- **Google OAuth 2.0** — authorization code flow. `/auth/google` exchanges the code for the user's
  profile, then finds or creates the user. If an email already exists, the Google account is
  **linked** to it.
- **Password reset** — OAuth-only accounts (Google provider, no password) are rejected with a clear
  HTTP 400; for non-existent emails a generic success message is returned to avoid revealing whether
  an account exists.

The `get_current_user` dependency (`utils/auth_dependency.py`) decodes the bearer token and loads
the user for every protected route.

---

## Rate Limiting

slowapi limits are keyed per authenticated user (not by IP):

| Endpoint | Limit |
|---|---|
| `/auth/google` | 5 / minute |
| `/ai/review`, `/ai/evaluate` | 10 / hour |
| `/ai/chat` | 20 / hour |
| `/ai/mock-interview/start` | 5 / hour |
| `/ai/mock-interview/answer` | 30 / hour |
| `/share/create` | 20 / hour |

Exceeding a limit returns HTTP 429 with `Retry-After: 60`.

---

## Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new autogenerated migration
alembic revision --autogenerate -m "describe the change"

# Roll back the last migration
alembic downgrade -1

# View history
alembic history
```

Current migrations:

- `001_add_oauth_columns_to_users` — adds `google_id`, `avatar_url`, `auth_provider` to `users`.
- `002_add_mock_interview_sessions` — adds the `mock_interview_sessions` table + indexes.

---

## Testing

```bash
cd backend

pytest                              # run everything
pytest tests/test_oauth_service.py  # a single file
pytest tests/test_property_*.py     # Hypothesis property-based tests
pytest --cov=. --cov-report=html    # coverage report
```

Coverage includes the OAuth code exchange and account linking, property-based invariants
(duplicate Google id, incomplete profile rejection, password-reset prevention), the mock interview
flow, end-to-end OAuth integration, and PDF upload validation
(`tests/test_pdf_upload_validation.py` — magic-byte acceptance across the wrong-MIME-type cases that
mobile pickers produce, spoofed-content-type rejection, and the post-read stream rewind).

---

## Deployment

Deploy to any Python host (Render, Railway, Fly.io, etc.).

1. Push the backend to GitHub and connect the repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT` (or use `gunicorn`).
4. Set every environment variable from `.env.example`. In particular:
   - `POSTGRES_URL` (not `DATABASE_URL`)
   - `ALLOWED_ORIGINS` must include your deployed frontend origin
   - `GOOGLE_REDIRECT_URI` and `FRONTEND_BASE_URL` must point at the production frontend
5. Run `alembic upgrade head` against the production database.

---

## Troubleshooting

**Server won't start / DB errors** — confirm `POSTGRES_URL` (not `DATABASE_URL`) and that the
database is reachable. OAuth env vars are validated at startup, so a misconfigured Google client
will also fail fast.

**`/ai/chat` returns 400 "No analysis found"** — run `/ai/review` or `/ai/evaluate` first so
embeddings exist in Pinecone.

**Pinecone errors / empty chat context** — verify `PINECONE_API_KEY` and `PINECONE_INDEX`, and that
the index dimensions match the embedding model. Embedding upserts run in a background thread; check
server logs for `[WARNING] Pinecone embedding failed`.

**GPT-4o unavailable** — expected when `GITHUB_TOKEN` is missing or rate-limited; the response falls
back to Gemini and includes a `fallback_warning`.

**PDF upload fails** — ensure the file is a real PDF (text, not a scanned image) and that the
Supabase Storage bucket exists and the service-role key is valid. `"Only PDF files allowed"` means
the leading bytes were not `%PDF-`, so the file genuinely is not a PDF regardless of its extension —
validation ignores the client-reported MIME type, so a mobile picker sending
`application/octet-stream` is not the cause.
