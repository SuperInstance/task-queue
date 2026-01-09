"""
Simple example demonstrating task-queue usage.

Run this example after starting a worker:
    python -m taskqueue worker --queues=default
"""

from taskqueue import TaskQueue
import time

# Initialize queue
queue = TaskQueue(broker='redis://localhost:6379/0')

# Define a simple task
@queue.task
def add(x, y):
    """Add two numbers."""
    return x + y

@queue.task
def process_data(data):
    """Process data with a delay."""
    print(f"Processing data: {data}")
    time.sleep(1)
    return {"processed": len(data), "sum": sum(data)}

# Define a task with retry
@queue.task(retries=3, retry_backoff=True)
def flaky_task(attempt):
    """Task that might fail."""
    print(f"Attempt {attempt}")
    if attempt < 3:
        raise Exception("Not ready yet!")
    return "Success!"

# Define a high-priority task
@queue.task(queue='high_priority', priority=0)
def urgent_task(message):
    """Urgent task that should be processed first."""
    print(f"URGENT: {message}")
    return message.upper()

if __name__ == "__main__":
    print("Enqueuing tasks...")

    # Simple task
    task1 = add.delay(5, 3)
    print(f"Task 1 ID: {task1.id}")

    # Task with complex arguments
    data = list(range(100))
    task2 = process_data.delay(data)
    print(f"Task 2 ID: {task2.id}")

    # Urgent task
    task3 = urgent_task.delay("Process this immediately!")
    print(f"Task 3 ID: {task3.id}")

    # Flaky task (will retry)
    task4 = flaky_task.delay(1)
    print(f"Task 4 ID: {task4.id}")

    print("\nWaiting for results...")

    # Get results
    result1 = task1.get(timeout=10)
    print(f"Result 1: {result1}")

    result2 = task2.get(timeout=10)
    print(f"Result 2: {result2}")

    result3 = task3.get(timeout=10)
    print(f"Result 3: {result3}")

    result4 = task4.get(timeout=30)
    print(f"Result 4: {result4}")

    print("\nAll tasks completed!")
