from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from conf import DEFAULT_TZ


class AutomationBase(BaseModel):
    name: str = Field(..., example="Pay Rent")
    enabled: bool = True
    payload: Optional[Dict[str, Any]] = Field(
        default={"amount": 1200.0, "currency": "EUR", "note": "Monthly rent", "to": "Expenses:Personal:Gifts", "from":"Assets:LB:LGB:Savings"}
    )
    cron_expression: str = Field(..., example="0 9 1 * *", description="Standard cron expression")
    timezone: str = DEFAULT_TZ


class AutomationCreate(AutomationBase):
    pass


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    payload: Optional[Dict[str, Any]] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None


class AutomationOut(AutomationBase):
    id: int
    last_ran_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True