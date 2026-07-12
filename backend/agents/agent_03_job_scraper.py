"""
Agent 03 — Multi-Source Job Scraper Agent (BeautifulSoup + Groq Enrichment)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scrapes jobs from:
  • RemoteOK  — JSON API (most reliable, no CAPTCHA)
  • Wellfound — HTML + BeautifulSoup
  • Indeed    — HTML + BeautifulSoup
  • HN Who's Hiring — Hacker News API + BS4

After scraping, uses Groq to:
  • Expand sparse job descriptions into full structured JDs
  • Classify apply method (email / form / easy-apply)
  • Extract key requirements for scoring
"""
import hashlib
import asyncio
import json
import re
import time
from datetime import datetime
from typing import Optional
from loguru import logger

import aiohttp
from bs4 import BeautifulSoup
from groq import Groq

from core.config import get_settings

settings = get_settings()
groq_client = Groq(api_key=settings.groq_api_key)

# ─── Rotation headers to reduce bot detection ───
HEADERS_POOL = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"},
]

_header_idx = 0
def _next_headers() -> dict:
    global _header_idx
    h = HEADERS_POOL[_header_idx % len(HEADERS_POOL)]
    _header_idx += 1
    return h


# ─── Unified Job Schema ───
def make_job(
    title: str,
    company: str,
    location: str,
    jd_text: str,
    apply_url: str,
    apply_method: str,
    source: str,
    salary: str = "",
    remote: bool = False,
    job_type: str = "full-time",
    posted_date: Optional[str] = None,
    tags: list[str] = None,
) -> dict:
    dedup_str = f"{title.lower().strip()}::{company.lower().strip()}::{(posted_date or '')[:10]}"
    dedup_hash = hashlib.sha256(dedup_str.encode()).hexdigest()[:16]
    return {
        "job_id": dedup_hash,
        "title": title.strip(),
        "company": company.strip(),
        "location": location.strip(),
        "jd_text": jd_text.strip(),
        "salary": salary.strip(),
        "apply_url": apply_url.strip(),
        "apply_method": apply_method,
        "source": source,
        "remote": remote or "remote" in location.lower() or "remote" in title.lower(),
        "job_type": job_type,
        "tags": tags or [],
        "posted_date": posted_date or datetime.utcnow().isoformat(),
        "scrape_date": datetime.utcnow().isoformat(),
        "dedup_hash": dedup_hash,
        "groq_enriched": False,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GROQ ENRICHMENT — expand short JDs into full JDs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENRICH_PROMPT = """You are a job description analyst. Given sparse job posting data, generate a realistic, detailed job description.

Job Title: {title}
Company: {company}
Location: {location}
Tags/Stack: {tags}
Existing Description: {existing_desc}

Generate a structured job description JSON:
{{
  "full_jd": "Complete 200-word job description with responsibilities and requirements",
  "required_skills": ["skill1", "skill2", "skill3"],
  "nice_to_have": ["skill1", "skill2"],
  "apply_method": "email|form|easy_apply|api",
  "job_level": "junior|mid|senior|staff|lead",
  "estimated_salary": "$120,000-$160,000 or Unknown"
}}
Return ONLY valid JSON."""


async def enrich_job_with_groq(job: dict) -> dict:
    """Use Groq to expand a short/sparse job description into a full structured JD."""
    if len(job.get("jd_text", "")) > 300:
        return job  # Already has enough content, skip API call

    try:
        response = groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=[{
                "role": "user",
                "content": ENRICH_PROMPT.format(
                    title=job.get("title", ""),
                    company=job.get("company", ""),
                    location=job.get("location", "Remote"),
                    tags=", ".join(job.get("tags", [])),
                    existing_desc=job.get("jd_text", "")[:500],
                )
            }],
            temperature=0.3,
            max_tokens=600,
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
        enriched = json.loads(content)

        job["jd_text"] = enriched.get("full_jd", job["jd_text"])
        job["required_skills"] = enriched.get("required_skills", [])
        job["nice_to_have"] = enriched.get("nice_to_have", [])
        job["apply_method"] = enriched.get("apply_method", job["apply_method"])
        job["job_level"] = enriched.get("job_level", "mid")
        if not job["salary"] and enriched.get("estimated_salary", "Unknown") != "Unknown":
            job["salary"] = enriched.get("estimated_salary", "")
        job["groq_enriched"] = True
    except Exception as e:
        logger.debug(f"[Agent 03] Groq enrichment skipped for '{job.get('title')}': {e}")

    return job


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SCRAPER 1: RemoteOK JSON API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def scrape_remoteok(keywords: list[str], max_jobs: int = 40) -> list[dict]:
    """Scrape RemoteOK's public JSON API — no auth, no CAPTCHA."""
    jobs = []
    keyword_lower = [k.lower() for k in keywords]
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                "https://remoteok.com/api",
                headers={"User-Agent": "ApplyMindAI/1.0", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=25, connect=10),
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"[RemoteOK] HTTP {resp.status}")
                    return []
                text = await resp.text()
                import json as _json
                data = _json.loads(text)

        for item in data[1:]:
            if not isinstance(item, dict):
                continue
            title = item.get("position", "")
            item_tags = " ".join(item.get("tags", [])).lower()
            item_desc = BeautifulSoup(item.get("description", ""), "html.parser").get_text(" ", strip=True)

            search_text = f"{title} {item_tags} {item_desc}".lower()
            if not any(kw in search_text for kw in keyword_lower):
                continue

            job = make_job(
                title=title,
                company=item.get("company", "Unknown"),
                location="Remote",
                jd_text=item_desc[:1000],
                salary=f"${item.get('salary_min', 0)//1000}k–${item.get('salary_max', 0)//1000}k"
                    if item.get("salary_min") and item.get("salary_max") else "",
                apply_url=item.get("apply_url") or item.get("url", ""),
                apply_method="email" if "@" in item.get("apply_url", "") else "form",
                source="remoteok",
                remote=True,
                tags=item.get("tags", []),
                posted_date=item.get("date", ""),
            )
            jobs.append(job)
            if len(jobs) >= max_jobs:
                break

        logger.success(f"[RemoteOK] Scraped {len(jobs)} jobs")
    except asyncio.TimeoutError:
        logger.warning("[RemoteOK] Timed out")
    except Exception as e:
        logger.error(f"[RemoteOK] Failed: {type(e).__name__}: {e}")
    return jobs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SCRAPER 2: Hacker News "Who's Hiring" (monthly thread)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def scrape_hn_hiring(keywords: list[str], max_jobs: int = 30) -> list[dict]:
    """Parse the monthly HN 'Who's Hiring' thread via HN Algolia API."""
    jobs = []
    keyword_lower = [k.lower() for k in keywords]
    try:
        # Search for the latest "Who's Hiring" thread using search_by_date and filtering by whoishiring author
        search_url = "https://hn.algolia.com/api/v1/search_by_date?query=Ask+HN+Who+is+hiring&tags=story,author_whoishiring&hitsPerPage=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return []
                meta = await resp.json()
                if not meta.get("hits"):
                    return []
                thread_id = meta["hits"][0]["objectID"]

            # Get all comments in the thread
            comments_url = f"https://hn.algolia.com/api/v1/search?tags=comment,story_{thread_id}&hitsPerPage=200"
            async with session.get(comments_url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        for hit in data.get("hits", []):
            text_html = hit.get("comment_text", "") or ""
            if not text_html:
                continue
            soup = BeautifulSoup(text_html, "html.parser")
            text = soup.get_text(" ", strip=True)

            if len(text) < 50:
                continue

            # Filter by keyword
            if not any(kw in text.lower() for kw in keyword_lower):
                continue

            # Extract company name (usually first word before | or at)
            company_match = re.match(r"^([A-Za-z0-9 &.,]+?)[\s|–-]", text)
            company = company_match.group(1).strip() if company_match else "Unknown"

            # Extract title
            title_patterns = [
                r"(?:hiring|looking for|seeking)\s+(?:a\s+)?([A-Za-z ]+Engineer|[A-Za-z ]+Developer|[A-Za-z ]+Designer|[A-Za-z ]+Manager)",
                r"(Senior|Staff|Lead|Junior|Mid)?\s*([A-Za-z]+)\s+Engineer",
            ]
            title = "Software Engineer"
            for pat in title_patterns:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    title = m.group(0).strip()[:60]
                    break

            # Extract location
            loc_match = re.search(r"\b(Remote|New York|San Francisco|London|Berlin|Austin|Seattle|Toronto)[/,\s]", text, re.I)
            location = loc_match.group(1) if loc_match else "Remote"

            # Extract salary
            sal_match = re.search(r"\$[\d,]+[kK]?\s*[-–]\s*\$[\d,]+[kK]?|\$[\d,]+[kK]", text)
            salary = sal_match.group(0) if sal_match else ""

            # Extract apply URL or email
            urls = []
            for a in soup.find_all("a"):
                href = a.get("href")
                if href and href.startswith(("http://", "https://")):
                    urls.append(href)
            
            # Find first link that doesn't look like a social media profile
            ignore_patterns = [
                r"github\.com/[a-zA-Z0-9_-]+$",  # User profile
                r"twitter\.com/",
                r"linkedin\.com/in/",
                r"medium\.com/",
                r"youtube\.com/",
                r"news\.ycombinator\.com/item\?id="
            ]
            
            apply_url = None
            for u in urls:
                if not any(re.search(pat, u, re.I) for pat in ignore_patterns):
                    apply_url = u
                    break
            
            if not apply_url:
                apply_url = urls[0] if urls else f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"

            job = make_job(
                title=title,
                company=company,
                location=location,
                jd_text=text[:800],
                apply_url=apply_url,
                apply_method="email" if "@" in text else "form",
                source="hn_hiring",
                salary=salary,
                remote="remote" in text.lower(),
                posted_date=hit.get("created_at"),
            )
            jobs.append(job)
            if len(jobs) >= max_jobs:
                break

        logger.success(f"[HN Hiring] Scraped {len(jobs)} jobs")
    except Exception as e:
        logger.error(f"[HN Hiring] Failed: {e}")
    return jobs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SCRAPER 3: Indeed (HTML + BeautifulSoup)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def scrape_indeed(keywords: list[str], location: str = "Remote", max_jobs: int = 30) -> list[dict]:
    """Scrape Indeed search results page using BeautifulSoup."""
    jobs = []
    for keyword in keywords[:2]:
        try:
            q = keyword.replace(" ", "+")
            l = location.replace(" ", "+")
            url = f"https://www.indeed.com/jobs?q={q}&l={l}&sort=date&limit=15&filter=0"

            async with aiohttp.ClientSession(headers=_next_headers()) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        logger.warning(f"[Indeed] HTTP {resp.status} for '{keyword}'")
                        continue
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # Indeed's job cards — try multiple selectors for different layouts
            cards = (
                soup.select("div.job_seen_beacon") or
                soup.select("div[data-jk]") or
                soup.select("li.css-5lfssm") or
                soup.select("div.tapItem")
            )

            if not cards:
                logger.warning(f"[Indeed] No job cards found for '{keyword}' — page structure may have changed")
                continue

            for card in cards[:max_jobs // 2]:
                # Title
                title_el = (
                    card.select_one("h2.jobTitle span[title]") or
                    card.select_one("h2.jobTitle a span") or
                    card.select_one("[data-testid='jobTitle'] span")
                )
                title = title_el.get("title") or title_el.get_text(strip=True) if title_el else keyword.title()

                # Company
                company_el = (
                    card.select_one("span.companyName") or
                    card.select_one("[data-testid='company-name']") or
                    card.select_one("a.companyName")
                )
                company = company_el.get_text(strip=True) if company_el else "Unknown Company"

                # Location
                loc_el = (
                    card.select_one("div.companyLocation") or
                    card.select_one("[data-testid='text-location']")
                )
                loc = loc_el.get_text(strip=True) if loc_el else location

                # Snippet / description
                snippet_el = (
                    card.select_one("div.job-snippet") or
                    card.select_one("[data-testid='job-snippet']") or
                    card.select_one("ul.jobCardShelfContainer")
                )
                snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

                # Salary
                sal_el = (
                    card.select_one("div.salary-snippet-container") or
                    card.select_one("div.metadata.salary-snippet-container")
                )
                salary = sal_el.get_text(strip=True) if sal_el else ""

                # Link
                link_el = card.select_one("h2.jobTitle a") or card.select_one("a[href*='/pagead/']") or card.select_one("a[data-jk]")
                job_url = "https://www.indeed.com" + link_el["href"] if link_el and link_el.get("href") else url

                if not title or not company:
                    continue

                jobs.append(make_job(
                    title=title,
                    company=company,
                    location=loc,
                    jd_text=snippet,
                    apply_url=job_url,
                    apply_method="indeed_apply",
                    source="indeed",
                    salary=salary,
                ))

            await asyncio.sleep(2)  # Polite delay
        except Exception as e:
            logger.error(f"[Indeed] Error for '{keyword}': {e}")

    logger.success(f"[Indeed] Scraped {len(jobs)} jobs")
    return jobs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SCRAPER 4: Wellfound / AngelList (HTML + BeautifulSoup)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def scrape_wellfound(keywords: list[str], location: str = "Remote", max_jobs: int = 30) -> list[dict]:
    """Scrape Wellfound job listings using BeautifulSoup."""
    jobs = []
    for keyword in keywords[:2]:
        try:
            q = keyword.replace(" ", "%20")
            url = f"https://wellfound.com/jobs?q={q}&l={location.replace(' ', '%20')}"
            headers = {
                **_next_headers(),
                "Accept": "text/html,application/xhtml+xml",
                "Referer": "https://wellfound.com",
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        logger.warning(f"[Wellfound] HTTP {resp.status}")
                        continue
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")

            # Try multiple selectors for Wellfound's React-rendered content
            cards = (
                soup.select("div[class*='JobListing']") or
                soup.select("div[data-test='JobListing']") or
                soup.select("div[class*='job-listing']") or
                soup.select("div.styles_jobsListingCard__")
            )

            if not cards:
                # Wellfound is heavily React — fall through to Groq-generated jobs
                logger.info(f"[Wellfound] JS-rendered page, no static cards found for '{keyword}'")
                continue

            for card in cards[:max_jobs // 2]:
                title_el = card.select_one("a[class*='title']") or card.select_one("h2") or card.select_one("h3")
                company_el = card.select_one("a[class*='startup']") or card.select_one("span[class*='company']")
                loc_el = card.select_one("span[class*='location']") or card.select_one("div[class*='location']")
                sal_el = card.select_one("span[class*='salary']") or card.select_one("div[class*='compensation']")
                link_el = card.select_one("a[href*='/jobs/']")

                if not title_el:
                    continue

                job_url = f"https://wellfound.com{link_el['href']}" if link_el and link_el.get("href", "").startswith("/") else url
                jobs.append(make_job(
                    title=title_el.get_text(strip=True),
                    company=company_el.get_text(strip=True) if company_el else "Startup",
                    location=loc_el.get_text(strip=True) if loc_el else location,
                    jd_text=card.get_text(" ", strip=True)[:500],
                    apply_url=job_url,
                    apply_method="wellfound_form",
                    source="wellfound",
                    salary=sal_el.get_text(strip=True) if sal_el else "",
                ))

            await asyncio.sleep(1.5)
        except Exception as e:
            logger.error(f"[Wellfound] Error for '{keyword}': {e}")

    logger.success(f"[Wellfound] Scraped {len(jobs)} jobs")
    return jobs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SCRAPER 5: LinkedIn (HTML + BeautifulSoup)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def scrape_linkedin(keywords: list[str], location: str = "Remote", max_jobs: int = 30, sort_by: str = "date") -> list[dict]:
    """Scrape LinkedIn public search results page using BeautifulSoup."""
    jobs = []
    for keyword in keywords[:2]:
        try:
            q = keyword.replace(" ", "%20")
            l = location.replace(" ", "%20")
            
            # Determine how many pages to fetch. LinkedIn has 25 results per page.
            jobs_per_keyword = max_jobs // min(len(keywords[:2]), 2)
            pages = max(1, (jobs_per_keyword + 24) // 25)
            
            for page in range(pages):
                start_val = page * 25
                sort_param = "&sortBy=DD" if sort_by == "date" else ""
                # f_TPR=r2592000 is 1 month in seconds
                date_filter = "&f_TPR=r2592000" if sort_by == "date" else ""
                
                url = f"https://www.linkedin.com/jobs/search?keywords={q}&location={l}&start={start_val}{sort_param}{date_filter}"
                logger.info(f"[LinkedIn] Fetching page {page+1} (start={start_val}) for '{keyword}': {url}")
                
                async with aiohttp.ClientSession(headers=_next_headers()) as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status != 200:
                            logger.warning(f"[LinkedIn] HTTP {resp.status} for '{keyword}' page {page+1}")
                            break
                        html = await resp.text()

                soup = BeautifulSoup(html, "html.parser")

                cards = (
                    soup.select("div.base-card") or
                    soup.select("li div.base-search-card") or
                    soup.select("a.base-card__full-link") or
                    soup.select("div.job-search-card")
                )

                if not cards:
                    # Fallback: find all anchor tags with /jobs/view/
                    cards = [a.find_parent("div") or a.find_parent("li") or a for a in soup.find_all("a", href=re.compile(r"/jobs/view/"))]
                    cards = [c for c in cards if c is not None]

                if not cards:
                    logger.warning(f"[LinkedIn] No job cards found on page {page+1} for '{keyword}'")
                    break

                page_jobs_added = 0
                for card in cards:
                    link_el = (
                        card if card.name == "a" and "jobs/view" in card.get("href", "") else
                        card.select_one("a.base-card__full-link") or
                        card.select_one("a[href*='/jobs/view/']") or
                        card.find("a", href=re.compile(r"/jobs/view/"))
                    )
                    if not link_el or not link_el.get("href"):
                        continue
                    job_url = link_el["href"].split("?")[0]

                    title_el = (
                        card.select_one("h3.base-search-card__title") or
                        card.select_one(".base-card__title") or
                        card.select_one(".job-search-card__title") or
                        card.select_one("h2") or
                        card.select_one("h3")
                    )
                    title = title_el.get_text(strip=True) if title_el else keyword.title()

                    company_el = (
                        card.select_one("h4.base-search-card__subtitle") or
                        card.select_one("a.base-search-card__subtitle-link") or
                        card.select_one(".base-card__subtitle") or
                        card.select_one(".job-search-card__subtitle")
                    )
                    company = company_el.get_text(strip=True) if company_el else "Unknown Company"

                    loc_el = (
                        card.select_one("span.job-search-card__location") or
                        card.select_one(".base-search-card__metadata span") or
                        card.select_one(".job-search-card__location")
                    )
                    loc = loc_el.get_text(strip=True) if loc_el else location

                    date_el = (
                        card.select_one("time.job-search-card__listdate") or
                        card.select_one("time.job-search-card__listdate--new") or
                        card.select_one("time")
                    )
                    posted_date = date_el.get("datetime") if date_el else None

                    snippet = f"Job opportunity for {title} at {company} in {loc}."

                    if not title or not company:
                        continue

                    jobs.append(make_job(
                        title=title,
                        company=company,
                        location=loc,
                        jd_text=snippet,
                        apply_url=job_url,
                        apply_method="linkedin_easy_apply" if "easy" in card.get_text().lower() else "linkedin",
                        source="linkedin",
                        posted_date=posted_date,
                    ))
                    page_jobs_added += 1

                logger.info(f"[LinkedIn] Added {page_jobs_added} jobs from page {page+1}")
                if len(jobs) >= max_jobs:
                    break

                await asyncio.sleep(2.0)  # Polite delay between pages
        except Exception as e:
            logger.error(f"[LinkedIn] Error for '{keyword}': {e}")

    logger.success(f"[LinkedIn] Scraped {len(jobs)} jobs total")
    return jobs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SCRAPER 6: Search Engine (Yahoo Search)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def scrape_search_engine(keywords: list[str], location: str = "Remote", max_jobs: int = 30) -> list[dict]:
    """Scrape Yahoo search for Lever/Greenhouse/Ashby/Workday job posts across the web."""
    from urllib.parse import unquote, urlparse
    jobs = []
    domains = ["greenhouse.io", "lever.co", "ashbyhq.com", "myworkdayjobs.com"]
    for keyword in keywords[:2]:
        try:
            # Query format: site:greenhouse.io OR site:lever.co "python developer"
            site_queries = " OR ".join([f"site:{d}" for d in domains])
            if location and location.lower() != "remote":
                q = f"({site_queries}) \"{keyword}\" \"{location}\""
            else:
                q = f"({site_queries}) \"{keyword}\" remote"
            
            q_encoded = q.replace(" ", "+").replace(":", "%3A").replace("(", "%28").replace(")", "%29")
            url = f"https://search.yahoo.com/search?p={q_encoded}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        logger.warning(f"[SearchEngine] Yahoo HTTP {resp.status} for query '{keyword}'")
                        continue
                    html = await resp.text()

            soup = BeautifulSoup(html, "html.parser")
            results = soup.select(".algo-sr") or soup.select(".compTitle") or soup.find_all("div", class_=re.compile(r"SearchResult"))

            if not results:
                logger.warning(f"[SearchEngine] No Yahoo search results found for '{keyword}'")
                continue

            for res in results[:max_jobs // 2]:
                title_el = res.find("a")
                if not title_el:
                    continue

                raw_url = title_el.get("href")
                if not raw_url:
                    continue

                # Clean Yahoo redirect wrappers
                job_url = raw_url
                if "/RU=" in raw_url:
                    try:
                        target_encoded = raw_url.split("/RU=")[1].split("/RK=")[0]
                        job_url = unquote(target_encoded)
                    except Exception as parse_err:
                        logger.debug(f"[SearchEngine] Redirect parse error: {parse_err}")

                # Ignore non-job board links
                if not any(domain in job_url for domain in domains):
                    continue

                # Clean title parsing from Yahoo's combined structure
                title_text = ""
                title_h3 = title_el.select_one("h3.title") or title_el.select_one("h3") or title_el.select_one("h2")
                if title_h3:
                    title_text = title_h3.get_text(strip=True)
                else:
                    title_text = title_el.get_text(strip=True)

                # Clean snippet parsing
                snippet_el = res.select_one(".compText p") or res.select_one(".compText") or res.find(class_=re.compile(r"compText|lh-16|fc-2nd|desc"))
                snippet_text = snippet_el.get_text(strip=True) if snippet_el else ""

                # Extract company name cleanly from URL/hostname
                company = "Unknown Tech"
                try:
                    parsed_url = urlparse(job_url)
                    hostname = parsed_url.hostname or ""
                    
                    if "myworkdayjobs.com" in hostname:
                        parts = hostname.split(".")
                        if len(parts) > 0:
                            company = parts[0].replace("-", " ").title()
                    elif any(d in hostname for d in ["greenhouse.io", "lever.co", "ashbyhq.com"]):
                        path_parts = [p for p in parsed_url.path.split("/") if p]
                        if len(path_parts) > 0:
                            first_part = path_parts[0]
                            if first_part.lower() in ["jobs", "job", "careers", "career", "embed"] and len(path_parts) > 1:
                                company = path_parts[1].replace("-", " ").title()
                            else:
                                company = first_part.replace("-", " ").title()
                except Exception as e:
                    logger.debug(f"[SearchEngine] Error parsing company: {e}")

                if company == "Unknown Tech":
                    m = re.search(r" at ([A-Za-z0-9 ]+)", title_text, re.I)
                    if m:
                        company = m.group(1).strip()
                    else:
                        m = re.search(r" - ([A-Za-z0-9 ]+)", title_text)
                        if m:
                            company = m.group(1).strip()

                title = title_text
                title = re.sub(r"\s+at\s+.*$", "", title, flags=re.I)
                title = re.sub(r"\s+-\s+.*$", "", title)
                title = re.sub(r"\s*\|\s*.*$", "", title)

                jobs.append(make_job(
                    title=title,
                    company=company,
                    location=location,
                    jd_text=snippet_text,
                    apply_url=job_url,
                    apply_method="form",
                    source="search_engine",
                    remote="remote" in location.lower() or "remote" in title_text.lower(),
                ))

            await asyncio.sleep(1.5)
        except Exception as e:
            logger.error(f"[SearchEngine] Error for '{keyword}': {e}")

    logger.success(f"[SearchEngine] Scraped {len(jobs)} jobs from web search")
    return jobs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GROQ FALLBACK — Generate realistic jobs when scraping yields 0
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERATE_JOBS_PROMPT = """Generate exactly {count} realistic job postings for "{keywords}" roles.
Return a JSON array. Each object MUST have these exact keys:
[{{"title": "...", "company": "...", "location": "Remote", "jd_text": "100 word job description", "salary": "$X-$Y", "apply_url": "https://...", "apply_method": "form", "tags": ["Python", "FastAPI"], "job_level": "senior"}}]
Use real companies (Stripe, Linear, Notion, Vercel, Supabase, Retool, Figma, Clerk).
Return ONLY the JSON array, no markdown, no extra text."""


async def generate_jobs_with_groq(keywords: list[str], location: str, count: int = 15) -> list[dict]:
    """Use Groq to generate realistic job postings when real scraping fails."""
    logger.info(f"[Agent 03] Groq fallback: generating {count} jobs for {keywords}")
    all_jobs = []
    # Generate in batches of 5 to avoid JSON truncation
    batch_size = 5
    batches = (count + batch_size - 1) // batch_size

    for batch_num in range(batches):
        batch_count = min(batch_size, count - len(all_jobs))
        if batch_count <= 0:
            break
        try:
            response = groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[{
                    "role": "user",
                    "content": GENERATE_JOBS_PROMPT.format(
                        count=batch_count,
                        keywords=", ".join(keywords),
                    )
                }],
                temperature=0.6,
                max_tokens=1500,
            )
            content = response.choices[0].message.content.strip()
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)

            # Ensure the array is closed (handle truncation)
            if content.count("[") > content.count("]"):
                content = content.rstrip("," + " \n") + "]]".replace("]]", "]")

            raw_jobs = json.loads(content)
            if not isinstance(raw_jobs, list):
                raw_jobs = [raw_jobs]

            for item in raw_jobs:
                if not item.get("title") or not item.get("company"):
                    continue
                job = make_job(
                    title=item.get("title", "Software Engineer"),
                    company=item.get("company", "Tech Company"),
                    location=item.get("location", location),
                    jd_text=item.get("jd_text", ""),
                    apply_url=item.get("apply_url", ""),
                    apply_method=item.get("apply_method", "form"),
                    source="groq_generated",
                    salary=item.get("salary", ""),
                    tags=item.get("tags", []),
                )
                job["job_level"] = item.get("job_level", "mid")
                job["groq_enriched"] = True
                all_jobs.append(job)
        except json.JSONDecodeError as e:
            logger.warning(f"[Agent 03] Groq batch {batch_num+1} JSON parse error: {e}")
        except Exception as e:
            logger.error(f"[Agent 03] Groq fallback batch {batch_num+1} failed: {e}")
            break

    logger.success(f"[Agent 03] Groq generated {len(all_jobs)} fallback jobs")
    return all_jobs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DEDUPLICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def deduplicate(jobs: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for job in jobs:
        h = job.get("dedup_hash", "")
        if h and h not in seen:
            seen.add(h)
            unique.append(job)
    return unique


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GROQ BATCH ENRICHMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def enrich_batch(jobs: list[dict], max_enrich: int = 20) -> list[dict]:
    """
    Enrich up to max_enrich sparse jobs with Groq.
    Only enriches jobs that have short descriptions (<300 chars).
    """
    to_enrich = [j for j in jobs if len(j.get("jd_text", "")) < 300][:max_enrich]
    already_good = [j for j in jobs if len(j.get("jd_text", "")) >= 300]

    enriched = []
    for job in to_enrich:
        enriched.append(await enrich_job_with_groq(job))
        await asyncio.sleep(0.3)  # Rate limit: ~3 req/sec

    return already_good + enriched


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def run_async(
    keywords: list[str] = None,
    location: str = "Remote",
    platforms: list[str] = None,
    max_jobs: int = 100,
    enrich: bool = True,
    sort_by: str = "date",
) -> dict:
    """
    Async scrape across all platforms + Groq enrichment.

    Args:
        keywords: Search terms (e.g. ["python developer", "backend engineer"])
        location: Target location ("Remote", "New York", etc.)
        platforms: Which to scrape (["linkedin", "search_engine", "remoteok", "hn", "indeed", "wellfound"])
        max_jobs: Max total jobs to return
        enrich: Whether to use Groq to expand sparse JDs
        sort_by: How to sort ("date" or "score")

    Returns:
        dict with jobs list, counts, sources breakdown
    """
    keywords = keywords or ["software engineer", "python developer"]
    platforms = platforms or ["linkedin", "search_engine", "remoteok", "hn", "indeed", "wellfound"]
    per_platform = max(max_jobs // len(platforms), 15)

    logger.info(f"[Agent 03] Scraping {platforms} | keywords={keywords} | location={location} | sort_by={sort_by}")

    tasks = []
    if "linkedin" in platforms:
        tasks.append(("linkedin", scrape_linkedin(keywords, location, per_platform, sort_by)))
    if "search_engine" in platforms or "web_search" in platforms:
        tasks.append(("search_engine", scrape_search_engine(keywords, location, per_platform)))
    if "remoteok" in platforms:
        tasks.append(("remoteok", scrape_remoteok(keywords, per_platform)))
    if "hn" in platforms or "hn_hiring" in platforms:
        tasks.append(("hn_hiring", scrape_hn_hiring(keywords, per_platform)))
    if "indeed" in platforms:
        tasks.append(("indeed", scrape_indeed(keywords, location, per_platform)))
    if "wellfound" in platforms:
        tasks.append(("wellfound", scrape_wellfound(keywords, location, per_platform)))

    # Run all scrapers in parallel
    results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

    all_jobs = []
    source_counts = {}
    for (name, _), result in zip(tasks, results):
        if isinstance(result, list):
            all_jobs.extend(result)
            source_counts[name] = len(result)
        else:
            logger.error(f"[Agent 03] {name} error: {result}")
            source_counts[name] = 0

    # Deduplicate
    unique = deduplicate(all_jobs)
    logger.info(f"[Agent 03] {len(all_jobs)} total → {len(unique)} unique after dedup")

    # ── Groq fallback: generate synthetic jobs if scrapers returned too few ──
    if len(unique) < 5:
        logger.warning(f"[Agent 03] Only {len(unique)} scraped — using Groq to generate synthetic jobs")
        synthetic = await generate_jobs_with_groq(keywords, location, max(10, max_jobs // 3))
        # Merge, deduplicate again
        unique = deduplicate(unique + synthetic)
        logger.info(f"[Agent 03] After Groq fallback: {len(unique)} total jobs")

    # Groq enrichment: expand short descriptions
    if enrich and unique:
        logger.info(f"[Agent 03] Enriching sparse JDs with Groq...")
        unique = await enrich_batch(unique, max_enrich=min(15, len(unique)))

    # Sort
    if sort_by == "date":
        unique.sort(key=lambda j: j.get("posted_date") or "", reverse=True)
    else:
        # Default: groq-enriched and real jobs first, then by JD length
        unique.sort(key=lambda j: (j.get("source") != "groq_generated", -len(j.get("jd_text", ""))), reverse=False)

    final = unique[:max_jobs]
    logger.success(
        f"[Agent 03] Done: {len(final)} jobs | sources: {source_counts} | "
        f"groq_enriched: {sum(1 for j in final if j.get('groq_enriched'))}"
    )

    return {
        "status": "success",
        "total_scraped": len(all_jobs),
        "unique_jobs": len(unique),
        "returned": len(final),
        "source_breakdown": source_counts,
        "groq_enriched_count": sum(1 for j in final if j.get("groq_enriched")),
        "jobs": final,
    }


def run(keywords: list[str] = None, location: str = "Remote",
        platforms: list[str] = None, max_jobs: int = 100, enrich: bool = True, sort_by: str = "date") -> dict:
    """Sync wrapper — safe to call from FastAPI BackgroundTasks."""
    return asyncio.run(run_async(keywords, location, platforms, max_jobs, enrich, sort_by))
