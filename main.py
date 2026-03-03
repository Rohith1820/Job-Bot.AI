# main.py — Complete single-file backend. No separate database.py needed.
# Place this file wherever your Render service points to.

import os, sys, uuid, json, base64, re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Database setup ────────────────────────────────────────────────────────
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("postgresql://jobbot_db_p253_user:WECrnZapWW6nltv7ed6wt219kvd9498K@dpg-d6j28lpaae7s739bgiag-a/jobbot_db_p253", "sqlite:///./jobbot.db")

# Fix Render's postgres:// → postgresql:// (SQLAlchemy requires this)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Safety check — if still broken URL, fall back to SQLite
try:
    engine = create_engine(DATABASE_URL)
    engine.connect()
    print(f"✅ Database connected: {DATABASE_URL[:30]}...")
except Exception as e:
    print(f"⚠️ DB connect failed ({e}), falling back to SQLite")
    engine = create_engine("sqlite:///./jobbot.db")
Session = sessionmaker(bind=engine)
Base    = declarative_base()

class Client(Base):
    __tablename__ = "clients"
    id         = Column(String,   primary_key=True)
    name       = Column(String,   nullable=False)
    email      = Column(String,   nullable=False, unique=True)
    phone      = Column(String,   default="")
    location   = Column(String,   default="")
    roles      = Column(Text,     default="[]")
    resume     = Column(Text,     default="")
    active     = Column(Integer,  default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"
    id          = Column(String,   primary_key=True)
    client_id   = Column(String,   nullable=False)
    company     = Column(String,   default="")
    role        = Column(String,   default="")
    job_url     = Column(String,   default="")
    status      = Column(String,   default="Applied")
    jd_text     = Column(Text,     default="")
    tailored_cv = Column(Text,     default="")
    pdf_data    = Column(Text,     default="")   # base64 PDF
    match_score = Column(Float,    default=0.0)
    email_used  = Column(String,   default="")
    applied_at  = Column(DateTime, default=datetime.utcnow)

class BotLog(Base):
    __tablename__ = "bot_logs"
    id         = Column(String,   primary_key=True)
    client_id  = Column(String,   nullable=False)
    message    = Column(Text,     default="")
    level      = Column(String,   default="info")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

# ── FastAPI app ───────────────────────────────────────────────────────────
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI(title="JobBot AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic schemas ──────────────────────────────────────────────────────
class ClientCreate(BaseModel):
    name:     str
    email:    str
    phone:    str = ""
    location: str = ""
    roles:    list
    resume:   str

class ToggleBot(BaseModel):
    active: int

# ── API Routes ────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "JobBot AI is running 🤖"}

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": str(datetime.utcnow())}

@app.post("/api/client")
def create_client(data: ClientCreate):
    db = Session()
    try:
        existing = db.query(Client).filter(Client.email == data.email).first()
        if existing:
            existing.active = 1
            db.commit()
            return {"id": existing.id, "message": "Client exists. Bot reactivated."}
        client = Client(
            id=str(uuid.uuid4()), name=data.name, email=data.email,
            phone=data.phone, location=data.location,
            roles=json.dumps(data.roles), resume=data.resume, active=1
        )
        db.add(client)
        db.commit()
        return {"id": client.id, "message": "Bot activated!"}
    finally:
        db.close()

@app.get("/api/client/{client_id}")
def get_client(client_id: str):
    db = Session()
    try:
        c = db.query(Client).filter(Client.id == client_id).first()
        if not c:
            raise HTTPException(404, "Client not found")
        return {"id": c.id, "name": c.name, "email": c.email,
                "phone": c.phone, "location": c.location,
                "roles": json.loads(c.roles), "active": c.active}
    finally:
        db.close()

@app.post("/api/client/{client_id}/toggle")
def toggle_bot(client_id: str, data: ToggleBot):
    db = Session()
    try:
        c = db.query(Client).filter(Client.id == client_id).first()
        if not c:
            raise HTTPException(404, "Client not found")
        c.active = data.active
        db.commit()
        return {"message": "Updated", "active": data.active}
    finally:
        db.close()

@app.get("/api/applications/{client_id}")
def get_applications(client_id: str):
    db = Session()
    try:
        apps = (db.query(Application)
                .filter(Application.client_id == client_id)
                .order_by(Application.applied_at.desc()).all())
        return [{"id": a.id, "company": a.company, "role": a.role,
                 "job_url": a.job_url, "status": a.status,
                 "score": a.match_score, "email_used": a.email_used,
                 "date": str(a.applied_at.date()), "has_pdf": bool(a.pdf_data)}
                for a in apps]
    finally:
        db.close()

@app.get("/api/resume/{application_id}/download")
def download_resume(application_id: str):
    db = Session()
    try:
        a = db.query(Application).filter(Application.id == application_id).first()
        if not a:
            raise HTTPException(404, "Not found")
        if not a.pdf_data:
            raise HTTPException(404, "No PDF available")
        pdf_bytes = base64.b64decode(a.pdf_data)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition":
                     f'attachment; filename="Resume_{a.company}_{a.role}.pdf"'}
        )
    finally:
        db.close()

@app.get("/api/resume/{application_id}/text")
def get_resume_text(application_id: str):
    db = Session()
    try:
        a = db.query(Application).filter(Application.id == application_id).first()
        if not a:
            raise HTTPException(404, "Not found")
        return {"resume": a.tailored_cv, "company": a.company, "role": a.role}
    finally:
        db.close()

@app.get("/api/botlog/{client_id}")
def get_bot_log(client_id: str):
    db = Session()
    try:
        logs = (db.query(BotLog)
                .filter(BotLog.client_id == client_id)
                .order_by(BotLog.created_at.desc()).limit(50).all())
        return [{"time": l.created_at.strftime("%H:%M:%S"),
                 "message": l.message, "level": l.level} for l in logs]
    finally:
        db.close()
