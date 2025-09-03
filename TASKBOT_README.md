# TaskBot System

A comprehensive task bot system that can assign and manage tasks for users and other bots. Built on top of the existing overwatch infrastructure with intelligent task assignment, bot management, and real-time monitoring capabilities.

## 🚀 Features

### Core Capabilities
- **Bot Registration & Management**: Register bots with specific capabilities and manage their lifecycle
- **Intelligent Task Assignment**: Multiple assignment strategies based on bot capabilities, load, and priorities
- **Real-time Monitoring**: Live system status, bot health monitoring, and performance metrics
- **Multi-bot Coordination**: Coordinate tasks across multiple bots with different specializations
- **REST API**: Complete HTTP API for integration with other systems
- **Web Dashboard**: Modern, responsive web interface for system management
- **CLI Interface**: Command-line tools for scripting and automation
- **Event System**: Real-time event notifications for system changes

### Assignment Strategies
- **Best Fit**: Assign tasks to bots with the highest capability scores
- **Load Balanced**: Distribute tasks evenly across available bots
- **Round Robin**: Simple round-robin task distribution
- **Priority First**: Prioritize bots that prefer specific task priorities

### Bot Types
- **System**: System administration and maintenance bots
- **Worker**: General-purpose task processing bots
- **Monitor**: Monitoring and alerting bots
- **Specialist**: Specialized bots for specific task types
- **Assistant**: General assistant bots for various tasks
- **User**: User-operated bots

## 📋 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Dashboard │    │   REST API      │    │   CLI Interface │
│   (HTML/JS)     │    │   (FastAPI)     │    │   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   TaskBot Core  │
                    │   - Assignment  │
                    │   - Monitoring  │
                    │   - Statistics  │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Overwatch System│
                    │ - Task Management│
                    │ - Health Checks │
                    │ - Task Execution│
                    └─────────────────┘
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- FastAPI and dependencies
- Modern web browser (for dashboard)

### Installation
1. Install dependencies:
```bash
pip install fastapi uvicorn pydantic
```

2. The TaskBot system is built into the existing ballsdeepnit infrastructure, so ensure the core system is set up properly.

## 🚀 Quick Start

### 1. Running the Demo
The fastest way to see TaskBot in action:

```bash
python task_bot_demo.py
```

This will:
- Initialize the TaskBot system
- Register 5 demo bots with different capabilities
- Create 8 demo tasks of various types
- Demonstrate intelligent task assignment
- Show real-time system monitoring
- Display comprehensive results

### 2. Starting the Web Dashboard
Run the web interface:

```bash
python -m src.ballsdeepnit.dashboard.task_bot_api
```

Then open `task_bot_dashboard.html` in your browser and set the API base URL to `http://localhost:8001/api/taskbot`.

### 3. Using the CLI
Basic CLI commands:

```bash
# Register a bot
python task_bot_cli.py register-bot "MyBot" --bot-type worker --capabilities "coding:custom,system_health"

# List all bots
python task_bot_cli.py list-bots

# Create a task
python task_bot_cli.py create-task "Health Check" --task-type system_health --priority high

# Check system status
python task_bot_cli.py status

# View system health
python task_bot_cli.py health
```

## 📖 Usage Guide

### Bot Registration

#### Programmatic Registration
```python
from src.ballsdeepnit.core.task_bot import Bot, BotType, BotCapability, TaskType

# Create a bot with capabilities
bot = Bot(
    name="Data Processing Bot",
    bot_type=BotType.WORKER,
    capabilities=[
        BotCapability(
            name="Data Backup",
            description="Handles data backup operations",
            task_types=[TaskType.DATA_BACKUP],
            priority_boost=10
        )
    ],
    max_concurrent_tasks=3
)

# Register with TaskBot
task_bot = get_task_bot()
success = task_bot.register_bot(bot)
```

#### CLI Registration
```bash
python task_bot_cli.py register-bot "DataBot" \
    --bot-type worker \
    --max-concurrent 3 \
    --capabilities "backup:data_backup:10" "health:system_health:5"
```

#### REST API Registration
```bash
curl -X POST "http://localhost:8001/api/taskbot/bots/register" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "DataBot",
       "bot_type": "worker",
       "max_concurrent_tasks": 3,
       "capabilities": [
         {
           "name": "backup",
           "description": "Data backup capability",
           "task_types": ["data_backup"],
           "priority_boost": 10
         }
       ]
     }'
```

### Task Creation

#### Programmatic Creation
```python
from src.ballsdeepnit.core.overwatch import Task, TaskType, TaskPriority, TaskContext

# Create a task
task = Task(
    name="System Health Check",
    description="Perform comprehensive health diagnostics",
    task_type=TaskType.SYSTEM_HEALTH,
    priority=TaskPriority.HIGH,
    context=TaskContext(subsystem="health_monitor")
)

# Queue for assignment
task_bot.queue_task(task)
```

#### CLI Creation
```bash
python task_bot_cli.py create-task "Health Check" \
    --task-type system_health \
    --priority high \
    --description "Comprehensive system health check"
```

#### REST API Creation
```bash
curl -X POST "http://localhost:8001/api/taskbot/tasks" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Health Check",
       "description": "Comprehensive system health check",
       "task_type": "system_health",
       "priority": "high",
       "subsystem": "health_monitor"
     }'
```

### Task Assignment

Tasks are automatically assigned based on the current assignment strategy, but you can also manually assign:

#### Manual Assignment
```python
# Assign to specific bot
assignment = await task_bot.assign_task(task, bot_id="bot-uuid")

# Auto-assign to best available bot
assignment = await task_bot.assign_task(task)
```

#### CLI Assignment
```bash
python task_bot_cli.py assign-task <task-id> --bot-id <bot-id>
```

### System Monitoring

#### Get System Statistics
```python
stats = task_bot.get_system_stats()
print(f"Total bots: {stats['total_bots']}")
print(f"Online bots: {stats['online_bots']}")
print(f"Queue size: {stats['queue_size']}")
```

#### CLI Monitoring
```bash
# System status
python task_bot_cli.py status

# Health check
python task_bot_cli.py health

# List assignments
python task_bot_cli.py list-assignments --status pending
```

## 🎛️ Configuration

### Assignment Strategies
Change the assignment strategy:

```python
# Programmatically
task_bot.current_strategy = "load_balanced"

# CLI
python task_bot_cli.py set-strategy load_balanced

# REST API
curl -X POST "http://localhost:8001/api/taskbot/system/config" \
     -H "Content-Type: application/json" \
     -d '{"assignment_strategy": "load_balanced"}'
```

Available strategies:
- `best_fit`: Highest capability score
- `load_balanced`: Even distribution
- `round_robin`: Simple rotation
- `priority_first`: Priority preference based

### Bot Configuration
Bots can be configured with:
- **Capabilities**: What task types they can handle
- **Priority Preferences**: Which task priorities they prefer
- **Concurrency Limits**: Maximum simultaneous tasks
- **Priority Boosts**: Score bonuses for specific task types

## 🔌 API Reference

### Core Endpoints

#### Bot Management
- `POST /api/taskbot/bots/register` - Register a new bot
- `GET /api/taskbot/bots` - List all bots
- `GET /api/taskbot/bots/{bot_id}` - Get bot details
- `PUT /api/taskbot/bots/{bot_id}/status` - Update bot status
- `DELETE /api/taskbot/bots/{bot_id}` - Unregister bot
- `GET /api/taskbot/bots/{bot_id}/stats` - Get bot statistics

#### Task Management
- `POST /api/taskbot/tasks` - Create and queue a task
- `POST /api/taskbot/assignments` - Manually assign a task
- `GET /api/taskbot/assignments` - List assignments
- `GET /api/taskbot/assignments/{assignment_id}` - Get assignment details
- `POST /api/taskbot/assignments/{assignment_id}/complete` - Complete assignment

#### System Management
- `GET /api/taskbot/system/stats` - Get system statistics
- `GET /api/taskbot/system/health` - Health check
- `POST /api/taskbot/system/config` - Update configuration

#### Utility Endpoints
- `GET /api/taskbot/available-bots` - Get available bots
- `GET /api/taskbot/task-types` - List task types
- `GET /api/taskbot/bot-types` - List bot types
- `GET /api/taskbot/priorities` - List priorities

## 📊 Monitoring & Analytics

### System Metrics
The TaskBot system tracks comprehensive metrics:

- **Bot Metrics**: Registration, status, utilization, performance
- **Task Metrics**: Creation, assignment, completion rates
- **Assignment Metrics**: Success rates, timing, strategy effectiveness
- **System Health**: Queue sizes, response times, error rates

### Real-time Monitoring
- Live bot status updates
- Real-time assignment tracking
- Performance dashboards
- Health alerts and notifications

## 🔧 Advanced Usage

### Custom Assignment Strategies
You can implement custom assignment strategies:

```python
async def custom_strategy(self, task: Task) -> Optional[Bot]:
    """Custom assignment logic."""
    available_bots = self.get_available_bots(task.task_type)
    # Implement your logic here
    return selected_bot

# Register the strategy
task_bot.assignment_strategies["custom"] = custom_strategy
task_bot.current_strategy = "custom"
```

### Event Handling
Register event handlers for system events:

```python
def on_bot_registered(data):
    print(f"Bot registered: {data['bot'].name}")

def on_task_assigned(data):
    print(f"Task {data['task'].name} assigned to {data['bot'].name}")

task_bot.add_event_handler("bot_registered", on_bot_registered)
task_bot.add_event_handler("task_assigned", on_task_assigned)
```

### Integration with Existing Systems
TaskBot integrates seamlessly with the existing overwatch infrastructure:

```python
# Use existing overwatch instance
overwatch = get_overwatch()
task_bot = initialize_task_bot(overwatch)

# TaskBot tasks flow through overwatch handlers
# Existing task handlers continue to work
```

## 🔍 Troubleshooting

### Common Issues

1. **No bots available for assignment**
   - Check bot status: `python task_bot_cli.py list-bots`
   - Verify bot capabilities match task types
   - Ensure bots are online and not at capacity

2. **Tasks stuck in queue**
   - Check assignment strategy effectiveness
   - Monitor bot utilization
   - Verify task priorities are appropriate

3. **API connection issues**
   - Ensure TaskBot API is running on port 8001
   - Check firewall settings
   - Verify API base URL in web dashboard

### Debugging
Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or use CLI verbose mode:
```bash
python task_bot_cli.py --verbose status
```

## 📈 Performance Optimization

### Bot Optimization
- Set appropriate concurrency limits based on bot capabilities
- Use priority boosts to optimize task routing
- Monitor bot utilization and adjust capacity

### Assignment Optimization
- Choose assignment strategies based on workload patterns
- Use priority preferences to reduce assignment overhead
- Monitor assignment times and success rates

### System Optimization
- Monitor queue sizes and adjust bot capacity
- Use health checks to identify bottlenecks
- Implement automated scaling based on metrics

## 🤝 Contributing

The TaskBot system is designed to be extensible:

1. **Add new bot types**: Extend the `BotType` enum
2. **Create custom capabilities**: Implement new `BotCapability` types
3. **Develop assignment strategies**: Add new logic to assignment strategies
4. **Extend monitoring**: Add custom metrics and health checks
5. **Improve UI**: Enhance the web dashboard with new features

## 📝 Examples

### Complete Bot Registration Example
```python
# Create a specialized OBD2 diagnostic bot
obd2_bot = Bot(
    name="OBD2 Specialist",
    bot_type=BotType.SPECIALIST,
    capabilities=[
        BotCapability(
            name="OBD2 Diagnostics",
            description="Vehicle diagnostic capabilities",
            task_types=[TaskType.OBD2_DIAGNOSTIC],
            priority_boost=20,
            max_concurrent=1
        )
    ],
    max_concurrent_tasks=1,
    priority_preference=[TaskPriority.HIGH, TaskPriority.CRITICAL],
    metadata={"specialization": "automotive"},
    contact_info={"email": "obd2-bot@example.com"}
)

# Register and start working
task_bot.register_bot(obd2_bot)
```

### Batch Task Processing Example
```python
# Create multiple related tasks
tasks = []
for i in range(10):
    task = Task(
        name=f"Data Processing Job {i}",
        task_type=TaskType.DATA_BACKUP,
        priority=TaskPriority.NORMAL,
        context=TaskContext(
            subsystem="batch_processor",
            metadata={"batch_id": "batch_001", "job_index": i}
        )
    )
    tasks.append(task)

# Queue all tasks
for task in tasks:
    task_bot.queue_task(task)

# Monitor progress
while True:
    stats = task_bot.get_system_stats()
    if stats['queue_size'] == 0:
        break
    print(f"Remaining: {stats['queue_size']}")
    await asyncio.sleep(1)
```

## 🎯 Use Cases

### Development Team Automation
- **Code Review Bots**: Automated code quality checks
- **Testing Bots**: Automated test execution and reporting
- **Deployment Bots**: Continuous deployment automation

### System Administration
- **Health Monitoring Bots**: Continuous system health checks
- **Backup Bots**: Automated data backup operations
- **Maintenance Bots**: Scheduled system maintenance

### Customer Service
- **Support Bots**: Automated ticket processing
- **Escalation Bots**: Intelligent issue routing
- **Response Bots**: Automated customer communications

### DevOps & Infrastructure
- **Monitoring Bots**: Infrastructure monitoring and alerting
- **Scaling Bots**: Automated resource scaling
- **Security Bots**: Security scanning and compliance

## 🔐 Security Considerations

- Bot authentication and authorization
- Task data encryption and security
- API access control and rate limiting
- Audit logging for all operations
- Secure communication between components

## 📞 Support

For issues, questions, or contributions:
1. Check the troubleshooting section
2. Review the API documentation
3. Run the demo to understand system behavior
4. Use verbose logging for debugging

The TaskBot system is designed to be self-documenting through its CLI help, API documentation, and web interface tooltips.