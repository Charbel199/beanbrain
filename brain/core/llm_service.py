import json
import re
from datetime import date as Date
from typing import Dict, Any
import conf
from openai import OpenAI
from core.beancount_service import (
    append_simple_tx,
    get_all_accounts_grouped,
    get_inline_account_comments_map,
    get_recent_narrations_and_payees
)

from core.log.logging_service import get_logger
logger = get_logger(__name__)

class LLMTransactionService:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.ledger_path = conf.BEANCOUNT_FILE

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
        accounts_comments = get_inline_account_comments_map(self.ledger_path)
        sections = []

        for group_name, accts in accounts.items():
            entries = []
            for acct in sorted(accts):
                comment = accounts_comments.get(acct)
                if comment:
                    entries.append(f"  - {acct}  # {comment}")
                else:
                    entries.append(f"  - {acct}")
            sections.append(f"{group_name} Accounts:\n" + "\n".join(entries))

        sample_accounts = "\n\n".join(sections)
        account_prompt = f"""
You are a financial assistant that classifies user-described transactions.

Given the user input: \"\"\"{natural_text}\"\"\"

And the following list of valid accounts:
{sample_accounts}


Your job is to return a JSON object like this:
- from_account # The account the money is coming from
- to_account # The account the money is going to

Guidelines:
- If the user is describing a **purchase or payment**, then:
    - "from_account" is the source of funds (e.g. a bank or cash account)
    - "to_account" is the destination (e.g. an expense or liability account)
- If the user is describing **income or a deposit**, then:
    - "from_account" is the origin (e.g. Income:Salary)
    - "to_account" is the destination (e.g. a bank or asset account)
- If the user is describing a **transfer between accounts**, then:
    - Use the appropriate asset or bank accounts for both "from_account" and "to_account"
- Only use account names that are listed above (ignore comments like # ...)
- Return only a JSON object with the selected accounts

Return ONLY the JSON. Do not include explanations.
"""
        logger.info(f"\n================\nInfer account prompt: {account_prompt}\n================")

        return self._ask("You help classify Beancount accounts.", account_prompt)

    def complete_transaction(self, natural_text: str, from_account: str, to_account: str) -> Dict[str, Any]:
        recent_narrations_and_payees = get_recent_narrations_and_payees(self.ledger_path, to_account)

        prompt = f"""
Input: \"\"\"{natural_text}\"\"\"
Accounts: {from_account} → {to_account}

Recent examples:
{recent_narrations_and_payees}

Your task is to extract and standardize transaction details in the same format and tone as the recent examples above..

Return a JSON object with the following fields:
- amount_value: number only (e.g. 15.50)
- currency: 3-letter code (e.g. "EUR", "USD"); default to "USD" if not mentioned
- narration: 2–4 words in Title Case, closely matching the phrasing style in recent examples (e.g. "Lunch Out", not "Meal at Restaurant")
- payee: specific business or place name mentioned; if none, return an empty string ""
"""
        logger.info(f"\n================\nComplete transaction prompt: {prompt}\n================")
        return self._ask("You complete Beancount transaction details.", prompt)

    def append_from_natural_text(self, natural_text: str) -> dict:
        logger.info("Inferring accounts...")
        accounts = self.infer_accounts(natural_text)
        from_account = accounts["from_account"]
        to_account = accounts["to_account"]
        logger.info(f"→ Accounts: {from_account} → {to_account}")

        logger.info("Completing transaction fields...")
        details = self.complete_transaction(natural_text, from_account, to_account)
        logger.info(f"→ Details: {details}")

        append_simple_tx(
            ledger_path=self.ledger_path,
            tx_date=Date.today(),
            amount_value=details["amount_value"],
            currency=details.get("currency", conf.DEFAULT_CURRENCY),
            from_account=from_account,
            to_account=to_account,
            narration=details.get("narration", ""),
            payee=details.get("payee", ""),
        )

        logger.info(f"Transaction appended -> \n {from_account} -> {to_account}\n{details}")

        return {
            "from_account": from_account,
            "to_account": to_account,
            "amount_value": details["amount_value"],
            "currency": details.get("currency", conf.DEFAULT_CURRENCY),
            "narration": details.get("narration", ""),
            "payee": details.get("payee", ""),
        }

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
