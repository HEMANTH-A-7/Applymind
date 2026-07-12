"""
Agent 06 — Cover Letter Generator
Generates personalized 250-word cover letters with A/B variants.
"""
from loguru import logger
from core.groq_llm import chat_json, GroqNotConfiguredError

COVER_LETTER_PROMPT = """You are a professional cover letter writer creating a tailored, high-converting cover letter.

STRICT RULES:
- Exactly 250 words (±10)
- Opening: reference something specific about the company (not generic)
- Body: highlight exactly 2-3 user achievements most relevant to this role
- Tone: {tone} (startup = conversational and energetic; enterprise = professional and precise)
- Do NOT start with "I am writing to..."
- Do NOT use generic phrases like "I believe I am a great fit"
- Use the EXACT job title from the posting
- Variant {variant}: {variant_instruction}

Candidate's top achievements (from resume):
{achievements}

Job: {job_title} at {company}
Company context: {company_context}
JD excerpt: {jd_excerpt}
Candidate name: {candidate_name}

Return JSON:
{{
  "cover_letter": "Full 250-word cover letter text...",
  "word_count": 250,
  "key_hooks": ["hook 1", "hook 2"],
  "tone_used": "startup|enterprise",
  "variant": "A|B"
}}

Return ONLY valid JSON."""


def detect_tone(company: str, jd_text: str) -> str:
    """Heuristic: detect if startup or enterprise based on JD language."""
    startup_signals = ["startup", "fast-paced", "agile", "we move fast", "small team", "equity", "seed", "series"]
    jd_lower = jd_text.lower()
    return "startup" if any(s in jd_lower for s in startup_signals) else "enterprise"


def extract_achievements(resume_json: dict) -> str:
    """Extract top 5 quantified achievements from resume."""
    achievements = []
    for exp in resume_json.get("experience", [])[:3]:
        for bullet in exp.get("bullets", [])[:2]:
            if any(c.isdigit() for c in bullet):  # Has metrics
                achievements.append(bullet)
    for proj in resume_json.get("projects", [])[:2]:
        for bullet in proj.get("bullets", [])[:1]:
            achievements.append(bullet)
    return "\n".join(f"• {a}" for a in achievements[:5])


def run(resume_json: dict, job: dict, variant: str = "A") -> dict:
    """
    Generate a cover letter for a specific job.

    Args:
        resume_json: Parsed resume from Agent 01
        job: Job posting dict
        variant: "A" (achievement-forward) or "B" (narrative-forward)

    Returns:
        dict with cover_letter text and metadata
    """
    logger.info(f"[Agent 06] Generating cover letter variant {variant} for {job.get('title')} @ {job.get('company')}")

    tone = detect_tone(job.get("company", ""), job.get("jd_text", ""))
    achievements = extract_achievements(resume_json)
    candidate_name = resume_json.get("contact", {}).get("name", "the candidate")

    variant_instructions = {
        "A": "Achievement-forward: Lead with your biggest quantified win, then connect it to the company's needs",
        "B": "Narrative-forward: Tell a brief career story that naturally leads to why this role is the perfect next chapter",
    }

    try:
        result = chat_json(
            messages=[
                {"role": "system", "content": "You are an expert cover letter writer. Output only valid JSON."},
                {
                    "role": "user",
                    "content": COVER_LETTER_PROMPT.format(
                        tone=tone,
                        variant=variant,
                        variant_instruction=variant_instructions.get(variant, variant_instructions["A"]),
                        achievements=achievements,
                        job_title=job.get("title", ""),
                        company=job.get("company", ""),
                        company_context=job.get("company_context", "A leading company in its sector"),
                        jd_excerpt=job.get("jd_text", "")[:1500],
                        candidate_name=candidate_name,
                    ),
                },
            ],
            temperature=0.6,
            max_tokens=2000,
        )

        if not result.get("cover_letter"):
            return {"status": "error", "message": "Model returned no cover letter text — try again"}

        logger.success(f"[Agent 06] Cover letter generated: {result.get('word_count')} words, tone={result.get('tone_used')}")
        return {"status": "success", **result}

    except GroqNotConfiguredError as e:
        logger.error(f"[Agent 06] {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"[Agent 06] Failed: {e}")
        return {"status": "error", "message": f"Cover letter generation failed: {e}"}
