# ResumeAI — AI-Powered Resume Reviewer

An intelligent resume analysis platform that gives you deep feedback, job match evaluation, and a conversational AI assistant grounded in your resume review.

**Live Demo:** [resume-reviewer-navy.vercel.app](https://resume-reviewer-navy.vercel.app)

---

## What It Does

- **AI Review** — Upload a PDF resume and get a scored analysis (0–100) with specific strengths, weaknesses, and actionable suggestions
- **Job Match Evaluation** — Paste a job description and get a match score, technical & behavioral interview questions, skill gap analysis, and a day-by-day preparation plan
- **Resume Chat** — Ask follow-up questions about your review in a conversational interface powered by semantic search over your analysis
- **Dual AI Models** — Choose between Gemini 2.5 Flash and GPT-4o per request, with automatic fallback if one is unavailable

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL via Supabase (SQLAlchemy ORM) |
| File Storage | Supabase Storage |
| Vector Search | Pinecone |
| Primary LLM | Gemini 2.5 Flash (LangChain) |
| Secondary LLM | GPT-4o via GitHub Models / Azure Inference |
| Embeddings | `models/gemini-embedding-001` |
| PDF Parsing | PyMuPDF |
| Auth | PyJWT (HS256) |
| Rate Limiting | slowapi (20 req/hour for chat, 10/hour for AI routes) |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 19 + Vite |
| Routing | React Router v7 |
| HTTP Client | Axios (with JWT interceptor) |
| File Upload | react-dropzone |
| Icons | react-icons |
| Styling | Pure CSS with design tokens |
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
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Fill in all values in .env (see Environment Variables section below)

# 5. Run database migrations
# Create the tables by running your SQLAlchemy models against the DB
python -c "from db.postgres import engine; from db.models import Base; Base.metadata.create_all(engine)"

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
# Create .env.local in the frontend root:
echo "VITE_API_URL=http://localhost:8000" > .env.local

# 4. Start dev server
npm run dev
```

Frontend will be live at `http://localhost:5173`

> **Important:** Always start the backend before the frontend. The frontend has no mock layer — all API calls go to the real backend.

---

## Environment Variables

### Backend (`.env`)

```env
# PostgreSQL
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname

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

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,https://your-frontend.vercel.app
```

### Frontend (`.env.local`)

```env
VITE_API_URL=http://localhost:8000
```

---

## Deployment

### Backend

Deploy to any platform that supports Python (Railway, Render, Fly.io, etc.).

Set all backend environment variables in your platform's dashboard. Make sure `ALLOWED_ORIGINS` includes your Vercel frontend URL.

```env
ALLOWED_ORIGINS=https://your-app.vercel.app
```

### Frontend (Vercel)

1. Push frontend to GitHub
2. Import the repo in Vercel
3. Add environment variable in Vercel dashboard:
   ```
   VITE_API_URL=https://your-deployed-backend-url.com
   ```
4. Deploy — Vercel handles the rest

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
│   ├── auth_service.py       # Signup/login business logic
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
  id          SERIAL PRIMARY KEY
  email       VARCHAR UNIQUE
  password    VARCHAR              -- pbkdf2_sha256 hashed
  created_at  TIMESTAMPTZ

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
  created_at  TIMESTAMPTZ
```

---

## Known Limitations

- Chat is not truly multi-turn — the backend receives each message independently with no conversation history. The frontend displays the history but does not send it to the API.
- PDF parsing is text-only. Scanned PDFs or image-heavy resumes may parse poorly.
- GPT-4o availability depends on GitHub Models rate limits. Gemini is always the fallback.
- Mobile PDF upload is not supported (browser limitation with file pickers on some mobile browsers).
