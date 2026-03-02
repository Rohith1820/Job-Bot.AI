from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"
    id         = Column(String, primary_key=True)
    name       = Column(String)
    email      = Column(String)          # used in job applications
    phone      = Column(String)
    location   = Column(String)
    roles      = Column(Text)            # JSON list of target roles
    resume     = Column(Text)            # base resume text
    active     = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"
    id           = Column(String, primary_key=True)
    client_id    = Column(String)
    company      = Column(String)
    role         = Column(String)
    job_url      = Column(String)
    status       = Column(String, default="Applied")  # Applied/Pending/Failed
    jd_text      = Column(Text)
    tailored_cv  = Column(Text)
    pdf_url      = Column(String)        # S3 link to download
    match_score  = Column(Float)
    applied_at   = Column(DateTime, default=datetime.utcnow)
    email_used   = Column(String)        # client's email used in form

Base.metadata.create_all(engine)
