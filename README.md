# ResumeAI — AI-Powered Resume Reviewer

An intelligent resume analysis platform that gives you deep feedback, job match evaluation, and a conversational AI assistant grounded in your resume review.

**Live Demo:** [resume-reviewer-navy.vercel.app](https://resume-reviewer-navy.vercel.app)

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [API Routes](#api-routes)
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

- **Job Match Evaluation** — Paste any job description to get:
  - Match percentage showing alignment with the role
  - Technical interview questions tailored to the position
  - Behavioral interview questions for preparation
  - Skill gap analysis identifying missing competencies
  - Day-by-day preparation plan for interview success

- **Conversational Resume Assistant** — Chat with an AI that:
  - Answers questions about your resume analysis
  - Uses semantic search (RAG) over your review data
  - Provides context-aware responses grounded in your specific analysis
  - Maintains chat history for natural conversation flow (frontend only)

### Technical Features

- **Dual AI Models** — Flexibility to choose between:
  - Gemini 2.5 Flash (primary, via Google AI)
  - GPT-4o (secondary, via GitHub Models)
  - Automatic fallback if preferred model is unavailable

- **Secure Authentication** — Multiple auth options:
  - Email/password registration with JWT tokens
  - Google OAuth 2.0 (authorization code flow)
  - Automatic account linking for existing email users
  - Password reset via email (with OAuth-only protection)

- **Smart Rate Limiting** — Protection against abuse:
  - User-based limits (not IP-based)
  - Clear error messages with retry timing
  - Different limits for different endpoints

- **Vector-Powered Chat** — Advanced semantic search:
  - Embeddings stored in Pinecone
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
- [ ] Google AI API key (for Gemini)
- [ ] Optional: GitHub Token (for GPT-4o)
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
| Primary LLM | Gemini 2.5 Flash (LangChain) |
| Secondary LLM | GPT-4o via GitHub Models / Azure Inference |
| Embeddings | `models/gemini-embedding-001` |
| PDF Parsing | PyMuPDF |
| Auth | PyJWT (HS256), Google OAuth 2.0 |
| Rate Limiting | slowapi (20 req/hour for chat, 10/hour for AI routes) |
| Testing | pytest + Hypothesis (Property-Based Testing) |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 19 + Vite 8 |
| Routing | React Router DOM v7 |
| HTTP Client | Axios (with JWT interceptor) |
| File Upload | react-dropzone |
| OAuth | @react-oauth/google |
| Icons | react-icons |
| Styling | Pure CSS with design tokens |
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
      ├── PostgreSQL (Supabase)     ← source of truth: users, resumes, analysis
      ├── Supabase Storage          ← raw PDF files
      └── Pinecone                  ← vector embeddings for chat semantic search

AI Pipeline:
  PDF Upload → PyMuPDF parse → stored in Postgres
  /ai/review → LLM structured output → saved to ResumeAnalysis → embeddings stored in Pinecone (background thread)
  /ai/chat   → embed question → query Pinecone → RAG prompt → LLM answer
```

---

## API Routes

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register new user, returns JWT |
| POST | `/auth/login` | Login, returns JWT |
| POST | `/auth/google` | Exchange Google auth code for JWT (5/min rate limit) |
| POST | `/auth/password-reset` | Request password reset (rejects OAuth-only accounts) |

### Resume
| Method | Endpoint | Description |
|---|---|---|
| POST | `/resume/upload` | Upload PDF, parse and store |
| GET | `/resume/list` | List all resumes with latest analysis |

### AI
| Method | Endpoint | Rate Limit | Description |
|---|---|---|---|
| POST | `/ai/review` | 10/hour | Score + strengths + weaknesses + suggestions |
| POST | `/ai/evaluate` | 10/hour | Job match score + interview prep report |
| POST | `/ai/chat` | 20/hour | Conversational Q&A over resume analysis |

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Supabase project (PostgreSQL + Storage)
- A Pinecone account with an index created
- Google AI API key (Gemini)
- GitHub Token (for GPT-4o via GitHub Models) — optional

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

# Google Generative AI (Gemini)
GOOGLE_API_KEY=your_google_genai_api_key

# GitHub Models (GPT-4o) — optional, falls back to Gemini if missing
GITHUB_TOKEN=your_github_models_token

# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback

# CORS (comma-separated list of allowed origins)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,https://resume-reviewer-navy.vercel.app
```

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

The backend includes comprehensive tests using pytest and Hypothesis for property-based testing:

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
- **Unit Tests**: Auth service, config validation, incomplete profile rejection

### Frontend Testing

The frontend uses Vitest with React Testing Library:

```bash
cd frontend

# Run tests (single run)
npm run test

# Run tests in watch mode
npm run dev -- --test

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
- Backend: Render (API endpoint not publicly exposed)

---

## How the Chat Works

The chat feature uses **Retrieval-Augmented Generation (RAG)**:

1. When you run `/ai/review` or `/ai/evaluate`, the analysis text is chunked (800 chars, 100 overlap) and embedded using `gemini-embedding-001`
2. Embeddings are stored in Pinecone in a background thread — this does not block the API response
3. When you send a chat message, it is embedded and used to query Pinecone for the top 5 most relevant chunks
4. Those chunks are injected into a prompt as context, and the LLM answers grounded in your specific analysis
5. Chat history is maintained on the frontend only — each request to `/ai/chat` is stateless on the backend

> **Note:** Chat only works after running at least one `/ai/review` or `/ai/evaluate` on a resume. The Chat button on the dashboard is disabled until analysis exists.

---

## Project Structure

```
backend/
├── main.py                   # FastAPI app, CORS, router mounting
├── ai/
│   ├── llm.py                # Gemini LLM client
│   ├── router.py             # LLM routing + GPT fallback logic
│   └── ChatGpt5.py           # Azure inference client (unused in active pipeline)
├── db/
│   ├── models.py             # SQLAlchemy models: User, Resume, ResumeAnalysis
│   ├── postgres.py           # DB engine + session factory
│   ├── pinecone_db.py        # Pinecone index client
│   └── supabase_storage.py   # Supabase Storage client
├── routes/
│   ├── auth.py               # /auth/signup, /auth/login
│   ├── resume.py             # /resume/upload, /resume/list
│   └── ai.py                 # /ai/review, /ai/evaluate, /ai/chat
├── services/
│   ├── auth_service.py       # Signup/login/password-reset business logic
│   ├── oauth_service.py      # Google OAuth code exchange + user linking
│   ├── resumeUpload.py       # PDF upload + parse pipeline
│   ├── ai_service.py         # Review + evaluate orchestration
│   ├── chat_service.py       # RAG chat logic
│   └── pinecone_service.py   # Embedding store + query
├── schemas/
│   ├── auth_schema.py
│   ├── resume_schema.py
│   ├── ai_schema.py          # Review + evaluate Pydantic models
│   └── chat_schema.py        # Chat request/response models
└── utils/
    ├── auth_dependency.py    # JWT bearer dependency
    ├── jwt_handler.py        # Token creation
    ├── oauth_config.py       # Google OAuth configuration
    ├── rate_limiter.py       # slowapi config (rate by user_id)
    ├── security.py           # Password hashing (pbkdf2_sha256)
    ├── text_chunker.py       # Word-boundary chunking for embeddings
    └── file_validator.py     # PDF MIME type validation

frontend/
├── src/
│   ├── api/axios.js          # Axios instance + JWT + 401 interceptors
│   ├── context/AuthContext.jsx
│   ├── components/
│   │   ├── Navbar.jsx
│   │   └── ProtectedRoute.jsx
│   └── pages/
│       ├── Login.jsx
│       ├── Signup.jsx
│       ├── Dashboard.jsx     # Upload + resume list + analysis preview
│       ├── ReviewResults.jsx # AI review output
│       ├── Evaluate.jsx      # Job match evaluation
│       └── ChatPage.jsx      # Conversational resume chat
└── index.css                 # Design tokens + all component styles
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
  created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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

### Rate Limiting

The API implements user-based rate limiting using slowapi:
- `/ai/review` and `/ai/evaluate`: 10 requests per hour per user
- `/ai/chat`: 20 requests per hour per user
- `/auth/google`: 5 requests per minute (to prevent abuse)

Rate limit responses include a `Retry-After` header (60 seconds).

### File Validation

PDF uploads are validated using:
- MIME type checking (`application/pdf`)
- File extension validation
- Handled by `utils/file_validator.py`

### OAuth Flow

1. Frontend initiates OAuth with Google
2. Google redirects back with authorization code
3. Frontend sends code to `/auth/google`
4. Backend exchanges code for user info
5. Backend finds or creates user (with account linking)
6. Backend returns JWT token
7. Frontend stores token and redirects to dashboard

---

## Known Limitations

- Chat is not truly multi-turn — the backend receives each message independently with no conversation history. The frontend displays the history but does not send it to the API.
- PDF parsing is text-only. Scanned PDFs or image-heavy resumes may parse poorly.
- GPT-4o availability depends on GitHub Models rate limits. Gemini is always the fallback.
- Mobile PDF upload is not supported (browser limitation with file pickers on some mobile browsers).
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
