"""
Example demonstrating scheduled tasks with cron syntax.
"""

from taskqueue import TaskQueue, schedule
from datetime import datetime, timedelta

queue = TaskQueue(broker='redis://localhost:6379/0')

@queue.task
def send_daily_report():
    """Generate and send daily report."""
    print(f"Generating daily report at {datetime.now()}")
    return {"report": "daily_report.pdf", "timestamp": datetime.now().isoformat()}

@queue.task
def cleanup_temp_files():
    """Clean up temporary files."""
    print(f"Cleaning up temp files at {datetime.now()}")
    return {"deleted_files": 150, "freed_space": "250MB"}

@queue.task
def send_reminder_email():
    """Send reminder email."""
    print(f"Sending reminder email at {datetime.now()}")
    return {"status": "sent", "recipients": 500}

@queue.task
def sync_data():
    """Sync data with external service."""
    print(f"Syncing data at {datetime.now()}")
    return {"synced_records": 1000, "duration": "5s"}

if __name__ == "__main__":
    print("Scheduled Tasks Examples")
    print("=" * 60)

    # Example 1: Cron expression (every 5 minutes)
    print("\n1. Schedule task every 5 minutes:")
    print("   Cron: '*/5 * * * *'")

    @schedule(cron='*/5 * * * *')
    def five_minute_task():
        return send_daily_report.delay()

    # Example 2: Daily at midnight
    print("\n2. Schedule task daily at midnight:")
    print("   Cron: '0 0 * * *'")

    @schedule(cron='0 0 * * *')
    def daily_midnight_task():
        return cleanup_temp_files.delay()

    # Example 3: Every hour
    print("\n3. Schedule task every hour:")
    print("   Cron: '0 * * * *'")

    @schedule(cron='0 * * * *')
    def hourly_task():
        return send_reminder_email.delay()

    # Example 4: Every Monday at 9 AM
    print("\n4. Schedule task every Monday at 9 AM:")
    print("   Cron: '0 9 * * 1'")

    @schedule(cron='0 9 * * 1')
    def weekly_monday_task():
        return send_daily_report.delay()

    # Example 5: Every weekday at 8 AM
    print("\n5. Schedule task every weekday at 8 AM:")
    print("   Cron: '0 8 * * 1-5'")

    @schedule(cron='0 8 * * 1-5')
    def weekday_task():
        return send_reminder_email.delay()

    # Example 6: Interval scheduling
    print("\n6. Schedule task every 30 seconds:")
    print("   Interval: timedelta(seconds=30)")

    @schedule(interval=timedelta(seconds=30))
    def frequent_task():
        return sync_data.delay()

    # Example 7: Schedule task for specific time
    print("\n7. Schedule task for specific time (ETA):")
    print("   ETA: datetime.now() + timedelta(minutes=5)")

    eta = datetime.now() + timedelta(minutes=5)
    task = send_daily_report.apply_async(eta=eta)
    print(f"   Task ID: {task.id}")
    print(f"   Scheduled for: {eta}")

    # Example 8: Schedule task with countdown
    print("\n8. Schedule task with countdown:")
    print("   Countdown: 60 seconds")

    task = cleanup_temp_files.apply_async(countdown=60)
    print(f"   Task ID: {task.id}")
    print(f"   Will execute in 60 seconds")

    print("\n" + "=" * 60)
    print("Scheduled tasks configured!")
    print("\nTo run the scheduler:")
    print("  python -m taskqueue scheduler --broker=redis://localhost")
    print("\nTo list scheduled tasks:")
    print("  python -m taskqueue inspect scheduled")
