# Task Queue - API Reference

## Table of Contents

1. [Python API](#python-api)
2. [Go API](#go-api)
3. [REST API](#rest-api)
4. [Configuration](#configuration)

---

## Python API

### TaskQueue Class

Main class for task queue management.

```python
from taskqueue import TaskQueue

queue = TaskQueue(
    broker: str = 'redis://localhost:6379/0',
    result_backend: str = None,
    serializer: str = 'json',
    compression: str = None,
    default_queue: str = 'default',
    default_priority: int = 5,
    default_timeout: int = 300,
    default_retries: int = 3
)
```

**Parameters**:
- `broker` (str): Broker connection URL
  - Redis: `redis://localhost:6379/0`
  - RabbitMQ: `amqp://guest:guest@localhost:5672/`
- `result_backend` (str): Result backend URL (optional)
- `serializer` (str): Serialization format (`json`, `msgpack`, `pickle`)
- `compression` (str): Compression algorithm (`gzip`, `bz2`, `lzma`)
- `default_queue` (str): Default queue name
- `default_priority` (int): Default priority (0-10)
- `default_timeout` (int): Default task timeout (seconds)
- `default_retries` (int): Default retry count

**Methods**:

##### `task decorator`
Register a task function.

```python
@queue.task(
    name: str = None,
    queue: str = None,
    priority: int = None,
    timeout: int = None,
    retries: int = None,
    retry_backoff: bool = False,
    retry_delay: float = None,
    retry_max_delay: float = None,
    retry_jitter: bool = False
)
def task_function(*args, **kwargs):
    pass
```

**Example**:
```python
@queue.task(retries=3, timeout=60)
def process_data(data):
    return {"result": len(data)}
```

##### `enqueue`
Manually enqueue a task.

```python
async def queue.enqueue(
    task_name: str,
    *args,
    **kwargs
) -> str
```

**Parameters**:
- `task_name` (str): Task function name
- `args`: Task positional arguments
- `kwargs`: Task keyword arguments

**Returns**: Task ID (str)

**Example**:
```python
task_id = await queue.enqueue('process_data', [1, 2, 3])
```

### Task Class

Represents an asynchronous task.

```python
from taskqueue import Task

task = Task(
    id: str,
    name: str,
    args: List[Any],
    kwargs: Dict[str, Any],
    options: Dict[str, Any]
)
```

**Methods**:

##### `delay`
Execute task asynchronously.

```python
task = task_function.delay(*args, **kwargs)
```

**Returns**: `AsyncResult` instance

##### `apply_async`
Execute task with options.

```python
task = task_function.apply_async(
    args: List[Any] = None,
    kwargs: Dict[str, Any] = None,
    queue: str = None,
    priority: int = None,
    timeout: int = None,
    retries: int = None,
    eta: datetime = None,
    countdown: int = None,
    expires: datetime = None
)
```

**Parameters**:
- `args`: Positional arguments
- `kwargs`: Keyword arguments
- `queue`: Target queue name
- `priority`: Task priority (0-10)
- `timeout`: Task timeout (seconds)
- `retries`: Maximum retry count
- `eta`: Scheduled execution time
- `countdown`: Delay before execution (seconds)
- `expires`: Task expiration time

**Returns**: `AsyncResult` instance

**Example**:
```python
from datetime import datetime, timedelta

task = process_data.apply_async(
    args=[[1, 2, 3]],
    queue='high_priority',
    priority=0,
    eta=datetime.now() + timedelta(minutes=5)
)
```

##### `apply`
Execute task synchronously (blocking).

```python
result = task_function.apply(*args, **kwargs)
```

**Returns**: Task result

### AsyncResult Class

Represents the result of an asynchronous task.

```python
from taskqueue import AsyncResult

result = AsyncResult(
    task_id: str,
    backend: ResultBackend = None
)
```

**Methods**:

##### `get`
Wait for and return result.

```python
result = async_result.get(timeout: int = None, interval: float = 0.5)
```

**Parameters**:
- `timeout` (int): Maximum wait time (seconds)
- `interval` (float): Poll interval (seconds)

**Returns**: Task result

**Raises**: `TimeoutError` if timeout exceeded

**Example**:
```python
try:
    result = task.get(timeout=10)
    print(result)
except TimeoutError:
    print("Task timed out")
```

##### `ready`
Check if task is complete.

```python
is_ready = async_result.ready()
```

**Returns**: `bool`

##### `successful`
Check if task succeeded.

```python
is_successful = async_result.successful()
```

**Returns**: `bool`

##### `failed`
Check if task failed.

```python
is_failed = async_result.failed()
```

**Returns**: `bool`

##### `status`
Get task status.

```python
status = async_result.status
```

**Returns**: `str` (`PENDING`, `STARTED`, `SUCCESS`, `FAILURE`, `RETRY`)

##### `info`
Get task information.

```python
info = async_result.info
```

**Returns**: `dict` with keys:
- `task_id`: Task ID
- `status`: Task status
- `result`: Task result (if successful)
- `error`: Error message (if failed)
- `timestamp`: Completion timestamp

##### `revoke`
Cancel task execution.

```python
async_result.revoke(terminate: bool = False, signal: str = 'SIGTERM')
```

**Parameters**:
- `terminate` (bool): Force-kill task
- `signal` (str): Signal to send (`SIGTERM`, `SIGKILL`)

### Worker Class

Worker process for executing tasks.

```python
from taskqueue import Worker

worker = Worker(
    queues: List[str] = ['default'],
    broker: str = 'redis://localhost:6379/0',
    concurrency: int = 100,
    prefetch_multiplier: int = 4,
    task_time_limit: int = None,
    task_soft_time_limit: int = None,
    max_tasks_per_child: int = None,
    enable_remote_control: bool = True
)
```

**Parameters**:
- `queues` (List[str]): List of queue names to process
- `broker` (str): Broker connection URL
- `concurrency` (int): Number of concurrent workers
- `prefetch_multiplier` (int): Prefetch multiplier
- `task_time_limit` (int): Hard time limit (seconds)
- `task_soft_time_limit` (int): Soft time limit (seconds)
- `max_tasks_per_child` (int): Max tasks before worker restart
- `enable_remote_control` (bool): Enable remote control commands

**Methods**:

##### `start`
Start worker process.

```python
worker.start()
```

##### `stop`
Stop worker gracefully.

```python
worker.start()
```

##### `register`
Register task function.

```python
worker.register(task_name: str, task_func: Callable)
```

**Example**:
```python
def my_task(x, y):
    return x + y

worker.register('my_task', my_task)
worker.start()
```

### Chain Class

Execute tasks sequentially.

```python
from taskqueue import chain

workflow = chain(*tasks)
```

**Methods**:

##### `apply_async`
Execute chain asynchronously.

```python
result = chain.apply_async(queue: str = None)
```

**Example**:
```python
from taskqueue import chain

workflow = chain(
    add.s(2, 2),           # Result: 4
    multiply.s(4),         # Result: 16
    subtract.s(10)         # Result: 6
)

result = workflow.apply_async()
final_result = result.get()
```

### Group Class

Execute tasks in parallel.

```python
from taskqueue import group

job = group(*tasks)
```

**Methods**:

##### `apply_async`
Execute group asynchronously.

```python
result = group.apply_async(queue: str = None)
```

**Example**:
```python
from taskqueue import group

job = group([
    process_user.s(user_id) for user_id in range(100)
])

result = job.apply_async()
results = result.get()  # List of 100 results
```

### Chord Class

Group with callback.

```python
from taskqueue import chord

workflow = chord(header, callback)
```

**Methods**:

##### `apply_async`
Execute chord asynchronously.

```python
result = chord.apply_async(queue: str = None)
```

**Example**:
```python
from taskqueue import chord

header = [process_data.s(i) for i in range(100)]
callback = summarize_results.s()

chord_task = chord(header)(callback)
result = chord_task.apply_async()
final_result = result.get()
```

---

## Go API

### Queue Package

#### NewQueue

Create a new task queue.

```go
package taskqueue

queue := NewQueue(
    name string,
    broker string,
    opts ...QueueOption,
)
```

**Parameters**:
- `name` (string): Queue name
- `broker` (string): Broker URL
- `opts`: Queue options

**Options**:
```go
// WithSerializer sets serializer
func WithSerializer(serializer string) QueueOption

// WithCompression sets compression
func WithCompression(compression string) QueueOption

// WithDefaultPriority sets default priority
func WithDefaultPriority(priority int) QueueOption

// WithDefaultTimeout sets default timeout
func WithDefaultTimeout(timeout time.Duration) QueueOption

// WithDefaultRetries sets default retry count
func WithDefaultRetries(retries int) QueueOption
```

**Example**:
```go
queue := taskqueue.NewQueue(
    "default",
    "redis://localhost:6379/0",
    taskqueue.WithDefaultPriority(5),
    taskqueue.WithDefaultTimeout(300*time.Second),
)
```

#### Enqueue

Enqueue a task.

```go
task, err := queue.Enqueue(
    name string,
    args ...interface{},
    opts ...EnqueueOption,
)
```

**Options**:
```go
// WithQueue sets target queue
func WithQueue(queue string) EnqueueOption

// WithPriority sets task priority
func WithPriority(priority int) EnqueueOption

// WithTimeout sets task timeout
func WithTimeout(timeout time.Duration) EnqueueOption

// WithRetries sets retry count
func WithRetries(retries int) EnqueueOption

// WithETA sets scheduled execution time
func WithETA(eta time.Time) EnqueueOption

// WithCountdown sets delay before execution
func WithCountdown(countdown time.Duration) EnqueueOption

// WithExpires sets expiration time
func WithExpires(expires time.Time) EnqueueOption

// WithRetryBackoff enables exponential backoff
func WithRetryBackoff(enabled bool) EnqueueOption

// WithRetryDelay sets initial retry delay
func WithRetryDelay(delay time.Duration) EnqueueOption

// WithRetryMaxDelay sets max retry delay
func WithRetryMaxDelay(delay time.Duration) EnqueueOption

// WithRetryJitter enables retry jitter
func WithRetryJitter(enabled bool) EnqueueOption
```

**Example**:
```go
task, err := queue.Enqueue(
    "process_data",
    []int{1, 2, 3},
    taskqueue.WithQueue("high_priority"),
    taskqueue.WithPriority(0),
    taskqueue.WithRetries(3),
)
```

#### EnqueueAt

Schedule task for specific time.

```go
task, err := queue.EnqueueAt(
    name string,
    eta time.Time,
    args ...interface{},
)
```

**Example**:
```go
eta := time.Date(2025, 1, 8, 12, 0, 0, 0, time.UTC)
task, err := queue.EnqueueAt("process_data", eta, data)
```

#### EnqueueIn

Schedule task with delay.

```go
task, err := queue.EnqueueIn(
    name string,
    delay time.Duration,
    args ...interface{},
)
```

**Example**:
```go
task, err := queue.EnqueueIn("process_data", 5*time.Minute, data)
```

### Task Package

#### Task Type

Represents a task.

```go
type Task struct {
    ID        string
    Name      string
    Args      []interface{}
    Kwargs    map[string]interface{}
    Options   TaskOptions
}
```

#### Get

Wait for and return result.

```go
result, err := task.Get(ctx context.Context)
```

**Parameters**:
- `ctx` (context.Context): Context with timeout

**Returns**: Task result (interface{})

**Example**:
```go
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()

result, err := task.Get(ctx)
if err != nil {
    log.Printf("Task failed: %v", err)
}
fmt.Println(result)
```

#### Ready

Check if task is complete.

```go
ready := task.Ready()
```

**Returns**: bool

#### Status

Get task status.

```go
status := task.Status()
```

**Returns**: string (`PENDING`, `STARTED`, `SUCCESS`, `FAILURE`, `RETRY`)

#### Info

Get task information.

```go
info := task.Info()
```

**Returns**: TaskInfo struct

```go
type TaskInfo struct {
    ID        string
    Name      string
    Status    string
    Result    interface{}
    Error     string
    Timestamp time.Time
    Runtime   float64
}
```

#### Revoke

Cancel task.

```go
err := task.Revoke(terminate bool)
```

### Worker Package

#### NewWorker

Create a new worker.

```go
worker := NewWorker(opts ...WorkerOption)
```

**Options**:
```go
// WithBroker sets broker URL
func WithBroker(broker string) WorkerOption

// WithQueues sets queue names
func WithQueues(queues ...string) WorkerOption

// WithConcurrency sets worker concurrency
func WithConcurrency(concurrency int) WorkerOption

// WithPrefetch sets prefetch multiplier
func WithPrefetch(prefetch int) WorkerOption

// WithTaskTimeLimit sets hard time limit
func WithTaskTimeLimit(limit time.Duration) WorkerOption

// WithTaskSoftTimeLimit sets soft time limit
func WithTaskSoftTimeLimit(limit time.Duration) WorkerOption
```

**Example**:
```go
worker := taskqueue.NewWorker(
    taskqueue.WithBroker("redis://localhost:6379/0"),
    taskqueue.WithQueues("default", "high_priority"),
    taskqueue.WithConcurrency(1000),
    taskqueue.WithPrefetch(4),
)
```

#### Register

Register task function.

```go
worker.Register(name string, handler TaskHandler)
```

**TaskHandler signature**:
```go
type TaskHandler func(ctx context.Context, args ...interface{}) (interface{}, error)
```

**Example**:
```go
func add(ctx context.Context, x, y int) (interface{}, error) {
    return x + y, nil
}

func processUser(ctx context.Context, userID int) (interface{}, error) {
    // Process user
    return map[string]interface{}{
        "user_id": userID,
        "status":  "processed",
    }, nil
}

func main() {
    worker := taskqueue.NewWorker(
        taskqueue.WithQueues("default"),
    )

    worker.Register("add", add)
    worker.Register("processUser", processUser)

    worker.Start(context.Background())
}
```

#### Start

Start worker.

```go
err := worker.Start(ctx context.Context)
```

#### Stop

Stop worker gracefully.

```go
err := worker.Stop(ctx context.Background())
```

#### Stats

Get worker statistics.

```go
stats := worker.Stats()
```

**Returns**: WorkerStats struct

```go
type WorkerStats struct {
    Total      int64
    Succeeded  int64
    Failed     int64
    Retried    int64
    Runtime    float64
    Uptime     float64
    Memory     uint64
    CPU        float64
}
```

### Chain Package

Execute tasks sequentially.

```go
package taskqueue

chain := NewChain(tasks ...*Task)
```

**Example**:
```go
chain := taskqueue.NewChain(
    taskqueue.NewTask("add", 2, 2),
    taskqueue.NewTask("multiply", 4),
    taskqueue.NewTask("subtract", 10),
)

result, err := chain.Execute(context.Background())
fmt.Println(result)  // 6
```

### Group Package

Execute tasks in parallel.

```go
package taskqueue

group := NewGroup(tasks ...*Task)
```

**Example**:
```go
var tasks []*taskqueue.Task
for i := 0; i < 100; i++ {
    tasks = append(tasks, taskqueue.NewTask("processUser", i))
}

group := taskqueue.NewGroup(tasks...)
results, err := group.Execute(context.Background())
fmt.Println(len(results))  // 100
```

### Chord Package

Group with callback.

```go
package taskqueue

chord := NewChord(tasks []*Task, callback *Task)
```

**Example**:
```go
var tasks []*taskqueue.Task
for i := 0; i < 100; i++ {
    tasks = append(tasks, taskqueue.NewTask("processData", i))
}

callback := taskqueue.NewTask("summarizeResults")
chord := taskqueue.NewChord(tasks, callback)

result, err := chord.Execute(context.Background())
```

---

## REST API

The task-queue library provides an optional REST API for monitoring and management.

### Start REST Server

**Python**:
```bash
python -m taskqueue api --host=0.0.0.0 --port=8000
```

**Go**:
```bash
tq-api --host=0.0.0.0 --port=8000
```

### Endpoints

#### GET /api/v1/health

Check API health.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-08T10:00:00Z"
}
```

#### GET /api/v1/workers

List all workers.

**Response**:
```json
{
  "workers": [
    {
      "hostname": "worker-1",
      "pid": 12345,
      "status": "running",
      "queues": ["default", "high_priority"],
      "concurrency": 100,
      "active_tasks": 45,
      "completed_tasks": 12345,
      "failed_tasks": 12
    }
  ]
}
```

#### GET /api/v1/workers/{hostname}

Get worker details.

**Response**:
```json
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

#### GET /api/v1/queues

List all queues.

**Response**:
```json
{
  "queues": [
    {
      "name": "default",
      "length": 1000,
      "waiting": 950,
      "active": 50
    },
    {
      "name": "high_priority",
      "length": 100,
      "waiting": 80,
      "active": 20
    }
  ]
}
```

#### GET /api/v1/queues/{name}

Get queue details.

**Response**:
```json
{
  "name": "default",
  "length": 1000,
  "waiting": 950,
  "active": 50,
  "stats": {
    "total_tasks": 50000,
    "succeeded": 45000,
    "failed": 5000,
    "avg_runtime": 0.234
  }
}
```

#### POST /api/v1/tasks

Enqueue a task.

**Request**:
```json
{
  "name": "process_data",
  "args": [1, 2, 3],
  "kwargs": {},
  "options": {
    "queue": "default",
    "priority": 5,
    "retries": 3,
    "timeout": 300
  }
}
```

**Response**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING"
}
```

#### GET /api/v1/tasks/{task_id}

Get task status.

**Response**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "result": {
    "sum": 6
  },
  "timestamp": "2025-01-08T10:00:01Z"
}
```

#### DELETE /api/v1/tasks/{task_id}

Cancel a task.

**Response**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "REVOKED"
}
```

#### GET /api/v1/tasks/{task_id}/result

Get task result.

**Response**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "result": {
    "sum": 6
  },
  "error": null,
  "traceback": null,
  "timestamp": "2025-01-08T10:00:01Z",
  "runtime": 0.234
}
```

#### GET /api/v1/scheduled

List scheduled tasks.

**Response**:
```json
{
  "scheduled_tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "daily_report",
      "eta": "2025-01-08T12:00:00Z"
    }
  ]
}
```

#### GET /api/v1/stats

Get system statistics.

**Response**:
```json
{
  "throughput": 10000.5,
  "latency": {
    "p50": 50,
    "p95": 95,
    "p99": 120
  },
  "tasks": {
    "total": 500000,
    "succeeded": 450000,
    "failed": 50000,
    "retried": 10000
  },
  "workers": {
    "total": 10,
    "active": 10,
    "offline": 0
  }
}
```

---

## Configuration

### Python Configuration

**Environment Variables**:
```bash
export TASKQUEUE_BROKER_URL="redis://localhost:6379/0"
export TASKQUEUE_RESULT_BACKEND="redis://localhost:6379/1"
export TASKQUEUE_DEFAULT_QUEUE="default"
export TASKQUEUE_DEFAULT_PRIORITY="5"
export TASKQUEUE_DEFAULT_TIMEOUT="300"
export TASKQUEUE_DEFAULT_RETRIES="3"
export TASKQUEUE_SERIALIZER="json"
export TASKQUEUE_COMPRESSION="gzip"
```

**Config File (taskqueue.yaml)**:
```yaml
broker:
  url: "redis://localhost:6379/0"
  type: "redis"
  connection_pool_size: 50

result_backend:
  url: "redis://localhost:6379/1"
  type: "redis"
  ttl: 86400

worker:
  concurrency: 100
  prefetch_multiplier: 4
  task_time_limit: 300
  task_soft_time_limit: 240
  max_tasks_per_child: 1000

task:
  default_queue: "default"
  default_priority: 5
  default_timeout: 300
  default_retries: 3
  retry_backoff: true
  retry_delay: 1.0
  retry_max_delay: 60.0
  retry_jitter: true

logging:
  level: "INFO"
  format: "json"
  file: "/var/log/taskqueue/worker.log"
```

**Usage**:
```python
from taskqueue import load_config

config = load_config('taskqueue.yaml')
queue = TaskQueue(**config.broker)
worker = Worker(**config.worker)
```

### Go Configuration

**Environment Variables**:
```bash
export TASKQUEUE_BROKER_URL="redis://localhost:6379/0"
export TASKQUEUE_RESULT_BACKEND="redis://localhost:6379/1"
export TASKQUEUE_DEFAULT_QUEUE="default"
export TASKQUEUE_CONCURRENCY="1000"
export TASKQUEUE_PREFETCH="4"
```

**Config File (config.yaml)**:
```yaml
broker:
  url: "redis://localhost:6379/0"
  type: "redis"
  connection_pool_size: 50

result_backend:
  url: "redis://localhost:6379/1"
  type: "redis"
  ttl: 86400

worker:
  queues:
    - "default"
    - "high_priority"
  concurrency: 1000
  prefetch: 4
  task_time_limit: 300
  task_soft_time_limit: 240

task:
  default_queue: "default"
  default_priority: 5
  default_timeout: 300
  default_retries: 3
  retry_backoff: true
  retry_delay: 1.0
  retry_max_delay: 60.0
  retry_jitter: true

logging:
  level: "info"
  format: "json"
  output: "/var/log/taskqueue/worker.log"
```

**Usage**:
```go
import (
    "github.com/task-queue/go/taskqueue"
    "gopkg.in/yaml.v3"
)

config := taskqueue.LoadConfig("config.yaml")
worker := taskqueue.NewWorker(
    taskqueue.WithBroker(config.Broker.URL),
    taskqueue.WithQueues(config.Worker.Queues...),
    taskqueue.WithConcurrency(config.Worker.Concurrency),
)
```

---

**Last Updated**: 2025-01-08
**Document Version**: 1.0
