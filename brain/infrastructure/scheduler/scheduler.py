from apscheduler.schedulers.background import BackgroundScheduler

# Single scheduler instance
scheduler = BackgroundScheduler(timezone="UTC")
scheduler.start()


def remove_job_if_exists(job_id: str):
    """Remove a scheduled job if it exists, ignoring errors if not found."""
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


def print_all_jobs():
    """Print all scheduled jobs with details."""
    jobs = scheduler.get_jobs()
    if not jobs:
        print("No scheduled jobs.")
        return
    print(f"Total jobs scheduled: {len(jobs)}")
    for job in jobs:
        print(f"- ID: {job.id}")
        print(f"  Next run: {job.next_run_time}")
        print(f"  Trigger: {job.trigger}")
        print("-" * 40)