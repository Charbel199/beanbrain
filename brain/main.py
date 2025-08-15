from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, conint
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, DateTime, JSON, Float
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import ConflictingIdError
from dateutil.tz import gettz
from api import automation
from conf  import DEFAULT_TZ
from domain.schemas.database import Base, engine
# --------------------------
# APScheduler
# --------------------------
scheduler = BackgroundScheduler(timezone=DEFAULT_TZ)
scheduler.start()



# --------------------------
# FastAPI app
# --------------------------
app = FastAPI(title="Recurring Automations API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)


app.include_router(automation.router)