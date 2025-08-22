# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from domain.schemas.database import Base, engine, SessionLocal
from core.automation_service import AutomationService
from infrastructure.scheduler.scheduler_service import build_scheduler
from api import automation, llm

app = FastAPI(title="Beancount Automations API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# Keep a reference on the app state
app.state.scheduler = None

@app.on_event("startup")
async def on_startup():
    # DB init
    Base.metadata.create_all(bind=engine)

    # Scheduler init
    sched = build_scheduler()
    sched.start()
    app.state.scheduler = sched

    # Re-sync automations (loads jobs into the scheduler)
    service = AutomationService(scheduler=sched)
    service.resync_all()




@app.on_event("shutdown")
async def on_shutdown():
    sched = getattr(app.state, "scheduler", None)
    if sched:
        sched.shutdown(wait=False)


app.include_router(automation.router)
app.include_router(llm.router)