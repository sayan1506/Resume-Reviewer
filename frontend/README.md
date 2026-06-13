# ResumeAI — Frontend

React + Vite single-page app for ResumeAI. It handles authentication (email/password and Google OAuth), PDF resume upload, AI review and job-match evaluation, a RAG chat assistant, turn-based mock interviews, public report sharing, and PDF export.

> Part of the [ResumeAI monorepo](../README.md). For the API it talks to, see [`../backend/README.md`](../backend/README.md).

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Scripts](#scripts)
- [Project Structure](#project-structure)
- [Routing](#routing)
- [API Layer & Auth](#api-layer--auth)
- [Features](#features)
- [Styling](#styling)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | React 19 + Vite 8 |
| Routing | React Router DOM v7 |
| HTTP Client | Axios (JWT request interceptor + 401 redirect) |
| Auth | `@react-oauth/google` (Google OAuth) + JWT in `localStorage` |
| File Upload | `react-dropzone` |
| Styling | Tailwind CSS v3 with a Material Design 3 token theme |
| PDF Export | `jspdf` + `html2canvas` |
| Icons | `react-icons` + Material Symbols |
| Testing | Vitest + React Testing Library + jsdom |
| Deployment | Vercel |

---

## Quick Start

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure environment (see below)
#    create .env with VITE_API_URL and VITE_GOOGLE_CLIENT_ID

# 3. Start the dev server
npm run dev
```

App runs at `http://localhost:5173`.

> Start the backend (`http://localhost:8000`) first — there is no mock layer; every call hits the
> real API.

---

## Environment Variables

### Development (`.env`)

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id
```

### Production (`.env.production`)

```env
VITE_API_URL=https://your-deployed-backend-url.com
```

All client env vars must be prefixed with `VITE_` to be exposed by Vite. `VITE_API_URL` defaults to
`http://localhost:8000` if unset (see `src/api/axios.js`).

---

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Start the Vite dev server with HMR |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run lint` | Run ESLint over the project |
| `npm run test` | Run the Vitest suite once |

---

## Project Structure

```
frontend/
├── index.html                    # App entry HTML
├── vite.config.js                # Vite + Vitest config; OAuth popup COOP header
├── tailwind.config.js            # Material Design 3 color/type/spacing tokens
├── postcss.config.js
├── eslint.config.js
├── vercel.json                   # SPA rewrite — all paths → index.html
├── public/                       # favicon, icons
└── src/
    ├── main.jsx                  # React root
    ├── App.jsx                   # Router + AuthProvider + backend warm-up ping
    ├── index.css                 # Tailwind layers + custom component styles
    ├── api/
    │   └── axios.js              # Axios instance, JWT interceptor, 401 handling
    ├── context/
    │   └── AuthContext.jsx       # Auth state (token, user) provider
    ├── components/
    │   ├── Navbar.jsx
    │   ├── ProtectedRoute.jsx    # Redirects unauthenticated users to /login
    │   ├── ShareModal.jsx        # Copy-to-clipboard share link dialog
    │   ├── InterviewScoreCard.jsx# Per-answer mock-interview feedback card
    │   └── InterviewSummary.jsx  # End-of-interview scorecard
    ├── pages/
    │   ├── LandingPage.jsx
    │   ├── Login.jsx
    │   ├── Signup.jsx
    │   ├── Dashboard.jsx         # Upload (dropzone) + resume list + analysis preview
    │   ├── ReviewResults.jsx     # AI review output (score, strengths, etc.)
    │   ├── Evaluate.jsx          # Job-match evaluation + share + PDF export
    │   ├── ChatPage.jsx          # RAG chat + turn-based mock interview
    │   └── SharedReportPage.jsx  # Public, no-auth view of a shared report
    ├── utils/
    │   └── exportPDF.js          # html2canvas + jsPDF export of a DOM element
    └── __tests__/
        └── GoogleOAuth.test.jsx
```

---

## Routing

Defined in `src/App.jsx` with React Router v7. Protected routes are wrapped in `ProtectedRoute`,
which redirects to `/login` when no token is present.

| Path | Page | Access |
|---|---|---|
| `/` | LandingPage | public |
| `/login` | Login | public |
| `/signup` | Signup | public |
| `/shared/:token` | SharedReportPage | public (no auth) |
| `/dashboard` | Dashboard | protected |
| `/review/:resumeId` | ReviewResults | protected |
| `/evaluate/:resumeId` | Evaluate | protected |
| `/chat/:resumeId` | ChatPage | protected |
| `*` | → redirect to `/login` | — |

`vercel.json` rewrites every path to `index.html` so client-side routing works on Vercel.

---

## API Layer & Auth

`src/api/axios.js` exports a configured Axios instance:

- **Request interceptor** — attaches `Authorization: Bearer <token>` from `localStorage`, and sets
  `Content-Type: application/json` for non-`FormData` requests (file uploads stay `multipart`).
- **Response interceptor** — on HTTP 401 it clears the token, stores a `session_expired` message,
  and redirects to `/login`.

Auth state lives in `AuthContext`. JWTs are persisted in `localStorage`. Google OAuth uses
`@react-oauth/google`; `vite.config.js` sets `Cross-Origin-Opener-Policy: same-origin-allow-popups`
so the OAuth popup can talk to the opener window in development.

`App.jsx` fires a warm-up `GET /health` on mount to mitigate backend cold starts on free hosting.

---

## Features

- **Authentication** — email/password sign-up and login, plus Google OAuth. Tokens are stored
  client-side and attached to every request.
- **Resume upload** — drag-and-drop PDF upload via `react-dropzone` on the Dashboard; the resume
  list shows each resume with its latest analysis preview.
- **AI Review** (`/review/:resumeId`) — score, strengths, weaknesses, and suggestions.
- **Job-Match Evaluation** (`/evaluate/:resumeId`) — match score, technical & behavioral interview
  questions, skill-gap analysis, and a day-by-day prep plan. Supports sharing and PDF export.
- **Chat assistant** (`/chat/:resumeId`, Chat mode) — RAG Q&A grounded in the resume's analysis,
  with suggestion chips and a model selector (Gemini / GPT-4o). Chat history is kept on the client;
  each request to the API is independent.
- **Mock Interview** (`/chat/:resumeId`, Mock Interview mode) — a turn-based flow: configure number
  of questions (3/5/7/10), type (mixed/technical/behavioral), and an optional job description. Each
  answer is scored with feedback (`InterviewScoreCard`), and the session ends with a full scorecard
  (`InterviewSummary`).
- **Report sharing** (`ShareModal`) — generates a public `/shared/:token` link rendered by
  `SharedReportPage` with no login required.
- **PDF export** (`utils/exportPDF.js`) — captures a report element with `html2canvas` and saves it
  via `jsPDF`.

### Model selection & fallback

Chat, evaluate, and mock-interview requests can select **Gemini** or **GPT-4o**. If GPT-4o is
unavailable on the backend, the request falls back to Gemini and the response carries a
`fallback_warning`, which the UI surfaces.

---

## Styling

Tailwind CSS v3 with a custom theme in `tailwind.config.js` built on **Material Design 3** tokens —
semantic color roles (`surface`, `primary`, `on-surface-variant`, etc.), a typographic scale
(`headline-*`, `body-*`, `label-*`), spacing tokens, and `Inter` / `Plus Jakarta Sans` fonts.
`darkMode: 'class'` is enabled. Component-level styles and helpers (e.g. `tonal-card`) live in
`src/index.css`. Material Symbols icons are used throughout the UI.

---

## Testing

```bash
cd frontend
npm run test         # Vitest single run (jsdom environment)
```

Vitest is configured in `vite.config.js` (`jsdom` environment, globals enabled,
`src/test-setup.js` setup file) with React Testing Library. Current coverage includes the Google
OAuth flow (`src/__tests__/GoogleOAuth.test.jsx`).

---

## Deployment (Vercel)

1. Import the repo in Vercel and set the root directory to `frontend`.
2. Vercel auto-detects Vite (`build` → `dist`).
3. Add environment variables in the Vercel dashboard:
   ```
   VITE_API_URL=https://your-deployed-backend-url.com
   VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id
   ```
4. `vercel.json` already handles the SPA rewrite so deep links resolve to `index.html`.
5. Ensure the backend's `ALLOWED_ORIGINS` includes your Vercel URL, and that the Google OAuth
   client lists your production origin/redirect URI.

Live demo: [resume-reviewer-navy.vercel.app](https://resume-reviewer-navy.vercel.app)
