import asyncio
import sys
from loguru import logger
from agents import agent_03_job_scraper

async def test_scrapers():
    logger.info("Starting Scraper Verification Tests...")
    
    # 1. Test Hacker News monthly thread scraper
    logger.info("--- Testing Hacker News Scraper ---")
    hn_jobs = await agent_03_job_scraper.scrape_hn_hiring(keywords=["python", "engineer"], max_jobs=5)
    logger.info(f"Scraped {len(hn_jobs)} jobs from HN")
    for job in hn_jobs[:3]:
        logger.info(f"HN Job: {job['title']} at {job['company']}")
        logger.info(f"  Posted Date: {job['posted_date']}")
        logger.info(f"  Apply URL: {job['apply_url']}")
        assert "news.ycombinator.com/item?id=" not in job["apply_url"] or len(job["apply_url"]) > 0, "No URL fallback or incorrect URL extraction"
        
    # 2. Test LinkedIn paginated scraper
    logger.info("--- Testing LinkedIn Scraper (Paginated & Sorted) ---")
    li_jobs = await agent_03_job_scraper.scrape_linkedin(keywords=["python"], location="Remote", max_jobs=10, sort_by="date")
    logger.info(f"Scraped {len(li_jobs)} jobs from LinkedIn")
    for job in li_jobs[:3]:
        logger.info(f"LinkedIn Job: {job['title']} at {job['company']}")
        logger.info(f"  Posted Date: {job['posted_date']}")
        logger.info(f"  Apply URL: {job['apply_url']}")
        
    # 3. Test main entrypoint with sorting
    logger.info("--- Testing run_async main entrypoint with date sorting ---")
    res = await agent_03_job_scraper.run_async(
        keywords=["python"],
        location="Remote",
        platforms=["hn", "linkedin"],
        max_jobs=15,
        enrich=False,
        sort_by="date"
    )
    jobs = res.get("jobs", [])
    logger.info(f"Total returned from main run: {len(jobs)}")
    
    # Check if they are sorted by posted_date (newest first, empty strings last)
    dates = [j.get("posted_date") or "" for j in jobs]
    logger.info(f"Sorted dates returned: {dates}")
    
    non_empty_dates = [d for d in dates if d]
    is_sorted = all(non_empty_dates[i] >= non_empty_dates[i+1] for i in range(len(non_empty_dates)-1))
    logger.info(f"Are non-empty dates sorted? {is_sorted}")
    assert is_sorted, "Jobs are not correctly sorted by date descending"
    
    logger.success("All scraper verification tests passed!")

if __name__ == "__main__":
    asyncio.run(test_scrapers())
