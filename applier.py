import asyncio
from playwright.async_api import async_playwright
from twocaptcha import TwoCaptcha
import os

solver = TwoCaptcha(os.getenv("TWO_CAPTCHA_KEY"))

async def auto_apply(job_url: str, client_data: dict, resume_pdf_path: str) -> dict:
    """
    Attempt to auto-fill and submit a job application form.
    client_data: {name, email, phone, location, resume_text}
    Returns: {success: bool, message: str}
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(job_url, timeout=30000)
            await page.wait_for_load_state("networkidle")

            # Click "Apply" button variants
            for btn_text in ["Apply Now", "Apply", "Easy Apply", "Apply for this job"]:
                btn = page.get_by_role("button", name=btn_text)
                if await btn.count() > 0:
                    await btn.first.click()
                    await page.wait_for_load_state("networkidle")
                    break

            # Fill common fields using client's REAL email
            field_map = {
                'input[name*="name"], input[placeholder*="name" i]':   client_data["name"],
                'input[name*="email"], input[type="email"]':            client_data["email"],
                'input[name*="phone"], input[type="tel"]':              client_data["phone"],
                'input[name*="location"], input[placeholder*="city" i]': client_data["location"],
            }
            for selector, value in field_map.items():
                try:
                    el = page.locator(selector).first
                    if await el.count() > 0:
                        await el.fill(value)
                except:
                    pass

            # Upload resume PDF
            file_input = page.locator('input[type="file"]').first
            if await file_input.count() > 0:
                await file_input.set_input_files(resume_pdf_path)

            # Handle CAPTCHA if present
            captcha = page.locator(".g-recaptcha, iframe[src*='recaptcha']").first
            if await captcha.count() > 0:
                site_key = await page.evaluate(
                    "document.querySelector('.g-recaptcha')?.dataset?.sitekey"
                )
                if site_key:
                    result = solver.recaptcha(sitekey=site_key, url=page.url)
                    await page.evaluate(
                        f"document.getElementById('g-recaptcha-response').innerHTML='{result['code']}'"
                    )

            # Submit the form
            for submit_text in ["Submit", "Submit Application", "Send Application"]:
                btn = page.get_by_role("button", name=submit_text)
                if await btn.count() > 0:
                    await btn.first.click()
                    await page.wait_for_load_state("networkidle")
                    break

            await browser.close()
            return {"success": True, "message": f"Applied using {client_data['email']}"}

        except Exception as e:
            await browser.close()
            return {"success": False, "message": str(e)}
