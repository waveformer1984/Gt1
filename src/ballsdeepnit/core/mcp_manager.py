"""
High-performance MCP (Model Context Protocol) Manager
Optimized for connecting agents to external data sources and tools.
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import weakref

try:
    import mcp
    from mcp import ClientSession, StdioServerParameters, types
    from mcp.client.session import ClientSession as MCPClientSession
    from mcp.server.session import ServerSession as MCPServerSession
    import httpx
    import anyio
except ImportError as e:
    logging.warning(f"MCP dependencies not available: {e}")
    mcp = None

from ..utils.logging import get_logger
from .config import settings
from .mcp_security import get_security_manager

logger = get_logger(__name__)
perf_logger = get_logger(f"{__name__}.performance")


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    priority: int = 1  # Higher numbers = higher priority
    function_types: List[str] = field(default_factory=list)  # Which agent functions can use this
    cache_ttl: int = 300  # Cache responses for 5 minutes by default


@dataclass
class MCPPerformanceMetrics:
    """Performance metrics for MCP operations."""
    server_name: str
    operation_type: str
    execution_time: float
    success: bool
    timestamp: float = field(default_factory=time.time)
    memory_usage: int = 0
    cache_hit: bool = False


class MCPConnectionPool:
    """Connection pool for MCP servers with automatic failover."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections: Dict[str, List[MCPClientSession]] = {}
        self.connection_locks: Dict[str, asyncio.Lock] = {}
        self.connection_health: Dict[str, bool] = {}
        
    async def get_connection(self, server_name: str, config: MCPServerConfig) -> MCPClientSession:
        """Get or create a connection to an MCP server."""
        if server_name not in self.connection_locks:
            self.connection_locks[server_name] = asyncio.Lock()
            
        async with self.connection_locks[server_name]:
            if server_name not in self.connections:
                self.connections[server_name] = []
                
            # Try to get an existing healthy connection
            for conn in self.connections[server_name]:
                if await self._test_connection_health(conn):
                    return conn
                    
            # Create new connection if needed
            if len(self.connections[server_name]) < self.max_connections:
                try:
                    conn = await self._create_connection(config)
                    self.connections[server_name].append(conn)
                    self.connection_health[server_name] = True
                    return conn
                except Exception as e:
                    logger.error(f"Failed to create MCP connection to {server_name}: {e}")
                    self.connection_health[server_name] = False
                    raise
                    
            # All connections are at limit and unhealthy
            raise ConnectionError(f"No healthy connections available for {server_name}")
    
    async def _create_connection(self, config: MCPServerConfig) -> MCPClientSession:
        """Create a new MCP connection."""
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env
        )
        
        session = ClientSession(server_params)
        await session.initialize()
        return session
    
    async def _test_connection_health(self, connection: MCPClientSession) -> bool:
        """Test if a connection is healthy."""
        try:
            # Quick ping test
            await asyncio.wait_for(connection.list_tools(), timeout=5.0)
            return True
        except Exception:
            return False
            
    async def close_all(self):
        """Close all connections."""
        for server_connections in self.connections.values():
            for conn in server_connections:
                try:
                    await conn.close()
                except Exception as e:
                    logger.warning(f"Error closing MCP connection: {e}")
        self.connections.clear()


class MCPCache:
    """High-performance cache for MCP responses."""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.timestamps: Dict[str, float] = {}
        self.max_size = max_size
        self.hit_count = 0
        self.miss_count = 0
        
    def _make_key(self, server_name: str, operation: str, params: Dict[str, Any]) -> str:
        """Create a cache key from operation parameters."""
        return f"{server_name}:{operation}:{hash(json.dumps(params, sort_keys=True))}"
    
    def get(self, server_name: str, operation: str, params: Dict[str, Any], ttl: int) -> Optional[Any]:
        """Get cached result if available and not expired."""
        key = self._make_key(server_name, operation, params)
        
        if key in self.cache:
            if time.time() - self.timestamps[key] < ttl:
                self.hit_count += 1
                return self.cache[key]
            else:
                # Expired
                del self.cache[key]
                del self.timestamps[key]
        
        self.miss_count += 1
        return None
    
    def set(self, server_name: str, operation: str, params: Dict[str, Any], result: Any):
        """Cache a result."""
        key = self._make_key(server_name, operation, params)
        
        # Implement LRU eviction if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entries
            oldest_keys = sorted(self.timestamps.keys(), key=lambda k: self.timestamps[k])[:50]
            for old_key in oldest_keys:
                self.cache.pop(old_key, None)
                self.timestamps.pop(old_key, None)
        
        self.cache[key] = result
        self.timestamps[key] = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "max_size": self.max_size
        }


class MCPFunctionOptimizer:
    """Per-function optimization for MCP operations."""
    
    def __init__(self):
        self.function_profiles: Dict[str, Dict[str, Any]] = {}
        self.optimization_strategies: Dict[str, Callable] = {
            "audio_processing": self._optimize_audio_processing,
            "file_operations": self._optimize_file_operations,
            "api_calls": self._optimize_api_calls,
            "database_queries": self._optimize_database_queries,
            "real_time_data": self._optimize_real_time_data,
        }
    
    def register_function_profile(self, function_type: str, profile: Dict[str, Any]):
        """Register performance profile for a function type."""
        self.function_profiles[function_type] = profile
        logger.info(f"Registered MCP function profile: {function_type}")
    
    def optimize_for_function(self, function_type: str, config: MCPServerConfig) -> MCPServerConfig:
        """Apply function-specific optimizations to MCP server config."""
        if function_type in self.optimization_strategies:
            return self.optimization_strategies[function_type](config)
        return config
    
    def _optimize_audio_processing(self, config: MCPServerConfig) -> MCPServerConfig:
        """Optimize for audio processing functions."""
        config.timeout = 60.0  # Audio processing can take longer
        config.cache_ttl = 0  # Don't cache audio results
        config.priority = 3  # High priority for real-time audio
        return config
    
    def _optimize_file_operations(self, config: MCPServerConfig) -> MCPServerConfig:
        """Optimize for file operations."""
        config.timeout = 30.0
        config.cache_ttl = 600  # Cache file results longer
        config.priority = 2
        return config
    
    def _optimize_api_calls(self, config: MCPServerConfig) -> MCPServerConfig:
        """Optimize for API calls."""
        config.timeout = 15.0
        config.cache_ttl = 300
        config.max_retries = 5  # More retries for API calls
        config.priority = 2
        return config
    
    def _optimize_database_queries(self, config: MCPServerConfig) -> MCPServerConfig:
        """Optimize for database queries."""
        config.timeout = 45.0
        config.cache_ttl = 900  # Cache DB results longer
        config.priority = 1
        return config
    
    def _optimize_real_time_data(self, config: MCPServerConfig) -> MCPServerConfig:
        """Optimize for real-time data operations."""
        config.timeout = 5.0  # Quick timeout for real-time
        config.cache_ttl = 30  # Short cache for real-time data
        config.priority = 5  # Highest priority
        return config


class MCPManager:
    """High-performance MCP manager with per-function optimization."""
    
    def __init__(self):
        self.servers: Dict[str, MCPServerConfig] = {}
        self.connection_pool = MCPConnectionPool(max_connections=settings.performance.MAX_WORKERS)
        self.cache = MCPCache(max_size=settings.performance.CACHE_TTL_SECONDS)
        self.function_optimizer = MCPFunctionOptimizer()
        self.performance_metrics: List[MCPPerformanceMetrics] = []
        self.executor = ThreadPoolExecutor(max_workers=settings.performance.MAX_WORKERS)
        self._initialized = False
        
        # Register default function profiles
        self._register_default_profiles()
    
    def _register_default_profiles(self):
        """Register default optimization profiles for common functions."""
        profiles = {
            "audio_processing": {
                "typical_latency": 2.0,
                "memory_intensive": True,
                "cache_suitable": False
            },
            "file_operations": {
                "typical_latency": 0.5,
                "memory_intensive": False,
                "cache_suitable": True
            },
            "api_calls": {
                "typical_latency": 1.0,
                "memory_intensive": False,
                "cache_suitable": True
            },
            "database_queries": {
                "typical_latency": 3.0,
                "memory_intensive": False,
                "cache_suitable": True
            },
            "real_time_data": {
                "typical_latency": 0.1,
                "memory_intensive": False,
                "cache_suitable": False
            }
        }
        
        for func_type, profile in profiles.items():
            self.function_optimizer.register_function_profile(func_type, profile)
    
    async def initialize(self):
        """Initialize the MCP manager."""
        if self._initialized:
            return
            
        logger.info("Initializing MCP Manager...")
        
        # Load server configurations
        await self._load_server_configs()
        
        # Test connections to all servers
        await self._test_all_connections()
        
        self._initialized = True
        logger.info("MCP Manager initialized successfully")
    
    async def _load_server_configs(self):
        """Load MCP server configurations."""
        # Default servers for common operations
        default_servers = {
            "filesystem": MCPServerConfig(
                name="filesystem",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
                function_types=["file_operations"],
                priority=2
            ),
            "web_search": MCPServerConfig(
                name="web_search",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-brave-search"],
                env={"BRAVE_API_KEY": settings.get("BRAVE_API_KEY", "")},
                function_types=["api_calls", "real_time_data"],
                priority=3
            ),
            "github": MCPServerConfig(
                name="github",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env={"GITHUB_PERSONAL_ACCESS_TOKEN": settings.get("GITHUB_TOKEN", "")},
                function_types=["api_calls", "file_operations"],
                priority=2
            )
        }
        
        for name, config in default_servers.items():
            # Apply function-specific optimizations
            for func_type in config.function_types:
                config = self.function_optimizer.optimize_for_function(func_type, config)
            
            self.servers[name] = config
            logger.info(f"Loaded MCP server config: {name}")
    
    async def _test_all_connections(self):
        """Test connections to all configured servers."""
        tasks = []
        for name, config in self.servers.items():
            tasks.append(self._test_server_connection(name, config))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy_servers = 0
        for i, result in enumerate(results):
            server_name = list(self.servers.keys())[i]
            if isinstance(result, Exception):
                logger.warning(f"MCP server {server_name} failed health check: {result}")
            else:
                healthy_servers += 1
                logger.info(f"MCP server {server_name} is healthy")
        
        logger.info(f"MCP health check complete: {healthy_servers}/{len(self.servers)} servers healthy")
    
    async def _test_server_connection(self, name: str, config: MCPServerConfig):
        """Test connection to a specific server."""
        try:
            connection = await self.connection_pool.get_connection(name, config)
            tools = await connection.list_tools()
            logger.debug(f"MCP server {name} has {len(tools)} tools available")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {name}: {e}")
            raise
    
    async def execute_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        function_type: Optional[str] = None,
        use_cache: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a tool on an MCP server with optimization."""
        start_time = time.time()
        cache_hit = False
        
        if context is None:
            context = {}
        
        try:
            if not self._initialized:
                await self.initialize()
            
            if server_name not in self.servers:
                raise ValueError(f"Unknown MCP server: {server_name}")
            
            config = self.servers[server_name]
            
            # Security validation
            security_manager = get_security_manager()
            if not await security_manager.validate_request(
                agent_id=context.get('agent_id', 'unknown'),
                capability=tool_name,
                arguments=arguments,
                context=context
            ):
                raise PermissionError("Security validation failed")
            
            # Check cache first
            if use_cache and config.cache_ttl > 0:
                cached_result = self.cache.get(server_name, f"tool:{tool_name}", arguments, config.cache_ttl)
                if cached_result is not None:
                    cache_hit = True
                    execution_time = time.time() - start_time
                    
                    # Record metrics
                    metric = MCPPerformanceMetrics(
                        server_name=server_name,
                        operation_type=f"tool:{tool_name}",
                        execution_time=execution_time,
                        success=True,
                        cache_hit=True
                    )
                    self.performance_metrics.append(metric)
                    
                    return cached_result
            
            # Get connection and execute tool
            connection = await self.connection_pool.get_connection(server_name, config)
            result = await connection.call_tool(tool_name, arguments)
            
            # Cache the result
            if use_cache and config.cache_ttl > 0:
                self.cache.set(server_name, f"tool:{tool_name}", arguments, result)
            
            execution_time = time.time() - start_time
            
            # Record metrics
            metric = MCPPerformanceMetrics(
                server_name=server_name,
                operation_type=f"tool:{tool_name}",
                execution_time=execution_time,
                success=True,
                cache_hit=cache_hit
            )
            self.performance_metrics.append(metric)
            
            perf_logger.info(f"MCP tool executed: {server_name}.{tool_name} in {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Record failure metrics
            metric = MCPPerformanceMetrics(
                server_name=server_name,
                operation_type=f"tool:{tool_name}",
                execution_time=execution_time,
                success=False,
                cache_hit=cache_hit
            )
            self.performance_metrics.append(metric)
            
            logger.error(f"MCP tool execution failed: {server_name}.{tool_name}: {e}")
            raise
    
    async def get_available_tools(self, function_type: Optional[str] = None) -> Dict[str, List[str]]:
        """Get available tools, optionally filtered by function type."""
        if not self._initialized:
            await self.initialize()
        
        available_tools = {}
        
        for name, config in self.servers.items():
            # Filter by function type if specified
            if function_type and function_type not in config.function_types:
                continue
            
            try:
                connection = await self.connection_pool.get_connection(name, config)
                tools = await connection.list_tools()
                available_tools[name] = [tool.name for tool in tools]
            except Exception as e:
                logger.warning(f"Failed to list tools for {name}: {e}")
                available_tools[name] = []
        
        return available_tools
    
    async def get_resources(self, server_name: str, use_cache: bool = True) -> List[Any]:
        """Get resources from an MCP server."""
        start_time = time.time()
        cache_hit = False
        
        try:
            if not self._initialized:
                await self.initialize()
            
            if server_name not in self.servers:
                raise ValueError(f"Unknown MCP server: {server_name}")
            
            config = self.servers[server_name]
            
            # Check cache first
            if use_cache and config.cache_ttl > 0:
                cached_result = self.cache.get(server_name, "resources", {}, config.cache_ttl)
                if cached_result is not None:
                    cache_hit = True
                    return cached_result
            
            # Get connection and list resources
            connection = await self.connection_pool.get_connection(server_name, config)
            resources = await connection.list_resources()
            
            # Cache the result
            if use_cache and config.cache_ttl > 0:
                self.cache.set(server_name, "resources", {}, resources)
            
            execution_time = time.time() - start_time
            
            # Record metrics
            metric = MCPPerformanceMetrics(
                server_name=server_name,
                operation_type="list_resources",
                execution_time=execution_time,
                success=True,
                cache_hit=cache_hit
            )
            self.performance_metrics.append(metric)
            
            return resources
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Record failure metrics
            metric = MCPPerformanceMetrics(
                server_name=server_name,
                operation_type="list_resources",
                execution_time=execution_time,
                success=False,
                cache_hit=cache_hit
            )
            self.performance_metrics.append(metric)
            
            logger.error(f"Failed to get resources from {server_name}: {e}")
            raise
    
    def register_server(self, config: MCPServerConfig):
        """Register a new MCP server."""
        # Apply function-specific optimizations
        for func_type in config.function_types:
            config = self.function_optimizer.optimize_for_function(func_type, config)
        
        self.servers[config.name] = config
        logger.info(f"Registered MCP server: {config.name}")
    
    def get_performance_metrics(self, limit: int = 100) -> List[MCPPerformanceMetrics]:
        """Get recent performance metrics."""
        return self.performance_metrics[-limit:]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        return self.cache.get_stats()
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up MCP Manager...")
        await self.connection_pool.close_all()
        self.executor.shutdown(wait=True)
        logger.info("MCP Manager cleanup complete")


# Global MCP manager instance
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """Get the global MCP manager instance."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager


@asynccontextmanager
async def mcp_context():
    """Context manager for MCP operations."""
    manager = get_mcp_manager()
    try:
        await manager.initialize()
        yield manager
    finally:
        await manager.cleanup()