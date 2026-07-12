"""
Agent 09 — Analytics & Optimization Agent
Tracks the full application funnel, monitors inboxes for recruiter replies,
A/B tests resume variants, and generates weekly optimization reports using Groq.
"""
import re
import json
import imaplib
import email
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger
from core.config import get_settings
from core.groq_llm import get_client

settings = get_settings()

# ─── Response detection keywords ───
INTERVIEW_KEYWORDS = [
    "interview", "schedule a call", "availability", "phone screen",
    "technical screen", "assessment", "meet with", "zoom", "google meet",
    "teams call", "next steps", "move forward", "impressed",
]
REJECTION_KEYWORDS = [
    "unfortunately", "not moving forward", "decided to pursue other candidates",
    "position has been filled", "not a fit", "appreciate your interest",
    "keep your resume on file", "not selected",
]
RECRUITER_KEYWORDS = [
    "recruiter", "talent acquisition", "hiring manager", "hr@", "careers@", "jobs@",
    "recruiting@", "people@", "talent@",
]


def classify_email(subject: str, body: str, sender: str) -> str:
    """Classify an inbound email as interview/rejection/recruiter_reach/unknown."""
    text = f"{subject} {body} {sender}".lower()
    if any(kw in text for kw in INTERVIEW_KEYWORDS):
        return "interview_invite"
    if any(kw in text for kw in REJECTION_KEYWORDS):
        return "rejection"
    if any(kw in text for kw in RECRUITER_KEYWORDS):
        return "recruiter_reach"
    return "unknown"


def check_inbox_for_responses(email_address: str, password: str, since_days: int = 7) -> list[dict]:
    """
    Connect to Gmail via IMAP and scan for job-related responses.

    Args:
        email_address: Gmail address
        password: Gmail App Password
        since_days: Days to look back

    Returns:
        List of classified email responses
    """
    responses = []
    try:
        since_date = (datetime.utcnow() - timedelta(days=since_days)).strftime("%d-%b-%Y")

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_address, password)
        mail.select("INBOX")

        # Search for recent emails
        _, msg_ids = mail.search(None, f'SINCE {since_date}')
        for msg_id in msg_ids[0].split()[-50:]:  # Last 50 emails
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = msg.get("Subject", "")
            sender = msg.get("From", "")
            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")[:1000]
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")[:1000]

            classification = classify_email(subject, body, sender)
            if classification != "unknown":
                responses.append({
                    "subject": subject,
                    "sender": sender,
                    "classification": classification,
                    "date": msg.get("Date", ""),
                    "preview": body[:200],
                })

        mail.logout()
        logger.success(f"[Agent 09] Found {len(responses)} job-related emails in inbox")

    except imaplib.IMAP4.error as e:
        logger.warning(f"[Agent 09] IMAP login failed: {e}")
    except Exception as e:
        logger.error(f"[Agent 09] Inbox check failed: {e}")

    return responses


def compute_funnel_metrics(submission_logs: list[dict]) -> dict:
    """Compute funnel metrics from submission logs."""
    total = len(submission_logs)
    if total == 0:
        return {"total": 0, "message": "No applications yet"}

    by_status = defaultdict(int)
    by_platform = defaultdict(int)
    by_day = defaultdict(int)

    for log in submission_logs:
        by_status[log.get("status", "UNKNOWN")] += 1
        by_platform[log.get("platform", "unknown")] += 1
        date = log.get("timestamp", "")[:10]
        if date:
            by_day[date] += 1

    success = by_status.get("SUCCESS", 0)
    response_rate = round(success / total * 100, 1) if total else 0

    return {
        "total_applications": total,
        "success_count": success,
        "response_rate_pct": response_rate,
        "by_status": dict(by_status),
        "by_platform": dict(by_platform),
        "by_day": dict(sorted(by_day.items())),
        "funnel": {
            "scraped": total * 8,  # Estimate
            "matched": total * 3,
            "applied": total,
            "responded": by_status.get("SUCCESS", 0),
            "interviewed": max(0, by_status.get("SUCCESS", 0) // 4),
            "offered": 0,
        }
    }


def ab_test_analysis(submission_logs: list[dict]) -> dict:
    """Analyze A/B test results between resume variants."""
    variant_results = defaultdict(lambda: {"applications": 0, "responses": 0})

    for log in submission_logs:
        variant = log.get("resume_variant_id", "")[-1:] or "A"  # Last char = A/B
        variant_results[variant]["applications"] += 1
        if log.get("status") == "SUCCESS":
            variant_results[variant]["responses"] += 1

    analysis = {}
    for variant, data in variant_results.items():
        apps = data["applications"]
        resp = data["responses"]
        analysis[f"variant_{variant}"] = {
            "applications": apps,
            "responses": resp,
            "response_rate": round(resp / apps * 100, 1) if apps else 0,
        }

    winner = max(analysis.items(), key=lambda x: x[1]["response_rate"], default=(None, {}))[0]
    return {"variants": analysis, "winner": winner}


def generate_weekly_report(submission_logs: list[dict], user_resume: dict = None) -> dict:
    """
    Generate a Groq-powered weekly optimization report with strategy recommendations.
    """
    metrics = compute_funnel_metrics(submission_logs)
    ab_results = ab_test_analysis(submission_logs)

    # Prepare context for Groq
    recent_logs_summary = json.dumps(submission_logs[-20:], indent=2)[:3000] if submission_logs else "No data yet"

    prompt = f"""You are an expert career strategy AI. Analyze this job application data and generate a concise weekly optimization report.

Application Metrics:
{json.dumps(metrics, indent=2)}

A/B Test Results:
{json.dumps(ab_results, indent=2)}

Recent Submissions Sample:
{recent_logs_summary}

Generate a JSON report with:
{{
  "performance_summary": "2-3 sentence summary of this week's performance",
  "top_insights": ["insight 1", "insight 2", "insight 3"],
  "platform_recommendations": [
    {{"platform": "linkedin", "action": "recommendation", "reason": "why"}}
  ],
  "resume_recommendations": ["What to change in the resume"],
  "strategy_pivots": ["Changes to job search strategy"],
  "next_week_targets": {{
    "applications": 150,
    "platforms_to_prioritize": ["wellfound", "linkedin"],
    "keywords_to_add": ["FastAPI", "LLM"],
    "apply_threshold": 65
  }}
}}

Return ONLY valid JSON."""

    try:
        response = get_client().chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
        ai_report = json.loads(content)
    except Exception as e:
        logger.error(f"[Agent 09] Groq report generation failed: {e}")
        ai_report = {"error": str(e), "performance_summary": "Report generation failed — check API key"}

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "ab_analysis": ab_results,
        "ai_report": ai_report,
    }


def run(
    action: str,
    submission_logs: list[dict] = None,
    email_address: str = "",
    email_password: str = "",
    since_days: int = 7,
) -> dict:
    """
    Main entry for Agent 09.

    Actions:
        funnel_metrics: Compute funnel stats from submission logs
        check_inbox: Scan email for recruiter responses
        weekly_report: Generate Groq AI weekly optimization report
        ab_analysis: Analyze A/B test results
    """
    submission_logs = submission_logs or []
    try:
        if action == "funnel_metrics":
            return {"status": "success", **compute_funnel_metrics(submission_logs)}
        elif action == "check_inbox":
            responses = check_inbox_for_responses(email_address, email_password, since_days)
            return {"status": "success", "responses": responses, "count": len(responses)}
        elif action == "weekly_report":
            return {"status": "success", **generate_weekly_report(submission_logs)}
        elif action == "ab_analysis":
            return {"status": "success", **ab_test_analysis(submission_logs)}
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
    except Exception as e:
        logger.error(f"[Agent 09] Failed: {e}")
        return {"status": "error", "message": str(e)}
