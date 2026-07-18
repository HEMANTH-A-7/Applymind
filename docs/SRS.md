# ApplyMind AI
## Automated Job Application Intelligence Platform
### Software Requirements Specification — v1.0 | June 2026

> **Prepared for:** Hemanth Kumar Amarthi | **Status:** DRAFT | **Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Goals](#2-product-vision--goals)
3. [9-Agent AI Architecture](#3-9-agent-ai-architecture)
4. [Technical Architecture](#4-technical-architecture)
5. [3D Interactive Website — Design Specification](#5-3d-interactive-website--design-specification)
6. [Pricing Model](#6-pricing-model)
7. [Ethical & Legal Framework](#7-ethical--legal-framework)
8. [Development Roadmap](#8-development-roadmap)
9. [The Master Prompt](#9-the-master-prompt)
10. [Glossary](#10-glossary)

---

## 1. Executive Summary

ApplyMind AI is a next-generation, fully automated job application intelligence platform that combines multi-agent AI orchestration, real-time internet scraping, ATS-optimized resume rewriting, and autonomous application submission — built to run 24/7 on behalf of the job seeker.

The platform addresses a fundamental market failure: **75% of resumes never reach human eyes** due to ATS rejection, and the average job seeker spends **11+ hours per week** manually applying to jobs with near-zero customization per role. ApplyMind AI solves both problems simultaneously.

---

### 1.1 Market Opportunity

| Metric | Data |
|--------|------|
| AI Agents Market 2025 | $7.84B → $52.62B by 2030 (CAGR 46.3%) |
| Agentic AI in HR/Recruitment | $842M (2024) → $23.17B by 2034 (CAGR 39.3%) |
| AI Recruitment Market | $660M (2025) → $1.13B by 2033 (CAGR 7.2%) |
| ATS Rejection Rate | 75% of resumes filtered before human review |
| Fortune 500 ATS Adoption | 97.8% of Fortune 500 career sites use ATS |
| Average Resume ATS Score | 48/100 on first submission (median, Q1 2026) |
| ATS-Optimized Score Uplift | +35 points after proper optimization (avg) |
| Resumes reaching human review | 3x more likely if ATS score >80% |

---

### 1.2 Competitive Landscape

| Tool | Pricing | Auto-Apply | ATS Rewrite | Gap / Weakness |
|------|---------|------------|-------------|----------------|
| LazyApply | $99–$999/yr | ✅ Yes | ⚠️ Partial | Generic outputs; low response rates (5–10x lower) |
| Simplify.jobs | Free/Freemium | ❌ No | ⚠️ Partial | Autofill only; user still clicks submit |
| Sonara AI | $20–$100/mo | ✅ Yes | ⚠️ Partial | Shut down Feb 2024; no longer operating |
| Scale.jobs | $199–$1,099 | 👤 Human | ✅ Yes | Human-assisted; slow; expensive |
| JobHire.AI | Subscription | ✅ Yes | ✅ Yes | Limited platform coverage; no 3D UI |
| Jobscan | $49.95/mo | ❌ No | ✅ Scan only | Score only; no rewrite; no submission |
| **ApplyMind AI** | **$29–$99/mo** | **✅ AI** | **✅ AI** | **Full-stack automation with per-JD AI rewrite** |

---

## 2. Product Vision & Goals

ApplyMind AI is not another bulk-apply bot. It is an **intelligent career operating system** that combines the precision of human-tailored applications with the speed and scale of full automation.

---

### 2.1 Core Value Proposition

- **Per-job ATS-optimized resume rewriting** using Claude AI — keyword injection from the exact JD
- **Full application submission automation** across LinkedIn Easy Apply, Indeed, Wellfound, email
- **Real-time internet job scraping** across 6+ job boards with deduplication
- **9-agent AI orchestration** — each agent is a specialist, none overlap
- **3D immersive interactive website** — built with Three.js, React Three Fiber, GSAP for premium brand positioning
- **Analytics dashboard** tracking response rate, conversion, A/B resume variants

---

### 2.2 Target Users

- Final-year CS/engineering students applying for internships and entry-level roles *(primary)*
- Recent graduates entering a competitive 2025/2026 job market
- Mid-career professionals in transition targeting 50–200 roles per week
- International applicants (India, SEA, LATAM) targeting US/EU remote roles
- Career changers needing resume repositioning for new domains

---

### 2.3 Success Metrics

| Metric | Target |
|--------|--------|
| Applications/Week | 50–200 auto-submitted per user per week |
| ATS Pass Rate | >80% keyword match on rewritten resumes |
| Response Rate | 10–20% of applications receive recruiter reply |
| Interview Conversion | 5–10% of responses → interview invitation |
| Time Saved (per user) | 11–15 hours/week vs manual application |
| User Retention | >70% monthly active at 60-day mark |

---

## 3. 9-Agent AI Architecture

ApplyMind AI is built on a **9-agent orchestration system**. Each agent is a fully independent specialist. No agent knows what another is doing at runtime — the orchestrator merges outputs. This is the **separation principle** that makes the system reliable and scalable.

---

### Agent Overview

| # | Agent Name | Primary Responsibility | Key Output |
|---|-----------|----------------------|------------|
| 01 | Resume Intake Agent | Parse master resume into structured schema | `resume.json` + skills/experience metadata |
| 02 | Market Research Agent | Identify top job boards, roles, salary bands | Market report + priority board list |
| 03 | Job Scraper Agent | Scrape LinkedIn, Indeed, Wellfound, Glassdoor | Normalized job database (JSON/CSV) |
| 04 | Job Match & Score Agent | Score each job posting against user's profile | Ranked job list with fit scores 0–100 |
| 05 | ATS Resume Rewriter Agent | Rewrite resume per JD for maximum ATS score | Tailored PDF/DOCX + keyword report |
| 06 | Cover Letter Agent | Generate 250-word tailored cover letter per job | Cover letter variant per posting |
| 07 | Credential Manager Agent | Manage platform logins, OAuth, sessions, tokens | Secure session store + rate limit log |
| 08 | Application Submission Agent | Auto-apply via Selenium, APIs, email SMTP | Submission log + error + manual queue |
| 09 | Analytics & Optimize Agent | Track response rate, A/B tests, pivot strategy | Dashboard + weekly optimization report |

---

### 3.1 Agent 01 — Resume Intake Agent

Responsible for parsing the user's uploaded master resume into a structured, machine-readable schema that all downstream agents can consume.

- **Accepts:** PDF, DOCX, plain text
- **Extracts:** Contact info, skills (technical + soft), experience (role, company, dates, bullets), education, certifications, projects, metrics
- **Detects:** Resume format, font, section structure, ATS-compliance status
- **Produces:** `resume.json` with nested schema + skills taxonomy + experience vector
- **Flags:** Missing sections, no quantified metrics, ATS-unsafe formatting

---

### 3.2 Agent 02 — Market Research Agent

Continuously analyzes the job market to ensure user is targeting high-ROI opportunities based on real demand signals.

- **Scrapes:** Job board category pages, salary aggregators, LinkedIn Insights
- **Produces:** Role-demand heatmap, salary range per role/location, top hiring companies, skill gap vs market
- **Updates:** Weekly refresh cycle to track market shifts

---

### 3.3 Agent 03 — Multi-Source Job Scraper Agent

The data engine. Fetches job postings 24/7 across all major platforms using platform-specific strategies.

| Platform | Method | Notes |
|----------|--------|-------|
| LinkedIn Jobs | Selenium + headless Chrome | Rate-limited ~150 req/hr; simulates logged-in browse |
| Indeed | Official API or Selenium fallback | Handles pagination, filters by role/location/date |
| Wellfound | Native GraphQL API | Clean, no CAPTCHA, startup-focused |
| Glassdoor | Selenium + JS rendering | Dynamic content, heavy JavaScript |
| GitHub Jobs / Dice | HTTP + XML parsing | RSS feeds available |
| Email Alerts | IMAP parsing | Extracts JDs from LinkedIn/Indeed/ZipRecruiter alert emails |

- **Deduplication:** `title + company + location + posting_date` hash to prevent duplicate applications
- **Normalizes:** Every posting into unified schema — title, company, JD text, salary, apply URL, method

---

### 3.4 Agent 04 — Job Match & Score Agent

Ranks scraped jobs by fit score so the system applies selectively to high-probability roles rather than blasting low-quality applications.

- **Method:** Cosine similarity between user's skills vector and JD keyword vector (sentence-transformers or TF-IDF)
- **Fit Score:** 0–100; threshold for auto-apply configurable by user (default: 65+)
- **Flags:** Overqualified (seniority mismatch), underqualified (critical missing skills), sweet spot (score 65–85)
- **Produces:** Ranked job list with score, gap explanation, apply recommendation

---

### 3.5 Agent 05 — ATS Resume Rewriter Agent

The most critical agent. Rewrites the master resume for **each individual job posting** to maximize ATS match score without fabricating qualifications.

- **Input:** `master resume.json` + target job posting JSON
- **Strategy:** Mirror JD language, inject exact keywords from requirements section, quantify all metrics, restructure bullets to lead with impact
- **Rules:** Never fabricate skills; reframe existing skills using JD terminology; maintain honesty
- **Format:** ATS-safe output — no images, no tables, no columns, no text boxes, no headers/footers
- **Fonts:** Calibri 11pt or Times New Roman 11pt
- **Output formats:** PDF (ReportLab), DOCX, plain text (3 variants per job)
- **Keyword Coverage Report:** % of required JD keywords matched, missing keywords flagged
- **Target ATS Score:** >80% match (3x higher recruiter visibility vs unoptimized)

---

### 3.6 Agent 06 — Cover Letter Generator Agent

Generates a personalized, 250-word cover letter per job that references specific company details and highlights top 2–3 relevant achievements.

- Pulls company details from JD + web search (founding year, product, recent news)
- Matches tone to company culture (startup = conversational, enterprise = formal)
- Highlights user's top 2–3 achievements most relevant to the role
- **A/B variants:** 2 styles per job — achievement-forward vs narrative-forward

---

### 3.7 Agent 07 — Credential & Session Manager Agent

Securely manages authentication across all job platforms. Prevents account lockouts by respecting rate limits.

- **Stores:** Encrypted credentials (AES-256) per platform in PostgreSQL credentials table
- **Handles:** OAuth flows (LinkedIn), form-based login (Indeed, Glassdoor), session cookie persistence
- **Rate Limits:** LinkedIn ≤50 applies/day, Indeed ≤100/day, Wellfound unlimited (API)
- **Monitors:** Login failures, CAPTCHA triggers, account warning emails
- **Rotates:** Sessions and delays to appear as natural human activity

---

### 3.8 Agent 08 — Application Submission Agent

Executes the actual job application across platforms using platform-appropriate methods.

**Platform Methods:**

| Platform | Method | Daily Cap |
|----------|--------|-----------|
| LinkedIn Easy Apply | Selenium — login → navigate → fill form → submit | 50/day |
| Indeed Apply | Native form fill via Selenium; detect internal vs external redirect | 100/day |
| Wellfound | GraphQL POST to apply endpoint | Unlimited |
| Email Applications | SMTP send with tailored email + resume attachment | Unlimited |
| Company Websites | Selenium form fill; fallback to manual queue | As available |

**CAPTCHA Strategy:**
- Option A — 2Captcha solver service ($0.50–$2/solve); adds 30–60 sec per submission
- Option B — Pause + notify user via dashboard alert; await manual solve, then resume
- Option C — Skip and flag for manual intervention (conservative approach)

**Anti-Detection / Human Simulation:**
- Randomized 2–5 sec delays between form field fills
- Simulated mouse movements before clicks
- Stagger submissions across 8am–8pm (not 3am spam)
- 50–100 applications per day per platform cap
- Vary application patterns per platform

**Submission Log Fields:**
```
timestamp | job_id | JD_url | company | resume_variant_id | 
cover_letter_id | platform | status | confirmation_text | error_text
```

**Status Codes:**
```
SUCCESS          → Application submitted, confirmation received
PENDING          → Queued, awaiting submission
CAPTCHA_REQUIRED → Paused, user intervention needed
FORM_ERROR       → Validation failed, investigating
RATE_LIMITED     → Platform cap hit, retry next day
AUTH_FAILED      → Credentials invalid/expired, refresh needed
DUPLICATE        → Already applied, skip
MANUAL_REQUIRED  → Form too complex, flagged for user
BLOCKED          → Detection likely, pause account 24hrs
```

---

### 3.9 Agent 09 — Analytics & Optimization Agent

The learning layer. Tracks what works and continuously improves the system's strategy.

- **Tracks:** Submissions sent, response rate per platform, interview conversion, rejection patterns
- **A/B Testing:** Which resume keywords convert? Which cover letter tone? Which job boards ROI?
- **Inbound Monitoring:** Parses inbox for recruiter replies, interview invites, rejections
- **Optimization Loop:** Weekly report with strategy recommendations
- **Dashboard:** Real-time funnel — scrape → match → apply → response → interview → offer

---

## 4. Technical Architecture

### 4.1 Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + FastAPI (REST API, agent orchestration) |
| AI / LLM | Anthropic Claude API — `claude-sonnet-4-6` (all 9 agents) |
| Browser Automation | Selenium 4 + Playwright (multi-browser, parallel sessions) |
| HTTP Scraping | aiohttp + BeautifulSoup4 (async, high-throughput) |
| Resume Generation | ReportLab (PDF) + python-docx (DOCX) + pypandoc |
| Task Queue | Celery + Redis (async job processing, scheduling) |
| Database | PostgreSQL (jobs, applications, credentials, resumes, analytics) |
| Frontend | React 18 + TypeScript + Tailwind CSS |
| 3D Website | Three.js + React Three Fiber + GSAP + Spline |
| Email Parsing | IMAP + Python email library (job alert parsing) |
| SMTP | Gmail API / SMTP (email application sending) |
| Encryption | AES-256 for credentials; bcrypt for user passwords |
| Deployment | Docker + Docker Compose + Nginx + Gunicorn |
| CI/CD | GitHub Actions → Vercel (frontend) + AWS/GCP (backend) |
| Monitoring | Sentry (errors) + Grafana + Prometheus (metrics) |

---

### 4.2 Database Schema

```sql
-- Core tables

users
  user_id, email, hashed_password, plan, created_at, settings_json

resumes
  resume_id, user_id, version, json_data, pdf_path, docx_path, created_at

jobs
  job_id, title, company, location, jd_text, salary, apply_url,
  apply_method, source, posted_date, scrape_date, dedup_hash

job_matches
  match_id, user_id, job_id, fit_score, gap_analysis,
  recommendation, created_at

resume_variants
  variant_id, user_id, job_id, resume_version, ats_score,
  keyword_coverage, pdf_path, docx_path

cover_letters
  cl_id, user_id, job_id, variant (A/B), text, created_at

applications
  app_id, user_id, job_id, variant_resume_id, cl_id, status,
  submitted_at, response_at, response_type, submission_log

credentials
  cred_id, user_id, platform, encrypted_username, encrypted_password,
  oauth_token, token_expires, last_login, rate_limit_hits

analytics
  metric_id, user_id, date, submissions, responses, interviews,
  offers, response_rate, a_b_winner
```

---

### 4.3 API Endpoints

#### Resume Management
```
POST  /api/resume/upload              Upload master resume (PDF/DOCX)
GET   /api/resume/parsed              Return parsed resume JSON schema
GET   /api/resume/variants/{job_id}   Get ATS-rewritten resume for a specific job
```

#### Job Discovery
```
POST  /api/jobs/scrape                Trigger manual scrape cycle
GET   /api/jobs/matches               Return ranked job matches for current user
GET   /api/jobs/{job_id}              Full job posting details
PATCH /api/jobs/{job_id}/skip         Mark job as skipped
```

#### Application Control
```
POST  /api/apply/{job_id}             Trigger application to a specific job
POST  /api/apply/batch                Apply to top-N matched jobs
GET   /api/applications               Full application history with status
GET   /api/applications/log/{app_id}  Detailed submission log
```

#### Analytics
```
GET   /api/analytics/dashboard        Funnel metrics (submissions → offers)
GET   /api/analytics/weekly           Weekly optimization report
GET   /api/analytics/ab-test          A/B test results by resume/cover variant
```

---

### 4.4 Automated Daily Workflow

```
12:00 AM  →  Job Scraper triggers across all platforms
              (LinkedIn, Indeed, Wellfound, Glassdoor, email)

12:30 AM  →  Deduplication engine removes already-seen jobs
              Inserts 500–2000 new jobs into database

01:00 AM  →  Match & Score Agent ranks all new jobs
              Returns top 100 (score ≥ 65) for the user

01:30 AM  →  ATS Rewriter generates per-job resume (parallel)
              Cover Letter Agent generates 250-word letter (parallel)

08:00 AM  →  Application Submission Agent begins applying
  to         50–100 applications/day across platforms
08:00 PM     2–5 min randomized gaps between submissions

All day   →  Analytics Agent monitors inbound email + LinkedIn
              Logs responses to dashboard in real time

Sunday    →  Weekly optimization report generated
              Strategy pivot recommendations presented to user
```

---

## 5. 3D Interactive Website — Design Specification

The ApplyMind AI marketing and app website is built as a **premium 3D immersive experience**. Interactive 3D visuals increase user engagement by 25% (Nielsen Norman Group) and Webflow's 2024 design report found 21% higher conversion on sites with advanced interactions. This isn't decoration — it's conversion strategy.

---

### 5.1 Tech Stack for 3D Website

| Tool | Purpose |
|------|---------|
| Three.js + React Three Fiber | Declarative 3D scenes in React |
| GSAP | Scroll-triggered animations, timelines, micro-interactions |
| Spline | Design 3D scenes, export to React component |
| Next.js 14 | App Router, SSR for SEO, fast page loads |
| Tailwind CSS | Utility-first styling + CSS custom properties |
| glTF/GLB | 3D model format; Draco-compressed |
| Lenis | Smooth scroll |
| GSAP ScrollTrigger | Scroll-activated animations |
| tsParticles / Three.js Points | Ambient particle background |

---

### 5.2 Color Palette & Visual Language

| Token | Hex | Usage |
|-------|-----|-------|
| Primary Background | `#0A0E1A` | Deep space navy — base |
| Card / Surface | `#131929` | Slightly lighter navy |
| Primary Accent | `#6C63FF` | Electric violet — brand color |
| Secondary Accent | `#00D4FF` | Cyan blue — highlights, glows |
| Success / Positive | `#00E5A0` | Neon mint green |
| Warning | `#FF6B35` | Electric orange |
| Error / Alert | `#FF4757` | Bright red |
| Primary Text | `#E8EAED` | Near-white |
| Secondary Text | `#9AA0B4` | Muted blue-grey |

**Visual Style:** Dark space theme · Glassmorphism cards · Neon glows · Particle systems

---

### 5.3 Page Sections & 3D Elements

#### Hero Section
- Full-viewport 3D scene: floating 3D resume document that rotates and morphs as user scrolls
- Particle system background: 2000 particles forming a neural-network constellation pattern
- Headline animates in with GSAP stagger: *"Your Dream Job. Automated."*
- CTA button glows with pulsing neon violet light effect
- Scroll indicator: animated 3D arrow descending
- Camera: slowly orbits the 3D resume model as the user hovers

#### How It Works — Agent Visualization
- 9 glowing 3D orbs in a circular constellation, one per agent
- Click/hover on any orb: expands with orbital ring, displays agent name and function
- Connection lines animate between orbs showing data flow
- GSAP scroll-triggered: orbs fly in one by one as user scrolls to section
- Central orb: "Orchestrator" pulsing, connecting all agents

#### Live Stats Counter Section
- Three floating 3D number cards: Applications Sent / Response Rate / Time Saved
- Numbers count up as user scrolls into view (GSAP CountUp animation)
- Cards have glassmorphism effect: frosted glass with neon border glow
- 3D depth: cards have parallax offset on mouse move

#### Dashboard Preview Section
- 3D mockup of the dashboard floating at 20-degree tilt
- Rotates to face user on scroll entry (Three.js rotation animation)
- Real data visualizations rendered inside the mockup using Recharts
- Mouse parallax: dashboard follows cursor movement slightly

#### Pricing Section
- Three pricing cards in 3D space: Starter, Pro, Enterprise
- Recommended plan (Pro) elevated higher and slightly larger with a glow ring
- Hover: card lifts further with shadow deepening and border glow intensifying
- Feature comparison checkmarks animate in with micro-bounce on scroll entry

#### Footer / CTA Section
- Full-width 3D landscape: abstract terrain mesh with animated vertex displacement
- Text floats above terrain with volumetric glow
- Final CTA button triggers confetti particle burst on hover

---

### 5.4 Performance Requirements

| Metric | Target |
|--------|--------|
| Initial Load | < 3 seconds on 4G mobile |
| 3D Frame Rate | ≥60fps desktop, ≥30fps mobile (LOD switching) |
| Mobile Fallback | CSS 3D transforms + Lottie on low-end devices |
| LCP | < 2.5s |
| CLS | < 0.1 |
| FID | < 100ms |
| 3D Model Budget | < 500KB (Draco compressed glTF) |
| Texture Budget | < 2MB (WebP, 1024x1024 max per texture) |

---

### 5.5 Claude Design Prompt *(Ready to Use)*

> Copy and paste this directly into Claude or Claude Design to start the 3D website build.

```
Build a premium 3D interactive marketing website for ApplyMind AI, an automated
job application AI platform. The site must feel like a dark-themed space-tech
product — think Linear.app meets Stripe meets a sci-fi command center.

Color palette: Primary background #0A0E1A (deep navy), card surfaces #131929,
primary accent #6C63FF (electric violet), secondary accent #00D4FF (cyan),
success green #00E5A0, text #E8EAED. Everything lives on a dark background.
No white backgrounds anywhere.

Technology: Next.js 14 + React Three Fiber + Three.js + GSAP + Tailwind CSS +
Spline for 3D assets. Use Lenis for smooth scrolling and GSAP ScrollTrigger
for scroll-activated animations.

Sections to build (in order):

1. HERO
Full-viewport dark 3D scene with a floating, slowly-rotating 3D resume document
at center. Particle constellation background (2000 points, neural-network
pattern). Headline: "ApplyMind AI" in 72px bold white, subheadline: "Your Dream
Job. Automated." GSAP stagger entrance. CTA button with violet glow pulse
animation. Scroll progress indicator.

2. HOW IT WORKS
9 glowing 3D orbs in a circular constellation (one per AI agent). Clicking or
hovering an orb expands it with an orbital ring and agent description. Animated
connection lines show data flow between orbs. ScrollTrigger: orbs fly in
sequentially. Central "Orchestrator" orb pulses in the middle.

3. STATS
Three glassmorphism 3D cards floating with parallax on mouse move. Numbers
count up on scroll entry: "10,000+ Applications Sent", "18% Response Rate",
"15 Hours/Week Saved". Cards have frosted-glass effect with neon border glow.

4. DASHBOARD PREVIEW
3D mockup of the app dashboard tilted at 20 degrees, rotates to face user on
scroll entry. Mouse parallax effect. Real chart elements rendered inside
the mockup using Recharts.

5. PRICING
Three 3D pricing cards in space. Pro card elevated higher with a glow ring.
Hover lifts cards and intensifies border glow. Feature rows animate in
with micro-bounce on scroll entry.

6. FOOTER CTA
Abstract 3D terrain mesh with animated vertex displacement. Text with
volumetric glow. CTA button triggers particle burst on hover.

Animations: All GSAP — stagger entrances, scroll-triggered reveals, hover
micro-interactions, smooth camera moves. No janky snaps. Everything should
feel like water.

Performance: Lazy-load Three.js. Mobile: replace 3D with CSS 3D transforms
+ Lottie. Target LCP < 2.5s. 3D models < 500KB (Draco compressed).

Typography: Inter font. Headings: 64–80px on desktop. Body: 16–18px.
Headings should have subtle text-shadow glow in the accent color.

Feel: Premium SaaS meets space station command center. Every interaction
should feel considered — nothing is static, nothing is boring. A user who
lands on this page should immediately feel this is a product worth $99/month.
```

---

## 6. Pricing Model

### 6.1 Subscription Tiers

| Feature | Starter (Free) | Pro ($29/mo) | Elite ($99/mo) |
|---------|---------------|--------------|----------------|
| Applications/Day | 5 manual | 50 auto | 200 auto |
| Platforms | Wellfound only | + LinkedIn + Indeed | + All platforms |
| Resume Rewrites | 3/month | Unlimited | Unlimited + priority |
| Cover Letters | ❌ No | ✅ AI-generated | ✅ A/B tested |
| Analytics | Basic | Full funnel | + A/B + advisor |
| CAPTCHA Handling | Manual | Solver included | Dedicated solver |
| Support | Community | Email (48hr) | Priority (4hr) |

**Revenue Model:** SaaS subscription (monthly/annual). Annual plan = 20% discount.  
**Target:** 1,000 Pro users = **$29,000 MRR** within 6 months of launch.

---

## 7. Ethical & Legal Framework

ApplyMind AI operates transparently about the risks and trade-offs of automation. Users are fully informed before any application is submitted.

### 7.1 Key Policies

**Resume Honesty**
The ATS Rewriter Agent NEVER fabricates skills. It reframes existing skills using JD terminology only. All rewriting is grounded in the user's verified experience.

**Terms of Service Disclosure**
LinkedIn and Indeed prohibit automated scraping and applying. Users see a clear disclosure before connecting platforms. Risk of account suspension is the user's responsibility.

**Responsible Rate Limiting**
Applications are staggered to simulate human behavior — 50–100/day per platform, 2–5 minute delays, 8am–8pm only. This reduces detection risk but cannot eliminate it.

**Data Privacy**
All user data (resume, credentials, job history) is encrypted at rest (AES-256). Credentials are never stored in plaintext. Users can delete all data at any time.

**CAPTCHA Ethics**
The platform offers user-solve, skip, or paid solver options. No dark patterns. Users choose their approach.

**GDPR Compliance**
EU users can request data export or deletion within 72 hours. Data minimization practiced — only data needed for function is stored.

> **Required UI Disclaimer:**  
> *"This tool automates job applications. By using it, you accept risk of account suspension on LinkedIn/Indeed. Use responsibly. Review your first 20 applications manually before enabling full automation."*

---

## 8. Development Roadmap

| Phase | Timeline | Deliverable |
|-------|----------|-------------|
| Phase 1 | Week 1–2 | Resume Intake Agent + Job Scraper (Wellfound, Indeed) + PostgreSQL schema |
| Phase 2 | Week 3–4 | Match & Score Agent + ATS Rewriter Agent (Claude API) + ReportLab PDF output |
| Phase 3 | Week 5–6 | Application Submission — Wellfound (GraphQL) + email + submission logger |
| Phase 4 | Week 7–8 | LinkedIn Easy Apply (Selenium) + CAPTCHA handling + Credential Manager |
| Phase 5 | Week 9 | Cover Letter Generator + A/B variant system + Indeed/Glassdoor submission |
| Phase 6 | Week 10 | Analytics Dashboard (React + Recharts) + response tracking (IMAP) |
| Phase 7 | Week 11–12 | 3D Website (Three.js + React Three Fiber + GSAP) + landing + pricing pages |
| Phase 8 | Week 13 | Docker + deployment (AWS/GCP) + CI/CD + security audit + beta launch |
| Phase 9 | Ongoing | A/B optimization + Market Research Agent + additional job boards |

**Total MVP Timeline: 13 weeks.** First paid users possible at Phase 3 completion (Week 6) with Wellfound + email submission live.

---

## 9. The Master Prompt

> Use this prompt to initialize the entire system with Claude or any capable LLM. Run it once to generate the foundational architecture plan across all 9 agents. Then use the per-agent sub-prompts below to go deeper on each.

---

### 9.1 The Master Prompt *(Ready to Use)*

```
Build ApplyMind AI: a fully automated job application intelligence platform
that scrapes the internet for job postings and applies to them on the user's
behalf with per-job ATS-optimized resumes and tailored cover letters.

Target users: Final-year CS/engineering students, recent graduates, career
changers, and international job seekers who want to apply to 50–200 jobs per
week automatically with maximum ATS score per application.

Core workflow: User uploads master resume → system parses it into structured
schema → scrapes jobs from LinkedIn, Indeed, Wellfound, Glassdoor, GitHub
Jobs, email alerts → scores each job against user profile (0–100 fit score)
→ rewrites resume per job JD for max ATS keyword coverage → generates
tailored cover letter → submits application autonomously via Selenium browser
automation, platform APIs, and SMTP email → logs all submissions → monitors
inboxes for responses → tracks analytics and optimizes strategy weekly.

Split this across nine independent specialized agents:

1. RESUME INTAKE AGENT
Parse master resume (PDF/DOCX) into structured JSON schema. Extract: skills,
experience, projects, certifications, metrics, education. Detect ATS compliance
issues. Produce: resume.json + skills taxonomy + formatting metadata.

2. MARKET RESEARCH AGENT
Identify top job boards per role, salary ranges, in-demand skills, best-fit
companies. Produce: market report + priority platform list + skill gap vs
market analysis.

3. JOB SCRAPER AGENT
Continuously scrape LinkedIn (Selenium + headless Chrome), Indeed (API or
Selenium), Wellfound (GraphQL API), Glassdoor (Selenium), GitHub Jobs, email
alert parsing (IMAP), RSS feeds. Normalize all postings to unified schema.
Deduplicate by hash. Run daily at midnight. Produce: normalized job database
(JSON/CSV) with 500–2000 new jobs/day.

4. JOB MATCH AGENT
Score each new job against user resume (cosine similarity on skills vectors).
Threshold: apply to jobs scoring 65+. Flag overqualified (mismatch) and
underqualified (skill gap). Produce: ranked opportunity list + gap analysis
+ apply/skip recommendations.

5. ATS RESUME REWRITER AGENT
Rewrite master resume for each individual job posting. Mirror JD language
exactly. Inject required keywords naturally. Quantify all metrics. Never
fabricate skills — reframe only. Enforce ATS-safe formatting (no images,
tables, columns, graphics). Output in PDF (Calibri/Times New Roman 11pt),
DOCX, and plain text. Produce: per-job resume variants + keyword coverage
report targeting >80% match.

6. COVER LETTER AGENT
Generate 250-word cover letter per job. Reference company-specific details
(mission, product, recent news). Match tone to company culture. Highlight
user's top 2–3 achievements most relevant to role. A/B variant per
application. Produce: cover letters per posting.

7. CREDENTIAL MANAGER AGENT
Securely store and manage user credentials for LinkedIn, Indeed, Wellfound,
Glassdoor, email. Handle OAuth and form-based auth. Maintain session cookies.
Enforce platform rate limits (LinkedIn ≤50/day, Indeed ≤100/day). Monitor
for account warning signals. Produce: encrypted session store + rate limit
tracker.

8. APPLICATION SUBMISSION AGENT
Auto-apply across platforms: LinkedIn Easy Apply (Selenium), Indeed
(Selenium), Wellfound (GraphQL API), email applications (SMTP), company
websites (Selenium form fill). Handle dynamic form questions using
LLM-generated answers. Manage CAPTCHAs (solver service / pause-and-notify
/ skip). Apply with human-like delays (2–5 sec between fields, 2–5 min
between applications, 8am–8pm window, 50–100/day cap). Log every submission:
timestamp, JD URL, resume version, cover letter variant, status
(SUCCESS/FAILED/CAPTCHA/MANUAL). Produce: submission log + manual
intervention queue + error reports.

9. ANALYTICS AGENT
Track full application funnel (scraped → matched → applied → responded →
interviewed → offered). Monitor inbound emails and LinkedIn for recruiter
responses. A/B test resume variants and cover letter styles. Generate weekly
optimization report with strategy pivot recommendations. Produce: real-time
dashboard + weekly report.

Each agent works independently first. The orchestrator merges outputs.
Separation is the system:
- Resume Intake Agent doesn't know about job boards.
- Scraper Agent doesn't touch resumes.
- ATS Rewriter doesn't decide which jobs to apply to.
- Submission Agent doesn't optimize resumes.
- Analytics Agent doesn't submit applications.

Each agent produces one real, standalone artifact:
  01 → resume.json schema
  02 → market analysis report
  03 → job database (JSON/CSV)
  04 → ranked match list with scores
  05 → ATS-optimized resume variants (PDF/DOCX/TXT) per job
  06 → cover letter variants per job
  07 → encrypted credential store + session manager
  08 → submission log + error report
  09 → analytics dashboard + weekly optimization report

Merge flow:
resume → parsed → jobs scraped → matches scored → resumes rewritten
→ applications submitted → responses tracked → strategy optimized → repeat

Tech stack: Python + FastAPI (backend), Claude claude-sonnet-4-6 (all 9
agents), Selenium 4 + Playwright (browser automation), aiohttp +
BeautifulSoup4 (scraping), ReportLab + python-docx (resume generation),
Celery + Redis (task queue), PostgreSQL (all data), React 18 + TypeScript
+ Tailwind (frontend), Three.js + React Three Fiber + GSAP (3D website),
Docker + AWS (deployment).

Constraints:
- Never fabricate skills. Reframe; never lie.
- Never store credentials in plaintext. AES-256 encryption.
- Rate limit all platforms to appear human.
- Show user ToS disclosure before connecting any platform.
- Log every single application submission with full metadata.
- User controls daily application limits (default 50, max 200).
- GDPR compliant — data export and deletion on request.

For each agent produce:
(1) complete technical specification
(2) data input/output schema
(3) implementation pseudocode
(4) error handling strategy
(5) integration points with other agents

Then produce a unified orchestration plan showing how all 9 agents connect
in the daily automation cycle.
```

---

### 9.2 Agent 05 — ATS Resume Rewriter Deep-Dive Prompt

```
You are the ATS Resume Rewriter Agent for ApplyMind AI.

Input:
  (1) master resume as JSON schema — skills, experience, projects, metrics
  (2) target job posting JSON — title, company, full JD text, required skills,
      preferred skills

Your job: Rewrite the resume for maximum ATS keyword match score targeting
>80% coverage.

Rules:
1. Mirror JD language exactly — if JD says "FastAPI", don't write "REST
   framework". If JD says "React.js", don't write "ReactJS".
2. Inject JD keywords naturally into bullet points — never keyword-stuff
   at the bottom of the page.
3. Quantify everything — "improved performance" becomes "improved API
   response time by 34%".
4. Never fabricate — only reframe. User has a React project? If JD wants
   "frontend development", use that framing.
5. ATS-safe format ONLY: no images, no tables, no columns, no text boxes,
   no headers/footers with critical info, no special characters.
6. Font: Calibri 11pt or Times New Roman 11pt. Single column. Standard
   sections: Summary, Skills, Experience, Projects, Education, Certifications.
7. 1–2 pages maximum. Prefer 1 page for < 3 years experience.

Output:
- ATS-optimized resume as PDF (ReportLab) + DOCX (python-docx) + plain text
- Keyword coverage report: required JD keywords, which matched, which missing,
  final match %
- Change log: every bullet rewritten and why
- ATS score estimate: 0–100

Do NOT change factual content — only language, structure, and emphasis.
```

---

### 9.3 Agent 08 — Application Submission Deep-Dive Prompt

```
You are the Application Submission Agent for ApplyMind AI. You execute
autonomous job applications on behalf of users using Selenium, platform
APIs, and SMTP.

For each job in the submission queue (status = READY):

LINKEDIN EASY APPLY:
- Login via Credential Manager session
- Navigate to job URL, locate Easy Apply button
- Fill form: name, email, phone (from user profile), resume upload (ATS PDF),
  cover letter (paste text)
- Dynamic questions:
    text fields → LLM-generate answer from resume + JD context
    dropdowns   → match to user skills list
    yes/no      → safe defaults
- Submit → capture confirmation → log SUCCESS
- Delay: 2–5 min to next application. Daily cap: 50.

INDEED APPLY:
- Detect if native Indeed form or external redirect
- Native: fill form via Selenium, upload resume, submit
- External redirect: attempt Selenium form-fill on company site
- If form too complex → add to MANUAL queue
- Daily cap: 100.

WELLFOUND (GraphQL API):
- POST to apply endpoint with job_id, resume_url, cover_letter_text
- Log response — no CAPTCHA, no delay needed, instant

EMAIL APPLICATIONS:
- Detect "apply via email" in JD or apply URL
- Extract hiring email using regex
- Compose: subject = "[Name] — Application for [Job Title]"
  body = cover letter text
  attachment = ATS PDF resume
- Send via Gmail API / SMTP
- Log sent email with full metadata

ERROR HANDLING:
- CAPTCHA → Option A: submit to 2Captcha, wait 30–60s, retry
           → Option B: pause + dashboard alert, await user solve, resume
- Form validation error → capture error, fix field, retry, log
- Rate limit hit → stop platform submissions, retry next day, log RATE_LIMITED
- Account warning → pause all activity, alert user, log BLOCKED
- Login failure → refresh OAuth token; if fails → notify user, log AUTH_FAILED

All submissions must log:
  timestamp, job_id, JD_url, company, resume_variant_id, cover_letter_id,
  platform, submission_status, confirmation_text, error_text

Human simulation requirements:
- Randomized 2–5 sec delays between form field fills
- Simulated mouse movements before all clicks
- Randomized submission order across platforms
- Submissions ONLY during 8am–8pm in user's local timezone
```

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| ATS | Applicant Tracking System — software used by employers to filter resumes before human review |
| ATS Score | Percentage of job description keywords matched in the resume (target: >80%) |
| Agent | An AI module with a single specialized responsibility in the 9-agent system |
| Orchestrator | The scheduler/workflow engine that coordinates all 9 agents and merges outputs |
| Dedup Hash | A unique fingerprint of each job posting used to prevent duplicate applications |
| Fit Score | 0–100 similarity score between user's skills and a job posting's requirements |
| glTF/GLB | 3D model format used for web delivery; compressed with Draco algorithm |
| GSAP | GreenSock Animation Platform — JavaScript animation library for all site motion |
| React Three Fiber | React renderer for Three.js — enables declarative 3D scenes in React |
| Selenium | Browser automation framework used to simulate human job application interactions |
| ReportLab | Python library for programmatic PDF generation (resume output) |
| Celery | Distributed task queue for handling async and scheduled background jobs |
| OAuth | Authentication protocol used by LinkedIn and other platforms for secure login |
| IMAP | Email protocol used to monitor inboxes for recruiter responses and job alerts |
| SMTP | Email sending protocol used for email-based job applications |
| Cosine Similarity | Mathematical measure of similarity between two skill vectors (0 = unrelated, 1 = identical) |
| Draco | Google's 3D geometry compression algorithm used to reduce glTF model file sizes |
| LCP | Largest Contentful Paint — Core Web Vitals metric for perceived page load speed |

---

*ApplyMind AI — SRS v1.0 — June 2026*  
*Built for Hemanth Kumar Amarthi · [github.com/HEMANTH-A-7](https://github.com/HEMANTH-A-7) · [linkedin.com/in/hemanth-kumar-amarthi](https://linkedin.com/in/hemanth-kumar-amarthi)*
