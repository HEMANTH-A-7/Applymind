"""
Agent 04 — Job Match & Score Agent
Primary: TF-IDF cosine similarity for fast bulk scoring.
Secondary: Groq-powered deep skill gap analysis for top matches.
"""
import re
from typing import Optional
import numpy as np
from loguru import logger
from core.config import get_settings
from core.groq_llm import chat_json

settings = get_settings()


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


def build_section_texts(resume_json: dict) -> dict[str, str]:
    """Split resume into independent scoring sections instead of one flat bag-of-words.

    Scoring skills/experience/projects/summary against the JD separately (then blending
    by weight) means a strong project or work-history match still counts even when its
    phrasing differs from the JD's skill list — a flat bag dominated by 3x-weighted
    skill tokens drowned that signal out before.
    """
    skills = resume_json.get("skills", {})
    all_skills = (
        skills.get("technical", []) +
        skills.get("tools", []) +
        skills.get("languages", [])
    )

    exp_parts = []
    for exp in resume_json.get("experience", []):
        exp_parts.append(exp.get("role", ""))
        exp_parts.extend(exp.get("bullets", []))
        exp_parts.extend(str(m) for m in exp.get("metrics", []))

    proj_parts = []
    for proj in resume_json.get("projects", []):
        proj_parts.append(proj.get("name", ""))
        proj_parts.append(proj.get("description", ""))
        proj_parts.extend(proj.get("tech_stack", []))
        proj_parts.extend(proj.get("bullets", []))

    return {
        "skills": " ".join(str(s) for s in all_skills),
        "experience": " ".join(str(p) for p in exp_parts),
        "projects": " ".join(str(p) for p in proj_parts),
        "summary": str(resume_json.get("summary", "")),
    }


# How much each resume section counts toward the keyword-similarity base score.
# Skills still lead (JDs are skill-list-heavy) but experience/projects together
# now outweigh skills, so hands-on work isn't drowned out by a skills list.
SECTION_WEIGHTS = {"skills": 0.35, "experience": 0.30, "projects": 0.25, "summary": 0.10}


def fast_score(resume_json: dict, job: dict) -> int:
    """Weighted multi-section TF-IDF cosine similarity, 0–100.

    This is the cheap bulk-pass score run against every job (an LLM call per job
    isn't feasible at scale) — see groq_deep_analysis() for the semantic pass that
    actually reads experience/project substance for the top matches.
    """
    sections = build_section_texts(resume_json)
    jd_text = f"{job.get('title', '')} {job.get('jd_text', '')} {' '.join(job.get('tags', []))} {' '.join(job.get('required_skills', []))}"
    jt = tokenize(jd_text)

    weighted_sum = 0.0
    total_weight = 0.0
    for section, weight in SECTION_WEIGHTS.items():
        st = tokenize(sections[section])
        if not st:
            continue
        vocab = list(set(st + jt))
        sv = tfidf_vector(st, vocab)
        jv = tfidf_vector(jt, vocab)
        weighted_sum += cosine_sim(sv, jv) * weight
        total_weight += weight

    if total_weight == 0:
        return 0

    raw = weighted_sum / total_weight
    # Scale from typical cosine range (0.02–0.4) to 0–100
    score = min(100, int(raw * 380))
    return score


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GROQ DEEP ANALYSIS (for top 10 matches only)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEEP_ANALYSIS_PROMPT = """You are a senior technical recruiter. Judge how well this candidate actually
fits this job — not by keyword overlap, but by whether their real work experience and projects
demonstrate the capabilities the job needs, even when worded differently than the JD.

Candidate Skills: {user_skills}

Candidate Work Experience:
{user_experience}

Candidate Projects:
{user_projects}

Job: {job_title} at {company}
Job Requirements: {jd_excerpt}

Consider:
- Does their work experience show they've actually done similar work, not just held a similar title?
- Do their projects demonstrate the core competencies this job needs, even under different terminology?
- Is their seniority/scope (intern/junior/senior, ownership, team size) appropriate for this role?

Return JSON:
{{
  "semantic_fit_score": 72,
  "fit_label": "Sweet Spot|Overqualified|Underqualified|Strong Match",
  "recommendation": "strong_apply|apply|apply_with_caution|skip",
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "experience_relevance": "One sentence on how well work experience maps to this role",
  "project_relevance": "One sentence on how well projects map to this role",
  "gap_severity": "none|minor|moderate|major",
  "quick_action": "One specific thing to do before applying (max 20 words)",
  "talking_points": ["1 achievement to highlight in cover letter"]
}}
Return ONLY valid JSON."""


def groq_deep_analysis(resume_json: dict, job: dict, base_score: int) -> dict:
    """Groq-powered semantic fit analysis for a single job.

    Reads actual experience/project bullets (not just role titles and a skill list) so the
    model can judge substance, then blends its semantic read with the keyword-based
    base_score — keyword overlap alone rewards phrasing coincidence, and an LLM score
    alone can be swayed by confident-sounding but shallow bullets, so neither is used
    on its own.
    """
    try:
        skills = resume_json.get("skills", {})
        user_skills_str = ", ".join(
            skills.get("technical", []) + skills.get("tools", [])
        )[:600]

        exp_lines = []
        for e in resume_json.get("experience", [])[:3]:
            bullets = "; ".join(e.get("bullets", [])[:3])
            role_line = f"{e.get('role', '')} at {e.get('company', '')}"
            exp_lines.append(f"{role_line} — {bullets}" if bullets else role_line)
        user_exp_str = "\n".join(exp_lines)[:1200] or "None listed"

        proj_lines = []
        for p in resume_json.get("projects", [])[:3]:
            tech = ", ".join(p.get("tech_stack", []))
            bullets = "; ".join(p.get("bullets", [])[:2])
            label = f"{p.get('name', '')} ({tech})" if tech else p.get("name", "")
            proj_lines.append(f"{label} — {bullets}" if bullets else label)
        user_proj_str = "\n".join(proj_lines)[:1200] or "None listed"

        jd_excerpt = f"{job.get('title')} | {job.get('jd_text', '')[:800]}"

        result = chat_json(
            messages=[{
                "role": "user",
                "content": DEEP_ANALYSIS_PROMPT.format(
                    user_skills=user_skills_str,
                    user_experience=user_exp_str,
                    user_projects=user_proj_str,
                    job_title=job.get("title", ""),
                    company=job.get("company", ""),
                    jd_excerpt=jd_excerpt,
                )
            }],
            temperature=0.2,
            max_tokens=600,
            retries=0,
        )

        semantic_score = max(0, min(100, int(result.get("semantic_fit_score", base_score))))
        # 60% semantic / 40% keyword — semantic read of actual substance leads,
        # keyword score still anchors it so a hallucinated read can't run away.
        blended = round(0.4 * base_score + 0.6 * semantic_score)
        result["semantic_fit_score"] = semantic_score
        result["adjusted_score"] = min(100, max(0, blended))
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
