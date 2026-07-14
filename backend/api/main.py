"""
ApplyMind AI — FastAPI Main Application
All REST API routes wired up — 9 agents fully integrated.
"""
import os
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, EmailStr
from loguru import logger
import asyncio
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from core.config import get_settings
from core.security import hash_password, verify_password, create_access_token
from core.firebase_admin import verify_firebase_token, optional_firebase_token, get_db
from core.rate_limit import (
    limiter, rate_limit_handler, RateLimitExceededError,
    AUTH_LIMIT, UPLOAD_LIMIT, SCRAPE_LIMIT, APPLY_LIMIT, GENERAL_LIMIT, REPORT_LIMIT,
)
from core.cache import get_cache, TTL_MARKET_REPORT, TTL_WEEKLY_REPORT, TTL_ATS_REWRITE

settings = get_settings()

if settings.sentry_dsn:
    logger.info("Initializing Sentry in FastAPI backend")
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[FastApiIntegration()],
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

# ─── Docs only in development ───────────────────────────────────────────────
_docs_url = "/docs" if settings.environment != "production" else None
_redoc_url = "/redoc" if settings.environment != "production" else None
_openapi_url = "/openapi.json" if settings.environment != "production" else None

app = FastAPI(
    title="ApplyMind AI API",
    description="9-Agent automated job application platform powered by Groq AI",
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

async def verify_admin_token(token: dict = Depends(verify_firebase_token)) -> dict:
    """Dependency that ensures the authenticated user is an administrator."""
    uid = token["uid"]
    db = get_db()
    user_doc = db.get_user(uid)
    if not user_doc or not user_doc.get("isAdmin"):
        logger.warning(f"Unauthorized admin access attempt by user {uid}")
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return token

# ─── Attach rate limiter ──────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceededError, rate_limit_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://applymind.ai",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Upload directory ───
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ─── Firebase Firestore is wired for all data storage ───


# ─── Root redirect → /docs ───
from fastapi.responses import RedirectResponse

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# ─── Health ───
@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "model": settings.groq_model,
        "version": "1.0.0",
        "agents": [f"agent_0{i}" for i in range(1, 10)],
        "docs": "http://localhost:8000/docs",
        "frontend": "http://localhost:3000",
        "dashboard": "http://localhost:3000/dashboard",
    }

@app.get("/status", tags=["System"])
async def status(token: Optional[dict] = Depends(optional_firebase_token)):
    """Quick system status — check what's loaded."""
    if not token:
        return {
            "backend": "running",
            "resume_loaded": False,
            "jobs_scraped": 0,
            "applications_logged": 0,
            "users_registered": 0,
            "market_reports_cached": [],
            "groq_model": settings.groq_model,
            "daily_limit": settings.daily_app_limit,
            "auto_apply_threshold": settings.auto_apply_threshold,
        }

    db = get_db()
    resume = db.get_latest_resume(token["uid"])
    jobs = db.get_jobs(token["uid"])
    apps = db.get_applications(token["uid"])

    return {
        "backend": "running",
        "resume_loaded": resume is not None,
        "jobs_scraped": len(jobs),
        "applications_logged": len(apps),
        "users_registered": 1,
        "market_reports_cached": [],
        "groq_model": settings.groq_model,
        "daily_limit": settings.daily_app_limit,
        "auto_apply_threshold": settings.auto_apply_threshold,
    }


# Legacy Auth Routes removed. Authentication is now handled client-side via Firebase Auth.


# ═══════════════════════════════════════════════
#  RESUME ROUTES
# ═══════════════════════════════════════════════

@app.post("/api/resume/upload", tags=["Resume"])
@limiter.limit(UPLOAD_LIMIT)
async def upload_resume(request: Request, file: UploadFile = File(...), token: dict = Depends(verify_firebase_token)):
    """Upload and parse a master resume (PDF/DOCX/TXT)."""
    allowed = {".pdf", ".docx", ".doc", ".txt"}
    ext = Path(file.filename or "resume.pdf").suffix.lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported. Use: {allowed}")

    file_path = UPLOAD_DIR / f"resume_{datetime.utcnow().timestamp()}{ext}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run Agent 01
    from agents import agent_01_resume_intake
    result = agent_01_resume_intake.run(str(file_path))

    if result["status"] == "error":
        raise HTTPException(status_code=422, detail=result["message"])

    db = get_db()
    db.save_resume(token["uid"], result["parsed_data"])

    # Invalidate user cache on resume upload
    try:
        get_cache().invalidate_user(token["uid"])
    except Exception as e:
        logger.debug(f"Cache invalidation error during upload: {e}")

    logger.info(f"Resume uploaded and parsed for user {token['uid']}: {file.filename}")
    return {
        "status": "success",
        "filename": file.filename,
        "word_count": result["word_count"],
        "skills_found": len(result["parsed_data"].get("skills_flat", [])),
        "ats_issues": result["ats_issues"],
        "parsed_data": result["parsed_data"],
    }


@app.get("/api/resume/parsed", tags=["Resume"])
@limiter.limit(GENERAL_LIMIT)
async def get_parsed_resume(request: Request, token: dict = Depends(verify_firebase_token)):
    """Get the currently parsed resume JSON."""
    db = get_db()
    resume = db.get_latest_resume(token["uid"])
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")
    return resume


@app.delete("/api/resume/{resume_id}", tags=["Resume"])
@limiter.limit(GENERAL_LIMIT)
async def delete_resume(request: Request, resume_id: str, token: dict = Depends(verify_firebase_token)):
    """Soft-delete a parsed resume."""
    db = get_db()
    success = db.soft_delete_resume(token["uid"], resume_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found or already deleted")
    # Invalidate user cache on resume deletion
    try:
        get_cache().invalidate_user(token["uid"])
    except Exception as e:
        logger.debug(f"Cache invalidation error during deletion: {e}")
    return {"status": "success", "message": "Resume soft-deleted"}


# ═══════════════════════════════════════════════
#  JOB DISCOVERY ROUTES
# ═══════════════════════════════════════════════

class ScrapeRequest(BaseModel):
    keywords: List[str] = ["software engineer", "python developer"]
    location: str = "Remote"
    # Verified-working public sources; "indeed"/"wellfound" are opt-in (both 403 anonymous scraping)
    # "adzuna" is a no-op unless ADZUNA_APP_ID/ADZUNA_APP_KEY are configured.
    platforms: List[str] = [
        "linkedin", "remotive", "arbeitnow", "jobicy", "themuse",
        "remoteok", "hn", "search_engine", "adzuna",
    ]
    max_jobs: int = 100
    sort_by: str = "date"
    country: str = "in"  # Adzuna country code; ignored by other sources


@app.get("/api/jobs/matches", tags=["Jobs"])
@limiter.limit(GENERAL_LIMIT)
async def get_job_matches(request: Request, min_score: int = 65, limit: int = 50, sort_by: str = "score", token: dict = Depends(verify_firebase_token)):
    """Return ranked job matches for current user."""
    db = get_db()
    matches = db.get_jobs(token["uid"], min_score=min_score, limit=100)
    
    # Sort in-memory
    if sort_by == "date":
        matches.sort(key=lambda j: j.get("posted_date") or "", reverse=True)
    else:
        matches.sort(key=lambda j: j.get("fit_score", 0), reverse=True)
        
    matches = matches[:limit]
    apply_queue_count = sum(1 for j in matches if j.get("recommendation") in ["strong_apply", "apply"])
    return {"matches": matches, "total": len(matches), "apply_queue_count": apply_queue_count}


@app.get("/api/jobs/{job_id}", tags=["Jobs"])
@limiter.limit(GENERAL_LIMIT)
async def get_job(request: Request, job_id: str, token: dict = Depends(verify_firebase_token)):
    """Get full details for a specific job posting."""
    db = get_db()
    doc = db.db.collection("users").document(token["uid"]).collection("jobs").document(job_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Job not found")
    return doc.to_dict()


# ═══════════════════════════════════════════════
#  ATS REWRITER ROUTES
# ═══════════════════════════════════════════════

class RewriteRequest(BaseModel):
    job_id: Optional[str] = None
    job_title: str
    company: str
    jd_text: str


@app.post("/api/resume/rewrite", tags=["Resume"])
@limiter.limit(GENERAL_LIMIT)
async def rewrite_resume(request: Request, req: RewriteRequest, token: dict = Depends(verify_firebase_token)):
    """Rewrite resume for a specific job using Agent 05."""
    db = get_db()
    resume = db.get_latest_resume(token["uid"])
    if not resume:
        raise HTTPException(status_code=400, detail="Upload a resume first")

    # Cache check
    import hashlib
    import json
    resume_str = json.dumps(resume, sort_keys=True)
    resume_hash = hashlib.md5(resume_str.encode()).hexdigest()
    job_key = req.job_id or f"{req.job_title}_{req.company}"
    cache = get_cache()
    cached_val = cache.get("ats", resume_hash, job_key)
    if cached_val:
        logger.info(f"Returning cached ATS rewrite for job: {job_key}")
        return cached_val

    from agents import agent_05_ats_rewriter
    result = agent_05_ats_rewriter.run(
        resume,
        {"title": req.job_title, "company": req.company, "jd_text": req.jd_text}
    )

    if result["status"] == "error":
        status_code = 503 if "GROQ_API_KEY" in result["message"] else 500
        raise HTTPException(status_code=status_code, detail=result["message"])

    cache.set("ats", resume_hash, job_key, value=result, ttl=TTL_ATS_REWRITE)
    return result


# ═══════════════════════════════════════════════
#  COVER LETTER ROUTES
# ═══════════════════════════════════════════════

@app.post("/api/cover-letter/generate", tags=["Cover Letter"])
@limiter.limit(GENERAL_LIMIT)
async def generate_cover_letter(request: Request, req: RewriteRequest, variant: str = "A", token: dict = Depends(verify_firebase_token)):
    """Generate a cover letter for a job using Agent 06."""
    db = get_db()
    resume = db.get_latest_resume(token["uid"])
    if not resume:
        raise HTTPException(status_code=400, detail="Upload a resume first")

    from agents import agent_06_cover_letter
    result = agent_06_cover_letter.run(
        resume,
        {"title": req.job_title, "company": req.company, "jd_text": req.jd_text},
        variant=variant,
    )

    if result["status"] == "error":
        status_code = 503 if "GROQ_API_KEY" in result["message"] else 500
        raise HTTPException(status_code=status_code, detail=result["message"])

    return result


# ═══════════════════════════════════════════════
#  APPLICATION ROUTES
# ═══════════════════════════════════════════════

class ApplicationLog(BaseModel):
    job_id: str
    job_title: str
    company: str
    platform: str
    status: str
    submitted_at: Optional[str] = None


@app.get("/api/applications", tags=["Applications"])
@limiter.limit(GENERAL_LIMIT)
async def get_applications(request: Request, status: Optional[str] = None, limit: int = 100, token: dict = Depends(verify_firebase_token)):
    """Return application history."""
    db = get_db()
    apps = db.get_applications(token["uid"], limit=limit)
    if status:
        apps = [a for a in apps if a.get("status") == status]
    return {"applications": apps, "total": len(apps)}


@app.post("/api/applications/log", tags=["Applications"])
@limiter.limit(GENERAL_LIMIT)
async def log_application(request: Request, app_log: ApplicationLog, token: dict = Depends(verify_firebase_token)):
    """Log a submitted application."""
    db = get_db()
    entry = app_log.model_dump()
    entry["submitted_at"] = entry.get("submitted_at") or datetime.utcnow().isoformat()
    app_id = db.log_application(token["uid"], entry)
    entry["id"] = app_id

    # Invalidate weekly report cache since data changed
    try:
        get_cache().delete("report", token["uid"], "weekly")
    except Exception as e:
        logger.debug(f"Cache invalidation error during application log: {e}")

    return {"status": "logged", "entry": entry}


@app.delete("/api/applications/{app_id}", tags=["Applications"])
@limiter.limit(GENERAL_LIMIT)
async def delete_application(request: Request, app_id: str, token: dict = Depends(verify_firebase_token)):
    """Soft-delete an application log entry."""
    db = get_db()
    success = db.soft_delete_application(token["uid"], app_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found or already deleted")
    # Invalidate weekly report cache since data changed
    try:
        get_cache().delete("report", token["uid"], "weekly")
    except Exception as e:
        logger.debug(f"Cache invalidation error during application deletion: {e}")
    return {"status": "success", "message": "Application log soft-deleted"}


# ═══════════════════════════════════════════════
#  ANALYTICS ROUTES
# ═══════════════════════════════════════════════

@app.get("/api/analytics/dashboard", tags=["Analytics"])
@limiter.limit(GENERAL_LIMIT)
async def get_dashboard(request: Request, token: dict = Depends(verify_firebase_token)):
    """Return funnel metrics for the dashboard."""
    db = get_db()
    apps = db.get_applications(token["uid"])
    from agents import agent_09_analytics
    result = agent_09_analytics.run("funnel_metrics", submission_logs=apps)
    return result


@app.get("/api/analytics/weekly", tags=["Analytics"])
@limiter.limit(REPORT_LIMIT)
async def get_weekly_report(request: Request, token: dict = Depends(verify_firebase_token)):
    """Generate AI-powered weekly optimization report using Agent 09 + Groq."""
    cache = get_cache()
    uid = token["uid"]
    cached = cache.get("report", uid, "weekly")
    if cached:
        logger.info(f"Returning cached weekly report for user {uid}")
        return cached

    db = get_db()
    apps = db.get_applications(uid)
    from agents import agent_09_analytics
    result = agent_09_analytics.run("weekly_report", submission_logs=apps)

    cache.set("report", uid, "weekly", value=result, ttl=TTL_WEEKLY_REPORT)
    return result


@app.get("/api/analytics/ab-test", tags=["Analytics"])
@limiter.limit(GENERAL_LIMIT)
async def get_ab_test(request: Request, token: dict = Depends(verify_firebase_token)):
    """A/B test results for resume/cover letter variants."""
    db = get_db()
    apps = db.get_applications(token["uid"])
    from agents import agent_09_analytics
    result = agent_09_analytics.run("ab_analysis", submission_logs=apps)
    return result


# ═══════════════════════════════════════════════
#  MARKET RESEARCH ROUTES
# ═══════════════════════════════════════════════

class MarketResearchRequest(BaseModel):
    role: str = "software engineer"
    location: str = "Remote"
    skills: List[str] = []


@app.post("/api/market/research", tags=["Market Research"])
@limiter.limit(REPORT_LIMIT)
async def run_market_research(request: Request, req: MarketResearchRequest, token: dict = Depends(verify_firebase_token)):
    """Run Agent 02 market research for a role."""
    cache = get_cache()
    # Cache key: market:{role}:{location}
    cached = cache.get("market", req.role.lower(), req.location.lower())
    if cached:
        logger.info(f"Returning cached market research for {req.role} in {req.location}")
        db = get_db()
        db.save_report(token["uid"], f"market_{req.role}", cached)
        return cached

    import asyncio
    from agents import agent_02_market_research
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: agent_02_market_research.run(req.role, req.location, req.skills)
    )
    db = get_db()
    db.save_report(token["uid"], f"market_{req.role}", result)

    cache.set("market", req.role.lower(), req.location.lower(), value=result, ttl=TTL_MARKET_REPORT)
    return result


@app.get("/api/market/report", tags=["Market Research"])
@limiter.limit(GENERAL_LIMIT)
async def get_market_report(request: Request, role: str = "software engineer", token: dict = Depends(verify_firebase_token)):
    """Get cached market research report."""
    db = get_db()
    report = db.get_report(token["uid"], f"market_{role}")
    if not report:
        raise HTTPException(status_code=404, detail="No market report for this role. POST /api/market/research first.")
    return report


# ═══════════════════════════════════════════════
#  SCRAPE ROUTES (Agent 03)
# ═══════════════════════════════════════════════

@app.post("/api/jobs/scrape", tags=["Jobs"])
@limiter.limit(SCRAPE_LIMIT)
async def trigger_scrape(request: Request, req: ScrapeRequest, background_tasks: BackgroundTasks, token: dict = Depends(verify_firebase_token)):
    """Trigger Agent 03 job scraper across platforms."""
    from agents import agent_03_job_scraper

    db = get_db()
    resume = db.get_latest_resume(token["uid"])
    if not resume:
        raise HTTPException(status_code=400, detail="Upload a resume first — jobs are scored against it, so scraping needs one to save any results.")

    async def do_scrape_async(uid: str):
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: agent_03_job_scraper.run(
                keywords=req.keywords,
                location=req.location,
                platforms=req.platforms,
                max_jobs=req.max_jobs,
                sort_by=req.sort_by,
                country=req.country,
            )
        )
        raw_jobs = result.get("jobs", [])

        # Score jobs using Agent 04
        from agents import agent_04_job_match
        match_result = agent_04_job_match.run(resume, raw_jobs)
        ranked_jobs = match_result.get("ranked_jobs", [])

        # Save to Firestore
        db.save_jobs(uid, ranked_jobs)
        logger.info(f"Scraped and saved {len(ranked_jobs)} matched jobs for user {uid}")

    background_tasks.add_task(do_scrape_async, token["uid"])
    return {
        "status": "queued",
        "message": f"Scraping {req.platforms} for {req.keywords} — check /api/jobs/matches in ~15 seconds",
    }


# ═══════════════════════════════════════════════
#  CREDENTIAL ROUTES (Agent 07)
# ═══════════════════════════════════════════════

class CredentialRequest(BaseModel):
    platform: str
    username: str
    password: str
    oauth_token: str = ""


@app.post("/api/credentials/store", tags=["Credentials"])
@limiter.limit(AUTH_LIMIT)
async def store_credential(request: Request, req: CredentialRequest, token: dict = Depends(verify_firebase_token)):
    """Store encrypted credentials for a platform via Agent 07."""
    from agents import agent_07_credential_manager
    result = agent_07_credential_manager.run(
        "store_cred", token["uid"], req.platform,
        username=req.username, password=req.password, oauth_token=req.oauth_token,
    )
    return {"status": "stored", "platform": req.platform}


@app.get("/api/credentials/status", tags=["Credentials"])
@limiter.limit(GENERAL_LIMIT)
async def get_credential_status(request: Request, token: dict = Depends(verify_firebase_token)):
    """Get session status across all platforms for a user."""
    from agents import agent_07_credential_manager
    return agent_07_credential_manager.run("status", token["uid"])


# ═══════════════════════════════════════════════
#  BATCH APPLY ROUTES (Agent 08)
# ═══════════════════════════════════════════════

class PlatformCredential(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    oauth_token: Optional[str] = None


class CredentialsPayload(BaseModel):
    linkedin: Optional[PlatformCredential] = None
    wellfound: Optional[PlatformCredential] = None


class BatchApplyRequest(BaseModel):
    candidate_name: str = "Candidate"
    candidate_email: str = ""
    daily_limit: int = 50
    min_score: int = 65
    apply_method_override: Optional[str] = None
    credentials: Optional[CredentialsPayload] = None


class SingleApplyRequest(BaseModel):
    credentials: Optional[CredentialsPayload] = None


@app.post("/api/apply/batch", tags=["Applications"])
@limiter.limit(APPLY_LIMIT)
async def batch_apply(request: Request, req: BatchApplyRequest, background_tasks: BackgroundTasks, token: dict = Depends(verify_firebase_token)):
    """Trigger Agent 08 to batch apply to all qualified jobs in the queue."""
    db = get_db()
    resume = db.get_latest_resume(token["uid"])
    if not resume:
        raise HTTPException(status_code=400, detail="Upload a resume first")

    jobs = db.get_jobs(token["uid"], min_score=req.min_score)
    if not jobs:
        raise HTTPException(status_code=400, detail="No jobs scraped yet. Scrape first!")

    def do_apply(uid: str, resume_data: dict, jobs_list: list):
        from agents import agent_08_application_submission
        apply_queue = [j for j in jobs_list if j.get("recommendation") in ["strong_apply", "apply"]][:req.daily_limit]
        if not apply_queue:
            logger.warning("No jobs meet the score threshold")
            return
        
        # Convert credentials payload if present
        creds_dict = req.credentials.model_dump() if req.credentials else None
        
        # Submit
        result = agent_08_application_submission.run(
            apply_queue, uid,
            candidate_name=req.candidate_name,
            candidate_email=req.candidate_email,
            daily_limit=req.daily_limit,
            apply_method_override=req.apply_method_override,
            credentials=creds_dict,
        )
        # Log successful submissions to Firestore
        db_instance = get_db()
        for entry in result.get("submission_log", []):
            db_instance.log_application(uid, entry)
        logger.info(f"Batch apply done: {result.get('success_count')} success")

    background_tasks.add_task(do_apply, token["uid"], resume, jobs)
    return {"status": "queued", "message": f"Applying to top {req.daily_limit} matched jobs in background"}


@app.post("/api/apply/{job_id}", tags=["Applications"])
@limiter.limit(APPLY_LIMIT)
async def apply_single_job(request: Request, job_id: str, req: Optional[SingleApplyRequest] = None, token: dict = Depends(verify_firebase_token)):
    """Trigger Agent 08 to apply to a specific job using its ID."""
    db = get_db()
    resume = db.get_latest_resume(token["uid"])
    if not resume:
        raise HTTPException(status_code=400, detail="Upload a resume first")

    # Fetch specific job from user's jobs collection
    job_ref = db.db.collection("users").document(token["uid"]).collection("jobs").document(job_id)
    doc = job_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Job not found in queue")
    job = doc.to_dict()
    job["job_id"] = doc.id

    from agents import agent_08_application_submission
    creds_dict = req.credentials.model_dump() if req and req.credentials else None
    
    result = agent_08_application_submission.run(
        [job], token["uid"],
        candidate_name=resume.get("contact", {}).get("name", "Candidate"),
        candidate_email=token.get("email", ""),
        daily_limit=1,
        credentials=creds_dict,
    )

    # Log submission to Firestore
    for entry in result.get("submission_log", []):
        db.log_application(token["uid"], entry)

    if result.get("success_count", 0) > 0:
        return {"status": "success", "message": "Application submitted successfully"}
    else:
        error_msg = result.get("submission_log", [{}])[0].get("error_text", "Submission failed")
        raise HTTPException(status_code=500, detail=f"Application failed: {error_msg}")


# ═══════════════════════════════════════════════
#  PDF DOWNLOAD (ReportLab)
# ═══════════════════════════════════════════════

@app.post("/api/resume/generate-pdf", tags=["Resume"])
@limiter.limit(GENERAL_LIMIT)
async def generate_pdf(request: Request, req: RewriteRequest, token: dict = Depends(verify_firebase_token)):
    """Rewrite resume for a job and generate downloadable ATS-safe PDF."""
    db = get_db()
    resume = db.get_latest_resume(token["uid"])
    if not resume:
        raise HTTPException(status_code=400, detail="Upload a resume first")

    # Agent 05: Rewrite
    from agents import agent_05_ats_rewriter
    rewrite = agent_05_ats_rewriter.run(
        resume,
        {"title": req.job_title, "company": req.company, "jd_text": req.jd_text}
    )
    if rewrite.get("status") == "error":
        status_code = 503 if "GROQ_API_KEY" in rewrite["message"] else 500
        raise HTTPException(status_code=status_code, detail=rewrite["message"])

    # Generate PDF
    try:
        from core.pdf_generator import generate_pdf_from_text
        candidate_name = resume.get("contact", {}).get("name", "Candidate")
        pdf_path = generate_pdf_from_text(
            rewrite.get("rewritten_resume_text", ""),
            candidate_name=candidate_name,
            job_title=req.job_title,
            company=req.company,
        )
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"resume_{candidate_name.replace(' ', '_')}_{req.company}.pdf"
        )
    except ImportError:
        # Return text if ReportLab not installed
        return {"status": "ok", "note": "Install reportlab for PDF. Text resume:", "text": rewrite.get("rewritten_resume_text")}


# ═══════════════════════════════════════════════
#  ADMIN PORTAL ROUTES
# ═══════════════════════════════════════════════

class AdminPlanRequest(BaseModel):
    plan: str

class AdminToggleRequest(BaseModel):
    is_admin: bool


@app.get("/api/admin/users", tags=["Admin"])
@limiter.limit(GENERAL_LIMIT)
async def admin_get_users(request: Request, admin_token: dict = Depends(verify_admin_token)):
    """Retrieve all user profiles (Admin Only)."""
    db = get_db()
    users = db.get_all_users()
    return {"users": users}


@app.post("/api/admin/users/{target_uid}/plan", tags=["Admin"])
@limiter.limit(GENERAL_LIMIT)
async def admin_update_plan(
    request: Request,
    target_uid: str,
    req: AdminPlanRequest,
    admin_token: dict = Depends(verify_admin_token)
):
    """Update a user's plan tier (Admin Only)."""
    db = get_db()
    target_user = db.get_user(target_uid)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.update_user_plan(target_uid, req.plan, admin_token["uid"])
    db.log_audit_action(
        admin_uid=admin_token["uid"],
        action="UPDATE_USER_PLAN",
        target_uid=target_uid,
        details={"old_plan": target_user.get("plan"), "new_plan": req.plan}
    )
    return {"status": "success", "message": f"User plan updated to {req.plan}"}


@app.post("/api/admin/users/{target_uid}/admin", tags=["Admin"])
@limiter.limit(GENERAL_LIMIT)
async def admin_toggle_status(
    request: Request,
    target_uid: str,
    req: AdminToggleRequest,
    admin_token: dict = Depends(verify_admin_token)
):
    """Toggle administrator status for a user (Admin Only)."""
    db = get_db()
    target_user = db.get_user(target_uid)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    db.update_user_admin_status(target_uid, req.is_admin, admin_token["uid"])
    db.log_audit_action(
        admin_uid=admin_token["uid"],
        action="UPDATE_USER_ADMIN_STATUS",
        target_uid=target_uid,
        details={"old_status": target_user.get("isAdmin", False), "new_status": req.is_admin}
    )
    return {"status": "success", "message": f"User admin status updated to {req.is_admin}"}


@app.get("/api/admin/backup", tags=["Admin"])
@limiter.limit(GENERAL_LIMIT)
async def admin_export_backup(request: Request, admin_token: dict = Depends(verify_admin_token)):
    """Export complete database backup JSON (Admin Only)."""
    db = get_db()
    backup_data = db.export_database_backup()
    db.log_audit_action(
        admin_uid=admin_token["uid"],
        action="EXPORT_BACKUP",
        target_uid="system",
        details={}
    )
    return backup_data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.app_host, port=settings.app_port, reload=settings.debug)

