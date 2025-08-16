# beancount_simple.py
from datetime import date as Date
from decimal import Decimal
from pathlib import Path

from beancount.core import data, amount, number
from beancount.parser import printer
from beancount import loader


def append_simple_tx(
    ledger_path: str,
    tx_date: Date,
    amount_value: Decimal | float | str,
    currency: str,
    from_account: str,
    to_account: str,
    narration: str = "",
    payee: str | None = None,
    auto_open_accounts: bool = True,
) -> None:
    """
    Append a simple 2-posting transaction to a Beancount ledger.

    Example:
        append_simple_tx(
            "ledger.beancount",
            Date(2025, 8, 16),
            50, "USD",
            "Assets:Cash", "Expenses:Groceries",
            "Grocery run"
        )
    """
    print("HI")
    ledger = Path(ledger_path)
    print(ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)

    original_text = ledger.read_text(encoding="utf-8") if ledger.exists() else ""

    # Collect existing opened accounts (only from 'open' directives for simplicity)
    existing_accounts = set()
    if original_text:
        entries, _, _ = loader.load_string(original_text)
        for e in entries:
            if isinstance(e, data.Open):
                existing_accounts.add(e.account)

    # Build transaction
    meta = data.new_metadata(str(ledger), 0)
    quant = number.D(str(amount_value))
    units = amount.Amount(quant, currency)
    neg_units = amount.Amount(-quant, currency)

    postings = [
        data.Posting(from_account, neg_units, None, None, None, None),
        data.Posting(to_account,   units,    None, None, None, None),
    ]

    txn = data.Transaction(
        meta=meta,
        date=tx_date,
        flag="*",
        payee=payee,
        narration=narration,
        tags=set(),
        links=set(),
        postings=postings,
    )

    # Auto-open any missing accounts
    open_block = ""
    if auto_open_accounts:
        needed = {from_account, to_account} - existing_accounts
        if needed:
            opens = []
            for acct in sorted(needed):
                ometa = data.new_metadata(str(ledger), 0)
                opens.append(printer.format_entry(data.Open(ometa, tx_date, acct, [], None)))
            open_block = "\n".join(opens) + "\n"

    # Render candidate ledger and validate before writing
    rendered_tx = printer.format_entry(txn)
    candidate = (
        (original_text.rstrip() + "\n\n" if original_text else "")
        + open_block
        + rendered_tx
        + "\n"
    )

    _, errors, _ = loader.load_string(candidate)
    if errors:
        raise ValueError(f"Beancount validation failed: {errors[0]}")

    ledger.write_text(candidate, encoding="utf-8")


if __name__ == "__main__":
    # Minimal example
    append_simple_tx(
        ledger_path="/data/budget.beancount",
        tx_date=Date(2025, 8, 16),
        amount_value=50,
        currency="USD",
        from_account="Assets:LB:LGB:Savings",
        to_account="Expenses:Personal:Gifts",
        narration="Grocery run",
    )
    print("Transaction appended to ledger.beancount")
