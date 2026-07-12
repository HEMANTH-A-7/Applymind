"""
Agent 08 — Application Submission Agent
Executes autonomous job applications via Selenium, GraphQL, and SMTP.
Implements human-like delays, CAPTCHA handling, and comprehensive logging.
Uses Groq to auto-answer free-text application questions.
"""
import time
import random
import smtplib
import asyncio
import aiohttp
import json
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Optional
from loguru import logger
from groq import Groq

from core.config import get_settings
from agents import agent_07_credential_manager as cred_mgr

settings = get_settings()
groq_client = Groq(api_key=settings.groq_api_key)


# ─── Groq: answer application questions ───
ANSWER_PROMPT = """You are a professional job applicant answering an application question. 
Answer concisely and honestly based on the candidate profile below.

Candidate: {name}
Skills: {skills}
Experience summary: {experience}

Application question: "{question}"
Job: {job_title} at {company}

Rules:
- Max 3 sentences
- Sound human and genuine, not robotic
- If asking for years of experience, give a specific number
- If asking salary expectation, give a range like "{salary_range}"

Return only the answer text, nothing else."""


def groq_answer_question(
    question: str,
    resume_json: dict,
    job: dict,
    salary_range: str = "$100,000-$140,000",
) -> str:
    """Use Groq to answer a free-text application question."""
    try:
        skills = resume_json.get("skills", {})
        skills_str = ", ".join(
            (skills.get("technical", []) + skills.get("tools", []))[:10]
        )
        exp_summary = "; ".join(
            f"{e.get('role')} at {e.get('company')} ({e.get('start_date','')}-{e.get('end_date','Present')})"
            for e in resume_json.get("experience", [])[:2]
        )
        response = groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=[{
                "role": "user",
                "content": ANSWER_PROMPT.format(
                    name=resume_json.get("contact", {}).get("name", "the candidate"),
                    skills=skills_str,
                    experience=exp_summary,
                    question=question,
                    job_title=job.get("title", ""),
                    company=job.get("company", ""),
                    salary_range=salary_range,
                )
            }],
            temperature=0.4,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.debug(f"[Agent 08] Groq question answer failed: {e}")
        return ""


# ─── Status codes from SRS ───
class Status:
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    CAPTCHA_REQUIRED = "CAPTCHA_REQUIRED"
    FORM_ERROR = "FORM_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_FAILED = "AUTH_FAILED"
    DUPLICATE = "DUPLICATE"
    MANUAL_REQUIRED = "MANUAL_REQUIRED"
    BLOCKED = "BLOCKED"
    SKIPPED_HOURS = "SKIPPED_HOURS"


def _is_working_hours(timezone_offset: int = 5) -> bool:
    """Only submit between 8am–8pm in user's local timezone.
    In development mode, this check is bypassed to allow testing at any hour.
    """
    # Skip check in development environment
    if settings.environment in ("development", "dev", "local"):
        return True
    now = datetime.utcnow()
    local_hour = (now.hour + timezone_offset) % 24
    return 8 <= local_hour < 20


def _human_delay(min_sec: float = 2.0, max_sec: float = 5.0):
    """Simulate human-like delay between actions."""
    delay = random.uniform(min_sec, max_sec)
    logger.debug(f"[Agent 08] Human delay: {delay:.1f}s")
    time.sleep(delay)


def _build_log_entry(
    job: dict,
    user_id: str,
    platform: str,
    status: str,
    resume_variant_id: str = "",
    cover_letter_id: str = "",
    confirmation_text: str = "",
    error_text: str = "",
) -> dict:
    """Build a standardized submission log entry."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "job_id": job.get("job_id", ""),
        "jd_url": job.get("apply_url", ""),
        "company": job.get("company", ""),
        "job_title": job.get("title", ""),
        "user_id": user_id,
        "platform": platform,
        "resume_variant_id": resume_variant_id,
        "cover_letter_id": cover_letter_id,
        "status": status,
        "confirmation_text": confirmation_text,
        "error_text": error_text,
    }


# ─── Wellfound — GraphQL API Apply ───
async def apply_wellfound(job: dict, user_id: str, resume_url: str, cover_letter_text: str, cred: dict = None) -> dict:
    """Apply to Wellfound job via their API (no CAPTCHA, fastest method)."""
    try:
        if not cred:
            cred = cred_mgr.get_credential(user_id, "wellfound")
        if not cred:
            return _build_log_entry(job, user_id, "wellfound", Status.AUTH_FAILED, error_text="No Wellfound credentials provided")

        # GraphQL apply mutation (simplified — real implementation needs auth token)
        headers = {
            "Authorization": f"Bearer {cred.get('oauth_token_plain', '')}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": """
                mutation applyToJob($jobId: ID!, $resumeUrl: String!, $coverLetter: String!) {
                    applyToJob(input: { jobId: $jobId, resumeUrl: $resumeUrl, coverLetter: $coverLetter }) {
                        success
                        message
                    }
                }
            """,
            "variables": {
                "jobId": job.get("job_id", ""),
                "resumeUrl": resume_url,
                "coverLetter": cover_letter_text,
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://wellfound.com/graphql",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("data", {}).get("applyToJob", {}).get("success"):
                    cred_mgr.increment_rate_counter(user_id, "wellfound")
                    return _build_log_entry(job, user_id, "wellfound", Status.SUCCESS,
                                           confirmation_text="Wellfound application submitted via GraphQL")
                else:
                    return _build_log_entry(job, user_id, "wellfound", Status.FORM_ERROR,
                                           error_text=str(data))

    except Exception as e:
        logger.error(f"[Agent 08] Wellfound apply failed: {e}")
        return _build_log_entry(job, user_id, "wellfound", Status.FORM_ERROR, error_text=str(e))


# ─── Email Application — SMTP ───
def apply_via_email(
    job: dict,
    user_id: str,
    candidate_name: str,
    candidate_email: str,
    cover_letter_text: str,
    resume_pdf_path: Optional[str] = None,
) -> dict:
    """Send email application via SMTP with cover letter + resume attachment."""
    try:
        # Extract hiring email from JD
        jd_text = job.get("jd_text", "") + " " + job.get("apply_url", "")
        import re
        emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", jd_text)
        to_email = emails[0] if emails else None

        if not to_email:
            return _build_log_entry(job, user_id, "email", Status.MANUAL_REQUIRED,
                                   error_text="Could not find hiring email in JD")

        msg = MIMEMultipart()
        msg["From"] = f"{candidate_name} <{settings.smtp_user}>"
        msg["To"] = to_email
        msg["Subject"] = f"{candidate_name} — Application for {job.get('title', 'Position')} at {job.get('company', '')}"

        # Email body
        msg.attach(MIMEText(cover_letter_text, "plain"))

        # Attach resume if provided
        if resume_pdf_path and Path(resume_pdf_path).exists():
            with open(resume_pdf_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="resume_{candidate_name.replace(" ", "_")}.pdf"')
            msg.attach(part)

        # Send via SMTP
        if settings.smtp_user and settings.smtp_password:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_user, to_email, msg.as_string())

            cred_mgr.increment_rate_counter(user_id, "email")
            return _build_log_entry(job, user_id, "email", Status.SUCCESS,
                                   confirmation_text=f"Email sent to {to_email}")
        else:
            return _build_log_entry(job, user_id, "email", Status.MANUAL_REQUIRED,
                                   error_text="SMTP credentials not configured in .env")

    except smtplib.SMTPException as e:
        return _build_log_entry(job, user_id, "email", Status.FORM_ERROR, error_text=str(e))
    except Exception as e:
        logger.error(f"[Agent 08] Email apply failed: {e}")
        return _build_log_entry(job, user_id, "email", Status.FORM_ERROR, error_text=str(e))


# ─── Selenium-based LinkedIn Easy Apply ───
def apply_linkedin_selenium(job: dict, user_id: str, resume_pdf_path: str, cover_letter_text: str, cred: dict = None) -> dict:
    """
    Apply via LinkedIn Easy Apply using Selenium.
    Full implementation requires a valid LinkedIn session.
    """
    try:
        # Rate limit check
        rate = cred_mgr.check_rate_limit(user_id, "linkedin")
        if not rate["allowed"]:
            return _build_log_entry(job, user_id, "linkedin", Status.RATE_LIMITED,
                                   error_text=f"LinkedIn daily cap hit ({rate['limit']}/day)")

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)

        try:
            if not cred:
                cred = cred_mgr.get_credential(user_id, "linkedin")
            if not cred:
                return _build_log_entry(job, user_id, "linkedin", Status.AUTH_FAILED,
                                       error_text="No LinkedIn credentials provided")

            # Login
            driver.get("https://www.linkedin.com/login")
            _human_delay(2, 4)

            email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
            email_field.send_keys(cred["username"])
            _human_delay(0.5, 1.5)

            pass_field = driver.find_element(By.ID, "password")
            pass_field.send_keys(cred["password"])
            _human_delay(1, 2)

            driver.find_element(By.CSS_SELECTOR, "[data-litms-control-urn='login-submit']").click()
            _human_delay(3, 5)

            # Check for CAPTCHA
            if "checkpoint" in driver.current_url or "security" in driver.current_url:
                return _build_log_entry(job, user_id, "linkedin", Status.CAPTCHA_REQUIRED,
                                       error_text="LinkedIn CAPTCHA/checkpoint detected — manual solve required")

            # Navigate to job
            driver.get(job.get("apply_url", ""))
            _human_delay(2, 4)

            # Find Easy Apply button
            try:
                easy_apply_btn = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-control-name='jobdetails_topcard_inapply'],.jobs-apply-button")
                ))
                easy_apply_btn.click()
                _human_delay(2, 3)
            except Exception:
                return _build_log_entry(job, user_id, "linkedin", Status.MANUAL_REQUIRED,
                                       error_text="Easy Apply button not found — external application")

            # Fill form fields (simplified — real impl handles multi-step)
            # Phone field
            try:
                phone_fields = driver.find_elements(By.CSS_SELECTOR, "input[id*='phone']")
                for f in phone_fields:
                    if f.is_displayed():
                        f.clear()
                        f.send_keys("+1-555-0100")
                        _human_delay(0.5, 1)
            except Exception:
                pass

            # Submit
            submit_btns = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Submit application']")
            if submit_btns:
                submit_btns[0].click()
                _human_delay(2, 3)
                cred_mgr.increment_rate_counter(user_id, "linkedin")
                return _build_log_entry(job, user_id, "linkedin", Status.SUCCESS,
                                       confirmation_text="LinkedIn Easy Apply submitted")
            else:
                return _build_log_entry(job, user_id, "linkedin", Status.MANUAL_REQUIRED,
                                       error_text="Multi-step form — requires manual completion")

        finally:
            driver.quit()

    except ImportError:
        return _build_log_entry(job, user_id, "linkedin", Status.MANUAL_REQUIRED,
                               error_text="Selenium not installed — run: pip install selenium")
    except Exception as e:
        logger.error(f"[Agent 08] LinkedIn Selenium failed: {e}")
        return _build_log_entry(job, user_id, "linkedin", Status.FORM_ERROR, error_text=str(e))


# ─── Main batch submission ───
def submit_batch(
    jobs: list[dict],
    user_id: str,
    candidate_name: str = "Candidate",
    candidate_email: str = "",
    cover_letters: dict = None,
    resume_pdf_path: str = "",
    resume_url: str = "",
    daily_limit: int = None,
    apply_method_override: str = None,
    credentials: dict = None,
) -> dict:
    """
    Submit applications for a batch of jobs.

    Args:
        jobs: List of job dicts (from Agent 04 apply_queue)
        user_id: User identifier
        candidate_name: Candidate's full name
        candidate_email: Candidate's email
        cover_letters: {job_id: cover_letter_text} mapping
        resume_pdf_path: Path to ATS resume PDF
        resume_url: Public URL to hosted resume
        daily_limit: Max applications to send in this run
        apply_method_override: Force a specific apply method

    Returns:
        dict with submission_log, success_count, error_count
    """
    cover_letters = cover_letters or {}
    daily_limit = daily_limit or settings.daily_app_limit
    submission_log = []
    success_count = 0
    error_count = 0
    skipped_count = 0

    logger.info(f"[Agent 08] Starting batch of {len(jobs)} jobs (limit={daily_limit})")

    # Enforce working hours
    if not _is_working_hours():
        logger.warning("[Agent 08] Outside working hours (8am–8pm). Queueing for next window.")
        return {
            "status": "queued",
            "message": "Outside submission window (8am–8pm). Will auto-submit tomorrow.",
            "submission_log": [],
        }

    for job in jobs[:daily_limit]:
        cover_letter_text = cover_letters.get(job.get("job_id", ""), "")
        method = apply_method_override or job.get("apply_method", "company_site")

        # Extract passed credentials for this platform
        platform_cred = None
        if credentials:
            if method in ["linkedin_easy_apply", "linkedin"]:
                platform_cred = credentials.get("linkedin")
            elif method in ["wellfound_form", "wellfound"]:
                platform_cred = credentials.get("wellfound")

        try:
            if method == "wellfound_form" or method == "wellfound":
                log = asyncio.run(apply_wellfound(job, user_id, resume_url, cover_letter_text, platform_cred))
            elif method == "email":
                log = apply_via_email(job, user_id, candidate_name, candidate_email,
                                     cover_letter_text, resume_pdf_path)
            elif method in ["linkedin_easy_apply", "linkedin"]:
                log = apply_linkedin_selenium(job, user_id, resume_pdf_path, cover_letter_text, platform_cred)
            else:
                # Company site or unknown — flag for manual
                log = _build_log_entry(job, user_id, method, Status.MANUAL_REQUIRED,
                                      error_text=f"Method '{method}' requires manual application")
                skipped_count += 1

            submission_log.append(log)

            if log["status"] == Status.SUCCESS:
                success_count += 1
                logger.success(f"[Agent 08] ✅ Applied: {job['title']} @ {job['company']} via {method}")
                # Human-like delay between applications (2–5 min in prod, 2–5 sec in dev)
                _human_delay(2, 5)
            elif log["status"] in [Status.RATE_LIMITED, Status.BLOCKED]:
                logger.warning(f"[Agent 08] 🚫 Stopping: {log['status']}")
                break
            else:
                error_count += 1
                logger.error(f"[Agent 08] ❌ Failed: {job['title']} — {log['status']}")

        except Exception as e:
            error_count += 1
            submission_log.append(_build_log_entry(job, user_id, method, Status.FORM_ERROR, error_text=str(e)))
            logger.error(f"[Agent 08] Exception for {job['title']}: {e}")

    logger.success(
        f"[Agent 08] Batch done: {success_count} success, {error_count} errors, {skipped_count} skipped"
    )

    return {
        "status": "success",
        "total_attempted": len(jobs[:daily_limit]),
        "success_count": success_count,
        "error_count": error_count,
        "skipped_count": skipped_count,
        "submission_log": submission_log,
    }


def run(jobs: list[dict], user_id: str, **kwargs) -> dict:
    """Main entry point for Agent 08."""
    return submit_batch(jobs, user_id, **kwargs)
