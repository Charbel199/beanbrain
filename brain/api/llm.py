from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette.status import HTTP_201_CREATED
import os
from core.llm_service import LLMTransactionService

router = APIRouter(prefix="/llm", tags=["LLM Transactions"])



class NaturalTextInput(BaseModel):
    text: str = Field(..., example="Bought groceries at Carrefour for 23.50 euros")



def get_llm_service() -> LLMTransactionService:
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    return LLMTransactionService(openai_api_key=openai_key)



@router.post("/append", status_code=HTTP_201_CREATED)
def append_transaction_from_text(
    body: NaturalTextInput,
    llm_service: LLMTransactionService = Depends(get_llm_service)
):
    transaction = llm_service.append_from_natural_text(body.text)
    return {
        "ok": True,
        "message": "Transaction successfully appended",
        "transaction": transaction
    }