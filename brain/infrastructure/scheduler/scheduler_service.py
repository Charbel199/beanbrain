from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from dateutil.tz import gettz
import logging, os
import conf

logger = logging.getLogger(__name__)

def build_scheduler() -> AsyncIOScheduler:
    jobstores = {
        # optional persistence for scheduled jobs
        # "default": SQLAlchemyJobStore(url=conf.DATABASE_URL)
    }
    executors = {
        "default": ThreadPoolExecutor(max_workers=10),
    }
    job_defaults = {"coalesce": True, "max_instances": 1}

    tz = gettz(conf.DEFAULT_TZ)
    sched = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=tz,
    )
    return sched

def remove_job_if_exists(scheduler, job_id: str):
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass