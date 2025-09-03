"""
BallsDeepnit Framework with integrated MCP (Model Context Protocol) support.
High-performance agent system with per-function optimization.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading
import weakref

from ..utils.logging import get_logger
from .config import settings
from .mcp_manager import get_mcp_manager, MCPManager, MCPServerConfig, mcp_context
from .mcp_servers import MCPServerFactory

logger = get_logger(__name__)


@dataclass
class AgentCapability:
    """Represents a capability/function that an agent can perform."""
    name: str
    function_type: str  # audio_processing, file_operations, api_calls, etc.
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    mcp_servers: List[str] = field(default_factory=list)  # Which MCP servers support this
    priority: int = 1
    performance_profile: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentContext:
    """Context information for an agent instance."""
    agent_id: str
    capabilities: List[AgentCapability]
    current_function: Optional[str] = None
    session_data: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    mcp_connections: Dict[str, Any] = field(default_factory=dict)


class AgentRegistry:
    """Registry for managing agent instances and their capabilities."""
    
    def __init__(self):
        self.agents: Dict[str, AgentContext] = {}
        self.capabilities: Dict[str, AgentCapability] = {}
        self.function_types: Dict[str, List[str]] = {}  # function_type -> list of agent_ids
        self.lock = threading.RLock()
    
    def register_agent(self, agent_id: str, capabilities: List[AgentCapability]) -> AgentContext:
        """Register a new agent with its capabilities."""
        with self.lock:
            context = AgentContext(agent_id=agent_id, capabilities=capabilities)
            self.agents[agent_id] = context
            
            # Index capabilities by function type
            for capability in capabilities:
                self.capabilities[f"{agent_id}.{capability.name}"] = capability
                
                if capability.function_type not in self.function_types:
                    self.function_types[capability.function_type] = []
                
                if agent_id not in self.function_types[capability.function_type]:
                    self.function_types[capability.function_type].append(agent_id)
            
            logger.info(f"Registered agent {agent_id} with {len(capabilities)} capabilities")
            return context
    
    def get_agent(self, agent_id: str) -> Optional[AgentContext]:
        """Get agent context by ID."""
        return self.agents.get(agent_id)
    
    def get_agents_by_function_type(self, function_type: str) -> List[str]:
        """Get list of agent IDs that can handle a specific function type."""
        return self.function_types.get(function_type, [])
    
    def get_capability(self, agent_id: str, capability_name: str) -> Optional[AgentCapability]:
        """Get a specific capability for an agent."""
        return self.capabilities.get(f"{agent_id}.{capability_name}")
    
    def update_agent_metrics(self, agent_id: str, metrics: Dict[str, Any]):
        """Update performance metrics for an agent."""
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id].performance_metrics.update(metrics)


class BallsDeepnitFramework:
    """Main framework class with integrated MCP support."""
    
    def __init__(self):
        self.mcp_manager: Optional[MCPManager] = None
        self.agent_registry = AgentRegistry()
        self.executor = ThreadPoolExecutor(max_workers=settings.performance.MAX_WORKERS)
        self.running = False
        self._startup_tasks: List[Callable] = []
        self._shutdown_tasks: List[Callable] = []
        
        # Performance monitoring
        self.performance_stats = {
            "requests_processed": 0,
            "total_execution_time": 0.0,
            "average_response_time": 0.0,
            "cache_hit_rate": 0.0,
            "error_count": 0
        }
        
        # Initialize MCP if enabled
        if settings.mcp.ENABLE_MCP:
            self.mcp_manager = get_mcp_manager()
    
    async def initialize(self):
        """Initialize the framework and all subsystems."""
        if self.running:
            return
        
        logger.info("Initializing BallsDeepnit Framework...")
        
        # Initialize MCP manager
        if self.mcp_manager:
            await self.mcp_manager.initialize()
            logger.info("MCP Manager initialized")
        
        # Register default agent capabilities
        await self._register_default_capabilities()
        
        # Run startup tasks
        for task in self._startup_tasks:
            try:
                if asyncio.iscoroutinefunction(task):
                    await task()
                else:
                    task()
            except Exception as e:
                logger.error(f"Startup task failed: {e}")
        
        self.running = True
        logger.info("BallsDeepnit Framework initialized successfully")
    
    async def _register_default_capabilities(self):
        """Register default agent capabilities based on available MCP servers."""
        if not self.mcp_manager:
            return
        
        # Audio processing capabilities
        audio_capabilities = [
            AgentCapability(
                name="record_audio",
                function_type="audio_processing",
                description="Record audio from input device",
                mcp_servers=["audio-processing"],
                priority=3,
                parameters={"duration": "float", "sample_rate": "int", "channels": "int"}
            ),
            AgentCapability(
                name="analyze_spectrum",
                function_type="audio_processing", 
                description="Analyze audio frequency spectrum",
                mcp_servers=["audio-processing"],
                priority=2,
                parameters={"audio_data": "array", "sample_rate": "int"}
            ),
            AgentCapability(
                name="apply_filter",
                function_type="audio_processing",
                description="Apply audio filters",
                mcp_servers=["audio-processing"],
                priority=2,
                parameters={"audio_data": "array", "filter_type": "string", "cutoff_freq": "float"}
            )
        ]
        
        # File operation capabilities
        file_capabilities = [
            AgentCapability(
                name="read_file",
                function_type="file_operations",
                description="Read file contents",
                mcp_servers=["file-operations", "filesystem"],
                priority=2,
                parameters={"file_path": "string", "encoding": "string"}
            ),
            AgentCapability(
                name="write_file",
                function_type="file_operations",
                description="Write content to file",
                mcp_servers=["file-operations", "filesystem"],
                priority=2,
                parameters={"file_path": "string", "content": "string", "append": "boolean"}
            ),
            AgentCapability(
                name="search_files",
                function_type="file_operations",
                description="Search for files by pattern",
                mcp_servers=["file-operations", "filesystem"],
                priority=1,
                parameters={"pattern": "string", "directory": "string", "recursive": "boolean"}
            )
        ]
        
        # API and web capabilities
        api_capabilities = [
            AgentCapability(
                name="web_search",
                function_type="api_calls",
                description="Search the web for information",
                mcp_servers=["web_search"],
                priority=2,
                parameters={"query": "string", "max_results": "int"}
            ),
            AgentCapability(
                name="github_operations",
                function_type="api_calls",
                description="GitHub repository operations",
                mcp_servers=["github"],
                priority=2,
                parameters={"operation": "string", "repository": "string"}
            )
        ]
        
        # Database capabilities
        db_capabilities = [
            AgentCapability(
                name="execute_query",
                function_type="database_queries",
                description="Execute SQL database queries",
                mcp_servers=["database"],
                priority=1,
                parameters={"query": "string", "params": "array"}
            ),
            AgentCapability(
                name="create_table",
                function_type="database_queries",
                description="Create database tables",
                mcp_servers=["database"],
                priority=1,
                parameters={"table_name": "string", "columns": "object"}
            )
        ]
        
        # Register agents with their capabilities
        all_capabilities = audio_capabilities + file_capabilities + api_capabilities + db_capabilities
        
        # Create specialized agents
        agents = {
            "audio_agent": [cap for cap in all_capabilities if cap.function_type == "audio_processing"],
            "file_agent": [cap for cap in all_capabilities if cap.function_type == "file_operations"],
            "api_agent": [cap for cap in all_capabilities if cap.function_type == "api_calls"],
            "db_agent": [cap for cap in all_capabilities if cap.function_type == "database_queries"],
            "universal_agent": all_capabilities  # Can handle all function types
        }
        
        for agent_id, capabilities in agents.items():
            self.agent_registry.register_agent(agent_id, capabilities)
            logger.info(f"Registered {agent_id} with {len(capabilities)} capabilities")
    
    async def execute_capability(
        self,
        agent_id: str,
        capability_name: str,
        arguments: Dict[str, Any],
        use_cache: bool = True
    ) -> Any:
        """Execute a capability for a specific agent."""
        start_time = time.time()
        
        try:
            # Get agent and capability
            agent = self.agent_registry.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent not found: {agent_id}")
            
            capability = self.agent_registry.get_capability(agent_id, capability_name)
            if not capability:
                raise ValueError(f"Capability not found: {agent_id}.{capability_name}")
            
            # Update agent context
            agent.current_function = capability_name
            
            if not self.mcp_manager:
                raise RuntimeError("MCP Manager not initialized")
            
            # Find the best MCP server for this capability
            best_server = None
            for server_name in capability.mcp_servers:
                if server_name in self.mcp_manager.servers:
                    best_server = server_name
                    break
            
            if not best_server:
                raise RuntimeError(f"No available MCP server for capability: {capability_name}")
            
            # Execute the tool via MCP
            result = await self.mcp_manager.execute_tool(
                server_name=best_server,
                tool_name=capability_name,
                arguments=arguments,
                function_type=capability.function_type,
                use_cache=use_cache
            )
            
            execution_time = time.time() - start_time
            
            # Update performance metrics
            self.agent_registry.update_agent_metrics(agent_id, {
                f"{capability_name}_last_execution_time": execution_time,
                f"{capability_name}_total_calls": agent.performance_metrics.get(f"{capability_name}_total_calls", 0) + 1
            })
            
            # Update framework stats
            self.performance_stats["requests_processed"] += 1
            self.performance_stats["total_execution_time"] += execution_time
            self.performance_stats["average_response_time"] = (
                self.performance_stats["total_execution_time"] / self.performance_stats["requests_processed"]
            )
            
            logger.info(f"Executed {agent_id}.{capability_name} in {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.performance_stats["error_count"] += 1
            
            logger.error(f"Capability execution failed: {agent_id}.{capability_name}: {e}")
            raise
        finally:
            # Clear current function
            if agent_id in self.agent_registry.agents:
                self.agent_registry.agents[agent_id].current_function = None
    
    async def auto_select_agent(self, function_type: str, task_description: str = "") -> Optional[str]:
        """Automatically select the best agent for a given function type."""
        available_agents = self.agent_registry.get_agents_by_function_type(function_type)
        
        if not available_agents:
            return None
        
        # Simple selection: prefer specialized agents over universal ones
        if len(available_agents) == 1:
            return available_agents[0]
        
        # Prioritize by agent type
        priority_order = [
            f"{function_type.split('_')[0]}_agent",  # Specialized agent
            "universal_agent"  # Fallback to universal
        ]
        
        for preferred_agent in priority_order:
            if preferred_agent in available_agents:
                return preferred_agent
        
        # Return first available if no preferred match
        return available_agents[0]
    
    async def execute_task(
        self,
        task: str,
        function_type: str,
        arguments: Dict[str, Any],
        agent_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Any:
        """Execute a task, automatically selecting an agent if not specified."""
        if not agent_id:
            agent_id = await self.auto_select_agent(function_type, task)
            if not agent_id:
                raise ValueError(f"No agents available for function type: {function_type}")
        
        # Map task to capability name (simplified mapping)
        capability_name = task.lower().replace(" ", "_")
        
        return await self.execute_capability(agent_id, capability_name, arguments, use_cache)
    
    def get_available_capabilities(self, function_type: Optional[str] = None) -> Dict[str, List[str]]:
        """Get available capabilities, optionally filtered by function type."""
        capabilities = {}
        
        for agent_id, agent in self.agent_registry.agents.items():
            agent_capabilities = []
            
            for capability in agent.capabilities:
                if function_type is None or capability.function_type == function_type:
                    agent_capabilities.append({
                        "name": capability.name,
                        "function_type": capability.function_type,
                        "description": capability.description,
                        "priority": capability.priority,
                        "parameters": capability.parameters
                    })
            
            if agent_capabilities:
                capabilities[agent_id] = agent_capabilities
        
        return capabilities
    
    async def get_mcp_status(self) -> Dict[str, Any]:
        """Get MCP system status and performance metrics."""
        if not self.mcp_manager:
            return {"mcp_enabled": False}
        
        mcp_metrics = self.mcp_manager.get_performance_metrics()
        cache_stats = self.mcp_manager.get_cache_stats()
        
        return {
            "mcp_enabled": True,
            "servers_count": len(self.mcp_manager.servers),
            "recent_operations": len(mcp_metrics),
            "cache_stats": cache_stats,
            "framework_stats": self.performance_stats,
            "agents_count": len(self.agent_registry.agents),
            "total_capabilities": len(self.agent_registry.capabilities)
        }
    
    def register_startup_task(self, task: Callable):
        """Register a task to run during framework startup."""
        self._startup_tasks.append(task)
    
    def register_shutdown_task(self, task: Callable):
        """Register a task to run during framework shutdown."""
        self._shutdown_tasks.append(task)
    
    async def shutdown(self):
        """Shutdown the framework and clean up resources."""
        if not self.running:
            return
        
        logger.info("Shutting down BallsDeepnit Framework...")
        
        # Run shutdown tasks
        for task in self._shutdown_tasks:
            try:
                if asyncio.iscoroutinefunction(task):
                    await task()
                else:
                    task()
            except Exception as e:
                logger.error(f"Shutdown task failed: {e}")
        
        # Cleanup MCP manager
        if self.mcp_manager:
            await self.mcp_manager.cleanup()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.running = False
        logger.info("BallsDeepnit Framework shutdown complete")
    
    @asynccontextmanager
    async def context(self):
        """Context manager for framework lifecycle."""
        try:
            await self.initialize()
            yield self
        finally:
            await self.shutdown()


# Global framework instance
_framework: Optional[BallsDeepnitFramework] = None


def get_framework() -> BallsDeepnitFramework:
    """Get the global framework instance."""
    global _framework
    if _framework is None:
        _framework = BallsDeepnitFramework()
    return _framework


@asynccontextmanager
async def framework_context():
    """Context manager for framework operations."""
    framework = get_framework()
    async with framework.context():
        yield framework


# Convenience functions for common operations
async def execute_audio_task(task: str, arguments: Dict[str, Any], agent_id: str = None) -> Any:
    """Execute an audio processing task."""
    framework = get_framework()
    return await framework.execute_task(task, "audio_processing", arguments, agent_id)


async def execute_file_task(task: str, arguments: Dict[str, Any], agent_id: str = None) -> Any:
    """Execute a file operation task."""
    framework = get_framework()
    return await framework.execute_task(task, "file_operations", arguments, agent_id)


async def execute_api_task(task: str, arguments: Dict[str, Any], agent_id: str = None) -> Any:
    """Execute an API call task."""
    framework = get_framework()
    return await framework.execute_task(task, "api_calls", arguments, agent_id)


async def execute_db_task(task: str, arguments: Dict[str, Any], agent_id: str = None) -> Any:
    """Execute a database query task."""
    framework = get_framework()
    return await framework.execute_task(task, "database_queries", arguments, agent_id)