"""
Worker example - demonstrates how to run a task queue worker.

Start this worker to process tasks from the queue.
"""

from taskqueue import Worker
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Define task handlers
def send_email(to, subject, body):
    """Send an email to a recipient."""
    logger.info(f"Sending email to {to}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Body: {body[:50]}...")
    # Email sending logic here
    return {
        "status": "sent",
        "to": to,
        "subject": subject
    }

def process_image(image_path):
    """Process an image file."""
    logger.info(f"Processing image: {image_path}")
    # Image processing logic here
    return {
        "status": "processed",
        "path": image_path,
        "size": 1024000
    }

def generate_report(report_type, date):
    """Generate a report for a specific date."""
    logger.info(f"Generating {report_type} report for {date}")
    # Report generation logic here
    return {
        "type": report_type,
        "date": date,
        "url": f"/reports/{report_type}_{date}.pdf"
    }

def cleanup_old_data(days=30):
    """Clean up data older than specified days."""
    logger.info(f"Cleaning up data older than {days} days")
    # Cleanup logic here
    return {
        "deleted_records": 1500,
        "freed_space": "250MB"
    }

if __name__ == "__main__":
    logger.info("Starting worker...")

    # Create worker
    worker = Worker(
        queues=['default', 'high_priority', 'low_priority'],
        broker='redis://localhost:6379/0',
        concurrency=100,
        prefetch_multiplier=4,
        loglevel=logging.INFO
    )

    # Register tasks
    worker.register('send_email', send_email)
    worker.register('process_image', process_image)
    worker.register('generate_report', generate_report)
    worker.register('cleanup_old_data', cleanup_old_data)

    # Start worker
    try:
        logger.info("Worker running, press Ctrl+C to stop")
        worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
        worker.stop()
        logger.info("Worker stopped")
