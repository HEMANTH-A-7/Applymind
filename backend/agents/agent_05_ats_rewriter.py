"""
Agent 05 — ATS Resume Rewriter Agent
Rewrites master resume per job description using Groq AI.
"""
import json
from loguru import logger
from core.groq_llm import chat_json, GroqNotConfiguredError

REWRITE_PROMPT = """You are an elite ATS Resume Optimizer. Rewrite this resume to fit ONE PAGE and score >85% keyword match against the job description, WITHOUT fabricating experience.

RULES:
1. Cover every JD keyword/required skill the candidate genuinely has — mirror JD wording exactly ("FastAPI" stays "FastAPI", not "REST framework")
2. Every bullet is metric-driven (a number, %, or concrete outcome proving impact) — no unquantified filler, lead with a strong action verb
3. No buzzwords/filler adjectives ("passionate", "dynamic", "results-driven", "hardworking", "team player"). No word or phrase repeated more than twice across the whole resume — vary vocabulary
4. NEVER invent skills, experience, or contact info — copy name/email/phone/location/links VERBATIM from resume_json.contact (never a placeholder like "John Doe"); omit a field entirely if it's missing rather than making one up
5. One page: max 3 bullets per role/project, each bullet one line (~20 words); trim skills to what's relevant to this JD; cut the weakest/least relevant bullets first
6. ATS-safe: no tables, columns, images, decorative characters

OUTPUT FORMAT for "rewritten_resume_text" — this candidate's resume has no Summary/Objective, follow exactly:

Line 1: candidate's full name ONLY — no title, tagline, or summary text.
Line 2: "{{email}} | [LinkedIn]({{linkedin_url}}) | [GitHub]({{github_url}}) | [Portfolio]({{portfolio_url}}) | {{phone}} | {{location}}" — only fields present in the resume JSON, same order, one line.
(blank line) "Skills" header, one line per category: "{{Category}}: {{comma-separated skills}}" — group into tight logical categories (Languages, Frontend, Backend & APIs, AI/ML, Testing & DevOps, Databases & Tools, Competencies, etc.) inferred from the candidate's actual skills, never invented.
(blank line) "Work Experience" header. Per role: "{{Role}} | {{Company}} | {{start_date}} - {{end_date or Present}}" then up to 3 "-" bullets.
(blank line) "Projects" header. Per project: "{{Project Name}} | {{tech stack}}" (append " | {{url}}" if present) then up to 3 "-" bullets.
(blank line, only if present in resume JSON) "Certifications" or "Achievements" header with a "-" bulleted list.
(blank line) "Education" header — ALWAYS the last section: "{{Degree}} | {{Institution}} | {{year}}" (append " | GPA {{gpa}}" if present).

INPUT — Master Resume (JSON):
{resume_json}

INPUT — Target Job Posting:
Title: {job_title}
Company: {company}
JD Text:
{jd_text}

OUTPUT (JSON only):
{{
  "rewritten_resume_text": "Full ATS-optimized resume as plain text, following the OUTPUT FORMAT above exactly...",
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

Keep changes_log to the 5 most important changes. Return ONLY valid JSON."""


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

        result = chat_json(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert ATS resume optimizer. Output only valid JSON.",
                },
                {
                    "role": "user",
                    "content": REWRITE_PROMPT.format(
                        resume_json=json.dumps(serializable_resume, indent=2)[:6000],
                        job_title=job.get("title", ""),
                        company=job.get("company", ""),
                        jd_text=job.get("jd_text", "")[:3000],
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=8000,
        )

        if not result.get("rewritten_resume_text"):
            return {"status": "error", "message": "Model returned no rewritten resume text — try again"}

        logger.success(
            f"[Agent 05] ATS Score: {result.get('ats_score_estimate')}% | "
            f"Match: {result.get('keyword_analysis', {}).get('match_percentage')}%"
        )
        return {"status": "success", **result}

    except GroqNotConfiguredError as e:
        logger.error(f"[Agent 05] {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"[Agent 05] Failed: {e}")
        return {"status": "error", "message": f"Resume rewrite failed: {e}"}
