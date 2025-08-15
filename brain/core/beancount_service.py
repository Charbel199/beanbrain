from __future__ import annotations
from datetime import date as Date
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Optional

from filelock import FileLock

from beancount.core import data, amount, number
from beancount.parser import printer
from beancount import loader


class BeancountService:
    """
    Append valid Beancount transactions using the official library.

    Example postings input:
      [
        {"account": "Assets:Bank:Checking", "amount": -1200.00, "currency": "EUR"},
        {"account": "Expenses:Rent"}  # balancing leg with no amount
      ]
    """

    def __init__(self, ledger_path: str):
        self.ledger_path = Path(ledger_path)
        self.lock_path = self.ledger_path.with_suffix(".lock")
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def add_entry(
        self,
        payee: str,
        narration: str,
        postings: Iterable[dict],
        entry_date: Optional[Date] = None,
        flag: str = "*",
        meta: Optional[dict] = None,
    ):
        """
        Create a Transaction and append to the ledger file after validating parse.
        - postings: iterable of dicts with keys:
            - account (str, required)
            - amount (float|Decimal|str, optional for balancing leg)
            - currency (str, required if amount present)
        - entry_date: defaults to today.
        - meta: dict of key/values added to the transaction metadata (not line comments).
        """
        entry_date = entry_date or Date.today()

        # Build metadata (filename/lineno are mostly informational)
        tx_meta = data.new_metadata(str(self.ledger_path), 0)
        if meta:
            # Copy user meta into metadata map
            tx_meta.update({str(k): v for k, v in meta.items()})

        # Build postings
        built_postings = []
        for p in postings:
            account_name = p["account"]
            amt = p.get("amount", None)
            cur = p.get("currency", None)

            beancount_amt = None
            if amt is not None:
                # Convert to Decimal via beancount.number.D for consistent quantization
                dec = number.D(str(amt)) if not isinstance(amt, Decimal) else amt
                beancount_amt = amount.Amount(dec, cur or "")

            built_postings.append(
                data.Posting(
                    account=account_name,
                    units=beancount_amt,   # None means balancing leg
                    cost=None,
                    price=None,
                    flag=None,
                    meta=None,
                )
            )

        # Construct the Transaction node
        txn = data.Transaction(
            meta=tx_meta,
            date=entry_date,
            flag=flag,
            payee=payee,
            narration=narration,
            tags=set(),
            links=set(),
            postings=built_postings,
        )

        # Render to Beancount syntax
        rendered = printer.format_entry(txn)

        # Validate by parsing the whole ledger plus new entry before writing
        lock = FileLock(str(self.lock_path))
        with lock:
            original_text = ""
            if self.ledger_path.exists():
                original_text = self.ledger_path.read_text(encoding="utf-8")

            candidate_text = original_text.rstrip() + ("\n\n" if original_text else "") + rendered + "\n"

            # Parse to ensure we're not corrupting the ledger
            _, errors, _ = loader.load_string(candidate_text)
            if errors:
                # Bubble up the first parse error with its message
                msg = errors[0].message if hasattr(errors[0], "message") else str(errors[0])
                raise ValueError(f"Beancount validation failed: {msg}")

            # Write only after successful parse
            self.ledger_path.write_text(candidate_text, encoding="utf-8")