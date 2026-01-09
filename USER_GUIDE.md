# Task Queue - User Guide

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Basic Concepts](#basic-concepts)
4. [Task Definition](#task-definition)
5. [Task Execution](#task-execution)
6. [Worker Configuration](#worker-configuration)
7. [Retries and Error Handling](#retries-and-error-handling)
8. [Scheduled Tasks](#scheduled-tasks)
9. [Task Priorities](#task-priorities)
10. [Result Handling](#result-handling)
11. [Task Chains and Groups](#task-chains-and-groups)
12. [Monitoring and Debugging](#monitoring-and-debugging)
13. [Production Deployment](#production-deployment)
14. [Best Practices](#best-practices)
15. [Troubleshooting](#troubleshooting)

## Installation

### Python

```bash
# Install with Redis support
pip install task-queue[redis]

# Install with RabbitMQ support
pip install task-queue[rabbitmq]

# Install with all backends
pip install task-queue[all]

# Install development dependencies
pip install task-queue[dev]
```

### Go

```bash
# Install Go library
go get github.com/task-queue/go

# Install command-line tools
go install github.com/task-queue/cmd/tq-worker@latest
go install github.com/task-queue/cmd/tq-scheduler@latest
```

### Dependencies

**Required**:
- Python 3.10+ or Go 1.21+
- Redis 7.0+ or RabbitMQ 3.12+

**Optional**:
- PostgreSQL 15+ (for result backend)
- Docker (for containerization)

## Quick Start

### Python Example

**1. Define tasks (tasks.py)**:
```python
from taskqueue import TaskQueue

# Initialize queue
queue = TaskQueue(
    broker='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1'
)

@queue.task
def send_email(to, subject, body):
    """Send an email"""
    # Email sending logic
    print(f"Sending email to {to}")
    return {"status": "sent", "to": to}

@queue.task
def process_data(data):
    """Process data"""
    result = sum(data)
    return {"sum": result}
```

**2. Start worker**:
```bash
# Start worker with default settings
python -m taskqueue worker --queues=default --broker=redis://localhost

# Or programmatically
from taskqueue import Worker

worker = Worker(
    queues=['default'],
    broker='redis://localhost'
)
worker.start()
```

**3. Enqueue tasks (main.py)**:
```python
from tasks import send_email, process_data

# Simple task execution
task = send_email.delay('user@example.com', 'Hello', 'Body')
result = task.get(timeout=10)
print(result)  # {"status": "sent", "to": "user@example.com"}

# Task with arguments
task = process_data.delay([1, 2, 3, 4, 5])
result = task.get()
print(result)  # {"sum": 15}
```

### Go Example

**1. Define tasks (main.go)**:
```go
package main

import (
    "context"
    "github.com/task-queue/go/taskqueue"
)

func sendEmail(ctx context.Context, to, subject, body string) (map[string]interface{}, error) {
    // Email sending logic
    return map[string]interface{}{
        "status": "sent",
        "to":     to,
    }, nil
}

func processData(ctx context.Context, data []int) (map[string]interface{}, error) {
    sum := 0
    for _, v := range data {
        sum += v
    }
    return map[string]interface{}{
        "sum": sum,
    }, nil
}
```

**2. Start worker**:
```bash
# Start worker
tq-worker --queues=default --broker=redis://localhost

# Or programmatically
worker := taskqueue.NewWorker(
    taskqueue.WithQueues("default"),
    taskqueue.WithBroker("redis://localhost"),
)
worker.Register("sendEmail", sendEmail)
worker.Register("processData", processData)
worker.Start(context.Background())
```

**3. Enqueue tasks (main.go)**:
```go
queue := taskqueue.NewQueue("default", "redis://localhost")

// Enqueue task
task, err := queue.Enqueue("sendEmail", "user@example.com", "Hello", "Body")

// Get result
result, err := task.Get(context.Background(), 10*time.Second)
fmt.Println(result)  // {"status": "sent", "to": "user@example.com"}
```

## Basic Concepts

### Tasks

Tasks are units of work that are executed asynchronously by workers.

**Key characteristics**:
- Defined as functions or methods
- Serializable arguments and return values
- Assigned to queues
- Tracked with unique IDs
- Can be retried on failure

### Queues

Queues organize tasks by type or priority.

**Default queues**:
- `default`: Standard tasks
- `high_priority`: Urgent tasks
- `low_priority`: Background tasks

### Workers

Workers process tasks from queues.

**Worker types**:
- **Foreground**: Run in terminal, log to stdout
- **Background**: Run as daemon/service
- **Containerized**: Run in Docker/Kubernetes

### Brokers

Brokers facilitate communication between producers and workers.

**Supported brokers**:
- **Redis**: Fast, simple, feature-rich
- **RabbitMQ**: Robust, enterprise-ready

### Result Backends

Result backends store task execution results.

**Supported backends**:
- **Redis**: Fast, in-memory
- **PostgreSQL**: Persistent, queryable

## Task Definition

### Basic Task

**Python**:
```python
from taskqueue import TaskQueue

queue = TaskQueue(broker='redis://localhost')

@queue.task
def add(x, y):
    return x + y
```

**Go**:
```go
func add(ctx context.Context, x, y int) (int, error) {
    return x + y, nil
}

worker.Register("add", add)
```

### Task with Options

**Python**:
```python
@queue.task(
    name='custom_name',      # Custom task name
    queue='high_priority',   # Specific queue
    retries=5,               # Max retries
    timeout=60,              # Timeout in seconds
    priority=0,              # Priority (0=highest)
)
def important_task(data):
    return process(data)
```

**Go**:
```go
task, err := queue.Enqueue(
    "importantTask",
    data,
    taskqueue.WithQueue("high_priority"),
    taskqueue.WithRetries(5),
    taskqueue.WithTimeout(60*time.Second),
    taskqueue.WithPriority(0),
)
```

### Task with Retry Configuration

**Python**:
```python
@queue.task(
    retries=3,
    retry_backoff=True,        # Exponential backoff
    retry_delay=1.0,           # Initial delay (seconds)
    retry_max_delay=60.0,      # Max delay (seconds)
    retry_jitter=True,         # Add randomness
)
def flaky_task(url):
    return fetch_data(url)
```

**Go**:
```go
task, err := queue.Enqueue(
    "flakyTask",
    url,
    taskqueue.WithRetries(3),
    taskqueue.WithRetryBackoff(true),
    taskqueue.WithRetryDelay(1.0),
    taskqueue.WithRetryMaxDelay(60.0),
    taskqueue.WithRetryJitter(true),
)
```

## Task Execution

### Delayed Execution

**Python**:
```python
# Execute asynchronously
task = add.delay(5, 3)

# Get result later
result = task.get(timeout=10)
print(result)  # 8
```

**Go**:
```go
// Execute asynchronously
task, _ := queue.Enqueue("add", 5, 3)

// Get result later
result, _ := task.Get(context.Background(), 10*time.Second)
fmt.Println(result)  // 8
```

### Scheduled Execution (ETA)

**Python**:
```python
from datetime import datetime, timedelta

# Execute at specific time
eta = datetime(2025, 1, 8, 12, 0, 0)
task = add.apply_async(args=(5, 3), eta=eta)

# Execute after delay
task = add.apply_async(args=(5, 3), countdown=60)  # 60 seconds
```

**Go**:
```go
// Execute at specific time
eta := time.Date(2025, 1, 8, 12, 0, 0, 0, time.UTC)
task, _ := queue.EnqueueAt("add", eta, 5, 3)

// Execute after delay
task, _ := queue.EnqueueIn("add", 60*time.Second, 5, 3)
```

### Synchronous Execution

**Python**:
```python
# Execute synchronously (blocking)
result = add.apply(args=(5, 3))
print(result)  # 8
```

**Go**:
```go
// Execute synchronously (blocking)
result, _ := queue.ExecuteSync("add", 5, 3)
fmt.Println(result)  // 8
```

## Worker Configuration

### Basic Worker

**Python**:
```python
from taskqueue import Worker

worker = Worker(
    broker='redis://localhost:6379/0',
    queues=['default'],
    concurrency=100
)
worker.start()
```

**Go**:
```go
worker := taskqueue.NewWorker(
    taskqueue.WithBroker("redis://localhost:6379/0"),
    taskqueue.WithQueues("default"),
    taskqueue.WithConcurrency(100),
)
worker.Start(context.Background())
```

### Multi-Queue Worker

**Python**:
```python
worker = Worker(
    queues=['high_priority', 'default', 'low_priority'],
    queue_order='priority'  # Process high_priority first
)
worker.start()
```

**Go**:
```go
worker := taskqueue.NewWorker(
    taskqueue.WithQueues("high_priority", "default", "low_priority"),
    taskqueue.WithQueueOrder("priority"),
)
worker.Start(context.Background())
```

### Worker with Prefetch

**Python**:
```python
worker = Worker(
    queues=['default'],
    concurrency=100,
    prefetch_multiplier=4,  # Fetch 400 tasks at once
)
worker.start()
```

**Go**:
```go
worker := taskqueue.NewWorker(
    taskqueue.WithQueues("default"),
    taskqueue.WithConcurrency(100),
    taskqueue.WithPrefetch(4),
)
worker.Start(context.Background())
```

### Worker with Time Limits

**Python**:
```python
worker = Worker(
    queues=['default'],
    task_time_limit=300,      # Hard limit: 5 minutes
    task_soft_time_limit=240, # Soft limit: 4 minutes
)
worker.start()
```

**Go**:
```go
worker := taskqueue.NewWorker(
    taskqueue.WithQueues("default"),
    taskqueue.WithTaskTimeLimit(300*time.Second),
    taskqueue.WithTaskSoftTimeLimit(240*time.Second),
)
worker.Start(context.Background())
```

## Retries and Error Handling

### Automatic Retries

**Python**:
```python
@queue.task(retries=3)
def fetch_url(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# Automatic retry on HTTP errors
task = fetch_url.delay('https://api.example.com')
```

**Go**:
```go
func fetchURL(ctx context.Context, url string) (map[string]interface{}, error) {
    resp, err := http.Get(url)
    if err != nil {
        return nil, err  // Will retry
    }
    defer resp.Body.Close()
    // Process response
}

worker.Register("fetchURL", fetchURL)
```

### Custom Retry Logic

**Python**:
```python
from taskqueue import Retry

def should_retry(exc):
    # Retry only on network errors
    return isinstance(exc, (ConnectionError, TimeoutError))

@queue.task(retry_for=should_retry)
def fetch_data(url):
    return requests.get(url).json()
```

**Go**:
```go
func shouldRetry(err error) bool {
    _, isNetErr := err.(net.Error)
    return isNetErr
}

worker.RegisterWithRetry("fetchData", fetchData, shouldRetry)
```

### Error Handling

**Python**:
```python
@queue.task
def process_data(data):
    try:
        result = complex_calculation(data)
        return {"success": True, "result": result}
    except ValueError as e:
        # Don't retry validation errors
        raise ValueError(f"Invalid data: {e}")
    except Exception as e:
        # Retry other errors
        raise  # Will be caught by retry mechanism
```

**Go**:
```go
func processData(ctx context.Context, data Data) (map[string]interface{}, error) {
    result, err := complexCalculation(data)
    if err != nil {
        if validationErr, ok := err.(*ValidationError); ok {
            // Don't retry validation errors
            return nil, validationErr
        }
        // Retry other errors
        return nil, err
    }
    return map[string]interface{}{
        "success": true,
        "result":  result,
    }, nil
}
```

### Dead Letter Queue

**Python**:
```python
@queue.task(
    retries=3,
    dead_letter_queue='failed_tasks'
)
def critical_task(data):
    return process(data)

# Monitor failed tasks
from taskqueue import inspect

insp = inspect('my_worker')
failed_tasks = insp.failed_tasks()
for task in failed_tasks:
    print(f"Failed: {task['name']}, Error: {task['error']}")
```

**Go**:
```go
task, _ := queue.Enqueue(
    "criticalTask",
    data,
    taskqueue.WithRetries(3),
    taskqueue.WithDeadLetterQueue("failed_tasks"),
)
```

## Scheduled Tasks

### Cron-like Scheduling

**Python**:
```python
from taskqueue import schedule

# Execute every 5 minutes
@schedule(cron='*/5 * * * *')
def cleanup():
    print("Cleaning up...")

# Execute every day at midnight
@schedule(cron='0 0 * * *')
def daily_report():
    generate_report()

# Execute every hour
@schedule(cron='0 * * * *')
def hourly_sync():
    sync_data()
```

**Go**:
```go
scheduler := taskqueue.NewScheduler("redis://localhost")

// Execute every 5 minutes
scheduler.AddCron("cleanup", "*/5 * * * *", cleanup)

// Execute every day at midnight
scheduler.AddCron("daily_report", "0 0 * * *", dailyReport)

scheduler.Start(context.Background())
```

### Interval Scheduling

**Python**:
```python
from datetime import timedelta

# Execute every hour
@schedule(interval=timedelta(hours=1))
def hourly_task():
    pass

# Execute every 30 seconds
@schedule(interval=timedelta(seconds=30))
def frequent_task():
    pass
```

**Go**:
```go
// Execute every hour
scheduler.AddInterval("hourly_task", time.Hour, hourlyTask)

// Execute every 30 seconds
scheduler.AddInterval("frequent_task", 30*time.Second, frequentTask)
```

### Scheduled Task Management

**Python**:
```python
from taskqueue import ScheduleManager

manager = ScheduleManager(broker='redis://localhost')

# List scheduled tasks
tasks = manager.list_schedules()

# Remove schedule
manager.remove_schedule('cleanup')

# Pause schedule
manager.pause_schedule('daily_report')

# Resume schedule
manager.resume_schedule('daily_report')
```

**Go**:
```go
manager := taskqueue.NewScheduleManager("redis://localhost")

// List scheduled tasks
tasks, _ := manager.ListSchedules()

// Remove schedule
manager.RemoveSchedule("cleanup")

// Pause schedule
manager.PauseSchedule("daily_report")

// Resume schedule
manager.ResumeSchedule("daily_report")
```

## Task Priorities

### Priority Levels

**Priority range**: 0-10 (0=highest, 10=lowest)

**Python**:
```python
@queue.task
def high_priority_task():
    pass

@queue.task
def low_priority_task():
    pass

# Enqueue with priority
high_priority_task.apply_async(priority=0)  # Highest
high_priority_task.apply_async(priority=5)  # Default
low_priority_task.apply_async(priority=10)  # Lowest
```

**Go**:
```go
// Enqueue with priority
queue.Enqueue("high_priority_task", taskqueue.WithPriority(0))  // Highest
queue.Enqueue("normal_task", taskqueue.WithPriority(5))         // Default
queue.Enqueue("low_priority_task", taskqueue.WithPriority(10))  // Lowest
```

### Priority Queues

**Python**:
```python
# Define task with default priority
@queue.task(queue='high_priority')
def urgent_task():
    pass

# Worker processes high_priority queue first
worker = Worker(
    queues=['high_priority', 'default', 'low_priority']
)
worker.start()
```

**Go**:
```go
worker := taskqueue.NewWorker(
    taskqueue.WithQueues("high_priority", "default", "low_priority"),
)
worker.Start(context.Background())
```

## Result Handling

### Async Result

**Python**:
```python
task = process_data.delay([1, 2, 3, 4, 5])

# Check if ready
if task.ready():
    result = task.get()
    print(result)
else:
    print("Task still running...")

# Wait with timeout
try:
    result = task.get(timeout=10)
except TimeoutError:
    print("Task timed out")
```

**Go**:
```go
task, _ := queue.Enqueue("process_data", []int{1, 2, 3, 4, 5})

// Check if ready
if task.Ready() {
    result, _ := task.Get(context.Background())
    fmt.Println(result)
} else {
    fmt.Println("Task still running...")
}

// Wait with timeout
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()
result, err := task.Get(ctx)
if err != nil {
    fmt.Println("Task timed out")
}
```

### Task Status

**Python**:
```python
task = process_data.delay([1, 2, 3])

# Check status
print(task.status)  # PENDING, STARTED, SUCCESS, FAILURE

# Get result info
info = task.info
print(info)
# {
#     'task_id': '550e8400-e29b-41d4-a716-446655440000',
#     'status': 'SUCCESS',
#     'result': {...},
#     'timestamp': '2025-01-08T10:00:00Z'
# }
```

**Go**:
```go
task, _ := queue.Enqueue("process_data", []int{1, 2, 3})

// Check status
fmt.Println(task.Status())  // PENDING, STARTED, SUCCESS, FAILURE

// Get result info
info := task.Info()
fmt.Println(info)
```

### Result Callbacks

**Python**:
```python
def on_success(result):
    print(f"Task succeeded: {result}")

def on_failure(exc, traceback):
    print(f"Task failed: {exc}")

task = process_data.delay(
    [1, 2, 3],
    on_success=on_success,
    on_failure=on_failure
)
```

**Go**:
```go
task, _ := queue.Enqueue(
    "process_data",
    []int{1, 2, 3},
    taskqueue.WithOnSuccess(func(result interface{}) {
        fmt.Printf("Task succeeded: %v\n", result)
    }),
    taskqueue.WithOnFailure(func(err error) {
        fmt.Printf("Task failed: %v\n", err)
    }),
)
```

## Task Chains and Groups

### Task Chains

Execute tasks sequentially, passing results.

**Python**:
```python
from taskqueue import chain

# Define chain
workflow = chain(
    add.s(2, 2),           # Result: 4
    multiply.s(4),         # Result: 16
    subtract.s(10)         # Result: 6
)

# Execute chain
result = workflow.delay()
final_result = result.get()
print(final_result)  # 6
```

**Go**:
```go
chain := taskqueue.NewChain(
    taskqueue.NewTask("add", 2, 2),
    taskqueue.NewTask("multiply", 4),
    taskqueue.NewTask("subtract", 10),
)

result, _ := chain.Execute(context.Background())
fmt.Println(result)  // 6
```

### Task Groups

Execute tasks in parallel, aggregate results.

**Python**:
```python
from taskqueue import group

# Define group
job = group([
    process_user.s(user_id) for user_id in range(100)
])

# Execute group
result = job.delay()

# Wait for all tasks to complete
results = result.get()
print(len(results))  # 100
```

**Go**:
```go
var tasks []*taskqueue.Task
for i := 0; i < 100; i++ {
    tasks = append(tasks, taskqueue.NewTask("process_user", i))
}

group := taskqueue.NewGroup(tasks...)
result, _ := group.Execute(context.Background())
fmt.Println(len(results))  // 100
```

### Chord

Group with callback on all results.

**Python**:
```python
from taskqueue import chord

# Define chord (group + callback)
callback = summarize_results.s()
header = [process_data.s(i) for i in range(100)]

chord_task = chord(header)(callback)
result = chord_task.delay()

# Callback receives all group results
final_result = result.get()
```

**Go**:
```go
var tasks []*taskqueue.Task
for i := 0; i < 100; i++ {
    tasks = append(tasks, taskqueue.NewTask("process_data", i))
}

callback := taskqueue.NewTask("summarize_results")
chord := taskqueue.NewChord(tasks, callback)
result, _ := chord.Execute(context.Background())
```

## Monitoring and Debugging

### Worker Statistics

**Python**:
```python
from taskqueue import inspect

# Get worker stats
insp = inspect('my_worker')
stats = insp.stats()

print(stats)
# {
#     'total': 10000,
#     'succeeded': 9500,
#     'failed': 500,
#     'retried': 300,
#     'runtime': 1234.56  # seconds
# }
```

**Go**:
```go
stats := worker.Stats()
fmt.Printf("Total: %d, Succeeded: %d, Failed: %d\n",
    stats.Total, stats.Succeeded, stats.Failed)
```

### Active Tasks

**Python**:
```python
# Get active tasks
active = insp.active()
for task in active:
    print(f"Task: {task['name']}, ID: {task['id']}")
```

**Go**:
```go
active := worker.ActiveTasks()
for _, task := range active {
    fmt.Printf("Task: %s, ID: %s\n", task.Name, task.ID)
}
```

### Scheduled Tasks

**Python**:
```python
# Get scheduled tasks
scheduled = insp.scheduled()
for task in scheduled:
    print(f"Task: {task['name']}, ETA: {task['eta']}")
```

**Go**:
```go
scheduled := worker.ScheduledTasks()
for _, task := range scheduled {
    fmt.Printf("Task: %s, ETA: %s\n", task.Name, task.ETA)
}
```

### Queue Monitoring

**Python**:
```python
from taskqueue import Queue

queue = Queue('default', broker='redis://localhost')

# Get queue length
length = queue.length()
print(f"Queue length: {length}")

# Get queue stats
stats = queue.stats()
print(stats)
# {
#     'length': 1000,
#     'waiting': 950,
#     'active': 50
# }
```

**Go**:
```go
queue := taskqueue.NewQueue("default", "redis://localhost")

// Get queue length
length := queue.Length()
fmt.Printf("Queue length: %d\n", length)

// Get queue stats
stats := queue.Stats()
fmt.Printf("Waiting: %d, Active: %d\n", stats.Waiting, stats.Active)
```

### Logging

**Python**:
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Task-specific logging
@queue.task
def my_task():
    logger = logging.getLogger(__name__)
    logger.info("Task started")
    result = process()
    logger.info("Task completed")
    return result
```

**Go**:
```go
import "log"

func myTask(ctx context.Context) (interface{}, error) {
    log.Println("Task started")
    result, err := process()
    if err != nil {
        log.Printf("Task failed: %v", err)
        return nil, err
    }
    log.Println("Task completed")
    return result, nil
}
```

## Production Deployment

### Docker Deployment

**Dockerfile (Python)**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run worker
CMD ["python", "-m", "taskqueue", "worker", \
     "--broker=redis://redis:6379", \
     "--queues=default"]
```

**Dockerfile (Go)**:
```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -o worker cmd/worker/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates

WORKDIR /root/
COPY --from=builder /app/worker .

# Run worker
CMD ["./worker", "--broker=redis://redis:6379", "--queues=default"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    depends_on:
      - redis
    environment:
      - BROKER_URL=redis://redis:6379
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '1'
          memory: 1G

  scheduler:
    build: .
    command: python -m taskqueue scheduler --broker=redis://redis:6379
    depends_on:
      - redis
```

### Kubernetes Deployment

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: task-queue-worker
spec:
  replicas: 4
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker
        image: task-queue-worker:latest
        env:
        - name: BROKER_URL
          value: "redis://redis-service:6379"
        - name: QUEUES
          value: "default,high_priority"
        - name: CONCURRENCY
          value: "100"
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - "pgrep -f worker"
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - "pgrep -f worker"
          initialDelaySeconds: 10
          periodSeconds: 5
```

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis-service
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

### Systemd Service

**/etc/systemd/system/task-queue-worker.service**:
```ini
[Unit]
Description=Task Queue Worker
After=network.target redis.service

[Service]
Type=simple
User=worker
Group=worker
WorkingDirectory=/opt/task-queue
Environment="BROKER_URL=redis://localhost:6379"
Environment="QUEUES=default"
ExecStart=/usr/bin/python -m taskqueue worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable task-queue-worker
sudo systemctl start task-queue-worker
sudo systemctl status task-queue-worker
```

## Best Practices

### 1. Task Design

**DO**:
- Keep tasks focused and single-purpose
- Use descriptive task names
- Include clear error messages
- Validate input data
- Handle exceptions properly

**DON'T**:
- Don't make tasks too long (break into smaller tasks)
- Don't use blocking operations (use async)
- Don't share state between tasks
- Don't ignore errors

### 2. Queue Organization

**DO**:
- Use separate queues for different task types
- Prioritize critical tasks
- Monitor queue depths
- Set appropriate queue limits

**DON'T**:
- Don't mix task priorities in same queue
- Don't create too many queues (complexity)
- Don't let queues grow indefinitely

### 3. Resource Management

**DO**:
- Set appropriate concurrency limits
- Use timeouts to prevent hanging tasks
- Monitor memory and CPU usage
- Scale workers based on load

**DON'T**:
- Don't set concurrency too high (memory issues)
- Don't ignore resource limits
- Don't run workers without monitoring

### 4. Error Handling

**DO**:
- Use appropriate retry strategies
- Log errors with context
- Set retry limits
- Use dead letter queues

**DON'T**:
- Don't retry indefinitely
- Don't swallow exceptions
- Don't ignore failed tasks

### 5. Monitoring

**DO**:
- Track task metrics (throughput, latency)
- Monitor queue depths
- Alert on failures
- Review logs regularly

**DON'T**:
- Don't deploy without monitoring
- Don't ignore error trends
- Don't forget to set up alerts

### 6. Security

**DO**:
- Use TLS for broker connections
- Validate task arguments
- Use secrets management
- Follow principle of least privilege

**DON'T**:
- Don't expose broker to internet
- Don't log sensitive data
- Don't use insecure serializers

### 7. Performance

**DO**:
- Use connection pooling
- Batch operations when possible
- Optimize serialization
- Use result caching

**DON'T**:
- Don't create connections per task
- Don't serialize large objects
- Don't poll results excessively

### 8. Testing

**DO**:
- Test tasks locally
- Use test brokers (Redis in-memory)
- Simulate failures
- Load test before production

**DON'T****:
- Don't skip testing
- Don't test with production broker
- Don't ignore test failures

## Troubleshooting

### Common Issues

#### 1. Workers Not Processing Tasks

**Symptoms**:
- Queue depth increasing
- No activity in worker logs

**Solutions**:
- Check worker is running: `ps aux | grep worker`
- Verify broker connection: `redis-cli ping`
- Check queue names match: worker vs. producer
- Review worker logs: `tail -f worker.log`

#### 2. High Memory Usage

**Symptoms**:
- Worker process consuming GBs of memory
- OOM kills

**Solutions**:
- Reduce concurrency: `--concurrency=50`
- Reduce prefetch: `--prefetch-multiplier=2`
- Check for memory leaks: profile worker
- Add memory limits: `ulimit -v 1000000`

#### 3. Tasks Timing Out

**Symptoms**:
- Tasks failing with timeout errors
- Incomplete task execution

**Solutions**:
- Increase task timeout: `@task(timeout=600)`
- Optimize slow tasks
- Check for blocking operations
- Monitor task runtime

#### 4. Retry Storm

**Symptoms**:
- Thousands of tasks retrying simultaneously
- Broker overload

**Solutions**:
- Add retry jitter: `retry_jitter=True`
- Increase retry delay: `retry_delay=5.0`
- Use exponential backoff: `retry_backoff=True`
- Set max retry limit: `retries=3`

#### 5. Lost Tasks

**Symptoms**:
- Tasks enqueued but never executed
- No error messages

**Solutions**:
- Check broker durability settings
- Verify queue names match
- Check worker queue subscriptions
- Review broker logs

### Debug Mode

**Python**:
```bash
# Enable debug logging
LOGLEVEL=DEBUG python -m taskqueue worker --broker=redis://localhost

# Enable task tracing
TRACE_TASKS=true python -m taskqueue worker --broker=redis://localhost
```

**Go**:
```bash
# Enable debug logging
LOGLEVEL=debug tq-worker --broker=redis://localhost

# Enable task tracing
TRACE_TASKS=true tq-worker --broker=redis://localhost
```

### Performance Profiling

**Python**:
```bash
# Profile worker
py-spy record -o profile.svg -- python -m taskqueue worker

# Memory profile
memory_profiler python -m taskqueue worker
```

**Go**:
```bash
# CPU profile
go tool pprof http://localhost:6060/debug/pprof/profile

# Memory profile
go tool pprof http://localhost:6060/debug/pprof/heap
```

### Health Checks

**Python**:
```python
from taskqueue import inspect

# Check worker health
insp = inspect('my_worker')
health = insp.health()
print(health)
# {
#     'status': 'healthy',
#     'uptime': 86400,
#     'active_tasks': 45,
#     'memory_usage': '512MB',
#     'cpu_usage': '45%'
# }
```

**Go**:
```go
health := worker.Health()
fmt.Printf("Status: %s, Uptime: %d\n", health.Status, health.Uptime)
```

---

**Last Updated**: 2025-01-08
**Document Version**: 1.0
