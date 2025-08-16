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
    
    # Action payload (e.g., payment details)
    payload = Column(JSON, nullable=True)
    
    # Simple cron-based scheduling
    cron_expression = Column(String, nullable=False)  # e.g., "0 9 * * 1" for 9 AM every Monday
    timezone = Column(String, default=DEFAULT_TZ)    # e.g., "America/New_York"
    
    # Tracking
    last_ran_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))