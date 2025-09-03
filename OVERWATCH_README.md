# Overwatch System - Task Generation and Dispatch

The Overwatch System is a comprehensive task generation and dispatch framework that can automatically create, schedule, and execute tasks based on system conditions and user requirements.

## 🌟 Features

- **Dynamic Task Generation**: Automatically generates tasks based on system state and conditions
- **Priority-Based Scheduling**: Tasks are executed based on priority levels (Critical, High, Normal, Low, Background)
- **Multi-threaded Dispatch**: Concurrent execution of multiple tasks with resource management
- **Health Monitoring Integration**: Real-time monitoring with automatic alert generation
- **Resource-Aware Execution**: Considers CPU, memory, and I/O requirements
- **Failure Recovery**: Automatic retry mechanisms with configurable policies
- **REST API**: Complete HTTP API for remote management and monitoring
- **CLI Interface**: Command-line tools for system administration

## 🏗️ Architecture

The Overwatch System consists of several key components:

### Core Components

1. **OverwatchSystem**: Main coordinator that manages all subsystems
2. **TaskScheduler**: Priority-based task queue with concurrent execution
3. **TaskGenerator**: Dynamic task creation based on rules and conditions
4. **TaskDispatcher**: Routes tasks to appropriate subsystems
5. **TaskHandlers**: Specialized handlers for different task types

### Task Types

- `SYSTEM_HEALTH`: System health checks and diagnostics
- `OBD2_DIAGNOSTIC`: OBD2 vehicle diagnostic scans
- `PERFORMANCE_CHECK`: Performance monitoring and analysis
- `DATA_BACKUP`: Data backup and archival operations
- `MAINTENANCE`: System maintenance and cleanup
- `SECURITY_SCAN`: Security vulnerability scanning
- `USER_TASK`: User-defined custom tasks

### Priority Levels

- `CRITICAL` (0): Emergency tasks that must run immediately
- `HIGH` (1): Important tasks with elevated priority
- `NORMAL` (2): Standard tasks with default priority
- `LOW` (3): Background tasks with lower priority
- `BACKGROUND` (4): Lowest priority maintenance tasks

## 🚀 Quick Start

### Using the CLI

1. **Start the Overwatch System**:
   ```bash
   python overwatch_cli.py start --daemon --enable-monitoring
   ```

2. **Check system status**:
   ```bash
   python overwatch_cli.py status
   ```

3. **Create a task**:
   ```bash
   python overwatch_cli.py create-task "System Health Check" --type system_health --priority high
   ```

4. **List recent tasks**:
   ```bash
   python overwatch_cli.py list-tasks --limit 10
   ```

5. **Run system tests**:
   ```bash
   python overwatch_cli.py test
   ```

### Using the Python API

```python
import asyncio
from src.ballsdeepnit.core.overwatch import get_overwatch, TaskType, TaskPriority
from src.ballsdeepnit.core.overwatch_handlers import register_all_handlers

async def main():
    # Get overwatch instance
    overwatch = get_overwatch()
    
    # Register task handlers
    register_all_handlers(overwatch)
    
    # Start the system
    await overwatch.start()
    
    # Create a task
    task = overwatch.create_task(
        name="My Custom Task",
        description="A test task",
        task_type=TaskType.SYSTEM_HEALTH,
        priority=TaskPriority.HIGH
    )
    
    print(f"Created task: {task.id}")
    
    # Wait a bit and check status
    await asyncio.sleep(5)
    status = overwatch.get_status()
    print(f"System status: {status}")
    
    # Stop the system
    overwatch.stop()

asyncio.run(main())
```

### Using the REST API

Start the dashboard to access the REST API:

```bash
python start_dashboard.py
```

Then use the API endpoints:

- `GET /api/overwatch/status` - Get system status
- `POST /api/overwatch/start` - Start the overwatch system
- `POST /api/overwatch/stop` - Stop the overwatch system
- `POST /api/overwatch/tasks` - Create a new task
- `GET /api/overwatch/tasks` - List tasks
- `GET /api/overwatch/stats` - Get task statistics

Example API usage:

```bash
# Get system status
curl http://localhost:8765/api/overwatch/status

# Create a health check task
curl -X POST http://localhost:8765/api/overwatch/tasks/health-check

# List recent tasks
curl http://localhost:8765/api/overwatch/tasks?limit=10
```

## 📊 Monitoring Integration

The Overwatch System integrates with existing monitoring infrastructure to provide:

- **Automatic Health Checks**: Regular system health monitoring
- **Performance Alerts**: Alerts when system resources exceed thresholds
- **Task Performance Monitoring**: Tracking task execution metrics
- **Alert Management**: Centralized alert handling and history

### Monitoring Thresholds

Default thresholds can be configured:

- CPU Usage: 80% (warning), 95% (critical)
- Memory Usage: 85% (warning), 95% (critical)
- Disk Usage: 90% (warning), 95% (critical)

## 🔧 Configuration

### Environment Variables

- `OVERWATCH_MAX_CONCURRENT_TASKS`: Maximum concurrent tasks (default: 10)
- `OVERWATCH_GENERATION_INTERVAL`: Task generation interval in seconds (default: 60)
- `OVERWATCH_LOG_LEVEL`: Logging level (default: INFO)

### Task Generation Rules

You can add custom task generation rules:

```python
def my_custom_rule():
    """Generate custom tasks based on business logic."""
    tasks = []
    
    # Your custom logic here
    if some_condition():
        task = Task(
            name="Custom Task",
            task_type=TaskType.CUSTOM,
            priority=TaskPriority.NORMAL
        )
        tasks.append(task)
    
    return tasks

# Register the rule
overwatch.add_task_generation_rule(my_custom_rule)
```

## 🛠️ Creating Custom Task Handlers

To create a custom task handler:

```python
from src.ballsdeepnit.core.overwatch import TaskHandler, Task, TaskResult, TaskStatus

class MyCustomHandler(TaskHandler):
    async def execute(self, task: Task) -> TaskResult:
        """Execute the custom task."""
        start_time = datetime.now()
        
        try:
            # Your custom task logic here
            result_data = {"message": "Task completed successfully"}
            
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result_data=result_data,
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now()
            )
        except Exception as e:
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now()
            )
    
    def can_handle(self, task: Task) -> bool:
        """Check if this handler can process the task."""
        return task.task_type == TaskType.CUSTOM

# Register the handler
overwatch.register_task_handler(TaskType.CUSTOM, MyCustomHandler())
```

## 📈 Performance Optimization

### Resource Management

Tasks can specify resource requirements:

```python
task = Task(
    name="Resource Intensive Task",
    cpu_requirement=0.5,      # 50% CPU
    memory_requirement=512,   # 512 MB RAM
    io_requirement=0.3        # 30% I/O capacity
)
```

### Execution Tuning

- Adjust `max_concurrent_tasks` based on system capacity
- Use appropriate priority levels to ensure critical tasks run first
- Set reasonable retry policies for failed tasks
- Monitor execution times and optimize slow handlers

## 🔍 Troubleshooting

### Common Issues

1. **Tasks not executing**:
   - Check if the overwatch system is running
   - Verify task handlers are registered
   - Check task queue size and running tasks

2. **High resource usage**:
   - Reduce `max_concurrent_tasks`
   - Check for memory leaks in custom handlers
   - Monitor task execution times

3. **Failed tasks**:
   - Check task handler logs
   - Verify task requirements and dependencies
   - Review retry configuration

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger('src.ballsdeepnit.core.overwatch').setLevel(logging.DEBUG)
```

View task execution details:

```bash
python overwatch_cli.py status --json
```

## 🤝 Contributing

To contribute to the Overwatch System:

1. Create custom task handlers for new task types
2. Add monitoring integrations for additional metrics
3. Implement new task generation rules
4. Improve error handling and recovery mechanisms
5. Add performance optimizations

## 📚 API Reference

### Core Classes

- **OverwatchSystem**: Main system coordinator
- **TaskScheduler**: Task queue and execution manager
- **TaskGenerator**: Dynamic task creation engine
- **TaskDispatcher**: Task routing and execution
- **Task**: Individual task representation
- **TaskResult**: Task execution results

### Task Handlers

- **SystemHealthTaskHandler**: System health monitoring
- **OBD2DiagnosticHandler**: OBD2 vehicle diagnostics
- **PerformanceCheckHandler**: Performance analysis
- **DataBackupHandler**: Data backup operations
- **MaintenanceHandler**: System maintenance
- **SecurityScanHandler**: Security vulnerability scanning

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/overwatch/status` | Get system status |
| POST | `/api/overwatch/start` | Start overwatch system |
| POST | `/api/overwatch/stop` | Stop overwatch system |
| POST | `/api/overwatch/tasks` | Create new task |
| GET | `/api/overwatch/tasks` | List tasks |
| GET | `/api/overwatch/tasks/{id}` | Get specific task |
| GET | `/api/overwatch/stats` | Get task statistics |
| POST | `/api/overwatch/tasks/generate` | Trigger task generation |
| GET | `/api/overwatch/config` | Get configuration |
| PUT | `/api/overwatch/config` | Update configuration |

## 📄 License

This project is part of the ballsDeepnit system and follows the same licensing terms.

---

**The Overwatch System**: *Keeping watch over your systems so you don't have to.*