#!/usr/bin/env python3
"""
Task Bot API
============

REST API endpoints for the TaskBot system, providing comprehensive task and bot management capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from ..core.task_bot import (
    TaskBot, Bot, BotType, BotStatus, BotCapability, TaskAssignment,
    get_task_bot, initialize_task_bot
)
from ..core.overwatch import Task, TaskType, TaskPriority, TaskStatus, TaskContext

logger = logging.getLogger(__name__)

# Pydantic Models for API

class BotCapabilityRequest(BaseModel):
    name: str
    description: str
    task_types: List[str]
    priority_boost: int = 0
    max_concurrent: int = 1
    metadata: Dict[str, Any] = {}

class BotRegistrationRequest(BaseModel):
    name: str
    bot_type: str = "worker"
    capabilities: List[BotCapabilityRequest] = []
    max_concurrent_tasks: int = 3
    priority_preference: List[str] = []
    metadata: Dict[str, Any] = {}
    contact_info: Dict[str, str] = {}

class BotStatusUpdate(BaseModel):
    status: str

class TaskCreationRequest(BaseModel):
    name: str
    description: str = ""
    task_type: str = "custom"
    priority: str = "normal"
    context: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    subsystem: str = "default"
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class TaskAssignmentRequest(BaseModel):
    task_id: str
    bot_id: Optional[str] = None
    notes: str = ""

class TaskResultSubmission(BaseModel):
    assignment_id: str
    status: str
    result_data: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

class SystemConfigUpdate(BaseModel):
    assignment_strategy: Optional[str] = None
    max_queue_size: Optional[int] = None

# Response Models

class BotResponse(BaseModel):
    id: str
    name: str
    bot_type: str
    status: str
    capabilities: List[Dict[str, Any]]
    max_concurrent_tasks: int
    current_tasks: List[str]
    completed_tasks: int
    failed_tasks: int
    last_seen: Optional[datetime]
    last_task_completed: Optional[datetime]

class TaskResponse(BaseModel):
    id: str
    name: str
    description: str
    task_type: str
    priority: str
    status: str
    created_at: Optional[datetime]
    metadata: Dict[str, Any]

class AssignmentResponse(BaseModel):
    id: str
    task_id: str
    bot_id: str
    assigned_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    notes: str

class SystemStatsResponse(BaseModel):
    task_bot_stats: Dict[str, Any]
    total_bots: int
    online_bots: int
    busy_bots: int
    total_assignments: int
    pending_assignments: int
    queue_size: int
    assignment_strategy: str

# API Setup
app = FastAPI(
    title="TaskBot API",
    description="REST API for TaskBot System - Manage bots and assign tasks",
    version="1.0.0"
)

# Dependency to get TaskBot instance
def get_task_bot_instance() -> TaskBot:
    return get_task_bot()

# Helper functions
def convert_bot_to_response(bot: Bot) -> BotResponse:
    """Convert Bot object to API response format."""
    return BotResponse(
        id=bot.id,
        name=bot.name,
        bot_type=bot.bot_type.value,
        status=bot.status.value,
        capabilities=[{
            "name": cap.name,
            "description": cap.description,
            "task_types": [tt.value for tt in cap.task_types],
            "priority_boost": cap.priority_boost,
            "max_concurrent": cap.max_concurrent,
            "metadata": cap.metadata
        } for cap in bot.capabilities],
        max_concurrent_tasks=bot.max_concurrent_tasks,
        current_tasks=list(bot.current_tasks),
        completed_tasks=bot.completed_tasks,
        failed_tasks=bot.failed_tasks,
        last_seen=bot.last_seen,
        last_task_completed=bot.last_task_completed
    )

def convert_task_to_response(task: Task) -> TaskResponse:
    """Convert Task object to API response format."""
    return TaskResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        task_type=task.task_type.value,
        priority=task.priority.value,
        status=task.status.value,
        created_at=task.created_at,
        metadata=task.metadata
    )

def convert_assignment_to_response(assignment: TaskAssignment) -> AssignmentResponse:
    """Convert TaskAssignment object to API response format."""
    return AssignmentResponse(
        id=assignment.id,
        task_id=assignment.task_id,
        bot_id=assignment.bot_id,
        assigned_at=assignment.assigned_at,
        started_at=assignment.started_at,
        completed_at=assignment.completed_at,
        status=assignment.status.value,
        notes=assignment.notes
    )

# Bot Management Endpoints

@app.post("/api/taskbot/bots/register", response_model=BotResponse)
async def register_bot(
    bot_request: BotRegistrationRequest,
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Register a new bot with the TaskBot system."""
    try:
        # Convert request to Bot object
        capabilities = []
        for cap_req in bot_request.capabilities:
            # Convert string task types to enums
            task_types = []
            for tt_str in cap_req.task_types:
                try:
                    task_types.append(TaskType(tt_str))
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid task type: {tt_str}"
                    )
            
            capability = BotCapability(
                name=cap_req.name,
                description=cap_req.description,
                task_types=task_types,
                priority_boost=cap_req.priority_boost,
                max_concurrent=cap_req.max_concurrent,
                metadata=cap_req.metadata
            )
            capabilities.append(capability)
        
        # Convert priority preferences
        priority_preference = []
        for pp_str in bot_request.priority_preference:
            try:
                priority_preference.append(TaskPriority(pp_str))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid priority: {pp_str}"
                )
        
        bot = Bot(
            name=bot_request.name,
            bot_type=BotType(bot_request.bot_type),
            capabilities=capabilities,
            max_concurrent_tasks=bot_request.max_concurrent_tasks,
            priority_preference=priority_preference,
            metadata=bot_request.metadata,
            contact_info=bot_request.contact_info
        )
        
        success = task_bot.register_bot(bot)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to register bot"
            )
        
        return convert_bot_to_response(bot)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering bot: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/taskbot/bots", response_model=List[BotResponse])
async def list_bots(
    status: Optional[str] = Query(None, description="Filter by bot status"),
    bot_type: Optional[str] = Query(None, description="Filter by bot type"),
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """List all registered bots with optional filtering."""
    try:
        bots = list(task_bot.bots.values())
        
        # Apply filters
        if status:
            try:
                status_enum = BotStatus(status)
                bots = [b for b in bots if b.status == status_enum]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}"
                )
        
        if bot_type:
            try:
                type_enum = BotType(bot_type)
                bots = [b for b in bots if b.bot_type == type_enum]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid bot type: {bot_type}"
                )
        
        return [convert_bot_to_response(bot) for bot in bots]
        
    except Exception as e:
        logger.error(f"Error listing bots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/taskbot/bots/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: str,
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Get details of a specific bot."""
    if bot_id not in task_bot.bots:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    bot = task_bot.bots[bot_id]
    return convert_bot_to_response(bot)

@app.put("/api/taskbot/bots/{bot_id}/status")
async def update_bot_status(
    bot_id: str,
    status_update: BotStatusUpdate,
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Update bot status."""
    try:
        status = BotStatus(status_update.status)
        success = task_bot.update_bot_status(bot_id, status)
        
        if not success:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        return {"message": "Bot status updated successfully"}
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {status_update.status}"
        )
    except Exception as e:
        logger.error(f"Error updating bot status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/taskbot/bots/{bot_id}")
async def unregister_bot(
    bot_id: str,
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Unregister a bot from the system."""
    success = task_bot.unregister_bot(bot_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return {"message": "Bot unregistered successfully"}

@app.get("/api/taskbot/bots/{bot_id}/stats")
async def get_bot_stats(
    bot_id: str,
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Get detailed statistics for a specific bot."""
    stats = task_bot.get_bot_stats(bot_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Convert Bot object to dict for JSON serialization
    stats["bot"] = convert_bot_to_response(stats["bot"]).dict()
    
    return stats

# Task Management Endpoints

@app.post("/api/taskbot/tasks", response_model=TaskResponse)
async def create_task(
    task_request: TaskCreationRequest,
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Create a new task and queue it for assignment."""
    try:
        # Convert string enums to proper enums
        task_type = TaskType(task_request.task_type)
        priority = TaskPriority(task_request.priority)
        
        # Create task context
        context = TaskContext(
            subsystem=task_request.subsystem,
            user_id=task_request.user_id,
            session_id=task_request.session_id,
            metadata=task_request.context
        )
        
        # Create task
        task = Task(
            name=task_request.name,
            description=task_request.description,
            task_type=task_type,
            priority=priority,
            context=context,
            metadata=task_request.metadata
        )
        
        # Queue the task
        success = task_bot.queue_task(task)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to queue task"
            )
        
        return convert_task_to_response(task)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/taskbot/assignments", response_model=AssignmentResponse)
async def assign_task(
    assignment_request: TaskAssignmentRequest,
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Assign a task to a bot."""
    try:
        # First, check if task exists in the overwatch system
        task = task_bot.overwatch.get_task(assignment_request.task_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )
        
        # Assign the task
        assignment = await task_bot.assign_task(
            task,
            bot_id=assignment_request.bot_id
        )
        
        if not assignment:
            raise HTTPException(
                status_code=400,
                detail="Failed to assign task - no suitable bot available"
            )
        
        # Add notes if provided
        assignment.notes = assignment_request.notes
        
        return convert_assignment_to_response(assignment)
        
    except Exception as e:
        logger.error(f"Error assigning task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/taskbot/assignments", response_model=List[AssignmentResponse])
async def list_assignments(
    status: Optional[str] = Query(None, description="Filter by assignment status"),
    bot_id: Optional[str] = Query(None, description="Filter by bot ID"),
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """List task assignments with optional filtering."""
    try:
        assignments = list(task_bot.assignments.values())
        
        # Apply filters
        if status:
            try:
                status_enum = TaskStatus(status)
                assignments = [a for a in assignments if a.status == status_enum]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}"
                )
        
        if bot_id:
            assignments = [a for a in assignments if a.bot_id == bot_id]
        
        return [convert_assignment_to_response(a) for a in assignments]
        
    except Exception as e:
        logger.error(f"Error listing assignments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/taskbot/assignments/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: str,
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Get details of a specific assignment."""
    if assignment_id not in task_bot.assignments:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment = task_bot.assignments[assignment_id]
    return convert_assignment_to_response(assignment)

@app.post("/api/taskbot/assignments/{assignment_id}/complete")
async def complete_assignment(
    assignment_id: str,
    result_submission: TaskResultSubmission,
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Mark an assignment as completed with results."""
    try:
        from ..core.overwatch import TaskResult
        
        # Validate assignment exists
        if assignment_id not in task_bot.assignments:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        assignment = task_bot.assignments[assignment_id]
        
        # Create task result
        status = TaskStatus(result_submission.status)
        result = TaskResult(
            task_id=assignment.task_id,
            status=status,
            result_data=result_submission.result_data,
            error_message=result_submission.error_message,
            end_time=datetime.now(),
            metadata=result_submission.metadata
        )
        
        # Complete the assignment
        success = await task_bot.complete_assignment(assignment_id, result)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to complete assignment"
            )
        
        return {"message": "Assignment completed successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing assignment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# System Management Endpoints

@app.get("/api/taskbot/system/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Get comprehensive system statistics."""
    try:
        stats = task_bot.get_system_stats()
        return SystemStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/taskbot/system/health")
async def health_check(
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """System health check endpoint."""
    try:
        stats = task_bot.get_system_stats()
        
        # Basic health metrics
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "total_bots": stats["total_bots"],
            "online_bots": stats["online_bots"],
            "queue_size": stats["queue_size"],
            "assignment_strategy": stats["assignment_strategy"]
        }
        
        # Determine health status
        if stats["online_bots"] == 0:
            health_status["status"] = "warning"
            health_status["message"] = "No bots online"
        elif stats["queue_size"] > 100:
            health_status["status"] = "warning"
            health_status["message"] = "Large task queue"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "message": "Health check failed"
        }

@app.post("/api/taskbot/system/config")
async def update_system_config(
    config_update: SystemConfigUpdate,
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Update system configuration."""
    try:
        updated_fields = []
        
        if config_update.assignment_strategy:
            if config_update.assignment_strategy in task_bot.assignment_strategies:
                task_bot.current_strategy = config_update.assignment_strategy
                updated_fields.append("assignment_strategy")
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid assignment strategy: {config_update.assignment_strategy}"
                )
        
        return {
            "message": "Configuration updated successfully",
            "updated_fields": updated_fields
        }
        
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Event Stream Endpoints (for real-time updates)

@app.get("/api/taskbot/events/stream")
async def event_stream():
    """Server-sent events stream for real-time updates."""
    # This would require additional implementation for SSE
    # For now, return a simple response
    return {"message": "Event streaming not yet implemented"}

# Utility Endpoints

@app.get("/api/taskbot/available-bots")
async def get_available_bots(
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    task_bot: TaskBot = Depends(get_task_bot_instance)
):
    """Get list of available bots for task assignment."""
    try:
        task_type_enum = None
        if task_type:
            try:
                task_type_enum = TaskType(task_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid task type: {task_type}"
                )
        
        available_bots = task_bot.get_available_bots(task_type_enum)
        return [convert_bot_to_response(bot) for bot in available_bots]
        
    except Exception as e:
        logger.error(f"Error getting available bots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/taskbot/task-types")
async def get_task_types():
    """Get list of available task types."""
    return [{"value": tt.value, "name": tt.value.replace("_", " ").title()} 
            for tt in TaskType]

@app.get("/api/taskbot/bot-types")
async def get_bot_types():
    """Get list of available bot types."""
    return [{"value": bt.value, "name": bt.value.replace("_", " ").title()} 
            for bt in BotType]

@app.get("/api/taskbot/priorities")
async def get_priorities():
    """Get list of available task priorities."""
    return [{"value": tp.value, "name": tp.value.replace("_", " ").title()} 
            for tp in TaskPriority]

# Application startup
@app.on_event("startup")
async def startup_event():
    """Initialize TaskBot system on startup."""
    logger.info("Starting TaskBot API...")
    task_bot = get_task_bot_instance()
    await task_bot.start()
    logger.info("TaskBot API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down TaskBot API...")
    task_bot = get_task_bot_instance()
    await task_bot.stop()
    logger.info("TaskBot API shut down")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Main function for running the API
def main():
    """Run the TaskBot API server."""
    uvicorn.run(
        "src.ballsdeepnit.dashboard.task_bot_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()