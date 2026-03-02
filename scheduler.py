from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database import Session, Client, Application
from scraper import scrape_jobs, get_job_description
from tailor import tailor_resume
from pdf_gen import generate_and_upload_pdf
from applier import auto_apply
from emailer import send_application_confirmation
import asyncio, uuid, json, tempfile, os

scheduler = BlockingScheduler()

def run_bot():
    """Main bot loop — runs every 30 minutes."""
    db = Session()
    clients = db.query(Client).filter(Client.active == 1).all()
    
    for client in clients:
        roles = json.loads(client.roles)
        print(f"[BOT] Running for {client.name} | Roles: {roles}")
        
        # 1. Scrape jobs
        jobs = asyncio.run(scrape_jobs(roles, client.location or "United States"))
        
        for job in jobs:
            # Skip already applied
            exists = db.query(Application).filter_by(
                client_id=client.id, job_url=job["url"]
            ).first()
            if exists:
                continue
            
            # 2. Get full JD
            jd = asyncio.run(get_job_description(job["url"]))
            if not jd:
                continue
            
            # 3. Tailor resume with Claude AI
            result = tailor_resume(
                base_resume=client.resume,
                jd=jd,
                role=job["role"],
                company=job["company"],
                candidate_name=client.name,
                email=client.email,      # CLIENT'S REAL EMAIL
                phone=client.phone
            )
            
            # 4. Generate PDF & upload to S3
            pdf_url = generate_and_upload_pdf(
                result["tailored"],
                filename=f"{client.id}_{job['company'].replace(' ','_')}.pdf"
            )
            
            # 5. Auto-apply on company site using client's email
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                # download pdf locally for upload
                import httpx
                f.write(httpx.get(pdf_url).content)
                tmp_path = f.name

            apply_result = asyncio.run(auto_apply(
                job_url=job["url"],
                client_data={
                    "name": client.name,
                    "email": client.email,   # REAL EMAIL used in forms
                    "phone": client.phone,
                    "location": client.location
                },
                resume_pdf_path=tmp_path
            ))
            os.unlink(tmp_path)
            
            status = "Applied" if apply_result["success"] else "Failed"
            
            # 6. Save to database
            app = Application(
                id=str(uuid.uuid4()),
                client_id=client.id,
                company=job["company"],
                role=job["role"],
                job_url=job["url"],
                status=status,
                jd_text=jd,
                tailored_cv=result["tailored"],
                pdf_url=pdf_url,
                match_score=result["score"],
                email_used=client.email
            )
            db.add(app)
            db.commit()
            
            # 7. Email client confirmation with PDF download link
            if apply_result["success"]:
                send_application_confirmation(
                    to_email=client.email,
                    candidate_name=client.name,
                    company=job["company"],
                    role=job["role"],
                    pdf_url=pdf_url,
                    match_score=result["score"]
                )
            
            print(f"[BOT] {status}: {job['role']} at {job['company']} | email: {client.email}")

    db.close()

# Run every 30 minutes, 24/7
scheduler.add_job(run_bot, IntervalTrigger(minutes=30))
scheduler.start()
