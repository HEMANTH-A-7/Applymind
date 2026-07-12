"""
Agent 02 — Market Research Agent
Analyzes job market trends, salary bands, in-demand skills, and top hiring companies.
"""
import json
import re
import asyncio
import aiohttp
from datetime import datetime
from loguru import logger
from groq import Groq
from core.config import get_settings

settings = get_settings()
client = Groq(api_key=settings.groq_api_key)

MARKET_ANALYSIS_PROMPT = """You are a job market analyst AI. Generate a comprehensive, data-driven market analysis report for a job seeker.

Target role: {role}
Target location: {location}
User's top skills: {skills}

Return a JSON market analysis report:
{{
  "role_demand": {{
    "overall_score": 85,
    "trend": "rising|stable|declining",
    "hot_locations": ["San Francisco", "New York", "Remote"],
    "top_companies_hiring": [
      {{"company": "Stripe", "openings_estimate": 15, "tier": "unicorn"}},
      {{"company": "Linear", "openings_estimate": 3, "tier": "startup"}}
    ]
  }},
  "salary_data": {{
    "currency": "USD",
    "junior_level": {{"min": 85000, "max": 120000}},
    "mid_level": {{"min": 120000, "max": 180000}},
    "senior_level": {{"min": 180000, "max": 280000}},
    "data_source": "Levels.fyi + LinkedIn + Glassdoor estimates"
  }},
  "skill_demand": {{
    "must_have": ["Python", "FastAPI", "PostgreSQL"],
    "nice_to_have": ["Kubernetes", "Rust", "LLMs"],
    "trending": ["RAG", "Vector DBs", "MCP protocol"],
    "oversupplied": ["jQuery", "PHP", "WordPress"]
  }},
  "user_gap_analysis": {{
    "strong_matches": ["skills user has that market wants"],
    "gaps": ["skills to learn for better positioning"],
    "quick_wins": ["small additions that boost ATS scores significantly"]
  }},
  "top_job_boards": [
    {{"platform": "Wellfound", "best_for": "startups", "avg_response_rate": "23%"}},
    {{"platform": "LinkedIn", "best_for": "enterprise", "avg_response_rate": "12%"}},
    {{"platform": "RemoteOK", "best_for": "remote-first", "avg_response_rate": "18%"}}
  ],
  "market_summary": "2-3 sentence strategic summary for this job seeker",
  "recommended_search_keywords": ["software engineer", "backend developer", "python engineer"],
  "generated_at": "{timestamp}"
}}

Return ONLY valid JSON. Be specific with real company names and realistic salary data."""


async def run_async(role: str, location: str = "Remote", skills: list[str] = None) -> dict:
    """
    Async market research for a given role and location.
    Uses Groq to generate data-driven market intelligence.
    """
    skills = skills or []
    logger.info(f"[Agent 02] Running market research for: {role} in {location}")

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "user",
                    "content": MARKET_ANALYSIS_PROMPT.format(
                        role=role,
                        location=location,
                        skills=", ".join(skills[:15]) or "Python, JavaScript, SQL",
                        timestamp=datetime.utcnow().isoformat(),
                    )
                }
            ],
            temperature=0.4,
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
        market_data = json.loads(content)

        logger.success(f"[Agent 02] Market report generated for '{role}'")
        return {"status": "success", "role": role, "location": location, **market_data}

    except json.JSONDecodeError as e:
        logger.error(f"[Agent 02] JSON parse error: {e}")
        return {"status": "error", "message": f"Failed to parse market data: {e}"}
    except Exception as e:
        logger.error(f"[Agent 02] Market research failed: {e}")
        return {"status": "error", "message": str(e)}


def run(role: str, location: str = "Remote", skills: list[str] = None) -> dict:
    """Sync wrapper."""
    return asyncio.run(run_async(role, location, skills))
