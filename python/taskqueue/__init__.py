"""
Task Queue - High-performance distributed task processing library.

This library provides a simple and powerful way to process tasks
asynchronously with support for retries, scheduling, and priorities.
"""

__version__ = "0.1.0-alpha"
__author__ = "Task Queue Contributors"
__license__ = "MIT"

from .core.queue import TaskQueue
from .core.task import task
from .core.result import AsyncResult
from .worker import Worker
from .scheduler import schedule, ScheduleManager
from .primitive import chain, group, chord

__all__ = [
    "TaskQueue",
    "task",
    "AsyncResult",
    "Worker",
    "schedule",
    "ScheduleManager",
    "chain",
    "group",
    "chord",
]
