from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List, Tuple, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from apscheduler.triggers.cron import CronTrigger
from dateutil.tz import gettz

from domain.schemas.automation import AutomationDB
from domain.models.enums.frequency import Frequency
from domain.models.dtos import (
    AutomationCreate,
    AutomationUpdate,
    AutomationOut,
)
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.scheduler.scheduler import scheduler, job_id, remove_job_if_exists, cron_kwargs
from core.beancount_service import BeancountService


class AutomationService:
    def __init__(self, db: Session, beancount: BeancountService):
        self.db = db
        self.repo = AutomationRepository(db)
        self.beancount = beancount

    # ---------- Public API used by router ----------
    
    def create(self, body: AutomationCreate) -> AutomationOut:
        """Create a new automation and schedule it."""
        self._validate(body)

        starts_utc, ends_utc = self._normalize_dates(
            tzname=body.timezone, starts_at=body.starts_at, ends_at=body.ends_at
        )

        a = AutomationDB(
            name=body.name,
            enabled=body.enabled,
            payload=body.payload,
            frequency=(body.frequency.value if isinstance(body.frequency, Frequency) else body.frequency),
            day_of_week=body.day_of_week,
            day_of_month=body.day_of_month,
            month_of_year=body.month_of_year,
            hour_utc=body.hour_utc,
            minute_utc=body.minute_utc,
            timezone=body.timezone,
            starts_at=starts_utc,
            ends_at=ends_utc,
        )
        a = self.repo.create(a)
        self._schedule(a)
        return self._to_out(a)

    def list(self) -> List[AutomationOut]:
        """List all automations."""
        return [self._to_out(a) for a in self.repo.list()]

    def get(self, id_: int) -> AutomationOut:
        """Get a specific automation by ID."""
        a = self.repo.get(id_)
        if not a:
            raise HTTPException(status_code=404, detail="Not found")
        return self._to_out(a)

    def update(self, id_: int, body: AutomationUpdate) -> AutomationOut:
        """Update an existing automation."""
        a = self.repo.get(id_)
        if not a:
            raise HTTPException(status_code=404, detail="Not found")

        # Validate first so we fail fast
        self._validate(body)

        data = body.model_dump(exclude_unset=True)

        # Coerce enum to string for the DB String column
        if "frequency" in data and isinstance(data["frequency"], Frequency):
            data["frequency"] = data["frequency"].value

        # Normalize dates to UTC if any of timezone/starts_at/ends_at provided
        if any(k in data for k in ("timezone", "starts_at", "ends_at")):
            tzname = data.get("timezone", a.timezone)
            starts = data.get("starts_at", a.starts_at)
            ends = data.get("ends_at", a.ends_at)
            s_utc, e_utc = self._normalize_dates(tzname, starts, ends)
            data["starts_at"] = s_utc
            data["ends_at"] = e_utc

        for k, v in data.items():
            setattr(a, k, v)

        a = self.repo.update(a)
        self._schedule(a)
        return self._to_out(a)

    def delete(self, id_: int) -> None:
        """Delete an automation and remove its scheduled job."""
        a = self.repo.get(id_)
        if not a:
            raise HTTPException(status_code=404, detail="Not found")
        remove_job_if_exists(job_id(a.id))
        self.repo.delete(a)

    def resync_all(self) -> None:
        """Resynchronize all automations with the scheduler."""
        for a in self.repo.list():
            self._schedule(a)

    # ---------- Internal methods ----------
    
    def _validate(self, body: AutomationCreate | AutomationUpdate) -> None:
        """Validate automation parameters based on frequency and other rules."""
        # Frequency-specific guardrails
        freq: Optional[str] = None
        if hasattr(body, "frequency") and body.frequency:
            freq = body.frequency.value if isinstance(body.frequency, Frequency) else body.frequency

        if freq == "WEEKLY" and getattr(body, "day_of_week", None) is None:
            raise HTTPException(400, "day_of_week is required for WEEKLY")
        if freq == "MONTHLY" and getattr(body, "day_of_month", None) is None:
            raise HTTPException(400, "day_of_month is required for MONTHLY")
        if freq == "YEARLY" and (
            getattr(body, "day_of_month", None) is None or getattr(body, "month_of_year", None) is None
        ):
            raise HTTPException(400, "month_of_year and day_of_month are required for YEARLY")

        # Timezone validity
        if hasattr(body, "timezone") and getattr(body, "timezone", None):
            if gettz(getattr(body, "timezone")) is None:
                raise HTTPException(400, f"Invalid timezone: {getattr(body, 'timezone')}")

    def _schedule(self, a: AutomationDB) -> None:
        """Schedule or reschedule an automation job."""
        # Always clear any prior job for this automation
        remove_job_if_exists(job_id(a.id))
        if not a.enabled:
            return

        kwargs = cron_kwargs(
            a.frequency,
            a.day_of_week,
            a.day_of_month,
            a.month_of_year,
            a.hour_utc,
            a.minute_utc,
            a.timezone,
        )
        trigger = CronTrigger(**kwargs)
        scheduler.add_job(
            func=self._execute_by_id,
            trigger=trigger,
            args=[a.id],
            id=job_id(a.id),
            replace_existing=True,
            misfire_grace_time=3600,  # Allow 1 hour grace period for missed executions
        )

    def _execute_by_id(self, automation_id: int) -> None:
        """Execute an automation by ID with time-based guards."""
        a = self.repo.get(automation_id)
        if not a or not a.enabled:
            return

        now = datetime.now(timezone.utc)
        if a.starts_at and now < a.starts_at:
            return
        if a.ends_at and now > a.ends_at:
            return

        try:
            self._execute(a)
        except Exception as e:
            # Log the error in production - for now just re-raise
            # logger.error(f"Failed to execute automation {automation_id}: {e}")
            raise

    def _execute(self, a: AutomationDB) -> None:
        """Execute an automation by creating a Beancount transaction."""
        p = a.payload or {}

        payee = p.get("payee", a.name)
        narration = p.get("narration", a.frequency)

        # Safer numeric handling
        amount_in = p.get("amount")
        amount: Optional[Decimal] = None
        if amount_in is not None:
            try:
                amount = Decimal(str(amount_in))
            except (InvalidOperation, ValueError, TypeError):
                amount = None  # ignore unusable amount

        currency = p.get("currency", "EUR")
        acc_from = p.get("from", "Assets:Bank:Checking")
        acc_to = p.get("to", "Expenses:Unknown")

        # Build postings as dictionaries for BeancountService
        postings = []
        if amount is not None and amount != 0:
            # Two-legged transaction with explicit amounts
            postings.extend([
                {"account": acc_from, "amount": -amount, "currency": currency},
                {"account": acc_to, "amount": amount, "currency": currency},
            ])
        else:
            # Single posting for cases where amount is not specified or zero
            postings.append({"account": acc_to})

        # Extract metadata (exclude known fields)
        meta = {
            k: v
            for k, v in p.items()
            if k not in {"payee", "narration", "amount", "currency", "from", "to"}
        }

        # Add automation metadata
        meta.update({
            "automation_id": str(a.id),
            "automation_name": a.name,
        })

        self.beancount.add_entry(
            payee=payee, 
            narration=narration, 
            postings=postings, 
            meta=meta
        )

    @staticmethod
    def _normalize_dates(
        tzname: str, starts_at: Optional[datetime], ends_at: Optional[datetime]
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Ensures stored datetimes are timezone-aware in UTC.
        If client sends naive datetimes, interpret them in the provided timezone.
        """
        tzinfo = gettz(tzname) or timezone.utc

        def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
            if dt is None:
                return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tzinfo)
            return dt.astimezone(timezone.utc)

        return to_utc(starts_at), to_utc(ends_at)

    @staticmethod
    def _to_out(a: AutomationDB) -> AutomationOut:
        """Convert database model to output DTO."""
        return AutomationOut.model_validate(a, from_attributes=True)