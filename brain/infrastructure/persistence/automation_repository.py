from typing import List, Optional
from sqlalchemy.orm import Session
from domain.schemas.automation import AutomationDB

class AutomationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, a: AutomationDB) -> AutomationDB:
        self.db.add(a)
        self.db.commit()
        self.db.refresh(a)
        return a

    def list(self) -> List[AutomationDB]:
        return self.db.query(AutomationDB).order_by(AutomationDB.id.desc()).all()

    def get(self, id_: int) -> Optional[AutomationDB]:
        return self.db.get(AutomationDB, id_)

    def update(self, a: AutomationDB) -> AutomationDB:
        self.db.add(a)
        self.db.commit()
        self.db.refresh(a)
        return a

    def delete(self, a: AutomationDB) -> None:
        self.db.delete(a)
        self.db.commit()
