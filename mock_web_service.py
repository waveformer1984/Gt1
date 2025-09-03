#!/usr/bin/env python3
"""
Mock Web Service for Testing
A simplified version of ballsDeepnit web service for testing purposes
"""

import asyncio
import json
import time
import sys
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Mock configuration
class MockSettings:
    APP_NAME = "ballsDeepnit"
    VERSION = "1.0.0"
    DEBUG = True
    HOST = "127.0.0.1"
    DASHBOARD_PORT = 8000

settings = MockSettings()

# Create FastAPI app
app = FastAPI(
    title="ballsDeepnit Mock Dashboard",
    description="Mock web service for testing purposes",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
mock_system_status = {
    "system": {
        "cpu_percent": 25.5,
        "memory_percent": 65.2,
        "memory_available_gb": 8.4,
        "disk_free_gb": 500.2,
        "uptime_seconds": 3600
    },
    "process": {
        "memory_rss_mb": 128.5,
        "memory_vms_mb": 256.8,
        "threads": 8,
        "cpu_percent": 12.3
    },
    "features": {
        "enabled": ["hot_reload", "web_dashboard", "performance_monitoring"],
        "performance_monitoring": True,
        "caching": True
    },
    "timestamp": time.time()
}

mock_performance_metrics = {
    "cpu_usage": 25.5,
    "memory_usage": 65.2,
    "request_count": 1250,
    "response_time_avg": 0.045,
    "error_rate": 0.02,
    "timestamp": time.time()
}

mock_config = {
    "app_name": settings.APP_NAME,
    "version": settings.VERSION,
    "debug": settings.DEBUG,
    "features": {
        "hot_reload": True,
        "voice_triggers": True,
        "midi_triggers": True,
        "web_dashboard": True
    },
    "performance": {
        "max_workers": 8,
        "async_pool_size": 100,
        "event_loop_policy": "uvloop",
        "caching_enabled": True
    }
}

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION
    }

@app.get("/api/system/status")
async def get_system_status():
    """Get system status."""
    # Update timestamp
    mock_system_status["timestamp"] = time.time()
    return mock_system_status

@app.get("/api/performance/metrics")
async def get_performance_metrics():
    """Get performance metrics."""
    # Update timestamp and add some variance
    mock_performance_metrics["timestamp"] = time.time()
    mock_performance_metrics["cpu_usage"] = 20 + (time.time() % 10)
    mock_performance_metrics["request_count"] += 1
    return mock_performance_metrics

@app.get("/api/performance/memory")
async def get_memory_info():
    """Get memory information."""
    return {
        "total_memory_mb": 16384,
        "used_memory_mb": 10689,
        "available_memory_mb": 5695,
        "memory_percent": 65.2,
        "swap_total_mb": 2048,
        "swap_used_mb": 512,
        "timestamp": time.time()
    }

@app.post("/api/performance/optimize")
async def optimize_performance():
    """Trigger performance optimization."""
    await asyncio.sleep(0.1)  # Simulate optimization work
    return {
        "message": "Performance optimization completed",
        "optimizations_applied": [
            "garbage_collection",
            "memory_defragmentation",
            "cache_cleanup"
        ],
        "timestamp": time.time()
    }

@app.get("/api/plugins")
async def get_plugins():
    """Get available plugins."""
    return {
        "plugins": [
            {"name": "voice_recognition", "status": "active", "version": "1.2.0"},
            {"name": "midi_controller", "status": "active", "version": "2.1.0"},
            {"name": "obd2_monitor", "status": "inactive", "version": "1.0.0"}
        ],
        "total_count": 3,
        "active_count": 2
    }

@app.post("/api/plugins/{plugin_name}/reload")
async def reload_plugin(plugin_name: str):
    """Hot reload a plugin."""
    await asyncio.sleep(0.2)  # Simulate reload time
    return {
        "message": f"Plugin {plugin_name} reloaded successfully",
        "plugin_name": plugin_name,
        "reload_time": 0.2,
        "timestamp": time.time()
    }

@app.get("/api/config")
async def get_config():
    """Get configuration."""
    return mock_config

@app.put("/api/config")
async def update_config(config_updates: Dict[str, Any]):
    """Update configuration."""
    return {
        "message": "Configuration updated successfully",
        "updated_fields": list(config_updates.keys()),
        "timestamp": time.time()
    }

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    return {
        "total_keys": 1250,
        "hit_rate": 0.87,
        "miss_rate": 0.13,
        "memory_usage_mb": 45.2,
        "oldest_entry_age": 3600,
        "newest_entry_age": 0.5,
        "timestamp": time.time()
    }

@app.delete("/api/cache")
async def clear_cache():
    """Clear cache."""
    await asyncio.sleep(0.05)  # Simulate clear operation
    return {
        "message": "Cache cleared successfully",
        "keys_removed": 1250,
        "timestamp": time.time()
    }

# WebSocket endpoint for real-time metrics
@app.websocket("/ws/metrics")
async def websocket_metrics(websocket):
    """WebSocket endpoint for real-time metrics."""
    await websocket.accept()
    
    try:
        while True:
            # Send updated metrics every 2 seconds
            metrics = {
                "cpu_usage": 20 + (time.time() % 20),
                "memory_usage": 60 + (time.time() % 30),
                "active_connections": 15 + int(time.time() % 10),
                "requests_per_second": 25 + int(time.time() % 15),
                "timestamp": time.time()
            }
            await websocket.send_json(metrics)
            await asyncio.sleep(2)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

def run_mock_service(host: str = "127.0.0.1", port: int = 8000):
    """Run the mock web service."""
    print(f"🚀 Starting mock ballsDeepnit web service on http://{host}:{port}")
    print("📋 Available endpoints:")
    print("   - GET  /health")
    print("   - GET  /api/system/status")
    print("   - GET  /api/performance/metrics")
    print("   - GET  /api/performance/memory")
    print("   - POST /api/performance/optimize")
    print("   - GET  /api/plugins")
    print("   - POST /api/plugins/{plugin}/reload")
    print("   - GET  /api/config")
    print("   - PUT  /api/config")
    print("   - GET  /api/cache/stats")
    print("   - DELETE /api/cache")
    print("   - WS   /ws/metrics")
    print("   - GET  /docs (API documentation)")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    run_mock_service()