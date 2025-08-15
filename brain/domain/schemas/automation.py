from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, JSON
)
from domain.schemas.database import Base
from conf import DEFAULT_TZ


class AutomationDB(Base):
    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)

    # Action payload example (e.g., payment details)
    # keep generic so you can plug into your real payments later
    payload = Column(JSON, nullable=True)

    # Recurrence
    frequency = Column(String, nullable=False)
    # For weekly: 0=mon .. 6=sun (Cron uses 0-6 = mon-sun)
    day_of_week = Column(Integer, nullable=True)
    # For monthly/yearly
    day_of_month = Column(Integer, nullable=True)   # 1..31
    month_of_year = Column(Integer, nullable=True)  # 1..12

    hour_utc = Column(Integer, default=9)     # run time in UTC (0..23)
    minute_utc = Column(Integer, default=0)   # 0..59
    timezone = Column(String, default=DEFAULT_TZ)

    # Optional guardrails
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
