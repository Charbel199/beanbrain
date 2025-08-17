from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.automation_service import AutomationService
from apscheduler.schedulers.background import BackgroundScheduler
from api import automation, llm
from conf  import DEFAULT_TZ, BEANCOUNT_FILE
from domain.schemas.database import Base, engine, SessionLocal

scheduler = BackgroundScheduler(timezone=DEFAULT_TZ)
scheduler.start()


app = FastAPI(title="Beancount Automations API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        service = AutomationService(db=db)
        service.resync_all()
    finally:
        db.close()


app.include_router(automation.router)
app.include_router(llm.router)