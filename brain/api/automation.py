from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from domain.schemas.database import get_db
from domain.models.dtos import AutomationCreate, AutomationUpdate, AutomationOut
from core.automation_service import AutomationService
from typing import List
from conf import BEANCOUNT_FILE

router = APIRouter(prefix="/automation", tags=["Automation"])


def get_service(db: Session = Depends(get_db)) -> AutomationService:
    return AutomationService(db=db)

@router.post("/automations", response_model=AutomationOut)
def create_automation(body: AutomationCreate, automation_service: AutomationService = Depends(get_service)):
    return automation_service.create(body)

@router.get("/automations", response_model=List[AutomationOut])
def list_automations(automation_service: AutomationService = Depends(get_service)):
    return automation_service.list()

@router.get("/automations/{id}", response_model=AutomationOut)
def get_automation(id: int, automation_service: AutomationService = Depends(get_service)):
    return automation_service.get(id)

@router.patch("/automations/{id}", response_model=AutomationOut)
def update_automation(id: int, body: AutomationUpdate, automation_service: AutomationService = Depends(get_service)):
    return automation_service.update(id, body)

@router.delete("/automations/{id}")
def delete_automation(id: int, automation_service: AutomationService = Depends(get_service)):
    automation_service.delete(id)
    return {"ok": True}
