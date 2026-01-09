"""
Example demonstrating task chains and groups.
"""

from taskqueue import TaskQueue, chain, group, chord
import time

queue = TaskQueue(broker='redis://localhost:6379/0')

@queue.task
def add(x, y):
    """Add two numbers."""
    print(f"Adding {x} + {y}")
    return x + y

@queue.task
def multiply(x, y):
    """Multiply two numbers."""
    print(f"Multiplying {x} * {y}")
    return x * y

@queue.task
def subtract(x, y):
    """Subtract y from x."""
    print(f"Subtracting {x} - {y}")
    return x - y

@queue.task
def process_item(item):
    """Process a single item."""
    print(f"Processing item: {item}")
    time.sleep(0.5)
    return item * 2

@queue.task
def summarize_results(results):
    """Summarize results from a group."""
    print(f"Summarizing {len(results)} results")
    return {
        "count": len(results),
        "sum": sum(results),
        "average": sum(results) / len(results)
    }

if __name__ == "__main__":
    print("Example 1: Task Chain")
    print("=" * 50)

    # Create a chain: add -> multiply -> subtract
    workflow = chain(
        add.s(2, 2),           # Result: 4
        multiply.s(4),         # Result: 16
        subtract.s(10)         # Result: 6
    )

    result = workflow.delay()
    final_result = result.get(timeout=10)
    print(f"Chain result: {final_result}")
    print()

    print("Example 2: Task Group")
    print("=" * 50)

    # Create a group of parallel tasks
    job = group([
        process_item.s(i) for i in range(10)
    ])

    result = job.delay()
    results = result.get(timeout=10)
    print(f"Group results: {results}")
    print()

    print("Example 3: Chord (Group + Callback)")
    print("=" * 50)

    # Create a chord: group with callback
    header = [process_item.s(i) for i in range(10)]
    callback = summarize_results.s()

    chord_task = chord(header)(callback)
    result = chord_task.delay()
    final_result = result.get(timeout=10)
    print(f"Chord result: {final_result}")
    print()
