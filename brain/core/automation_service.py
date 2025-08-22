from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session
from apscheduler.triggers.cron import CronTrigger
from dateutil.tz import gettz

from domain.schemas.automation import AutomationDB
from domain.models.dtos import (
    AutomationCreate,
    AutomationUpdate,
    AutomationOut,
)

from core.log.logging_service import get_logger
logger = get_logger(__name__)
from infrastructure.persistence.automation_repository import AutomationRepository
from core.beancount_service import append_simple_tx
from conf import BEANCOUNT_FILE
from infrastructure.scheduler.scheduler_service import remove_job_if_exists

class AutomationService:
    def __init__(self, scheduler):
        self.repo = AutomationRepository()
        self.scheduler = scheduler



    def create(self, body: AutomationCreate) -> AutomationOut:
        a = self.repo.create(AutomationDB(**body.model_dump()))
        self._schedule(a)
        return self._to_out(a)

    def list(self) -> List[AutomationOut]:
        return [self._to_out(a) for a in self.repo.list()]

    def get(self, id_: int) -> AutomationOut:
        a = self.repo.get(id_)
        if not a:
            raise HTTPException(status_code=404, detail="Not found")
        return self._to_out(a)

    def update(self, id_: int, body: AutomationUpdate) -> AutomationOut:
        a = self.repo.get(id_)
        if not a:
            raise HTTPException(status_code=404, detail="Not found")


        data = body.model_dump(exclude_unset=True)

        for k, v in data.items():
            setattr(a, k, v)

        a = self.repo.update(a)
        self._schedule(a)
        return self._to_out(a)

    def delete(self, id_: int) -> None:
        a = self.repo.get(id_)
        if not a:
            raise HTTPException(status_code=404, detail="Not found")
        remove_job_if_exists(a.id, self.scheduler)
        self.repo.delete(a)

    def resync_all(self) -> None:
        for a in self.repo.list():
            self._schedule(a)

    # ---------- Internal methods ----------

    def _schedule(self, a: AutomationDB) -> None:

        # Always clear any prior job for this automation
        remove_job_if_exists(a.id, self.scheduler)
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

            self.scheduler.add_job(
                func=self._execute_by_id,
                trigger=trigger,
                args=[a.id],
                id=a.id,
                replace_existing=True,
                misfire_grace_time=3600,  # Allow 1 hour grace period for missed executions
            )
        except Exception as e:
            print(e)
            raise HTTPException(400, f"Failed to schedule automation: {str(e)}")

    def _execute_by_id(self, automation_id: str) -> None:
        a = self.repo.get(automation_id)
        if not a or not a.enabled:
            return

        try:
            # Update last_ran_at timestamp
            a.last_ran_at = datetime.now(timezone.utc)
            self.repo.update(a)
            
            self._execute(a)
        except Exception:
            # In production, log this properly
            raise

    def _execute(self, a: AutomationDB) -> None:
        logger.info("Excuting automation")
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
        logger.info(f"Appending to : {ledger_path} on {tx_date} {acc_from} -> {acc_to} {amt} {currency} {narration}, {payee}")
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
