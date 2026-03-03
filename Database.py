# backend/database.py

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer,
    DateTime, Text, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jobbot.db")

# Render PostgreSQL URLs start with "postgres://" — SQLAlchemy needs "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base    = declarative_base()


class Client(Base):
    __tablename__ = "clients"

    id         = Column(String,  primary_key=True)
    name       = Column(String,  nullable=False)
    email      = Column(String,  nullable=False, unique=True)
    phone      = Column(String,  default="")
    location   = Column(String,  default="")
    roles      = Column(Text,    default="[]")   # JSON list
    resume     = Column(Text,    default="")
    active     = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class Application(Base):
    __tablename__ = "applications"

    id           = Column(String,  primary_key=True)
    client_id    = Column(String,  nullable=False)
    company      = Column(String,  default="")
    role         = Column(String,  default="")
    job_url      = Column(String,  default="")
    status       = Column(String,  default="Applied")
    jd_text      = Column(Text,    default="")
    tailored_cv  = Column(Text,    default="")
    pdf_data     = Column(Text,    default="")   # base64 PDF — no S3 needed
    match_score  = Column(Float,   default=0.0)
    email_used   = Column(String,  default="")
    applied_at   = Column(DateTime, default=datetime.utcnow)


class BotLog(Base):
    __tablename__ = "bot_logs"

    id         = Column(String,  primary_key=True)
    client_id  = Column(String,  nullable=False)
    message    = Column(Text,    default="")
    level      = Column(String,  default="info")  # info / success / warning / error
    created_at = Column(DateTime, default=datetime.utcnow)


# Create all tables on startup
Base.metadata.create_all(engine)
