from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.tz import gettz

# Single scheduler instance
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.start()


def remove_job_if_exists(job_id: str):
    """Remove a scheduled job if it exists, ignoring errors if not found."""
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


def job_id(automation_id: int) -> str:
    """Generate a unique job ID for an automation."""
    return f"auto-{automation_id}"


def cron_kwargs(
    frequency: str, 
    day_of_week, 
    day_of_month, 
    month_of_year, 
    hour, 
    minute, 
    tzname: str
):
    """
    Convert automation parameters to APScheduler CronTrigger kwargs.
    
    Args:
        frequency: One of DAILY, WEEKLY, MONTHLY, YEARLY
        day_of_week: Day of week (0-6, Monday=0) for WEEKLY frequency
        day_of_month: Day of month (1-31) for MONTHLY and YEARLY
        month_of_year: Month (1-12) for YEARLY frequency
        hour: Hour (0-23) in the specified timezone
        minute: Minute (0-59)
        tzname: Timezone name (e.g., 'America/New_York')
    
    Returns:
        Dictionary of kwargs for CronTrigger
    """
    tz = gettz(tzname) or gettz("UTC")
    
    if frequency == "DAILY":
        return dict(hour=hour, minute=minute, timezone=tz)
    elif frequency == "WEEKLY":
        return dict(day_of_week=str(day_of_week), hour=hour, minute=minute, timezone=tz)
    elif frequency == "MONTHLY":
        return dict(day=day_of_month, hour=hour, minute=minute, timezone=tz)
    elif frequency == "YEARLY":
        return dict(month=month_of_year, day=day_of_month, hour=hour, minute=minute, timezone=tz)
    else:
        # Fallback to daily for unknown frequencies
        return dict(hour=hour, minute=minute, timezone=tz)