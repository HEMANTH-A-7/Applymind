"""
Agent 04 — Job Match & Score Agent
Primary: TF-IDF cosine similarity for fast bulk scoring.
Secondary: Groq-powered deep skill gap analysis for top matches.
"""
import re
import json
import asyncio
from typing import Optional
import numpy as np
from loguru import logger
from groq import Groq
from core.config import get_settings

settings = get_settings()
groq_client = Groq(api_key=settings.groq_api_key)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TF-IDF COSINE SIMILARITY (fast — for all jobs)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must", "shall", "can",
    "we", "you", "our", "your", "us", "them", "their", "its", "this",
    "that", "these", "those", "we", "not", "no", "more", "most", "also",
}


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9#+.\s]", " ", text)  # Keep # and + for C#, C++
    tokens = [t for t in text.split() if len(t) > 1 and t not in STOP_WORDS]
    return tokens


def tfidf_vector(doc_tokens: list[str], vocab: list[str]) -> np.ndarray:
    token_counts: dict[str, int] = {}
    for t in doc_tokens:
        token_counts[t] = token_counts.get(t, 0) + 1
    total = len(doc_tokens) if doc_tokens else 1
    vec = np.array([token_counts.get(w, 0) / total for w in vocab], dtype=np.float32)
    return vec


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def build_resume_text(resume_json: dict) -> str:
    """Flatten resume to single scoring string. Skills are weighted 3x."""
    parts = []
    skills = resume_json.get("skills", {})
    all_skills = (
        skills.get("technical", []) +
        skills.get("tools", []) +
        skills.get("languages", [])
    )
    # Weight skills 3x — most important for job matching
    parts.extend(all_skills * 3)

    for exp in resume_json.get("experience", []):
        parts.append(exp.get("role", ""))
        parts.extend(exp.get("bullets", []))

    for proj in resume_json.get("projects", []):
        parts.extend(proj.get("tech_stack", []) * 2)
        parts.extend(proj.get("bullets", []))

    parts.append(resume_json.get("summary", ""))
    return " ".join(str(p) for p in parts)


def fast_score(resume_json: dict, job: dict) -> int:
    """TF-IDF cosine similarity score 0–100."""
    user_text = build_resume_text(resume_json)
    jd_text = f"{job.get('title', '')} {job.get('jd_text', '')} {' '.join(job.get('tags', []))} {' '.join(job.get('required_skills', []))}"

    ut = tokenize(user_text)
    jt = tokenize(jd_text)
    vocab = list(set(ut + jt))

    uv = tfidf_vector(ut, vocab)
    jv = tfidf_vector(jt, vocab)

    raw = cosine_sim(uv, jv)
    # Scale from typical cosine range (0.02–0.4) to 0–100
    score = min(100, int(raw * 380))
    return score


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GROQ DEEP ANALYSIS (for top 10 matches only)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEEP_ANALYSIS_PROMPT = """You are a career coach. Analyze how well this candidate fits this job.

Candidate Skills: {user_skills}
Candidate Experience: {user_experience}

Job: {job_title} at {company}
Job Requirements: {jd_excerpt}

Return JSON:
{{
  "fit_score_adjustment": 5,
  "fit_label": "Sweet Spot|Overqualified|Underqualified|Strong Match",
  "recommendation": "strong_apply|apply|apply_with_caution|skip",
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "gap_severity": "none|minor|moderate|major",
  "quick_action": "One specific thing to do before applying (max 20 words)",
  "talking_points": ["1 achievement to highlight in cover letter"]
}}
Return ONLY valid JSON."""


def groq_deep_analysis(resume_json: dict, job: dict, base_score: int) -> dict:
    """Groq-powered deep gap analysis for a single job."""
    try:
        skills = resume_json.get("skills", {})
        user_skills_str = ", ".join(
            skills.get("technical", []) + skills.get("tools", [])
        )[:600]
        user_exp_str = "; ".join(
            f"{e.get('role')} at {e.get('company')}"
            for e in resume_json.get("experience", [])[:3]
        )
        jd_excerpt = f"{job.get('title')} | {job.get('jd_text', '')[:600]}"

        response = groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=[{
                "role": "user",
                "content": DEEP_ANALYSIS_PROMPT.format(
                    user_skills=user_skills_str,
                    user_experience=user_exp_str,
                    job_title=job.get("title", ""),
                    company=job.get("company", ""),
                    jd_excerpt=jd_excerpt,
                )
            }],
            temperature=0.2,
            max_tokens=400,
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
        result = json.loads(content)

        # Apply Groq's score adjustment (±10 points max)
        adjustment = max(-10, min(10, int(result.get("fit_score_adjustment", 0))))
        result["adjusted_score"] = min(100, max(0, base_score + adjustment))
        result["groq_analyzed"] = True
        return result
    except Exception as e:
        logger.debug(f"[Agent 04] Groq analysis failed for '{job.get('title')}': {e}")
        return {
            "fit_label": "Sweet Spot" if 65 <= base_score <= 85 else ("Overqualified" if base_score > 85 else "Underqualified"),
            "recommendation": "strong_apply" if base_score >= 80 else ("apply" if base_score >= 65 else ("apply_with_caution" if base_score >= 50 else "skip")),
            "matching_skills": [],
            "missing_skills": [],
            "gap_severity": "none",
            "adjusted_score": base_score,
            "groq_analyzed": False,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN SCORING PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def score_job(resume_json: dict, job: dict) -> dict:
    """Score a single job (TF-IDF only — fast pass)."""
    score = fast_score(resume_json, job)
    result = dict(job)
    result.update({
        "fit_score": score,
        "fit_label": "Sweet Spot" if 65 <= score <= 85 else ("Overqualified" if score > 85 else "Underqualified"),
        "recommendation": (
            "strong_apply" if score >= 80
            else "apply" if score >= 65
            else "apply_with_caution" if score >= 50
            else "skip"
        ),
    })
    return result


def run(
    resume_json: dict,
    jobs: list[dict],
    threshold: Optional[int] = None,
    deep_analyze_top_n: int = 10,
) -> dict:
    """
    Main entry — score all jobs then Groq-analyze the top N.

    Args:
        resume_json: Parsed resume from Agent 01
        jobs: List of job dicts from Agent 03
        threshold: Min score to include in apply queue
        deep_analyze_top_n: How many top jobs to send to Groq for deep analysis

    Returns:
        dict with ranked_jobs, apply_queue, groq_analyzed_count
    """
    threshold = threshold or settings.auto_apply_threshold
    logger.info(f"[Agent 04] Scoring {len(jobs)} jobs (threshold={threshold}, groq_top_n={deep_analyze_top_n})")

    # Fast TF-IDF pass — all jobs
    scored = [score_job(resume_json, job) for job in jobs]
    scored.sort(key=lambda x: x["fit_score"], reverse=True)

    # Groq deep analysis — top N only (to save API calls)
    if deep_analyze_top_n > 0 and resume_json:
        job_map = {j.get("job_id", ""): j for j in jobs}
        groq_count = 0
        for i, scored_job in enumerate(scored[:deep_analyze_top_n]):
            original_job = job_map.get(scored_job["job_id"], scored_job)
            deep = groq_deep_analysis(resume_json, original_job, scored_job["fit_score"])
            scored[i].update(deep)
            scored[i]["fit_score"] = deep.get("adjusted_score", scored_job["fit_score"])
            if deep.get("groq_analyzed"):
                groq_count += 1

        # Re-sort after Groq adjustments
        scored.sort(key=lambda x: x["fit_score"], reverse=True)
        logger.info(f"[Agent 04] Groq-analyzed {groq_count}/{deep_analyze_top_n} top jobs")

    apply_queue = [j for j in scored if j["fit_score"] >= threshold]
    logger.success(
        f"[Agent 04] {len(scored)} scored | {len(apply_queue)} qualify (>= {threshold})"
    )

    return {
        "status": "success",
        "total_scored": len(scored),
        "apply_queue_count": len(apply_queue),
        "ranked_jobs": scored,
        "apply_queue": apply_queue,
        "groq_analyzed_count": sum(1 for j in scored if j.get("groq_analyzed")),
    }
