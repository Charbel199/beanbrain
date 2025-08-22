from typing import List, Optional
from sqlalchemy.orm import Session
from domain.schemas.automation import AutomationDB
from domain.schemas.database import SessionLocal

class AutomationRepository:
    def create(self, a: AutomationDB) -> AutomationDB:
        with SessionLocal() as db:
            db.add(a)
            db.commit()
            db.refresh(a)
            return a

    def list(self) -> List[AutomationDB]:
        with SessionLocal() as db:
            return db.query(AutomationDB).order_by(AutomationDB.id.desc()).all()

    def get(self, id_: int) -> Optional[AutomationDB]:
        with SessionLocal() as db:
            return db.get(AutomationDB, id_)
        
    def update(self, a: AutomationDB) -> AutomationDB:
        with SessionLocal() as db:
            merged = db.merge(a)
            db.commit()
            db.refresh(merged)
            return merged

    def delete(self, a: AutomationDB) -> None:
        with SessionLocal() as db:
            db.delete(db.merge(a))
            db.commit()
