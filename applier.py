# applier.py — No Playwright. Opens job URL for manual apply
# or submits via email-based application where supported.

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def get_apply_info(job_url: str) -> dict:
    """
    Visit job page and extract:
    - Direct apply URL (if form-based)
    - HR email (if email-based apply)
    - ATS platform detected (Greenhouse, Lever, Workday, etc.)
    """
    try:
        resp = httpx.get(job_url, headers=HEADERS, timeout=15, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "lxml")
        final_url = str(resp.url)

        # Detect ATS platform
        ats = "unknown"
        apply_url = job_url

        if "greenhouse.io" in final_url:
            ats = "greenhouse"
            btn = soup.select_one("a#btn-apply, a.btn-apply, a[href*='apply']")
            apply_url = btn["href"] if btn else job_url

        elif "lever.co" in final_url:
            ats = "lever"
            btn = soup.select_one("a.template-btn-submit, a[href*='apply']")
            apply_url = btn["href"] if btn else job_url

        elif "workday.com" in final_url:
            ats = "workday"

        elif "linkedin.com" in final_url:
            ats = "linkedin"

        elif "indeed.com" in final_url:
            ats = "indeed"

        # Try to find HR/apply email on page
        import re
        emails = re.findall(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
            resp.text
        )
        hr_email = next(
            (e for e in emails if any(
                kw in e.lower() for kw in ["hr", "recruit", "career", "jobs", "talent", "hiring"]
            )), None
        )

        return {
            "ats":       ats,
            "apply_url": apply_url,
            "hr_email":  hr_email,
            "success":   True,
        }

    except Exception as e:
        return {"success": False, "message": str(e), "ats": "unknown", "apply_url": job_url}


def apply_via_email(
    hr_email: str,
    candidate: dict,
    company: str,
    role: str,
    resume_pdf_path: str,
    sendgrid_key: str,
    from_email: str,
) -> dict:
    """
    Send application directly via email when HR email is found on job page.
    candidate = {name, email, phone, location}
    """
    try:
        import sendgrid
        from sendgrid.helpers.mail import (
            Mail, Attachment, FileContent, FileName,
            FileType, Disposition
        )
        import base64

        sg = sendgrid.SendGridAPIClient(api_key=sendgrid_key)

        body = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {role} position at {company}.

Please find my tailored resume attached for your consideration.

Best regards,
{candidate['name']}
{candidate['email']}
{candidate.get('phone', '')}
"""
        message = Mail(
            from_email=from_email,
            to_emails=hr_email,
            subject=f"Application for {role} — {candidate['name']}",
            plain_text_content=body,
        )

        # Attach resume PDF
        with open(resume_pdf_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode()

        attachment = Attachment(
            FileContent(pdf_data),
            FileName(f"Resume_{candidate['name'].replace(' ', '_')}.pdf"),
            FileType("application/pdf"),
            Disposition("attachment"),
        )
        message.attachment = attachment

        sg.send(message)
        return {"success": True, "method": "email", "sent_to": hr_email}

    except Exception as e:
        return {"success": False, "message": str(e)}


def auto_apply(job_url: str, client_data: dict, resume_pdf_path: str,
               sendgrid_key: str = None, from_email: str = None) -> dict:
    """
    Main apply function. Strategy:
    1. Check if job has HR email  → apply via email
    2. Greenhouse/Lever ATS       → return apply URL (direct API possible)
    3. Others                     → return apply URL for manual apply
    """
    info = get_apply_info(job_url)

    # Strategy 1: Email apply
    if info.get("hr_email") and sendgrid_key:
        result = apply_via_email(
            hr_email=info["hr_email"],
            candidate=client_data,
            company=client_data.get("company", ""),
            role=client_data.get("role", ""),
            resume_pdf_path=resume_pdf_path,
            sendgrid_key=sendgrid_key,
            from_email=from_email,
        )
        if result["success"]:
            return {
                "success": True,
                "method":  "email",
                "message": f"Applied via email to {info['hr_email']}",
            }

    # Strategy 2: Known ATS (Greenhouse / Lever — no CAPTCHA)
    if info["ats"] in ("greenhouse", "lever"):
        return {
            "success":   True,
            "method":    "ats_url",
            "apply_url": info["apply_url"],
            "message":   f"Greenhouse/Lever job — apply URL captured: {info['apply_url']}",
        }

    # Strategy 3: Fallback — log URL for manual apply
    return {
        "success":   False,
        "method":    "manual",
        "apply_url": job_url,
        "message":   "No auto-apply method found. URL saved for manual apply.",
    }
