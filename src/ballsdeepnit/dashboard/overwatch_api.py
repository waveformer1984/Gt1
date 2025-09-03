#!/usr/bin/env python3
"""
Overwatch System API Endpoints
==============================

REST API endpoints for managing and monitoring the overwatch system.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field

from ..core.overwatch import (
    get_overwatch, TaskType, TaskPriority, TaskStatus, Task, TaskContext
)
from ..core.overwatch_handlers import register_all_handlers

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/overwatch", tags=["overwatch"])

# Pydantic models for API requests/responses
class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""
    name: str = Field(..., description="Task name")
    description: str = Field("", description="Task description")
    task_type: TaskType = Field(TaskType.USER_TASK, description="Type of task")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="Task priority")
    subsystem: str = Field("core", description="Target subsystem")
    scheduled_at: Optional[datetime] = Field(None, description="When to execute the task")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TaskResponse(BaseModel):
    """Response model for task information."""
    id: str
    name: str
    description: str
    task_type: str
    priority: str
    status: str
    created_at: datetime
    scheduled_at: Optional[datetime]
    subsystem: str
    execution_time: Optional[float] = None
    error_message: Optional[str] = None


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    running: bool
    uptime: float
    system_state: Dict[str, Any]
    scheduler_stats: Dict[str, Any]
    last_generation: str
    generation_interval: int
    health_status: str


class TaskStatsResponse(BaseModel):
    """Response model for task statistics."""
    total_submitted: int
    total_completed: int
    total_failed: int
    currently_running: int
    queue_size: int
    average_execution_time: float
    recent_tasks: List[TaskResponse]


def get_overwatch_system():
    """Dependency to get the overwatch system instance."""
    overwatch = get_overwatch()
    
    # Register handlers if not already done
    if not hasattr(overwatch, '_handlers_registered'):
        register_all_handlers(overwatch)
        overwatch._handlers_registered = True
    
    return overwatch


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(overwatch=Depends(get_overwatch_system)):
    """Get comprehensive system status."""
    try:
        status = overwatch.get_status()
        return SystemStatusResponse(
            running=status["running"],
            uptime=status["system_state"]["uptime"],
            system_state=status["system_state"],
            scheduler_stats=status["scheduler_stats"],
            last_generation=status["last_generation"],
            generation_interval=status["generation_interval"],
            health_status=status["system_state"].get("health_status", "unknown")
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_overwatch(background_tasks: BackgroundTasks, overwatch=Depends(get_overwatch_system)):
    """Start the overwatch system."""
    try:
        if overwatch.running:
            return {"message": "Overwatch system is already running"}
        
        # Start the system in background
        background_tasks.add_task(overwatch.start)
        
        return {"message": "Overwatch system starting"}
    except Exception as e:
        logger.error(f"Error starting overwatch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_overwatch(overwatch=Depends(get_overwatch_system)):
    """Stop the overwatch system."""
    try:
        if not overwatch.running:
            return {"message": "Overwatch system is not running"}
        
        overwatch.stop()
        return {"message": "Overwatch system stopped"}
    except Exception as e:
        logger.error(f"Error stopping overwatch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskCreateRequest, overwatch=Depends(get_overwatch_system)):
    """Create and submit a new task."""
    try:
        # Create task context
        context = TaskContext(
            subsystem=task_request.subsystem,
            metadata=task_request.metadata
        )
        
        # Create the task
        task = Task(
            name=task_request.name,
            description=task_request.description,
            task_type=task_request.task_type,
            priority=task_request.priority,
            scheduled_at=task_request.scheduled_at,
            context=context
        )
        
        # Submit to overwatch
        overwatch.submit_task(task)
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            priority=task.priority.value,
            status=task.status.value,
            created_at=task.created_at,
            scheduled_at=task.scheduled_at,
            subsystem=task.context.subsystem
        )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    task_type: Optional[TaskType] = Query(None, description="Filter by task type"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of tasks to return"),
    overwatch=Depends(get_overwatch_system)
):
    """List tasks with optional filtering."""
    try:
        tasks = []
        
        # Get tasks from scheduler
        scheduler = overwatch.task_scheduler
        
        # Running tasks
        for task in scheduler.running_tasks.values():
            if status and task.status != status:
                continue
            if task_type and task.task_type != task_type:
                continue
            
            tasks.append(TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                task_type=task.task_type.value,
                priority=task.priority.value,
                status=task.status.value,
                created_at=task.created_at,
                scheduled_at=task.scheduled_at,
                subsystem=task.context.subsystem
            ))
        
        # Completed tasks
        for task in list(scheduler.completed_tasks)[-limit:]:
            if len(tasks) >= limit:
                break
            if status and task.status != status:
                continue
            if task_type and task.task_type != task_type:
                continue
            
            execution_time = scheduler.execution_times.get(task.id)
            tasks.append(TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                task_type=task.task_type.value,
                priority=task.priority.value,
                status=task.status.value,
                created_at=task.created_at,
                scheduled_at=task.scheduled_at,
                subsystem=task.context.subsystem,
                execution_time=execution_time
            ))
        
        # Failed tasks
        for task in list(scheduler.failed_tasks)[-limit:]:
            if len(tasks) >= limit:
                break
            if status and task.status != status:
                continue
            if task_type and task.task_type != task_type:
                continue
            
            execution_time = scheduler.execution_times.get(task.id)
            tasks.append(TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                task_type=task.task_type.value,
                priority=task.priority.value,
                status=task.status.value,
                created_at=task.created_at,
                scheduled_at=task.scheduled_at,
                subsystem=task.context.subsystem,
                execution_time=execution_time
            ))
        
        # Sort by creation time (most recent first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, overwatch=Depends(get_overwatch_system)):
    """Get detailed information about a specific task."""
    try:
        scheduler = overwatch.task_scheduler
        
        # Check running tasks
        if task_id in scheduler.running_tasks:
            task = scheduler.running_tasks[task_id]
            return TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                task_type=task.task_type.value,
                priority=task.priority.value,
                status=task.status.value,
                created_at=task.created_at,
                scheduled_at=task.scheduled_at,
                subsystem=task.context.subsystem
            )
        
        # Check completed tasks
        for task in scheduler.completed_tasks:
            if task.id == task_id:
                execution_time = scheduler.execution_times.get(task.id)
                return TaskResponse(
                    id=task.id,
                    name=task.name,
                    description=task.description,
                    task_type=task.task_type.value,
                    priority=task.priority.value,
                    status=task.status.value,
                    created_at=task.created_at,
                    scheduled_at=task.scheduled_at,
                    subsystem=task.context.subsystem,
                    execution_time=execution_time
                )
        
        # Check failed tasks
        for task in scheduler.failed_tasks:
            if task.id == task_id:
                execution_time = scheduler.execution_times.get(task.id)
                return TaskResponse(
                    id=task.id,
                    name=task.name,
                    description=task.description,
                    task_type=task.task_type.value,
                    priority=task.priority.value,
                    status=task.status.value,
                    created_at=task.created_at,
                    scheduled_at=task.scheduled_at,
                    subsystem=task.context.subsystem,
                    execution_time=execution_time
                )
        
        raise HTTPException(status_code=404, detail="Task not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=TaskStatsResponse)
async def get_task_stats(overwatch=Depends(get_overwatch_system)):
    """Get task execution statistics."""
    try:
        scheduler = overwatch.task_scheduler
        stats = scheduler.get_stats()
        
        # Get recent tasks (last 10)
        recent_tasks = []
        all_tasks = []
        
        # Combine all tasks
        all_tasks.extend([
            TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                task_type=task.task_type.value,
                priority=task.priority.value,
                status=task.status.value,
                created_at=task.created_at,
                scheduled_at=task.scheduled_at,
                subsystem=task.context.subsystem
            ) for task in scheduler.running_tasks.values()
        ])
        
        all_tasks.extend([
            TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                task_type=task.task_type.value,
                priority=task.priority.value,
                status=task.status.value,
                created_at=task.created_at,
                scheduled_at=task.scheduled_at,
                subsystem=task.context.subsystem,
                execution_time=scheduler.execution_times.get(task.id)
            ) for task in list(scheduler.completed_tasks)[-10:]
        ])
        
        all_tasks.extend([
            TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                task_type=task.task_type.value,
                priority=task.priority.value,
                status=task.status.value,
                created_at=task.created_at,
                scheduled_at=task.scheduled_at,
                subsystem=task.context.subsystem,
                execution_time=scheduler.execution_times.get(task.id)
            ) for task in list(scheduler.failed_tasks)[-10:]
        ])
        
        # Sort by creation time and take most recent
        all_tasks.sort(key=lambda t: t.created_at, reverse=True)
        recent_tasks = all_tasks[:10]
        
        return TaskStatsResponse(
            total_submitted=stats["task_stats"].get("submitted", 0),
            total_completed=stats["task_stats"].get("completed", 0),
            total_failed=stats["task_stats"].get("failed", 0),
            currently_running=stats["running_tasks"],
            queue_size=stats["queue_size"],
            average_execution_time=stats["average_execution_time"],
            recent_tasks=recent_tasks
        )
    except Exception as e:
        logger.error(f"Error getting task stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/generate")
async def generate_tasks(overwatch=Depends(get_overwatch_system)):
    """Manually trigger task generation."""
    try:
        if not overwatch.running:
            raise HTTPException(status_code=400, detail="Overwatch system is not running")
        
        # Generate and submit tasks
        await overwatch.generate_and_submit_tasks()
        
        return {"message": "Tasks generated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/health-check")
async def create_health_check_task(overwatch=Depends(get_overwatch_system)):
    """Create an immediate system health check task."""
    try:
        task = overwatch.create_task(
            name="Manual Health Check",
            description="Manually triggered system health check",
            task_type=TaskType.SYSTEM_HEALTH,
            priority=TaskPriority.HIGH
        )
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            priority=task.priority.value,
            status=task.status.value,
            created_at=task.created_at,
            scheduled_at=task.scheduled_at,
            subsystem=task.context.subsystem
        )
    except Exception as e:
        logger.error(f"Error creating health check task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/performance-check")
async def create_performance_check_task(overwatch=Depends(get_overwatch_system)):
    """Create an immediate performance check task."""
    try:
        task = overwatch.create_task(
            name="Manual Performance Check",
            description="Manually triggered performance monitoring",
            task_type=TaskType.PERFORMANCE_CHECK,
            priority=TaskPriority.HIGH
        )
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            priority=task.priority.value,
            status=task.status.value,
            created_at=task.created_at,
            scheduled_at=task.scheduled_at,
            subsystem=task.context.subsystem
        )
    except Exception as e:
        logger.error(f"Error creating performance check task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/backup")
async def create_backup_task(overwatch=Depends(get_overwatch_system)):
    """Create a data backup task."""
    try:
        task = overwatch.create_task(
            name="Manual Data Backup",
            description="Manually triggered data backup",
            task_type=TaskType.DATA_BACKUP,
            priority=TaskPriority.NORMAL
        )
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            priority=task.priority.value,
            status=task.status.value,
            created_at=task.created_at,
            scheduled_at=task.scheduled_at,
            subsystem=task.context.subsystem
        )
    except Exception as e:
        logger.error(f"Error creating backup task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/maintenance")
async def create_maintenance_task(overwatch=Depends(get_overwatch_system)):
    """Create a system maintenance task."""
    try:
        task = overwatch.create_task(
            name="Manual System Maintenance",
            description="Manually triggered system maintenance",
            task_type=TaskType.MAINTENANCE,
            priority=TaskPriority.NORMAL
        )
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            priority=task.priority.value,
            status=task.status.value,
            created_at=task.created_at,
            scheduled_at=task.scheduled_at,
            subsystem=task.context.subsystem
        )
    except Exception as e:
        logger.error(f"Error creating maintenance task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/security-scan")
async def create_security_scan_task(overwatch=Depends(get_overwatch_system)):
    """Create a security scan task."""
    try:
        task = overwatch.create_task(
            name="Manual Security Scan",
            description="Manually triggered security scan",
            task_type=TaskType.SECURITY_SCAN,
            priority=TaskPriority.NORMAL
        )
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            priority=task.priority.value,
            status=task.status.value,
            created_at=task.created_at,
            scheduled_at=task.scheduled_at,
            subsystem=task.context.subsystem
        )
    except Exception as e:
        logger.error(f"Error creating security scan task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/obd2-diagnostic")
async def create_obd2_diagnostic_task(overwatch=Depends(get_overwatch_system)):
    """Create an OBD2 diagnostic task."""
    try:
        task = overwatch.create_task(
            name="Manual OBD2 Diagnostic",
            description="Manually triggered OBD2 diagnostic scan",
            task_type=TaskType.OBD2_DIAGNOSTIC,
            priority=TaskPriority.NORMAL,
            subsystem="obd2"
        )
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type.value,
            priority=task.priority.value,
            status=task.status.value,
            created_at=task.created_at,
            scheduled_at=task.scheduled_at,
            subsystem=task.context.subsystem
        )
    except Exception as e:
        logger.error(f"Error creating OBD2 diagnostic task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_configuration(overwatch=Depends(get_overwatch_system)):
    """Get overwatch system configuration."""
    try:
        return {
            "max_concurrent_tasks": overwatch.task_scheduler.max_concurrent_tasks,
            "generation_interval": overwatch.generation_interval,
            "registered_handlers": list(overwatch.task_scheduler.handlers.keys()),
            "subsystem_handlers": list(overwatch.task_dispatcher.subsystem_handlers.keys())
        }
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_configuration(
    generation_interval: Optional[int] = None,
    overwatch=Depends(get_overwatch_system)
):
    """Update overwatch system configuration."""
    try:
        updated = {}
        
        if generation_interval is not None:
            overwatch.generation_interval = generation_interval
            updated["generation_interval"] = generation_interval
        
        return {
            "message": "Configuration updated successfully",
            "updated": updated
        }
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))