import json
from datetime import date as Date
from typing import Optional, Dict, Any
from openai import OpenAI
from core.beancount_service import (
    append_simple_tx,
    get_all_accounts_grouped,
)
import re
LEDGER_PATH = "/data/budget.beancount"
DEFAULT_CURRENCY = "USD"

class LLMTransactionService:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.ledger_path = LEDGER_PATH

    def _build_prompt(self, natural_text: str) -> str:
        accounts = get_all_accounts_grouped(self.ledger_path)

        sections = []
        for group_name in ["Assets", "Expenses", "Income", "Equity"]:
            if group_name in accounts:
                entries = "\n".join(f"  - {acct}" for acct in sorted(accounts[group_name]))
                sections.append(f"{group_name} Accounts:\n{entries}")

        sample_accounts = "\n\n".join(sections)

        prompt = f"""
You are a helpful assistant that extracts Beancount transaction details from natural language.

Respond ONLY with a valid JSON object with these keys:
- amount_value: number (no currency symbol)
- currency: default to "USD" if not specified
- from_account: must match one of the accounts listed
- to_account: must match one of the accounts listed
- narration: short and clean summary (e.g. "gift", "groceries", etc.)
- payee: optional, or empty string

Available accounts:
{sample_accounts}

User input:
\"\"\"{natural_text}\"\"\"
"""
        return prompt.strip()

    def parse_transaction(self, natural_text: str) -> Dict[str, Any]:
        prompt = self._build_prompt(natural_text)

        print(f"prompt: {prompt}")
        response = self.client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a finance assistant that translates natural language into Beancount transactions."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)

        try:
            # Parse response safely
            tx = json.loads(content)
            return tx
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response as JSON:\n{content}\nError: {e}")

    def append_from_natural_text(self, natural_text: str):
        tx = self.parse_transaction(natural_text)
        print(f"tx: {tx}")
        tx_date = Date.today()
        amount_value = tx["amount_value"]
        currency = tx.get("currency", DEFAULT_CURRENCY)
        from_account = tx["from_account"]
        to_account = tx["to_account"]
        narration = tx.get("narration", "")
        payee = tx.get("payee", "")

        append_simple_tx(
            ledger_path=self.ledger_path,
            tx_date=tx_date,
            amount_value=amount_value,
            currency=currency,
            from_account=from_account,
            to_account=to_account,
            narration=narration,
            payee=payee,
        )

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()
    service = LLMTransactionService(openai_api_key=os.getenv("OPENAI_API_KEY"))

    service.append_from_natural_text("I ate at roadster for 11 dollars and I paid with my lgb card ")
