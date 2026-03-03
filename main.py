# backend/main.py
import sys
import os

# Force Python to find all modules in the same folder — fixes Render import errors
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from database import Session, Client, Application, BotLog
import uuid, json, base64
from datetime import datetime

app = FastAPI(title="JobBot AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic Models ────────────────────────────────────────────────────────
class ClientCreate(BaseModel):
    name: str
    email: str
    phone: str = ""
    location: str = ""
    roles: list
    resume: str

class ToggleBot(BaseModel):
    active: int  # 1 = on, 0 = off

# ── Routes ────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "JobBot AI is running 🤖"}

@app.post("/api/client")
def create_client(data: ClientCreate):
    db = Session()
    try:
        existing = db.query(Client).filter(Client.email == data.email).first()
        if existing:
            existing.active = 1
            db.commit()
            return {"id": existing.id, "message": "Client already exists. Bot reactivated."}
        client = Client(
            id=str(uuid.uuid4()),
            name=data.name,
            email=data.email,
            phone=data.phone,
            location=data.location,
            roles=json.dumps(data.roles),
            resume=data.resume,
            active=1
        )
        db.add(client)
        db.commit()
        return {"id": client.id, "message": "Client created. Bot is now active!"}
    finally:
        db.close()

@app.get("/api/client/{client_id}")
def get_client(client_id: str):
    db = Session()
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        return {
            "id": client.id, "name": client.name,
            "email": client.email, "phone": client.phone,
            "location": client.location,
            "roles": json.loads(client.roles),
            "active": client.active
        }
    finally:
        db.close()

@app.post("/api/client/{client_id}/toggle")
def toggle_bot(client_id: str, data: ToggleBot):
    db = Session()
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        client.active = data.active
        db.commit()
        return {"message": "Bot status updated", "active": data.active}
    finally:
        db.close()

@app.get("/api/applications/{client_id}")
def get_applications(client_id: str):
    db = Session()
    try:
        apps = (
            db.query(Application)
            .filter(Application.client_id == client_id)
            .order_by(Application.applied_at.desc())
            .all()
        )
        return [
            {
                "id":         a.id,
                "company":    a.company,
                "role":       a.role,
                "job_url":    a.job_url,
                "status":     a.status,
                "score":      a.match_score,
                "email_used": a.email_used,
                "date":       str(a.applied_at.date()),
                "has_pdf":    bool(a.pdf_data),
            }
            for a in apps
        ]
    finally:
        db.close()

@app.get("/api/resume/{application_id}/download")
def download_resume(application_id: str):
    db = Session()
    try:
        app_record = db.query(Application).filter(Application.id == application_id).first()
        if not app_record:
            raise HTTPException(status_code=404, detail="Application not found")
        if not app_record.pdf_data:
            raise HTTPException(status_code=404, detail="No PDF available")
        pdf_bytes = base64.b64decode(app_record.pdf_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; filename="Resume_{app_record.company}_{app_record.role}.pdf"'
            }
        )
    finally:
        db.close()

@app.get("/api/resume/{application_id}/text")
def get_resume_text(application_id: str):
    db = Session()
    try:
        app_record = db.query(Application).filter(Application.id == application_id).first()
        if not app_record:
            raise HTTPException(status_code=404, detail="Application not found")
        return {"resume": app_record.tailored_cv, "company": app_record.company, "role": app_record.role}
    finally:
        db.close()

@app.get("/api/botlog/{client_id}")
def get_bot_log(client_id: str):
    db = Session()
    try:
        logs = (
            db.query(BotLog)
            .filter(BotLog.client_id == client_id)
            .order_by(BotLog.created_at.desc())
            .limit(50)
            .all()
        )
        return [
            {
                "time":    l.created_at.strftime("%H:%M:%S"),
                "message": l.message,
                "level":   l.level,
            }
            for l in logs
        ]
    finally:
        db.close()

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": str(datetime.utcnow())}
