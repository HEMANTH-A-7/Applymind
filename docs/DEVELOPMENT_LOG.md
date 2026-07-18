# ApplyMind AI - Project Instructions & Context Resume

This document contains full context and status updates of all changes made across sessions. When starting a new chat session, read this file to immediately resume development.

---

## 1. Project Overview & Architecture

ApplyMind AI is a 9-agent automated job application platform powered by FastAPI (backend), Next.js (frontend), and Groq AI (`llama-3.3-70b` / `mixtral-8x7b`).

- **Frontend:** Next.js application inside `/website` running on `http://localhost:3000`.
- **Backend:** FastAPI REST API inside `/backend` running on `http://localhost:8000`.
- **Database:** Firestore (Firebase Admin SDK configured on the backend).

---

## 2. Completed Features & Core Fixes

### A. Job Scraper & Scored Description Fixes
1. **Hacker News Recency:** Switched search logic from standard search to Algolia's `search_by_date` API, targeted specifically to the `whoishiring` author and `story` tags to prevent fetching obsolete threads.
2. **HN Link Extraction:** Extracted career application links directly using BeautifulSoup parsed elements to resolve HTML entities.
3. **LinkedIn Pagination & Dates:** LinkedIn scraper paginates via the `start` parameter with recency filtering (`sortBy=DD` - Date Descending and `f_TPR=r2592000` - last 30 days).
4. **Job Description Retention Fix (`agent_04_job_match.py`):** Fixed a bug where the scoring pipeline stripped the `jd_text` and `tags` keys from job matches before saving to Firestore. `score_job` now replicates the entire original job dictionary before adding matching scores, ensuring the UI receives the full description string.

### B. Cover Letter & Resume PDF Generation Fixes
1. **JSON Serialization Fix (`agent_05_ats_rewriter.py`):** Fixed an `Object of type DatetimeWithNanoseconds is not JSON serializable` crash. Added a recursive dictionary cleaning helper (`clean_for_json`) to strip Firestore database metadata prior to serialization.
2. **Cover Letter UI Key Rendering Fix (`website/app/dashboard/page.tsx`):** Fixed a frontend bug where the cover letter modal rendered `"No text returned."` by updating UI binding to check `data.cover_letter` (returned by Agent 06) first.

### C. Job Matching & Date Sorting (`api/main.py` & `page.tsx`)
1. **Relevance vs. Date Sorting:** Added a "Sort By" select dropdown in the Jobs Queue panel of the dashboard.
2. **Dropdown Options:** Toggle between **Time Listed (Date)** (newest first) and **Relevance (Score)**.
3. **Backend Support:** Toggled sorting parameters on `/api/jobs/matches?sort_by=date` with fast in-memory sorting.

### D. Stateless, Cookie-Based Platform Credentials (GDPR Compliant Auto-Apply)
To prevent storing sensitive credentials (LinkedIn, Wellfound) on backend databases and avoid GDPR liability, credentials are stored **only browser-side in cookies** and passed dynamically to the API.

1. **Dashboard Credentials Panel:** Added a `🔑 Platform Credentials` action button in the Job Queue control panel bar.
2. **Consent & Privacy Gate:** Added a Platform Credentials Modal prompting the user for credentials, coupled with an explicit privacy policy consent checkbox.
3. **Cookies Helper Scope:** Credentials are saved locally on the client using browser cookies if consent is granted, and deleted when cleared.
4. **Stateless API Routes (`api/main.py`):** Modified `/api/apply/batch` and `/api/apply/{job_id}` endpoints to accept an optional `credentials` request body schema.
5. **Stateless Agent 08 Runner (`agent_08_application_submission.py`):** Updated Selenium (LinkedIn Easy Apply) and GraphQL (Wellfound apply) wrappers to accept in-memory credentials payloads, bypassing Firestore lookups.
6. **Privacy Policy (`website/app/privacy/page.tsx`):** Updated Sections 2, 7, and 8 of the Privacy Policy to document local browser cookie storage and memory-only backend processing of platform credentials.

### E. Landing Page Hydration Mismatches
1. **Hydration Normalization (`HeroSection.tsx` & `FooterCTA.tsx`):** Removed trailing whitespace characters from conditional class bindings and verified that the `mounted` state correctly triggers post-render to ensure a mismatch-free client-side hydration process.

---

## 3. Verification & Testing

### Scraper and Date Sorting Validation
Verify the scraper recency and pagination pipeline:
```bash
cd backend
python test_pipeline_date.py
```

### Stateless Credentials Injection Test
Verify that Agent 08 successfully runs applications in-memory without contacting Firestore:
```bash
cd backend
python test_stateless_apply.py
```

---

## 4. Run Guide

To start the application locally:

### 1. Start Backend Server
Ensure Python dependencies are installed and run the API:
```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

### 2. Start Frontend Next.js Dev Server
```bash
cd website
npm install
npm run dev
```
Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard) to test.
