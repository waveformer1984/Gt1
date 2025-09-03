"""
High-performance FastAPI dashboard with optimizations for ballsDeepnit.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

try:
    import orjson
    JSON_AVAILABLE = True
except ImportError:
    JSON_AVAILABLE = False

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from ..core.config import settings
from ..monitoring.performance import performance_monitor, get_memory_usage, optimize_memory_usage
from ..utils.logging import get_logger, timing_decorator
from ..utils.cache import CacheManager


class OptimizedJSONResponse(JSONResponse):
    """JSON response using orjson for better performance."""
    
    def render(self, content: Any) -> bytes:
        if JSON_AVAILABLE:
            return orjson.dumps(content)
        return super().render(content)


# Performance-optimized lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan with performance optimizations."""
    logger = get_logger(__name__)
    
    # Startup
    logger.info("Starting ballsDeepnit dashboard")
    
    # Start performance monitoring
    if settings.monitoring.ENABLE_PERFORMANCE_MONITORING:
        await performance_monitor.start_monitoring()
    
    # Initialize cache
    app.state.cache_manager = CacheManager()
    await app.state.cache_manager.initialize()
    
    # Pre-warm critical endpoints
    await _prewarm_cache(app)
    
    logger.info("Dashboard startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down dashboard")
    
    if hasattr(app.state, 'cache_manager'):
        await app.state.cache_manager.close()
    
    if settings.monitoring.ENABLE_PERFORMANCE_MONITORING:
        await performance_monitor.stop_monitoring()
    
    logger.info("Dashboard shutdown completed")


async def _prewarm_cache(app: FastAPI) -> None:
    """Pre-warm cache with frequently accessed data."""
    logger = get_logger(__name__)
    try:
        # Pre-cache system status
        cache_manager = app.state.cache_manager
        await cache_manager.set("system_status", await _get_system_status(), ttl=30)
        logger.info("Cache pre-warming completed")
    except Exception as e:
        logger.warning(f"Cache pre-warming failed: {e}")


# Create FastAPI app with optimizations
app = FastAPI(
    title="ballsDeepnit Dashboard",
    description="High-performance dashboard for the ballsDeepnit bot framework",
    version=settings.VERSION,
    lifespan=lifespan,
    default_response_class=OptimizedJSONResponse,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add performance middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PerformanceMiddleware:
    """Custom middleware for performance tracking."""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger(__name__)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.perf_counter()
        request_size = scope.get("content_length", 0)
        
        # Create a custom send function to track response size
        response_size = 0
        
        async def custom_send(message):
            nonlocal response_size
            if message["type"] == "http.response.body":
                response_size += len(message.get("body", b""))
            await send(message)
        
        try:
            await self.app(scope, receive, custom_send)
        finally:
            duration = time.perf_counter() - start_time
            
            # Log slow requests
            if duration > 1.0:  # Requests taking more than 1 second
                path = scope.get("path", "unknown")
                method = scope.get("method", "unknown")
                self.logger.warning(
                    f"Slow request: {method} {path} took {duration:.3f}s",
                    extra={
                        "performance": {
                            "duration_ms": duration * 1000,
                            "request_size_bytes": request_size,
                            "response_size_bytes": response_size,
                            "path": path,
                            "method": method,
                        }
                    }
                )


app.add_middleware(PerformanceMiddleware)


# Dependency for cache manager
async def get_cache_manager() -> "CacheManager":
    """Get the cache manager dependency."""
    return app.state.cache_manager


# Performance monitoring endpoints
@app.get("/api/performance/metrics")
@timing_decorator("dashboard.performance_metrics")
async def get_performance_metrics(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """Get current performance metrics with caching."""
    cache_key = "performance_metrics"
    
    # Try to get from cache first
    cached_metrics = await cache_manager.get(cache_key)
    if cached_metrics:
        return cached_metrics
    
    # Get fresh metrics
    metrics = performance_monitor.get_performance_report()
    
    # Cache for 5 seconds to reduce load
    await cache_manager.set(cache_key, metrics, ttl=5)
    
    return metrics


@app.get("/api/performance/memory")
async def get_memory_metrics():
    """Get current memory usage information."""
    return get_memory_usage()


@app.post("/api/performance/optimize")
async def optimize_performance(background_tasks: BackgroundTasks):
    """Trigger performance optimization in the background."""
    background_tasks.add_task(optimize_memory_usage)
    return {"message": "Performance optimization started"}


@app.get("/api/system/status")
@timing_decorator("dashboard.system_status")
async def get_system_status(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """Get cached system status for fast dashboard loading."""
    cache_key = "system_status"
    
    cached_status = await cache_manager.get(cache_key)
    if cached_status:
        return cached_status
    
    status = await _get_system_status()
    await cache_manager.set(cache_key, status, ttl=10)
    
    return status


async def _get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status."""
    try:
        import psutil
        
        # System information
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Process information
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / 1024 / 1024 / 1024,
                "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                "uptime_seconds": time.time() - process.create_time(),
            },
            "process": {
                "memory_rss_mb": process_memory.rss / 1024 / 1024,
                "memory_vms_mb": process_memory.vms / 1024 / 1024,
                "threads": process.num_threads(),
                "cpu_percent": process.cpu_percent(),
            },
            "features": {
                "enabled": list(settings.enabled_features),
                "performance_monitoring": settings.monitoring.ENABLE_PERFORMANCE_MONITORING,
                "caching": True,
            },
            "timestamp": time.time(),
        }
    except Exception as e:
        return {"error": str(e), "timestamp": time.time()}


# Plugin management endpoints
@app.get("/api/plugins")
async def get_plugins():
    """Get list of available plugins."""
    import os
    import importlib.util
    from pathlib import Path
    
    plugins = []
    plugins_dir = Path("src/ballsdeepnit/plugins")
    
    # Create plugins directory if it doesn't exist
    plugins_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Scan for Python files in plugins directory
        for plugin_file in plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue
                
            plugin_name = plugin_file.stem
            
            try:
                # Load plugin metadata
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Extract plugin info
                    plugin_info = {
                        "name": plugin_name,
                        "file": str(plugin_file),
                        "enabled": True,
                        "version": getattr(module, "__version__", "1.0.0"),
                        "description": getattr(module, "__description__", "No description"),
                        "author": getattr(module, "__author__", "Unknown"),
                        "functions": [
                            name for name in dir(module) 
                            if callable(getattr(module, name)) and not name.startswith("_")
                        ],
                        "last_modified": plugin_file.stat().st_mtime
                    }
                    plugins.append(plugin_info)
            except Exception as e:
                # Add error info for problematic plugins
                plugins.append({
                    "name": plugin_name,
                    "file": str(plugin_file),
                    "enabled": False,
                    "error": str(e),
                    "last_modified": plugin_file.stat().st_mtime
                })
                
    except Exception as e:
        return {"error": f"Failed to scan plugins directory: {str(e)}", "plugins": []}
    
    return {
        "plugins": plugins,
        "total": len(plugins),
        "enabled": len([p for p in plugins if p.get("enabled", False)]),
        "plugins_dir": str(plugins_dir.absolute())
    }


@app.post("/api/plugins/{plugin_name}/reload")
async def reload_plugin(plugin_name: str):
    """Hot reload a specific plugin."""
    import importlib
    import sys
    from pathlib import Path
    
    plugins_dir = Path("src/ballsdeepnit/plugins")
    plugin_file = plugins_dir / f"{plugin_name}.py"
    
    if not plugin_file.exists():
        return {
            "success": False,
            "error": f"Plugin '{plugin_name}' not found",
            "plugin_file": str(plugin_file)
        }
    
    try:
        # Module name for the plugin
        module_name = f"ballsdeepnit.plugins.{plugin_name}"
        
        # Remove from sys.modules if it exists
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        # Import the plugin module
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        if not spec or not spec.loader:
            return {
                "success": False,
                "error": f"Could not create module spec for {plugin_name}"
            }
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Extract plugin info after reload
        plugin_info = {
            "name": plugin_name,
            "file": str(plugin_file),
            "enabled": True,
            "version": getattr(module, "__version__", "1.0.0"),
            "description": getattr(module, "__description__", "No description"),
            "author": getattr(module, "__author__", "Unknown"),
            "functions": [
                name for name in dir(module) 
                if callable(getattr(module, name)) and not name.startswith("_")
            ],
            "last_modified": plugin_file.stat().st_mtime,
            "reloaded_at": time.time()
        }
        
        # Call plugin's reload hook if it exists
        if hasattr(module, "on_reload"):
            try:
                module.on_reload()
                plugin_info["reload_hook_called"] = True
            except Exception as hook_error:
                plugin_info["reload_hook_error"] = str(hook_error)
        
        return {
            "success": True,
            "message": f"Plugin '{plugin_name}' reloaded successfully",
            "plugin": plugin_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to reload plugin '{plugin_name}': {str(e)}",
            "plugin_file": str(plugin_file)
        }


# Configuration endpoints
@app.get("/api/config")
async def get_config():
    """Get current configuration (sanitized)."""
    config = {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
        "features": {
            "hot_reload": settings.ENABLE_HOT_RELOAD,
            "voice_triggers": settings.ENABLE_VOICE_TRIGGERS,
            "midi_triggers": settings.ENABLE_MIDI_TRIGGERS,
            "web_dashboard": settings.ENABLE_WEB_DASHBOARD,
        },
        "performance": {
            "max_workers": settings.performance.MAX_WORKERS,
            "async_pool_size": settings.performance.ASYNC_POOL_SIZE,
            "event_loop_policy": settings.performance.EVENT_LOOP_POLICY,
            "caching_enabled": settings.performance.ENABLE_REDIS_CACHE,
        },
    }
    return config


@app.put("/api/config")
async def update_config(config_updates: Dict[str, Any]):
    """Update configuration (limited subset)."""
    import os
    import json
    from pathlib import Path
    
    # Define allowed configuration keys for security
    allowed_updates = {
        "features.hot_reload": bool,
        "features.voice_triggers": bool,
        "features.midi_triggers": bool,
        "features.web_dashboard": bool,
        "performance.max_workers": int,
        "performance.async_pool_size": int,
        "performance.caching_enabled": bool,
        "debug": bool
    }
    
    # Track successful and failed updates
    successful_updates = {}
    failed_updates = {}
    
    try:
        config_file = Path("config.json")
        
        # Load existing config
        if config_file.exists():
            with open(config_file, 'r') as f:
                current_config = json.load(f)
        else:
            current_config = {}
        
        # Process each update request
        for key, new_value in config_updates.items():
            if key not in allowed_updates:
                failed_updates[key] = f"Configuration key '{key}' is not allowed to be updated"
                continue
            
            expected_type = allowed_updates[key]
            if not isinstance(new_value, expected_type):
                failed_updates[key] = f"Expected {expected_type.__name__}, got {type(new_value).__name__}"
                continue
            
            # Apply the update using dot notation
            keys = key.split('.')
            config_section = current_config
            
            # Navigate to the correct nested section
            for k in keys[:-1]:
                if k not in config_section:
                    config_section[k] = {}
                config_section = config_section[k]
            
            # Update the final key
            old_value = config_section.get(keys[-1])
            config_section[keys[-1]] = new_value
            successful_updates[key] = {
                "old_value": old_value,
                "new_value": new_value
            }
        
        # Save updated configuration if any updates were successful
        if successful_updates:
            # Create backup of current config
            backup_file = config_file.with_suffix('.json.backup')
            if config_file.exists():
                import shutil
                shutil.copy2(config_file, backup_file)
            
            # Write new configuration
            with open(config_file, 'w') as f:
                json.dump(current_config, f, indent=2)
            
            # Update runtime settings where possible
            _apply_runtime_config_updates(successful_updates)
        
        return {
            "success": len(successful_updates) > 0,
            "message": f"Updated {len(successful_updates)} configuration(s)",
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "config_file": str(config_file.absolute()),
            "backup_created": len(successful_updates) > 0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update configuration: {str(e)}",
            "successful_updates": successful_updates,
            "failed_updates": failed_updates
        }


def _apply_runtime_config_updates(updates: Dict[str, Any]):
    """Apply configuration updates to runtime settings where possible."""
    try:
        from src.ballsdeepnit.config import settings
        
        for key, update_info in updates.items():
            new_value = update_info["new_value"]
            
            # Map configuration keys to settings attributes
            if key == "debug":
                settings.DEBUG = new_value
            elif key == "features.hot_reload":
                settings.ENABLE_HOT_RELOAD = new_value
            elif key == "features.voice_triggers":
                settings.ENABLE_VOICE_TRIGGERS = new_value
            elif key == "features.midi_triggers":
                settings.ENABLE_MIDI_TRIGGERS = new_value
            elif key == "features.web_dashboard":
                settings.ENABLE_WEB_DASHBOARD = new_value
            elif key == "performance.max_workers":
                settings.performance.MAX_WORKERS = new_value
            elif key == "performance.async_pool_size":
                settings.performance.ASYNC_POOL_SIZE = new_value
            elif key == "performance.caching_enabled":
                settings.performance.ENABLE_REDIS_CACHE = new_value
                
    except Exception as e:
        # Runtime update failures are non-fatal
        logger = get_logger(__name__)
        logger.warning(f"Failed to apply runtime config updates: {e}")


# WebSocket endpoint for real-time metrics
@app.websocket("/ws/metrics")
async def websocket_metrics(websocket):
    """WebSocket endpoint for real-time performance metrics."""
    await websocket.accept()
    logger = get_logger(__name__)
    
    try:
        while True:
            # Send metrics every 2 seconds
            metrics = performance_monitor.get_performance_report()
            await websocket.send_json(metrics)
            await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Fast health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
    }


# Cache management endpoints
@app.get("/api/cache/stats")
async def get_cache_stats(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """Get cache statistics."""
    return await cache_manager.get_stats()


@app.delete("/api/cache")
async def clear_cache(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """Clear all cached data."""
    await cache_manager.clear()
    return {"message": "Cache cleared successfully"}


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors with optimized response."""
    return OptimizedJSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url.path)}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Handle 500 errors with logging."""
    logger = get_logger(__name__)
    logger.error(f"Internal server error: {exc}", exc_info=True)
    
    return OptimizedJSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


class DashboardApp:
    """Main dashboard application wrapper."""
    
    def __init__(self) -> None:
        self.app = app
        self.logger = get_logger(__name__)
    
    def run(self, host: str = None, port: int = None) -> None:
        """Run the dashboard with optimized uvicorn settings."""
        host = host or settings.HOST
        port = port or settings.DASHBOARD_PORT
        
        # Optimized uvicorn configuration
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            loop="uvloop" if settings.performance.EVENT_LOOP_POLICY == "uvloop" else "asyncio",
            workers=1,  # Single worker for dashboard
            log_level="info" if settings.DEBUG else "warning",
            access_log=settings.DEBUG,
            use_colors=settings.DEBUG,
            # Performance optimizations
            limit_concurrency=1000,
            limit_max_requests=10000,
            timeout_keep_alive=30,
            h11_max_incomplete_event_size=16 * 1024,  # 16KB
        )
        
        server = uvicorn.Server(config)
        
        self.logger.info(f"Starting dashboard on http://{host}:{port}")
        server.run()
    
    async def start_async(self, host: str = None, port: int = None) -> None:
        """Start the dashboard asynchronously."""
        host = host or settings.HOST
        port = port or settings.DASHBOARD_PORT
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            loop="uvloop" if settings.performance.EVENT_LOOP_POLICY == "uvloop" else "asyncio",
        )
        
        server = uvicorn.Server(config)
        await server.serve()


def main() -> None:
    """Entry point for the dashboard application."""
    dashboard = DashboardApp()
    dashboard.run()


if __name__ == "__main__":
    main()