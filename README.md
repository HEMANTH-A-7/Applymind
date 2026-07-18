# ApplyMind AI

An autonomous, AI-powered job application platform. Upload a resume once, and a pipeline of nine cooperating agents researches the market, finds relevant openings, tailors your resume and cover letter per job, and tracks every application through to a reply.

**Live app:** [applymind-frontend.onrender.com](https://applymind-frontend.onrender.com)

> Hosted on Render's free tier — the backend spins down after inactivity, so the first request after a while can take up to a minute to wake up.

## How it works

Resume upload triggers a pipeline of nine agents:

| # | Agent | Responsibility |
|---|-------|-----------------|
| 01 | Resume Intake | Parses uploaded PDF/DOCX resumes into a structured JSON schema |
| 02 | Market Research | Analyzes job market trends, salary bands, in-demand skills, and top hiring companies |
| 03 | Job Scraper | Pulls listings from multiple public sources (HN Who's Hiring, LinkedIn, Adzuna, etc.) |
| 04 | Job Match & Score | Ranks scraped jobs against the resume via TF-IDF cosine similarity, with LLM re-scoring |
| 05 | ATS Resume Rewriter | Rewrites the master resume per job description using Groq AI |
| 06 | Cover Letter Generator | Generates personalized cover letters with A/B variants |
| 07 | Credential Manager | AES-256 encrypted storage of platform credentials |
| 08 | Application Submission | Executes applications via Selenium, GraphQL, and SMTP |
| 09 | Analytics | Tracks the full application funnel and monitors inboxes for recruiter replies |

## Tech stack

- **Frontend:** Next.js 16 (App Router), React 19, Tailwind CSS, Firebase Auth
- **Backend:** FastAPI, served with Uvicorn
- **Database:** Firestore
- **LLMs:** Groq (`llama-3.3-70b`) primary, Gemini fallback
- **Deployment:** Render (see [`render.yaml`](render.yaml))

## Repository structure

```
.
├── backend/          FastAPI service — agents, API routes, core services
│   ├── agents/        The 9-agent pipeline (agent_01 … agent_09)
│   ├── api/            Route definitions (main.py)
│   ├── core/           Config, Firebase admin, caching, rate limiting, security
│   ├── models/         Pydantic/data models
│   └── scratch/        Ad hoc scripts used during development, not part of the app
├── website/          Next.js frontend
│   ├── app/            Pages (dashboard, login, portal-admin, ...)
│   ├── components/     UI components
│   └── lib/             Firebase client, auth context
├── docs/              Project docs (SRS, development log, checklist)
├── docker-compose.yml Local multi-service dev environment
├── render.yaml        Render deployment blueprint (backend + frontend)
├── firebase.json / firestore.rules / .firebaserc   Firebase project config
```

## Running locally

### Prerequisites

- Python 3.12+
- Node.js 20+
- A Firebase project (Firestore + Auth enabled)
- API keys: [Groq](https://console.groq.com/keys) (required), [Gemini](https://aistudio.google.com/apikey) and [Adzuna](https://developer.adzuna.com/) (optional)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd website
npm install
cp .env.local.example .env.local   # fill in your Firebase web config
npm run dev
```

The frontend runs on `http://localhost:3000` and expects the backend at `http://localhost:8000` (set via `NEXT_PUBLIC_API_URL`).

### Docker Compose

`docker-compose.yml` at the repo root brings up backend + frontend together for local development.

## Deployment

The app deploys to Render via the [`render.yaml`](render.yaml) blueprint, which defines two services: `applymind-backend` (Docker) and `applymind-frontend` (Node/Next.js). Secrets are entered directly in the Render dashboard rather than committed — see the env var lists in `backend/.env.example` and `website/.env.local.example` for what's required.

## Docs

Deeper project context — the original spec, development log, and QA checklist — lives in [`docs/`](docs).
