from datetime import datetime
from typing import Optional,  Dict, Any
from pydantic import BaseModel, Field, conint
from domain.models.enums.frequency import Frequency
from conf import DEFAULT_TZ
class AutomationBase(BaseModel):
    name: str = Field(..., example="Pay Rent")
    enabled: bool = True
    payload: Optional[Dict[str, Any]] = Field(
        default={"amount": 1200.0, "currency": "EUR", "note": "Monthly rent"}
    )

    frequency: Frequency
    day_of_week: Optional[conint(ge=0, le=6)] = None
    day_of_month: Optional[conint(ge=1, le=31)] = None
    month_of_year: Optional[conint(ge=1, le=12)] = None

    # time-of-day to run in the selected timezone
    hour_utc: conint(ge=0, le=23) = 9
    minute_utc: conint(ge=0, le=59) = 0
    timezone: str = DEFAULT_TZ

    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

class AutomationCreate(AutomationBase):
    pass

class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    payload: Optional[Dict[str, Any]] = None

    frequency: Optional[Frequency] = None
    day_of_week: Optional[conint(ge=0, le=6)] = None
    day_of_month: Optional[conint(ge=1, le=31)] = None
    month_of_year: Optional[conint(ge=1, le=12)] = None

    hour_utc: Optional[conint(ge=0, le=23)] = None
    minute_utc: Optional[conint(ge=0, le=59)] = None
    timezone: Optional[str] = None

    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

class AutomationOut(AutomationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
