from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import Session, Client, Application
from pydantic import BaseModel
import uuid, json

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ClientCreate(BaseModel):
    name: str
    email: str
    phone: str
    location: str
    roles: list
    resume: str

@app.post("/api/client")
def create_client(data: ClientCreate):
    db = Session()
    client = Client(
        id=str(uuid.uuid4()),
        name=data.name,
        email=data.email,
        phone=data.phone,
        location=data.location,
        roles=json.dumps(data.roles),
        resume=data.resume
    )
    db.add(client)
    db.commit()
    return {"id": client.id, "message": "Bot activated!"}

@app.get("/api/applications/{client_id}")
def get_applications(client_id: str):
    db = Session()
    apps = db.query(Application).filter_by(client_id=client_id).order_by(
        Application.applied_at.desc()
    ).all()
    return [{"id": a.id, "company": a.company, "role": a.role,
             "status": a.status, "score": a.match_score,
             "pdf_url": a.pdf_url, "email_used": a.email_used,
             "date": str(a.applied_at.date())} for a in apps]

@app.get("/api/resume/{application_id}/download")
def get_resume_download(application_id: str):
    db = Session()
    app = db.query(Application).filter_by(id=application_id).first()
    if not app:
        raise HTTPException(404, "Not found")
    return {"pdf_url": app.pdf_url, "company": app.company, "role": app.role}
