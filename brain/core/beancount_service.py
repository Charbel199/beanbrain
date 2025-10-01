from datetime import date as Date
from decimal import Decimal
from pathlib import Path
from typing import List, Dict
from beancount.core import data, amount, number
from beancount.parser import printer
from beancount import loader
import fcntl  # Unix only
from collections import defaultdict
import conf
from core.log.logging_service import get_logger
logger = get_logger(__name__)

def _safe_append_to_file(path: Path, text: str, lock: bool = True):
    with open(path, "a", encoding="utf-8") as f:
        if lock:
            fcntl.flock(f, fcntl.LOCK_EX)
        f.write(text)
        if lock:
            fcntl.flock(f, fcntl.LOCK_UN)


# Beancount specific functionalities

def get_all_accounts_grouped(ledger_path: str) -> Dict[str, List[str]]:
    entries, _, _ = loader.load_file(ledger_path)
    grouped_accounts = defaultdict(list)

    for entry in entries:
        if isinstance(entry, data.Open):
            account_type = entry.account.split(":")[0]
            grouped_accounts[account_type].append(entry.account)

    for group in grouped_accounts:
        grouped_accounts[group].sort()

    return dict(grouped_accounts)

def get_recent_transactions(ledger_path: str, account: str, limit: int = 5) -> List[data.Transaction]:
    entries, _, _ = loader.load_file(ledger_path)
    txns = [
        entry for entry in entries
        if isinstance(entry, data.Transaction)
        and any(post.account == account for post in entry.postings)
    ]
    return txns[-limit:]

def format_recent_transactions(ledger_path: str, account: str, limit: int = 5) -> str:
    txns = get_recent_transactions(ledger_path, account, limit)
    formatted_txns = [printer.format_entry(txn) for txn in txns]
    return "\n".join(formatted_txns)

def get_recent_narrations_and_payees(ledger_path: str, account: str, limit: int = 5) -> list[tuple[str, str]]:
    entries, _, _ = loader.load_file(ledger_path)
    txns = [
        entry for entry in entries
        if isinstance(entry, data.Transaction)
        and any(post.account == account for post in entry.postings)
    ]

    recent = txns[-limit:]
    result = [
        (txn.narration.strip(), txn.payee.strip() if txn.payee else "")
        for txn in recent
    ]
    return result




def get_inline_account_comments_map(ledger_path: str) -> Dict[str, str]:
    """
    Extract inline comments (on the same line) for account 'Open' directives
    by reading the raw file text.

    Args:
        ledger_path (str): Path to the Beancount ledger file.

    Returns:
        Dict[str, str]: A mapping of account names to inline comments.
    """
    with open(ledger_path, encoding="utf-8") as f:
        lines = f.readlines()

    entries, _, _ = loader.load_file(ledger_path)
    comments_map = {}

    for entry in entries:
        if isinstance(entry, data.Open):
            lineno = entry.meta["lineno"] - 1  # 0-based index
            line = lines[lineno]
            if ";" in line:
                comment = line.split(";", 1)[1].strip()
                comments_map[entry.account] = comment

    return comments_map

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
    ledger = Path(ledger_path)
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

    _safe_append_to_file(ledger, open_block + "\n" + rendered_tx + "\n")


if __name__ == "__main__":
    # Minimal example
    append_simple_tx(
        ledger_path=conf.BEANCOUNT_FILE,
        tx_date=Date(2025, 8, 16),
        amount_value=50,
        currency="USD",
        from_account="Assets:Bank:Savings",
        to_account="Expenses:Personal:Groceries",
        narration="Grocery run",
    )
    #print("Transaction appended to ledger.beancount")
    #print(get_all_accounts_grouped(conf.BEANCOUNT_FILE))
    #print(format_recent_transactions(conf.BEANCOUNT_FILE, "Expenses:Personal:Groceries"))
    print(get_inline_account_comments_map(conf.BEANCOUNT_FILE))
