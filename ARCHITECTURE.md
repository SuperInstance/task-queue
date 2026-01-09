# Task Queue - Architecture Design

## System Overview

The task-queue library is designed as a distributed task processing system following Celery/Bull patterns, with implementations in both Python and Go. The architecture prioritizes performance, reliability, and scalability.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application Layer                        │
│  (Python/Go applications producing/consuming tasks)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Task Queue Library                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Task Producer│  │ Task Consumer│  │   Scheduler  │          │
│  │   (Client)   │  │   (Worker)   │  │              │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│  ┌──────▼──────────────────▼──────────────────▼───────┐        │
│  │              Task Queue Abstraction Layer           │        │
│  │  - Serialization  - Routing  - Monitoring           │        │
│  └──────┬──────────────────┬──────────────────┬───────┘        │
└─────────┼──────────────────┼──────────────────┼────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼────────────────┐
│                     Message Broker Layer                         │
│  ┌──────────────┐          ┌──────────────┐                    │
│  │ Redis        │          │  RabbitMQ    │                    │
│  │ - Streams    │          │  - AMQP      │                    │
│  │ - Pub/Sub    │          │  - Exchanges │                    │
│  │ - Sorted Sets│          │  - Queues    │                    │
│  └──────────────┘          └──────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼────────────────┐
│                     Result Backend Layer                         │
│  ┌──────────────┐          ┌──────────────┐                    │
│  │ Redis        │          │  PostgreSQL  │                    │
│  │ - Keys       │          │  - Tables    │                    │
│  │ - Hashes     │          │  - Indexes   │                    │
│  │ - TTL        │          │  - JSONB     │                    │
│  └──────────────┘          └──────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Task Producer (Client)

**Responsibilities**:
- Task creation and validation
- Task serialization
- Task enqueueing with options
- Result retrieval (async/sync)
- Task cancellation

**Python API**:
```python
from taskqueue import TaskQueue, Task

# Initialize queue
queue = TaskQueue('my_queue', broker='redis://localhost')

# Define task
@queue.task
def process_data(user_id, data):
    # Task implementation
    return {"status": "success", "processed": len(data)}

# Enqueue task
task = process_data.delay(user_id=123, data=[1, 2, 3])

# Get result
result = task.get(timeout=10)
```

**Go API**:
```go
package main

import (
    "context"
    "github.com/task-queue/go/taskqueue"
)

func processData(ctx context.Context, userID int, data []int) (map[string]interface{}, error) {
    return map[string]interface{}{
        "status": "success",
        "processed": len(data),
    }, nil
}

func main() {
    queue := taskqueue.NewQueue("my_queue", "redis://localhost")

    task, err := queue.Enqueue("processData", 123, []int{1, 2, 3})
    result, err := task.Get(context.Background(), 10*time.Second)
}
```

### 2. Task Consumer (Worker)

**Architecture**:
```
Worker Process
├── Main Process
│   ├── Task Fetcher (prefetch N tasks)
│   ├── Task Router (route to executor)
│   └── Worker Pool (N workers)
│       ├── Worker 1 (goroutine/task)
│       ├── Worker 2 (goroutine/task)
│       ├── Worker 3 (goroutine/task)
│       └── Worker N (goroutine/task)
├── Result Handler (async)
├── Error Handler (async)
├── Health Monitor
└── Shutdown Handler
```

**Worker Lifecycle**:
1. **Initialization**: Connect to broker, register tasks
2. **Fetch**: Prefetch tasks from queue (configurable batch size)
3. **Execute**: Process tasks concurrently
4. **Handle**: Store results, handle errors/retries
5. **Heartbeat**: Send worker health status
6. **Shutdown**: Graceful shutdown on SIGTERM/SIGINT

**Python Implementation**:
```python
from taskqueue import Worker

worker = Worker(
    queues=['default', 'high_priority'],
    broker='redis://localhost',
    concurrency=100,  # Number of async workers
    prefetch_multiplier=4,  # Fetch 400 tasks at once
)

# Task registry
@worker.task
def send_email(to, subject, body):
    # Send email logic
    pass

worker.start()
```

**Go Implementation**:
```go
worker := taskqueue.NewWorker(
    taskqueue.WithQueues("default", "high_priority"),
    taskqueue.WithBroker("redis://localhost"),
    taskqueue.WithConcurrency(1000),
    taskqueue.WithPrefetch(4),
)

worker.Register("sendEmail", sendEmail)
worker.Start(context.Background())
```

### 3. Message Broker Abstraction

**Broker Interface**:
```python
class BrokerBackend(ABC):
    @abstractmethod
    async def enqueue(self, queue: str, task: Task) -> str:
        """Add task to queue"""
        pass

    @abstractmethod
    async def dequeue(self, queues: List[str]) -> Optional[Task]:
        """Fetch task from queues (priority ordered)"""
        pass

    @abstractmethod
    async def ack(self, task_id: str) -> None:
        """Acknowledge task completion"""
        pass

    @abstractmethod
    async def nack(self, task_id: str, requeue: bool) -> None:
        """Negative acknowledgement"""
        pass

    @abstractmethod
    async def schedule(self, task: Task, eta: datetime) -> str:
        """Schedule task for future execution"""
        pass
```

**Redis Backend**:
- **Queue**: Redis Sorted Sets (score = priority)
- **Scheduled Tasks**: Redis Sorted Sets (score = timestamp)
- **Reliability**: Redis Streams for at-least-once delivery
- **Pub/Sub**: For broadcast messages (worker coordination)

**RabbitMQ Backend**:
- **Queue**: AMQP Queues with priority support
- **Exchanges**: Direct routing for task types
- **Reliability**: Publisher confirms, consumer acknowledgements
- **Scheduled Tasks**: Dead-letter exchanges with TTL

### 4. Result Backend

**Result Storage**:
```python
class ResultBackend(ABC):
    @abstractmethod
    async def store_result(self, task_id: str, result: Result) -> None:
        """Store task result"""
        pass

    @abstractmethod
    async def get_result(self, task_id: str) -> Optional[Result]:
        """Retrieve task result"""
        pass

    @abstractmethod
    async def wait_for_result(self, task_id: str, timeout: float) -> Result:
        """Block until result is ready"""
        pass

    @abstractmethod
    async def set_status(self, task_id: str, status: str) -> None:
        """Update task status"""
        pass
```

**Redis Result Backend**:
- **Key Pattern**: `task:result:{task_id}`
- **Data Structure**: Hash with fields:
  - `status`: PENDING, STARTED, SUCCESS, FAILURE, RETRY
  - `result`: Serialized result data
  - `error`: Error message (if failed)
  - `traceback`: Stack trace (if failed)
  - `timestamp`: ISO timestamp
  - `runtime`: Execution time in seconds
- **TTL**: 24 hours (configurable)

**PostgreSQL Result Backend**:
- **Table**: `task_results`
- **Columns**: task_id, status, result, error, traceback, created_at, updated_at
- **Indexes**: task_id (primary), status, created_at
- **Cleanup**: Partitioning by date, retention policy

### 5. Scheduler

**Scheduler Architecture**:
```
Scheduler Process
├── Cron Parser
├── Task Calendar (in-memory + persistent)
├── Due Detector (ticks every second)
├── Task Enqueuer
└── Leader Election (for distributed mode)
```

**Distributed Scheduling**:
- Multiple scheduler instances for HA
- Leader election via Redis distributed lock
- Follower schedulers on standby
- Automatic failover <5s

**Cron Support**:
```python
# Standard cron
@schedule(cron='*/5 * * * *')  # Every 5 minutes
def cleanup_task():
    pass

# Seconds precision
@schedule(cron='0 */2 * * * *')  # Every 2 minutes
def sync_data():
    pass

# Interval syntax
@schedule(interval=timedelta(hours=1))
def hourly_report():
    pass
```

## Task Execution Flow

### Normal Flow

```
[Producer]                      [Broker]                      [Worker]
    |                              |                              |
    |--(1) Create Task------------->|                              |
    |                              |                              |
    |--(2) Enqueue----------------->|                              |
    |                              |                              |
    |                              |<-(3) Dequeue-----------------|
    |                              |                              |
    |                              |<-(4) ACK---------------------|
    |                              |                              |
    |<-(5) Poll for Result---------|                              |
    |                              |<-(6) Store Result------------|
    |                              |                              |
    |<-(7) Get Result--------------|                              |
    |                              |                              |
```

### Retry Flow

```
[Worker]                      [Broker]                      [Retry Logic]
    |                              |                              |
    |--(1) Execute Task------------>|                              |
    |                              |                              |
    |--(2) Task Fails------------->|                              |
    |                              |                              |
    |                              |<-(3) Check Retry Policy------|
    |                              |                              |
    |                              |<-(4) Calculate Backoff-------|
    |                              |                              |
    |                              |<-(5) Schedule Retry----------|
    |                              |                              |
    |                              |                              |--(6) Wait
    |                              |                              |
    |                              |<-(7) Re-enqueue--------------|
    |                              |                              |
    |<-(8) Dequeue-----------------|                              |
    |                              |                              |
    |--(9) Execute Task------------>|                              |
```

## Data Structures

### Task Message

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "process_data",
  "args": [123, [1, 2, 3]],
  "kwargs": {"priority": "high"},
  "options": {
    "queue": "default",
    "priority": 5,
    "retries": 3,
    "timeout": 300,
    "eta": "2025-01-08T12:00:00Z",
    "expires": "2025-01-08T13:00:00Z",
    "retry_delay": 1.0,
    "retry_backoff": true,
    "retry_max_delay": 60.0,
    "retry_jitter": true
  },
  "metadata": {
    "timestamp": "2025-01-08T10:00:00Z",
    "hostname": "worker-1",
    "worker_pid": 12345
  },
  "callbacks": [
    {"name": "on_success", "args": []},
    {"name": "on_failure", "args": []}
  ]
}
```

### Result Object

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "processed": 3
  },
  "error": null,
  "traceback": null,
  "timestamp": "2025-01-08T10:00:01Z",
  "runtime": 0.234,
  "worker": {
    "hostname": "worker-1",
    "pid": 12345
  },
  "retries": 0,
  "retry_count": 0
}
```

## Concurrency Model

### Python (AsyncIO + Multiprocessing)

```
Process 1 (Main)
├── Event Loop (asyncio)
│   ├── Task Fetcher (coroutine)
│   ├── 100 Async Workers (tasks/coroutines)
│   │   ├── Worker 1
│   │   ├── Worker 2
│   │   └── ...
│   ├── Result Handler (coroutine)
│   └── Health Monitor (coroutine)

Process 2-N (Optional CPU-bound)
└── Process Pool Executor
    ├── Worker 1 (process)
    ├── Worker 2 (process)
    └── ...
```

**Concurrency Limits**:
- 100-500 async workers per process (I/O-bound)
- CPU count processes (CPU-bound)
- Prefetch: concurrency * 4 tasks

### Go (Goroutines + Worker Pools)

```
Main Goroutine
├── Worker Pool (1000-10000 goroutines)
│   ├── Worker 1 (goroutine)
│   ├── Worker 2 (goroutine)
│   └── ...
├── Task Fetcher (goroutine)
├── Result Handler (goroutine)
├── Health Monitor (goroutine)
└── Shutdown Handler (goroutine)
```

**Concurrency Limits**:
- 1000-10000 goroutines per process
- Auto-scaling based on queue depth
- GOMAXPROCS = CPU count (default)

## Performance Optimization

### 1. Batching

**Batch Enqueue**:
```python
tasks = [create_task(i) for i in range(1000)]
await queue.enqueue_many(tasks)  # Single Redis pipeline
```

**Batch Result Query**:
```python
results = await backend.get_results(task_ids)  # MGET
```

### 2. Pipelining

**Redis Pipeline**:
```python
async with redis.pipeline() as pipe:
    for task in tasks:
        pipe.enqueue(task)
    await pipe.execute()  # Single round-trip
```

### 3. Prefetching

**Worker Prefetch**:
- Fetch N tasks at once (N = concurrency * prefetch_multiplier)
- Keep local queue
- Reduce broker round-trips
- Balance memory vs. latency

### 4. Connection Pooling

**Redis Connection Pool**:
- Min connections: 10
- Max connections: 100
- Connection timeout: 10s
- Idle timeout: 300s

### 5. Serialization

**MessagePack** (optional):
```python
# Faster than JSON, but not human-readable
queue.serializer = MessagePackSerializer()
```

**Comparison**:
- JSON: 10K ops/sec, readable
- MessagePack: 15K ops/sec, binary
- Pickle: 8K ops/sec, Python-only

## Reliability Features

### 1. At-Least-Once Delivery

**Redis Streams**:
```python
# Consumer group
XGROUP CREATE queue_tasks group1 $ MKSTREAM

# Read with acknowledgement
XREADGROUP GROUP group1 consumer1 STREAMS queue_tasks >

# Acknowledge processing
XACK queue_tasks group1 task_id
```

### 2. Dead Letter Queue

**DLQ Flow**:
```
Task fails → Check retry limit → If exhausted → Move to DLQ
```

**DLQ Structure**:
```python
{
  "original_task": {...},
  "error": "error message",
  "traceback": "...",
  "retries": 3,
  "failed_at": "2025-01-08T10:00:00Z"
}
```

### 3. Graceful Shutdown

**Shutdown Sequence**:
1. Stop accepting new tasks
2. Wait for running tasks to finish (with timeout)
3. Force-kill remaining tasks (timeout exceeded)
4. Close connections
5. Exit process

**Implementation**:
```python
worker = Worker(concurrency=100)
worker.start()

# SIGTERM/SIGINT handler
signal.signal(signal.SIGTERM, worker.shutdown)
signal.signal(signal.SIGINT, worker.shutdown)
```

### 4. Health Monitoring

**Worker Health**:
```python
{
  "hostname": "worker-1",
  "pid": 12345,
  "status": "running",
  "queues": ["default", "high_priority"],
  "concurrency": 100,
  "active_tasks": 45,
  "completed_tasks": 12345,
  "failed_tasks": 12,
  "uptime": 86400,
  "memory_usage": "512MB",
  "cpu_usage": "45%"
}
```

### 5. Distributed Locking

**Task Locking**:
```python
# Prevent duplicate execution
@task(lock=True, lock_timeout=300)
def process_payment(user_id, amount):
    # Only one instance per user_id
    pass
```

**Implementation**:
```python
lock_key = f"task:lock:{task.name}:{args[0]}"
acquired = await redis.set(lock_key, "1", nx=True, ex=timeout)
if not acquired:
    raise TaskLockedError()
```

## Scalability

### Horizontal Scaling

**Worker Scaling**:
- Add more worker processes/machines
- Load balance across workers
- No shared state (except broker)
- Auto-discovery via broker

**Scheduler Scaling**:
- Multiple scheduler instances
- Leader election for active scheduler
- Failover to standby scheduler

### Vertical Scaling

**Worker Optimization**:
- Increase concurrency (more workers)
- Increase prefetch (more tasks in memory)
- Batch operations (reduce round-trips)
- Optimize serialization

### Queue Sharding

**Multi-Queue Strategy**:
```
Queue per task type:
- email_queue
- notification_queue
- processing_queue
- reporting_queue

Worker per queue:
- worker-1 (email_queue)
- worker-2 (notification_queue)
- worker-3 (processing_queue)
- worker-4 (reporting_queue)
```

## Monitoring & Observability

### Metrics

**System Metrics**:
- Task throughput (tasks/sec)
- Task latency (p50, p95, p99)
- Queue depth
- Worker utilization
- Error rate
- Retry rate

**Business Metrics**:
- Tasks by type
- Tasks by status
- Tasks by queue
- Runtime distribution
- Failure reasons

### Distributed Tracing

**OpenTelemetry Integration**:
```python
from opentelemetry import trace

@task
def process_order(order_id):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("process_order"):
        # Task implementation
        pass
```

**Trace Context**:
- Task ID (span)
- Parent span ID (caller)
- Trace ID (end-to-end)

### Logging

**Structured Logging**:
```python
logger.info(
    "Task started",
    extra={
        "task_id": task.id,
        "task_name": task.name,
        "worker": worker.hostname,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

**Log Format** (JSON):
```json
{
  "level": "INFO",
  "message": "Task started",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "process_order",
  "worker": "worker-1",
  "timestamp": "2025-01-08T10:00:00Z"
}
```

## Security Considerations

### 1. Task Validation

**Input Validation**:
- Validate task arguments
- Sanitize user input
- Limit argument size
- Type checking

### 2. Serialization Security

**Safe Serialization**:
- Prefer JSON (safe but limited)
- Avoid Pickle (Python code execution)
- Validate MessagePack types
- Sandbox custom serializers

### 3. Broker Security

**Connection Security**:
- TLS/SSL encryption
- SASL authentication
- ACL for queue access
- Network isolation (VPC)

### 4. Task Authentication

**Task Signing**:
```python
# HMAC signature
signature = hmac_sha256(task_data, secret_key)
task["signature"] = signature

# Worker validation
if not verify_signature(task, secret_key):
    raise InvalidTaskError()
```

## Deployment Architecture

### Development
```
Single machine:
- Redis (Docker)
- Worker process
- Application
```

### Production
```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
└─────────────┬───────────────────────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼────┐        ┌────▼───┐
│ App 1  │        │  App 2 │
└───┬────┘        └────┬───┘
    │                  │
    └─────────┬────────┘
              │
    ┌─────────▼─────────┐
    │   Redis Cluster   │
    │   (3 masters)     │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────────────────┐
    │                               │
┌───▼────┐  ┌────┬───┐  ┌────────▼─┐
│Worker 1│  │Wkr 2│  │  │Worker N  │
└────────┘  └────┘   │  └──────────┘
                      │
              ┌───────▼────────┐
              │  Result DB     │
              │  (PostgreSQL)  │
              └────────────────┘
```

---

**Last Updated**: 2025-01-08
**Document Version**: 1.0
