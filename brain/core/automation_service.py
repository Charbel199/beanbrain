from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from apscheduler.triggers.cron import CronTrigger
from dateutil.tz import gettz
from croniter import croniter

from domain.schemas.automation import AutomationDB
from domain.models.dtos import (
    AutomationCreate,
    AutomationUpdate,
    AutomationOut,
)

import logging
logger = logging.getLogger(__name__)
from infrastructure.persistence.automation_repository import AutomationRepository
from infrastructure.scheduler.scheduler import scheduler, job_id, remove_job_if_exists, print_all_jobs
from core.beancount_service import append_simple_tx
from conf import BEANCOUNT_FILE

class AutomationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AutomationRepository(db)

    # ---------- Public API used by router ----------
    
    def create(self, body: AutomationCreate) -> AutomationOut:
        """Create a new automation and schedule it."""
        self._validate(body)

        a = AutomationDB(
            name=body.name,
            enabled=body.enabled,
            payload=body.payload,
            cron_expression=body.cron_expression,
            timezone=body.timezone,
        )
        a = self.repo.create(a)
        self._schedule(a)
        return self._to_out(a)

    def list(self) -> List[AutomationOut]:
        print(print_all_jobs())
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
        """Validate automation parameters."""
        # Validate cron expression
        if hasattr(body, "cron_expression") and getattr(body, "cron_expression", None):
            cron_expr = getattr(body, "cron_expression")
            if not croniter.is_valid(cron_expr):
                raise HTTPException(400, f"Invalid cron expression: {cron_expr}")

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

        # Parse cron expression and create trigger
        try:
            # Split cron expression into components (minute, hour, day, month, day_of_week)
            cron_parts = a.cron_expression.split()
            if len(cron_parts) != 5:
                raise ValueError("Cron expression must have exactly 5 parts")
            
            minute, hour, day, month, day_of_week = cron_parts
            
            # Get timezone info
            tz = gettz(a.timezone) or timezone.utc
            
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=tz
            )
            
            scheduler.add_job(
                func=self._execute_by_id,
                trigger=trigger,
                args=[a.id],
                id=job_id(a.id),
                replace_existing=True,
                misfire_grace_time=3600,  # Allow 1 hour grace period for missed executions
            )
        except Exception as e:
            raise HTTPException(400, f"Failed to schedule automation: {str(e)}")

    def _execute_by_id(self, automation_id: int) -> None:
        print("Hello from job!", flush=True)

        """Execute an automation by ID."""
        a = self.repo.get(automation_id)
        if not a or not a.enabled:
            return

        try:
            logger.info(f"a {a}")
            # Update last_ran_at timestamp
            a.last_ran_at = datetime.now(timezone.utc)
            self.repo.update(a)
            
            self._execute(a)
        except Exception:
            # In production, log this properly
            raise

    def _execute(self, a: AutomationDB) -> None:
        logger.info("EXECUTING")
        """Execute an automation by creating a Beancount transaction using append_simple_tx."""
        p = a.payload or {}

        ledger_path = BEANCOUNT_FILE
        payee = p.get("payee")  # optional
        narration = p.get("narration", f"Automated: {a.name}")

        # Date: use payload.date (YYYY-MM-DD) if provided; else "today" in the automation's TZ
        date_str = p.get("date")
        if date_str:
            try:
                # Accept YYYY-MM-DD
                tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(400, f"Invalid date format '{date_str}', expected YYYY-MM-DD")
        else:
            tz = gettz(a.timezone) or timezone.utc
            tx_date = datetime.now(tz).date()

        # Required money fields
        raw_amount = p.get("amount")
        if raw_amount is None:
            raise HTTPException(400, "Missing 'amount' in payload")

        try:
            amt = Decimal(str(raw_amount))
        except (InvalidOperation, ValueError, TypeError):
            raise HTTPException(400, f"Invalid 'amount': {raw_amount}")

        currency = p.get("currency")
        if not currency:
            raise HTTPException(400, "Missing 'currency' in payload")

        acc_from = p.get("from")
        acc_to = p.get("to")
        if not acc_from or not acc_to:
            raise HTTPException(400, "Missing 'from' or 'to' account in payload")

        # Append the 2-posting transaction (from = negative leg, to = positive leg)
        try:
            append_simple_tx(
                ledger_path=ledger_path,
                tx_date=tx_date,
                amount_value=amt,
                currency=currency,
                from_account=acc_from,
                to_account=acc_to,
                narration=narration,
                payee=payee,
                auto_open_accounts=True,
            )
        except ValueError as e:
            # Bubble up Beancount validation/parse issues clearly
            raise HTTPException(400, f"Beancount validation failed: {e}")

    @staticmethod
    def _to_out(a: AutomationDB) -> AutomationOut:
        """Convert database model to output DTO."""
        return AutomationOut.model_validate(a, from_attributes=True)
