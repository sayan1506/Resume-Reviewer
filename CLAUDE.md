# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Monorepo with two independent apps: `backend/` (Python 3.11+ / FastAPI) and `frontend/` (React 19 / Vite 8). It's an AI resume-review platform. Deep docs live in `README.md`, `backend/README.md`, and `frontend/README.md`; project-specific steering is in `.kiro/steering/*.md`. Consult those for the full API reference, DB schema, and feature list — this file covers what's needed to be productive quickly.

## Commands

Run backend commands from `backend/`, frontend commands from `frontend/`.

### Backend
```bash
uvicorn main:app --reload --port 8000   # dev server -> http://localhost:8000, docs at /docs
alembic upgrade head                    # apply migrations (required after schema changes)
alembic revision --autogenerate -m "msg"  # generate a migration
alembic downgrade -1                    # roll back one

pytest                                  # all tests
pytest tests/test_oauth_service.py      # single file
pytest tests/test_oauth_service.py::test_name  # single test
pytest tests/test_property_*.py         # property-based (Hypothesis) tests only
pytest --cov=. --cov-report=html        # with coverage
```

### Frontend
```bash
npm run dev                    # vite dev server -> http://localhost:5173
npm run build                  # production build
npm run lint                   # eslint
npm run test                   # vitest single run
npm run test -- src/__tests__/Foo.test.jsx  # single test file
```

Always start the backend before the frontend — there is no mock/stub layer, every call hits the real API.

## Platform (Windows)

- Virtualenv: `venv\Scripts\activate`.
- In PowerShell, chain commands with `;` (not `&&`); the Bash tool here uses POSIX `sh` where `&&` is fine.
- Start long-running processes (`uvicorn --reload`, `npm run dev`) manually / in the background, not as blocking commands.

## Architecture

### Backend: strict layering, one trio per domain
`routes/` (thin HTTP) → `services/` (business logic, owns DB sessions + external calls) → `db/` + `utils/`. Each domain has a matching trio: `routes/<x>.py`, `services/<x>_service.py`, `schemas/<x>_schema.py`. When adding a feature, follow this pattern — keep routes thin and put logic in the service.

- Protect endpoints with the JWT dependency in `utils/auth_dependency.py`.
- Apply rate limits via the shared limiter in `utils/rate_limiter.py` — it is keyed by **user_id**, not IP.
- A new DB column means a new Alembic migration. Do not rely on `create_all` auto-create in production.

### AI model routing + fallback (central pattern)
Every AI call goes through `invoke_with_fallback(model_choice, chain_factory, inputs)` in `ai/router.py`. `chain_factory` is a callable `lambda llm: prompt | llm.with_structured_output(Schema)`. The selected model (`gpt` / `gemini` / `gpt5`) is tried first, then the remaining models cascade in a fixed order, so every request gets full coverage. A successful response after a failure carries a `fallback_warning`; total failure raises `HTTPException(502)`. GPT-4o and GPT-5 both need `GITHUB_TOKEN`; Gemini needs `GOOGLE_API_KEY` and is always in the chain. `ai/ChatGpt5.py` is legacy and unused by the active pipeline.

### RAG + embeddings flow
`/ai/review` and `/ai/evaluate` produce structured LLM output; the analysis text is chunked (`utils/text_chunker.py`) and embedded (`gemini-embedding-001`) into Pinecone in a **background thread** so it does not block the response. `/ai/chat` embeds the question, queries Pinecone for top-k chunks, and answers grounded in them. Chat is **stateful**: pass the returned `session_id` back to continue; the last `MAX_HISTORY_TURNS` turns are replayed into the prompt. Mock interview is also stateful — sessions persist server-side and the per-question `ideal_answer` rubric is never sent to the client.

### Frontend
- All API calls go through `src/api/axios.js` so the JWT request interceptor and 401 response handling apply uniformly. Never call `fetch` or a bare axios directly.
- Wrap authenticated routes with `ProtectedRoute`; read auth state from `AuthContext`.
- Route screens live in `pages/`, reusable UI in `components/`.
- Styling uses Tailwind 3 with the "Precision Path" design tokens in `tailwind.config.js`; shared helpers and font imports live in `src/index.css`.
- PDF export (`src/utils/exportPDF.js`) targets specific container element IDs — `review-report-content`, `evaluate-report-content`, `shared-report-content`. Preserve these IDs when editing report pages.

## Gotchas

- The Postgres connection env var is `POSTGRES_URL`, **not** `DATABASE_URL`. `alembic.ini`'s `sqlalchemy.url` is a placeholder overridden by `migrations/env.py`.
- `GOOGLE_CLIENT_ID` must match between the frontend and backend env files.
- CORS origins are controlled by `ALLOWED_ORIGINS` (comma-separated) in the backend `.env`.
- `/ai/evaluate` results are not persisted server-side — sharing an evaluate report sends the rendered payload from the client.
- Naming: Python is `snake_case` (`_service.py` / `_schema.py` suffixes); React components are `PascalCase.jsx`; backend tests `test_*.py` (property tests `test_property_*.py`), frontend tests `*.test.jsx`.
