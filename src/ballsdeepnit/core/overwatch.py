#!/usr/bin/env python3
"""
Overwatch System - Task Generation and Dispatch
==============================================

A comprehensive overwatch system that can generate tasks dynamically
and dispatch them to appropriate subsystems for execution.

Features:
- Dynamic task generation based on system conditions
- Priority-based task scheduling
- Multi-threaded task dispatch
- Health monitoring integration
- Resource-aware execution
- Failure recovery and retry mechanisms
"""

import asyncio
import logging
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from queue import PriorityQueue
import json

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class TaskType(Enum):
    """Types of tasks that can be generated."""
    SYSTEM_HEALTH = "system_health"
    OBD2_DIAGNOSTIC = "obd2_diagnostic"
    PERFORMANCE_CHECK = "performance_check"
    DATA_BACKUP = "data_backup"
    MAINTENANCE = "maintenance"
    SECURITY_SCAN = "security_scan"
    USER_TASK = "user_task"
    CUSTOM = "custom"


@dataclass
class TaskContext:
    """Context information for task execution."""
    subsystem: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    status: TaskStatus
    result_data: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """A task that can be executed by the overwatch system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.CUSTOM
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    
    # Execution details
    handler: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    
    # Scheduling
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    
    # Retry configuration
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: float = 1.0
    
    # Context and dependencies
    context: TaskContext = field(default_factory=lambda: TaskContext("core"))
    dependencies: List[str] = field(default_factory=list)
    
    # Resource requirements
    cpu_requirement: float = 0.1  # 0.0 to 1.0
    memory_requirement: int = 64  # MB
    io_requirement: float = 0.1   # 0.0 to 1.0
    
    def __lt__(self, other):
        """For priority queue ordering."""
        if not isinstance(other, Task):
            return NotImplemented
        return (self.priority.value, self.created_at) < (other.priority.value, other.created_at)


class TaskHandler(ABC):
    """Abstract base class for task handlers."""
    
    @abstractmethod
    async def execute(self, task: Task) -> TaskResult:
        """Execute a task and return the result."""
        pass
    
    @abstractmethod
    def can_handle(self, task: Task) -> bool:
        """Check if this handler can execute the given task."""
        pass


class SystemHealthTaskHandler(TaskHandler):
    """Handler for system health check tasks."""
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute system health check."""
        start_time = datetime.now()
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_data = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available": memory.available,
                "disk_usage": disk.percent,
                "disk_free": disk.free,
                "timestamp": datetime.now().isoformat()
            }
            
            # Determine health status
            status = "healthy"
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = "warning"
            if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
                status = "critical"
            
            health_data["status"] = status
            
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result_data=health_data,
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            end_time = datetime.now()
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                execution_time=(end_time - start_time).total_seconds(),
                start_time=start_time,
                end_time=end_time
            )
    
    def can_handle(self, task: Task) -> bool:
        """Check if this handler can execute the given task."""
        return task.task_type == TaskType.SYSTEM_HEALTH


class TaskGenerator:
    """Generates tasks dynamically based on system conditions."""
    
    def __init__(self):
        self.generation_rules: List[Callable[[], List[Task]]] = []
        self.last_generation_time = datetime.now()
        self.generation_interval = timedelta(minutes=5)
        
    def add_generation_rule(self, rule: Callable[[], List[Task]]):
        """Add a rule for generating tasks."""
        self.generation_rules.append(rule)
    
    def generate_periodic_tasks(self) -> List[Task]:
        """Generate periodic system tasks."""
        tasks = []
        
        # System health check every 5 minutes
        health_task = Task(
            name="System Health Check",
            description="Check system CPU, memory, and disk usage",
            task_type=TaskType.SYSTEM_HEALTH,
            priority=TaskPriority.NORMAL,
            scheduled_at=datetime.now() + timedelta(minutes=5)
        )
        tasks.append(health_task)
        
        # Performance check every 15 minutes
        perf_task = Task(
            name="Performance Monitor",
            description="Monitor system performance metrics",
            task_type=TaskType.PERFORMANCE_CHECK,
            priority=TaskPriority.LOW,
            scheduled_at=datetime.now() + timedelta(minutes=15)
        )
        tasks.append(perf_task)
        
        return tasks
    
    def generate_conditional_tasks(self, system_state: Dict[str, Any]) -> List[Task]:
        """Generate tasks based on current system conditions."""
        tasks = []
        
        # Example: Generate maintenance task if system has been running too long
        uptime = system_state.get("uptime", 0)
        if uptime > 86400:  # 24 hours
            maintenance_task = Task(
                name="System Maintenance",
                description="Perform routine system maintenance",
                task_type=TaskType.MAINTENANCE,
                priority=TaskPriority.HIGH,
                scheduled_at=datetime.now() + timedelta(hours=1)
            )
            tasks.append(maintenance_task)
        
        # Example: Generate backup task if no recent backup
        last_backup = system_state.get("last_backup")
        if last_backup and (datetime.now() - last_backup).days > 7:
            backup_task = Task(
                name="Data Backup",
                description="Backup system data and configurations",
                task_type=TaskType.DATA_BACKUP,
                priority=TaskPriority.NORMAL,
                scheduled_at=datetime.now() + timedelta(hours=2)
            )
            tasks.append(backup_task)
        
        return tasks
    
    async def generate_tasks(self, system_state: Dict[str, Any] = None) -> List[Task]:
        """Generate tasks based on rules and system state."""
        if system_state is None:
            system_state = {}
            
        all_tasks = []
        
        # Generate periodic tasks
        all_tasks.extend(self.generate_periodic_tasks())
        
        # Generate conditional tasks
        all_tasks.extend(self.generate_conditional_tasks(system_state))
        
        # Apply custom generation rules
        for rule in self.generation_rules:
            try:
                rule_tasks = rule()
                if rule_tasks:
                    all_tasks.extend(rule_tasks)
            except Exception as e:
                logger.error(f"Error in task generation rule: {e}")
        
        return all_tasks


class TaskScheduler:
    """Schedules and manages task execution with priority queuing."""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.task_queue = PriorityQueue()
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: deque = deque(maxlen=1000)
        self.failed_tasks: deque = deque(maxlen=100)
        
        self.max_concurrent_tasks = max_concurrent_tasks
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self.handlers: Dict[TaskType, TaskHandler] = {}
        
        # Metrics
        self.task_stats = defaultdict(int)
        self.execution_times: Dict[str, float] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default task handlers."""
        self.register_handler(TaskType.SYSTEM_HEALTH, SystemHealthTaskHandler())
    
    def register_handler(self, task_type: TaskType, handler: TaskHandler):
        """Register a handler for a specific task type."""
        self.handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    def submit_task(self, task: Task):
        """Submit a task for execution."""
        if task.scheduled_at and task.scheduled_at > datetime.now():
            # Task is scheduled for later
            logger.info(f"Task {task.id} scheduled for {task.scheduled_at}")
        
        self.task_queue.put(task)
        self.task_stats["submitted"] += 1
        logger.info(f"Task submitted: {task.name} ({task.id})")
    
    def submit_tasks(self, tasks: List[Task]):
        """Submit multiple tasks for execution."""
        for task in tasks:
            self.submit_task(task)
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a single task."""
        task.status = TaskStatus.RUNNING
        self.running_tasks[task.id] = task
        
        try:
            # Find appropriate handler
            handler = self.handlers.get(task.task_type)
            if not handler:
                # Try to find a handler that can handle this task
                for h in self.handlers.values():
                    if h.can_handle(task):
                        handler = h
                        break
            
            if not handler:
                raise ValueError(f"No handler found for task type: {task.task_type}")
            
            # Execute the task
            result = await handler.execute(task)
            
            # Update task status
            task.status = result.status
            
            if result.status == TaskStatus.COMPLETED:
                self.completed_tasks.append(task)
                self.task_stats["completed"] += 1
            else:
                self.failed_tasks.append(task)
                self.task_stats["failed"] += 1
            
            # Record execution time
            if result.execution_time:
                self.execution_times[task.id] = result.execution_time
            
            return result
            
        except Exception as e:
            error_result = TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error_message=str(e),
                end_time=datetime.now()
            )
            
            task.status = TaskStatus.FAILED
            self.failed_tasks.append(task)
            self.task_stats["failed"] += 1
            
            logger.error(f"Task execution failed: {task.name} - {e}")
            return error_result
            
        finally:
            # Remove from running tasks
            self.running_tasks.pop(task.id, None)
    
    def get_next_task(self) -> Optional[Task]:
        """Get the next task to execute."""
        if self.task_queue.empty():
            return None
        
        # Check if we can run more tasks
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return None
        
        task = self.task_queue.get()
        
        # Check if task is scheduled for later
        if task.scheduled_at and task.scheduled_at > datetime.now():
            # Put it back and wait
            self.task_queue.put(task)
            return None
        
        return task
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "queue_size": self.task_queue.qsize(),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "task_stats": dict(self.task_stats),
            "average_execution_time": sum(self.execution_times.values()) / len(self.execution_times) if self.execution_times else 0
        }


class TaskDispatcher:
    """Dispatches tasks to appropriate subsystems and manages execution."""
    
    def __init__(self, scheduler: TaskScheduler):
        self.scheduler = scheduler
        self.running = False
        self.dispatch_thread: Optional[threading.Thread] = None
        
        # Subsystem mapping
        self.subsystem_handlers: Dict[str, Callable] = {}
        
    def register_subsystem_handler(self, subsystem: str, handler: Callable):
        """Register a handler for a specific subsystem."""
        self.subsystem_handlers[subsystem] = handler
        logger.info(f"Registered subsystem handler: {subsystem}")
    
    async def dispatch_to_subsystem(self, task: Task) -> TaskResult:
        """Dispatch a task to its target subsystem."""
        subsystem = task.context.subsystem
        
        if subsystem in self.subsystem_handlers:
            handler = self.subsystem_handlers[subsystem]
            try:
                result = await handler(task)
                return result
            except Exception as e:
                return TaskResult(
                    task_id=task.id,
                    status=TaskStatus.FAILED,
                    error_message=f"Subsystem {subsystem} error: {e}"
                )
        else:
            # Use default scheduler execution
            return await self.scheduler.execute_task(task)
    
    def start_dispatch_loop(self):
        """Start the task dispatch loop."""
        if self.running:
            logger.warning("Dispatcher is already running")
            return
        
        self.running = True
        self.dispatch_thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self.dispatch_thread.start()
        logger.info("Task dispatcher started")
    
    def stop_dispatch_loop(self):
        """Stop the task dispatch loop."""
        self.running = False
        if self.dispatch_thread:
            self.dispatch_thread.join(timeout=5)
        logger.info("Task dispatcher stopped")
    
    def _dispatch_loop(self):
        """Main dispatch loop (runs in thread)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._async_dispatch_loop())
        finally:
            loop.close()
    
    async def _async_dispatch_loop(self):
        """Async dispatch loop."""
        while self.running:
            try:
                # Get next task from scheduler
                task = self.scheduler.get_next_task()
                
                if task:
                    # Execute task
                    asyncio.create_task(self.dispatch_to_subsystem(task))
                else:
                    # No tasks available, wait a bit
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error in dispatch loop: {e}")
                await asyncio.sleep(1)


class OverwatchSystem:
    """Main overwatch system that coordinates task generation and dispatch."""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.task_generator = TaskGenerator()
        self.task_scheduler = TaskScheduler(max_concurrent_tasks)
        self.task_dispatcher = TaskDispatcher(self.task_scheduler)
        
        self.running = False
        self.generation_interval = 60  # seconds
        self.last_generation = datetime.now()
        
        # System state tracking
        self.system_state: Dict[str, Any] = {
            "started_at": datetime.now(),
            "uptime": 0,
            "last_backup": None,
            "health_status": "unknown"
        }
        
        logger.info("Overwatch system initialized")
    
    def register_task_handler(self, task_type: TaskType, handler: TaskHandler):
        """Register a task handler."""
        self.task_scheduler.register_handler(task_type, handler)
    
    def register_subsystem_handler(self, subsystem: str, handler: Callable):
        """Register a subsystem handler."""
        self.task_dispatcher.register_subsystem_handler(subsystem, handler)
    
    def add_task_generation_rule(self, rule: Callable[[], List[Task]]):
        """Add a custom task generation rule."""
        self.task_generator.add_generation_rule(rule)
    
    def submit_task(self, task: Task):
        """Submit a task for execution."""
        self.task_scheduler.submit_task(task)
    
    def create_task(self, 
                   name: str,
                   description: str = "",
                   task_type: TaskType = TaskType.USER_TASK,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   handler: Optional[Callable] = None,
                   subsystem: str = "core",
                   **kwargs) -> Task:
        """Create and submit a new task."""
        task = Task(
            name=name,
            description=description,
            task_type=task_type,
            priority=priority,
            handler=handler,
            context=TaskContext(subsystem=subsystem),
            **kwargs
        )
        
        self.submit_task(task)
        return task
    
    async def generate_and_submit_tasks(self):
        """Generate new tasks and submit them for execution."""
        try:
            # Update system state
            self._update_system_state()
            
            # Generate tasks
            new_tasks = await self.task_generator.generate_tasks(self.system_state)
            
            # Submit tasks
            if new_tasks:
                self.task_scheduler.submit_tasks(new_tasks)
                logger.info(f"Generated and submitted {len(new_tasks)} tasks")
                
        except Exception as e:
            logger.error(f"Error generating tasks: {e}")
    
    def _update_system_state(self):
        """Update system state information."""
        now = datetime.now()
        self.system_state["uptime"] = (now - self.system_state["started_at"]).total_seconds()
        
        # Update health status from recent health checks
        recent_completed = list(self.task_scheduler.completed_tasks)[-10:]
        for task in recent_completed:
            if hasattr(task, 'result_data') and isinstance(task.result_data, dict):
                if "status" in task.result_data:
                    self.system_state["health_status"] = task.result_data["status"]
                    break
    
    async def start(self):
        """Start the overwatch system."""
        if self.running:
            logger.warning("Overwatch system is already running")
            return
        
        self.running = True
        
        # Start task dispatcher
        self.task_dispatcher.start_dispatch_loop()
        
        # Generate initial tasks
        await self.generate_and_submit_tasks()
        
        logger.info("Overwatch system started")
    
    def stop(self):
        """Stop the overwatch system."""
        self.running = False
        
        # Stop dispatcher
        self.task_dispatcher.stop_dispatch_loop()
        
        logger.info("Overwatch system stopped")
    
    async def run_forever(self):
        """Run the overwatch system indefinitely."""
        await self.start()
        
        try:
            while self.running:
                # Check if it's time to generate new tasks
                if (datetime.now() - self.last_generation).total_seconds() >= self.generation_interval:
                    await self.generate_and_submit_tasks()
                    self.last_generation = datetime.now()
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "running": self.running,
            "system_state": self.system_state,
            "scheduler_stats": self.task_scheduler.get_stats(),
            "last_generation": self.last_generation.isoformat(),
            "generation_interval": self.generation_interval
        }


# Global overwatch instance
_overwatch_instance: Optional[OverwatchSystem] = None


def get_overwatch() -> OverwatchSystem:
    """Get the global overwatch instance."""
    global _overwatch_instance
    if _overwatch_instance is None:
        _overwatch_instance = OverwatchSystem()
    return _overwatch_instance


def initialize_overwatch(**kwargs) -> OverwatchSystem:
    """Initialize the global overwatch instance with custom settings."""
    global _overwatch_instance
    _overwatch_instance = OverwatchSystem(**kwargs)
    return _overwatch_instance


if __name__ == "__main__":
    # Example usage
    async def main():
        overwatch = get_overwatch()
        
        # Create some example tasks
        overwatch.create_task(
            name="Example Health Check",
            description="Check system health",
            task_type=TaskType.SYSTEM_HEALTH,
            priority=TaskPriority.HIGH
        )
        
        overwatch.create_task(
            name="Example User Task",
            description="Process user request",
            task_type=TaskType.USER_TASK,
            priority=TaskPriority.NORMAL
        )
        
        # Run for a short time
        await overwatch.start()
        await asyncio.sleep(10)
        
        # Show status
        status = overwatch.get_status()
        print(json.dumps(status, indent=2, default=str))
        
        overwatch.stop()
    
    asyncio.run(main())