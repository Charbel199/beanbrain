import shutil
from datetime import datetime
from pathlib import Path
import subprocess

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
# Config
LEDGER_PATH = Path("/data/budget.beancount")
BACKUP_DIR = Path("/data/backups")
RCLONE_REMOTE = "gdrive"
RCLONE_REMOTE_FOLDER = "beancount-backups"
BACKUP_HOUR = 0  # Run every day at 00:00 AM
MISSING_GRACE_TIME = 3600  # 1 hour window to still run missed jobs

def run_backup_once():
    if not LEDGER_PATH.exists():
        print("Ledger file not found. Skipping backup.")
        return

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    backup_path = BACKUP_DIR / f"{LEDGER_PATH.stem}_{timestamp}{LEDGER_PATH.suffix}"
    shutil.copy2(LEDGER_PATH, backup_path)
    print(f"Created backup: {backup_path}")

    try:
        subprocess.run([
            "rclone", "copy", str(backup_path),
            f"{RCLONE_REMOTE}:{RCLONE_REMOTE_FOLDER}",
            "--progress"
        ], check=True)
        print(f"Uploaded to Google Drive: {backup_path.name}")
    except subprocess.CalledProcessError as e:
        print(f"Upload failed:\n{e}")

if __name__ == "__main__":
    print("Starting backup service. Running initial backup...")
    run_backup_once()

    scheduler = BlockingScheduler()


    scheduler.add_job(
        run_backup_once,
        trigger=CronTrigger(hour=BACKUP_HOUR, minute=0),
        misfire_grace_time=MISSING_GRACE_TIME,
        coalesce=True,
        max_instances=1,
    )

    # For testing, runs once per minute
    # scheduler.add_job(
    #     run_backup_once,
    #     trigger="interval",
    #     minutes=1,
    #     misfire_grace_time=MISSING_GRACE_TIME,
    #     coalesce=True,
    #     max_instances=1,
    # )

    print(f"Scheduled daily backup at {BACKUP_HOUR:02d}:00 with {MISSING_GRACE_TIME//60} minute grace.")
    scheduler.start()
