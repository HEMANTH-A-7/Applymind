"""Quick pipeline test: scrape + match + Groq enrichment."""
import asyncio, sys
sys.path.insert(0, ".")

from agents.agent_03_job_scraper import run_async as scrape
from agents.agent_04_job_match import run as match_score


FAKE_RESUME = {
    "contact": {"name": "Test User", "email": "test@example.com"},
    "summary": "Backend engineer with 4 years Python experience",
    "skills": {
        "technical": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        "tools": ["Git", "Linux", "AWS", "Celery"],
        "languages": ["Python", "JavaScript", "SQL"],
    },
    "experience": [
        {
            "role": "Backend Engineer",
            "company": "Acme Corp",
            "start_date": "2021",
            "end_date": "Present",
            "bullets": [
                "Built FastAPI microservices serving 2M req/day",
                "Reduced PostgreSQL query time by 60% via indexing",
            ],
        }
    ],
    "projects": [],
    "education": [{"degree": "B.Tech Computer Science", "institution": "VIT", "year": "2021"}],
}


async def main():
    print("=" * 60)
    print("STEP 1: Scraping jobs (remoteok + hn_hiring)...")
    print("=" * 60)
    scrape_result = await scrape(
        keywords=["python developer", "backend engineer"],
        location="Remote",
        platforms=["linkedin", "search_engine", "remoteok", "hn"],
        max_jobs=15,
        enrich=False,  # skip enrichment for speed in test
    )
    print(f"  Status     : {scrape_result['status']}")
    print(f"  Returned   : {scrape_result['returned']}")
    print(f"  Sources    : {scrape_result['source_breakdown']}")

    jobs = scrape_result["jobs"]
    if not jobs:
        print("  No jobs scraped — check network. Stopping test.")
        return

    print()
    print("=" * 60)
    print(f"STEP 2: Scoring {len(jobs)} jobs (TF-IDF + Groq top-3)...")
    print("=" * 60)
    match_result = match_score(FAKE_RESUME, jobs, threshold=40, deep_analyze_top_n=3)
    print(f"  Total scored : {match_result['total_scored']}")
    print(f"  Apply queue  : {match_result['apply_queue_count']}")
    print(f"  Groq analyzed: {match_result.get('groq_analyzed_count', 0)}")

    print()
    print("TOP 5 JOB MATCHES:")
    for j in match_result["ranked_jobs"][:5]:
        score = j.get("fit_score", 0)
        label = j.get("fit_label", "")
        rec   = j.get("recommendation", "")
        gaps  = j.get("missing_skills", [])
        print(f"  [{score:3d}] {j['title'][:40]:<40} @ {j['company'][:20]:<20} | {label} | {rec}")
        if gaps:
            print(f"        Missing: {', '.join(gaps[:3])}")

    print()
    print("PIPELINE TEST PASSED")

asyncio.run(main())
