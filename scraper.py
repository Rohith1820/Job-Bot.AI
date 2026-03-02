import asyncio
from playwright.async_api import async_playwright
import httpx, json

TARGET_BOARDS = {
    "linkedin": "https://www.linkedin.com/jobs/search/?keywords={role}&location={location}",
    "indeed":   "https://www.indeed.com/jobs?q={role}&l={location}",
    "greenhouse": "https://boards.greenhouse.io/{company}/jobs",
}

async def scrape_jobs(roles: list, location: str, max_per_role: int = 10) -> list:
    """Scrape job listings for given roles. Returns list of job dicts."""
    jobs = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set realistic user agent
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        for role in roles:
            url = TARGET_BOARDS["indeed"].format(
                role=role.replace(" ", "+"),
                location=location.replace(" ", "+")
            )
            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_selector(".job_seen_beacon", timeout=10000)
                
                cards = await page.query_selector_all(".job_seen_beacon")
                for card in cards[:max_per_role]:
                    title = await card.query_selector(".jobTitle")
                    company = await card.query_selector(".companyName")
                    link = await card.query_selector("a")
                    
                    if title and company and link:
                        jobs.append({
                            "role": await title.inner_text(),
                            "company": await company.inner_text(),
                            "url": "https://www.indeed.com" + await link.get_attribute("href"),
                            "source": "indeed"
                        })
            except Exception as e:
                print(f"Scrape error for {role}: {e}")

        await browser.close()
    return jobs


async def get_job_description(url: str) -> str:
    """Visit job URL and extract full job description text."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle")
            # Try common JD containers
            for selector in ["#jobDescriptionText", ".jobsearch-jobDescriptionText", 
                             ".job-description", "#job-description", "main"]:
                el = await page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    await browser.close()
                    return text[:4000]  # limit tokens
        except Exception as e:
            print(f"JD fetch error: {e}")
        await browser.close()
    return ""
