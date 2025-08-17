from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from conf import DEFAULT_TZ
from croniter import croniter
from dateutil.tz import gettz

class AutomationBase(BaseModel):
    name: str = Field(..., example="Pay Rent")
    enabled: bool = True
    payload: Optional[Dict[str, Any]] = Field(
        default={"amount": 1200.0, "currency": "EUR", "note": "Monthly rent", "to": "Expenses:Personal:Gifts", "from":"Assets:LB:LGB:Savings"}
    )
    cron_expression: str = Field(..., example="0 9 1 * *", description="Standard cron expression")
    timezone: str = DEFAULT_TZ

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, value):
        if not croniter.is_valid(value):
            raise ValueError(f"Invalid cron expression: {value}")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value):
        if gettz(value) is None:
            raise ValueError(f"Invalid timezone: {value}")
        return value

class AutomationCreate(AutomationBase):
    pass


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    payload: Optional[Dict[str, Any]] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None


class AutomationOut(AutomationBase):
    id: str
    last_ran_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True