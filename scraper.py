# scraper.py — No Playwright. Uses httpx + BeautifulSoup only.

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_jobs(roles: list, location: str, max_per_role: int = 10) -> list:
    """Scrape job listings from Indeed for given roles. No browser needed."""
    jobs = []

    for role in roles:
        url = (
            "https://www.indeed.com/jobs"
            f"?q={role.replace(' ', '+')}"
            f"&l={location.replace(' ', '+')}"
        )
        try:
            resp = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
            soup = BeautifulSoup(resp.text, "lxml")

            cards = soup.select(".job_seen_beacon")
            for card in cards[:max_per_role]:
                title   = card.select_one(".jobTitle")
                company = card.select_one(".companyName")
                link    = card.select_one("a[href]")

                if title and company and link:
                    href = link.get("href", "")
                    full_url = (
                        "https://www.indeed.com" + href
                        if href.startswith("/")
                        else href
                    )
                    jobs.append({
                        "role":    title.get_text(strip=True),
                        "company": company.get_text(strip=True),
                        "url":     full_url,
                        "source":  "indeed",
                    })

            print(f"[SCRAPER] Found {len(cards)} jobs for '{role}'")

        except Exception as e:
            print(f"[SCRAPER] Error scraping '{role}': {e}")

    return jobs


def get_job_description(url: str) -> str:
    """Fetch full job description text from a job URL."""
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "lxml")

        # Try common JD containers across job boards
        selectors = [
            "#jobDescriptionText",
            ".jobsearch-jobDescriptionText",
            ".job-description",
            "#job-description",
            ".description__text",      # LinkedIn
            ".jobDetails",             # Greenhouse
            "[data-testid='job-description']",
            "main",
        ]
        for selector in selectors:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(separator="\n", strip=True)
                if len(text) > 100:    # ignore tiny/empty matches
                    return text[:4000]

    except Exception as e:
        print(f"[SCRAPER] JD fetch error for {url}: {e}")

    return ""
