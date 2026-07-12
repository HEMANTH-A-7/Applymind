"""
Agent 05 — ATS Resume Rewriter Agent
Rewrites master resume per job description using Groq AI.
"""
import json
import re
from loguru import logger
from groq import Groq
from core.config import get_settings

settings = get_settings()
client = Groq(api_key=settings.groq_api_key)

REWRITE_PROMPT = """You are an elite ATS Resume Optimizer. Your task is to rewrite a resume to achieve >80% keyword match with a specific job description WITHOUT fabricating any experience.

RULES:
1. Mirror JD language EXACTLY — if JD says "FastAPI", use "FastAPI", not "REST framework"
2. Inject JD keywords NATURALLY into existing bullet points
3. Quantify all metrics — "improved X" → "improved X by 34%"
4. NEVER fabricate skills. Reframe existing skills using JD terminology only
5. ATS-safe format: no tables, no columns, no images, no special decorative characters
6. Standard sections: Summary, Technical Skills, Experience, Projects, Education, Certifications
7. 1-2 pages max. Lead every bullet with a strong action verb
8. Use exact words from "Required Skills" section of JD

INPUT — Master Resume (JSON):
{resume_json}

INPUT — Target Job Posting:
Title: {job_title}
Company: {company}
JD Text:
{jd_text}

OUTPUT (JSON only):
{{
  "rewritten_resume_text": "Full ATS-optimized resume as plain text...",
  "summary": "Tailored 3-line professional summary",
  "keyword_analysis": {{
    "required_keywords": ["list from JD"],
    "matched_keywords": ["keywords that appear in rewritten resume"],
    "missing_keywords": ["keywords not covered"],
    "match_percentage": 82
  }},
  "changes_log": [
    {{"section": "Experience", "original": "...", "rewritten": "...", "reason": "..."}}
  ],
  "ats_score_estimate": 85
}}

Return ONLY valid JSON."""


def clean_for_json(data):
    """Recursively clean dict to remove/convert DatetimeWithNanoseconds / datetimes for JSON serialization."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if k in ["createdAt", "updatedAt", "savedAt", "deletedAt", "loggedAt", "timestamp", "generatedAt"]:
                continue
            cleaned[k] = clean_for_json(v)
        return cleaned
    elif isinstance(data, list):
        return [clean_for_json(item) for item in data]
    elif hasattr(data, "isoformat"):
        return data.isoformat()
    else:
        return data


def run(resume_json: dict, job: dict) -> dict:
    """
    Main entry — rewrites resume for a specific job posting.

    Args:
        resume_json: Parsed resume dict from Agent 01
        job: Job posting dict (title, company, jd_text, etc.)

    Returns:
        dict with rewritten_resume_text, keyword_analysis, ats_score_estimate
    """
    logger.info(f"[Agent 05] Rewriting resume for: {job.get('title')} @ {job.get('company')}")

    try:
        # Clean DatetimeWithNanoseconds objects
        serializable_resume = clean_for_json(resume_json)
        
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert ATS resume optimizer. Output only valid JSON.",
                },
                {
                    "role": "user",
                    "content": REWRITE_PROMPT.format(
                        resume_json=json.dumps(serializable_resume, indent=2)[:3000],
                        job_title=job.get("title", ""),
                        company=job.get("company", ""),
                        jd_text=job.get("jd_text", "")[:3000],
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=4000,
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
        result = json.loads(content)

        logger.success(
            f"[Agent 05] ATS Score: {result.get('ats_score_estimate')}% | "
            f"Match: {result.get('keyword_analysis', {}).get('match_percentage')}%"
        )
        return {"status": "success", **result}

    except Exception as e:
        logger.error(f"[Agent 05] Failed: {e}")
        return {"status": "error", "message": str(e)}
