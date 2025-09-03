#!/usr/bin/env python3
"""
Task Bot System
===============

A comprehensive task bot system that can assign and manage tasks for users and other bots.
Built on top of the existing overwatch infrastructure.

Features:
- Bot registration and capability management
- Intelligent task assignment based on bot capabilities
- Task delegation and tracking
- Multi-bot coordination
- User and bot task management
- Real-time task monitoring
- Automated task distribution
"""

import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable
from collections import defaultdict, deque

from .overwatch import (
    Task, TaskType, TaskPriority, TaskStatus, TaskContext, TaskResult,
    OverwatchSystem, get_overwatch
)

logger = logging.getLogger(__name__)


class BotType(Enum):
    """Types of bots that can be managed."""
    ASSISTANT = "assistant"
    SYSTEM = "system"
    WORKER = "worker"
    MONITOR = "monitor"
    SPECIALIST = "specialist"
    USER = "user"


class BotStatus(Enum):
    """Bot status levels."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    IDLE = "idle"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class BotCapability:
    """Represents a capability that a bot can handle."""
    name: str
    description: str
    task_types: List[TaskType]
    priority_boost: int = 0  # Boost for tasks this bot is good at
    max_concurrent: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Bot:
    """Represents a bot that can execute tasks."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    bot_type: BotType = BotType.WORKER
    status: BotStatus = BotStatus.OFFLINE
    
    # Capabilities and configuration
    capabilities: List[BotCapability] = field(default_factory=list)
    max_concurrent_tasks: int = 3
    priority_preference: List[TaskPriority] = field(default_factory=list)
    
    # Runtime state
    current_tasks: Set[str] = field(default_factory=set)
    completed_tasks: int = 0
    failed_tasks: int = 0
    last_seen: Optional[datetime] = None
    last_task_completed: Optional[datetime] = None
    
    # Configuration
    metadata: Dict[str, Any] = field(default_factory=dict)
    contact_info: Dict[str, str] = field(default_factory=dict)
    
    def can_handle_task(self, task: Task) -> bool:
        """Check if this bot can handle the given task."""
        if self.status not in [BotStatus.ONLINE, BotStatus.IDLE]:
            return False
            
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return False
            
        # Check if any capability matches the task type
        for capability in self.capabilities:
            if task.task_type in capability.task_types:
                return True
                
        return False
    
    def get_task_score(self, task: Task) -> int:
        """Calculate a score for how well this bot can handle the task."""
        if not self.can_handle_task(task):
            return -1
            
        score = 0
        
        # Base score from priority preference
        if task.priority in self.priority_preference:
            score += 10 - self.priority_preference.index(task.priority)
        
        # Capability-based scoring
        for capability in self.capabilities:
            if task.task_type in capability.task_types:
                score += 20 + capability.priority_boost
                
        # Load balancing - prefer bots with fewer current tasks
        score -= len(self.current_tasks) * 5
        
        # Recent activity bonus
        if self.last_task_completed:
            time_since_last = datetime.now() - self.last_task_completed
            if time_since_last < timedelta(minutes=30):
                score += 5
                
        return score


@dataclass
class TaskAssignment:
    """Represents an assignment of a task to a bot."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    bot_id: str = ""
    assigned_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskBot:
    """
    Main TaskBot system for managing and assigning tasks to bots and users.
    """
    
    def __init__(self, overwatch_system: Optional[OverwatchSystem] = None):
        self.overwatch = overwatch_system or get_overwatch()
        self.bots: Dict[str, Bot] = {}
        self.assignments: Dict[str, TaskAssignment] = {}
        self.task_queue: deque = deque()
        self.assignment_history: List[TaskAssignment] = []
        
        # Assignment strategies
        self.assignment_strategies: Dict[str, Callable] = {
            "round_robin": self._assign_round_robin,
            "best_fit": self._assign_best_fit,
            "load_balanced": self._assign_load_balanced,
            "priority_first": self._assign_priority_first
        }
        self.current_strategy = "best_fit"
        
        # Statistics
        self.stats = {
            "total_assignments": 0,
            "successful_assignments": 0,
            "failed_assignments": 0,
            "avg_assignment_time": 0.0,
            "bot_utilization": defaultdict(float)
        }
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        logger.info("TaskBot system initialized")
    
    async def start(self):
        """Start the TaskBot system."""
        logger.info("Starting TaskBot system...")
        
        # Register with overwatch system
        await self._register_with_overwatch()
        
        # Start background tasks
        asyncio.create_task(self._assignment_loop())
        asyncio.create_task(self._health_monitor())
        asyncio.create_task(self._statistics_updater())
        
        logger.info("TaskBot system started successfully")
    
    async def stop(self):
        """Stop the TaskBot system."""
        logger.info("Stopping TaskBot system...")
        
        # Cancel all pending assignments
        for assignment in self.assignments.values():
            if assignment.status == TaskStatus.PENDING:
                assignment.status = TaskStatus.CANCELLED
        
        # Notify all bots
        for bot in self.bots.values():
            bot.status = BotStatus.OFFLINE
            
        logger.info("TaskBot system stopped")
    
    # Bot Management
    def register_bot(self, bot: Bot) -> bool:
        """Register a new bot with the system."""
        try:
            bot.last_seen = datetime.now()
            bot.status = BotStatus.ONLINE
            self.bots[bot.id] = bot
            
            logger.info(f"Registered bot: {bot.name} ({bot.id})")
            self._emit_event("bot_registered", {"bot": bot})
            
            return True
        except Exception as e:
            logger.error(f"Failed to register bot {bot.name}: {e}")
            return False
    
    def unregister_bot(self, bot_id: str) -> bool:
        """Unregister a bot from the system."""
        if bot_id not in self.bots:
            return False
            
        bot = self.bots[bot_id]
        
        # Cancel any pending assignments for this bot
        for assignment in self.assignments.values():
            if assignment.bot_id == bot_id and assignment.status == TaskStatus.PENDING:
                assignment.status = TaskStatus.CANCELLED
                # Re-queue the task
                task = self.overwatch.get_task(assignment.task_id)
                if task:
                    self.queue_task(task)
        
        del self.bots[bot_id]
        logger.info(f"Unregistered bot: {bot.name} ({bot_id})")
        self._emit_event("bot_unregistered", {"bot_id": bot_id})
        
        return True
    
    def update_bot_status(self, bot_id: str, status: BotStatus) -> bool:
        """Update bot status."""
        if bot_id not in self.bots:
            return False
            
        self.bots[bot_id].status = status
        self.bots[bot_id].last_seen = datetime.now()
        
        self._emit_event("bot_status_updated", {
            "bot_id": bot_id, 
            "status": status
        })
        
        return True
    
    def get_available_bots(self, task_type: Optional[TaskType] = None) -> List[Bot]:
        """Get list of available bots, optionally filtered by task type."""
        available = []
        
        for bot in self.bots.values():
            if bot.status in [BotStatus.ONLINE, BotStatus.IDLE]:
                if task_type is None:
                    available.append(bot)
                else:
                    # Check if bot can handle this task type
                    for capability in bot.capabilities:
                        if task_type in capability.task_types:
                            available.append(bot)
                            break
        
        return available
    
    # Task Assignment
    def queue_task(self, task: Task) -> bool:
        """Queue a task for assignment to a bot."""
        self.task_queue.append(task)
        logger.info(f"Queued task: {task.name} ({task.id})")
        self._emit_event("task_queued", {"task": task})
        return True
    
    async def assign_task(self, task: Task, bot_id: Optional[str] = None) -> Optional[TaskAssignment]:
        """Assign a task to a specific bot or find the best available bot."""
        start_time = datetime.now()
        
        try:
            # If specific bot requested, use it
            if bot_id:
                if bot_id not in self.bots:
                    logger.error(f"Bot {bot_id} not found")
                    return None
                    
                bot = self.bots[bot_id]
                if not bot.can_handle_task(task):
                    logger.error(f"Bot {bot.name} cannot handle task {task.name}")
                    return None
            else:
                # Find best bot using current strategy
                bot = await self._find_best_bot(task)
                if not bot:
                    logger.warning(f"No available bot found for task {task.name}")
                    return None
            
            # Create assignment
            assignment = TaskAssignment(
                task_id=task.id,
                bot_id=bot.id,
                status=TaskStatus.PENDING
            )
            
            # Update bot state
            bot.current_tasks.add(task.id)
            if len(bot.current_tasks) >= bot.max_concurrent_tasks:
                bot.status = BotStatus.BUSY
            
            # Store assignment
            self.assignments[assignment.id] = assignment
            self.assignment_history.append(assignment)
            
            # Update statistics
            self.stats["total_assignments"] += 1
            assignment_time = (datetime.now() - start_time).total_seconds()
            self._update_avg_assignment_time(assignment_time)
            
            logger.info(f"Assigned task {task.name} to bot {bot.name}")
            self._emit_event("task_assigned", {
                "task": task, 
                "bot": bot, 
                "assignment": assignment
            })
            
            return assignment
            
        except Exception as e:
            logger.error(f"Failed to assign task {task.name}: {e}")
            return None
    
    async def complete_assignment(self, assignment_id: str, result: TaskResult) -> bool:
        """Mark an assignment as completed."""
        if assignment_id not in self.assignments:
            return False
            
        assignment = self.assignments[assignment_id]
        assignment.status = result.status
        assignment.result = result
        assignment.completed_at = datetime.now()
        
        # Update bot state
        bot = self.bots.get(assignment.bot_id)
        if bot:
            bot.current_tasks.discard(assignment.task_id)
            bot.last_task_completed = datetime.now()
            
            if result.status == TaskStatus.COMPLETED:
                bot.completed_tasks += 1
                self.stats["successful_assignments"] += 1
            else:
                bot.failed_tasks += 1
                self.stats["failed_assignments"] += 1
            
            # Update bot status
            if len(bot.current_tasks) == 0:
                bot.status = BotStatus.IDLE
            elif bot.status == BotStatus.BUSY and len(bot.current_tasks) < bot.max_concurrent_tasks:
                bot.status = BotStatus.ONLINE
        
        self._emit_event("assignment_completed", {
            "assignment": assignment,
            "result": result
        })
        
        return True
    
    # Assignment Strategies
    async def _find_best_bot(self, task: Task) -> Optional[Bot]:
        """Find the best bot for a task using the current strategy."""
        strategy = self.assignment_strategies.get(self.current_strategy)
        if not strategy:
            logger.error(f"Unknown assignment strategy: {self.current_strategy}")
            return None
            
        return await strategy(task)
    
    async def _assign_best_fit(self, task: Task) -> Optional[Bot]:
        """Assign to the bot with the highest score for this task."""
        available_bots = self.get_available_bots(task.task_type)
        if not available_bots:
            return None
            
        best_bot = None
        best_score = -1
        
        for bot in available_bots:
            score = bot.get_task_score(task)
            if score > best_score:
                best_score = score
                best_bot = bot
                
        return best_bot
    
    async def _assign_load_balanced(self, task: Task) -> Optional[Bot]:
        """Assign to the bot with the lowest current load."""
        available_bots = self.get_available_bots(task.task_type)
        if not available_bots:
            return None
            
        # Sort by current task count (ascending)
        available_bots.sort(key=lambda b: len(b.current_tasks))
        return available_bots[0]
    
    async def _assign_round_robin(self, task: Task) -> Optional[Bot]:
        """Assign tasks in round-robin fashion."""
        available_bots = self.get_available_bots(task.task_type)
        if not available_bots:
            return None
            
        # Simple round-robin based on total assignments
        bot_index = self.stats["total_assignments"] % len(available_bots)
        return available_bots[bot_index]
    
    async def _assign_priority_first(self, task: Task) -> Optional[Bot]:
        """Assign to bots that prefer this task priority."""
        available_bots = self.get_available_bots(task.task_type)
        if not available_bots:
            return None
            
        # Prefer bots that have this priority in their preference list
        preferred_bots = [b for b in available_bots if task.priority in b.priority_preference]
        if preferred_bots:
            # Among preferred bots, use best fit
            return await self._assign_best_fit(task)
        
        return available_bots[0]
    
    # Background Tasks
    async def _assignment_loop(self):
        """Background loop for processing task assignments."""
        while True:
            try:
                if self.task_queue:
                    task = self.task_queue.popleft()
                    assignment = await self.assign_task(task)
                    
                    if not assignment:
                        # Re-queue if assignment failed
                        self.task_queue.appendleft(task)
                        await asyncio.sleep(5)  # Wait before retrying
                
                await asyncio.sleep(1)  # Check queue every second
                
            except Exception as e:
                logger.error(f"Error in assignment loop: {e}")
                await asyncio.sleep(5)
    
    async def _health_monitor(self):
        """Monitor bot health and handle disconnections."""
        while True:
            try:
                current_time = datetime.now()
                timeout_threshold = timedelta(minutes=5)
                
                for bot_id, bot in list(self.bots.items()):
                    if bot.last_seen and (current_time - bot.last_seen) > timeout_threshold:
                        logger.warning(f"Bot {bot.name} appears disconnected")
                        bot.status = BotStatus.OFFLINE
                        
                        # Handle any running tasks
                        for assignment in self.assignments.values():
                            if (assignment.bot_id == bot_id and 
                                assignment.status in [TaskStatus.PENDING, TaskStatus.RUNNING]):
                                assignment.status = TaskStatus.FAILED
                                assignment.result = TaskResult(
                                    task_id=assignment.task_id,
                                    status=TaskStatus.FAILED,
                                    error_message="Bot disconnected"
                                )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(60)
    
    async def _statistics_updater(self):
        """Update system statistics."""
        while True:
            try:
                # Update bot utilization
                for bot in self.bots.values():
                    if bot.max_concurrent_tasks > 0:
                        utilization = len(bot.current_tasks) / bot.max_concurrent_tasks
                        self.stats["bot_utilization"][bot.id] = utilization
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error updating statistics: {e}")
                await asyncio.sleep(30)
    
    # Utility Methods
    async def _register_with_overwatch(self):
        """Register TaskBot as a service with the overwatch system."""
        if self.overwatch:
            # Could register as a special overwatch handler
            pass
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to registered handlers."""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler."""
        self.event_handlers[event_type].append(handler)
    
    def _update_avg_assignment_time(self, new_time: float):
        """Update the average assignment time."""
        current_avg = self.stats["avg_assignment_time"]
        total_assignments = self.stats["total_assignments"]
        
        if total_assignments == 1:
            self.stats["avg_assignment_time"] = new_time
        else:
            # Running average
            self.stats["avg_assignment_time"] = (
                (current_avg * (total_assignments - 1) + new_time) / total_assignments
            )
    
    # API Methods
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            "task_bot_stats": self.stats,
            "total_bots": len(self.bots),
            "online_bots": len([b for b in self.bots.values() if b.status == BotStatus.ONLINE]),
            "busy_bots": len([b for b in self.bots.values() if b.status == BotStatus.BUSY]),
            "total_assignments": len(self.assignments),
            "pending_assignments": len([a for a in self.assignments.values() if a.status == TaskStatus.PENDING]),
            "queue_size": len(self.task_queue),
            "assignment_strategy": self.current_strategy
        }
    
    def get_bot_stats(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific bot."""
        if bot_id not in self.bots:
            return None
            
        bot = self.bots[bot_id]
        assignments = [a for a in self.assignments.values() if a.bot_id == bot_id]
        
        return {
            "bot": bot,
            "total_assignments": len(assignments),
            "completed_assignments": len([a for a in assignments if a.status == TaskStatus.COMPLETED]),
            "failed_assignments": len([a for a in assignments if a.status == TaskStatus.FAILED]),
            "current_load": len(bot.current_tasks),
            "utilization": self.stats["bot_utilization"].get(bot_id, 0.0),
            "last_active": bot.last_task_completed
        }


# Global TaskBot instance
_task_bot_instance: Optional[TaskBot] = None


def get_task_bot() -> TaskBot:
    """Get the global TaskBot instance."""
    global _task_bot_instance
    if _task_bot_instance is None:
        _task_bot_instance = TaskBot()
    return _task_bot_instance


def initialize_task_bot(overwatch_system: Optional[OverwatchSystem] = None) -> TaskBot:
    """Initialize the global TaskBot instance."""
    global _task_bot_instance
    _task_bot_instance = TaskBot(overwatch_system)
    return _task_bot_instance