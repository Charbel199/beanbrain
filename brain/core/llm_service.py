import json
import re
from datetime import date as Date
from typing import Optional, Dict, Any

from openai import OpenAI
from core.beancount_service import (
    append_simple_tx,
    get_all_accounts_grouped,
    format_recent_transactions,
    get_recent_narrations_and_payees
)

LEDGER_PATH = "/data/budget.beancount"
DEFAULT_CURRENCY = "USD"

class LLMTransactionService:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.ledger_path = LEDGER_PATH

    def _clean_json(self, content: str) -> str:
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
        return content.strip()

    def _ask(self, system_msg: str, user_msg: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
        )
        content = self._clean_json(response.choices[0].message.content)
        try:
            return json.loads(content)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response as JSON:\n{content}\nError: {e}")

    def infer_accounts(self, natural_text: str) -> Dict[str, str]:
        accounts = get_all_accounts_grouped(self.ledger_path)

        sections = []
        for group_name in ["Assets", "Expenses", "Income", "Equity"]:
            if group_name in accounts:
                entries = "\n".join(f"  - {acct}" for acct in sorted(accounts[group_name]))
                sections.append(f"{group_name} Accounts:\n{entries}")

        sample_accounts = "\n\n".join(sections)
        account_prompt = f"""
You are an assistant that classifies transactions by matching accounts.

Given the user input: \"\"\"{natural_text}\"\"\"

We have the following accounts: 
{sample_accounts}

Return a JSON object with:
- from_account: one of the provided accounts
- to_account: one of the provided accounts

Choose the most reasonable pair based on typical financial logic.
"""
        print(f"account_prompt: {account_prompt}")

        return self._ask("You help classify Beancount accounts.", account_prompt)

    def complete_transaction(self, natural_text: str, from_account: str, to_account: str) -> Dict[str, Any]:
        recent_examples_from = format_recent_transactions(self.ledger_path, from_account)
        recent_narrations_and_payees = get_recent_narrations_and_payees(self.ledger_path, to_account)

        prompt = f"""
Input: \"\"\"{natural_text}\"\"\"
Accounts: {from_account} → {to_account}
Recent examples: {recent_narrations_and_payees}

Follow the recent examples format closely. If recent examples show "Groceries", use "Groceries" not "Grocery Shopping".

Return JSON:
- amount_value: number only
- currency: code (default "USD") 
- narration: match recent example style, 2-4 words, title case
- payee: specific business name if mentioned, else ""
"""
        print(f"prompt: {prompt}")
        return self._ask("You complete Beancount transaction details.", prompt)

    def append_from_natural_text(self, natural_text: str):
        print("🔍 Inferring accounts...")
        accounts = self.infer_accounts(natural_text)
        from_account = accounts["from_account"]
        to_account = accounts["to_account"]
        print(f"→ Accounts: {from_account} → {to_account}")

        print("🧠 Completing transaction fields...")
        details = self.complete_transaction(natural_text, from_account, to_account)
        print(f"→ Details: {details}")

        append_simple_tx(
            ledger_path=self.ledger_path,
            tx_date=Date.today(),
            amount_value=details["amount_value"],
            currency=details.get("currency", DEFAULT_CURRENCY),
            from_account=from_account,
            to_account=to_account,
            narration=details.get("narration", ""),
            payee=details.get("payee", ""),
        )
        print(f"✅ Transaction appended -> \n {from_account} -> {to_account}\n{details}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    import argparse
    import os

    load_dotenv()

    parser = argparse.ArgumentParser(description="Append a Beancount transaction from natural language")
    parser.add_argument("text", type=str, help="Natural language transaction (in quotes)")
    args = parser.parse_args()

    service = LLMTransactionService(openai_api_key=os.getenv("OPENAI_API_KEY"))
    service.append_from_natural_text(args.text)
