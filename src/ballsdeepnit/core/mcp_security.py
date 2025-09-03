"""
MCP Security Framework
Comprehensive security for Model Context Protocol operations.
"""

import asyncio
import time
import hashlib
import hmac
import json
import logging
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from functools import wraps
import ipaddress
import re

from ..utils.logging import get_logger
from .config import settings

logger = get_logger(__name__)


@dataclass
class SecurityEvent:
    """Represents a security event."""
    timestamp: float
    event_type: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    capability: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info, warning, error, critical


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    name: str
    max_requests: int
    window_seconds: int
    scope: str = "global"  # global, ip, user, agent
    capability_pattern: Optional[str] = None


class InputValidator:
    """Validates inputs for MCP operations."""
    
    def __init__(self):
        self.max_string_length = 10000
        self.max_array_length = 1000
        self.max_object_depth = 10
        self.forbidden_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'javascript:',  # JavaScript URLs
            r'data:.*base64',  # Base64 data URLs
            r'\\x[0-9a-fA-F]{2}',  # Hex encoded
            r'eval\s*\(',  # Eval calls
            r'exec\s*\(',  # Exec calls
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                 for pattern in self.forbidden_patterns]
    
    def validate_string(self, value: str, field_name: str = "string") -> bool:
        """Validate string input."""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        
        if len(value) > self.max_string_length:
            raise ValueError(f"{field_name} exceeds maximum length of {self.max_string_length}")
        
        # Check for malicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                logger.warning(f"Malicious pattern detected in {field_name}: {pattern.pattern}")
                raise ValueError(f"Invalid content detected in {field_name}")
        
        return True
    
    def validate_array(self, value: List[Any], field_name: str = "array") -> bool:
        """Validate array input."""
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be an array")
        
        if len(value) > self.max_array_length:
            raise ValueError(f"{field_name} exceeds maximum length of {self.max_array_length}")
        
        # Validate array elements
        for i, item in enumerate(value):
            if isinstance(item, str):
                self.validate_string(item, f"{field_name}[{i}]")
            elif isinstance(item, dict):
                self.validate_object(item, f"{field_name}[{i}]", depth=1)
        
        return True
    
    def validate_object(self, value: Dict[str, Any], field_name: str = "object", depth: int = 0) -> bool:
        """Validate object input."""
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be an object")
        
        if depth > self.max_object_depth:
            raise ValueError(f"{field_name} exceeds maximum nesting depth of {self.max_object_depth}")
        
        # Validate object values
        for key, val in value.items():
            if isinstance(val, str):
                self.validate_string(val, f"{field_name}.{key}")
            elif isinstance(val, list):
                self.validate_array(val, f"{field_name}.{key}")
            elif isinstance(val, dict):
                self.validate_object(val, f"{field_name}.{key}", depth + 1)
        
        return True
    
    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """Validate MCP tool arguments."""
        try:
            self.validate_object(arguments, "arguments")
            return True
        except ValueError as e:
            logger.warning(f"Argument validation failed: {e}")
            raise


class RateLimiter:
    """Rate limiting for MCP operations."""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.rules: List[RateLimitRule] = []
        self.lock = asyncio.Lock()
        
        # Default rate limiting rules
        self.add_rule(RateLimitRule(
            name="global_default",
            max_requests=settings.security.RATE_LIMIT_PER_MINUTE,
            window_seconds=60,
            scope="global"
        ))
        
        self.add_rule(RateLimitRule(
            name="ip_default",
            max_requests=100,
            window_seconds=60,
            scope="ip"
        ))
        
        # Stricter limits for sensitive operations
        self.add_rule(RateLimitRule(
            name="file_operations",
            max_requests=30,
            window_seconds=60,
            scope="ip",
            capability_pattern=".*file.*"
        ))
        
        self.add_rule(RateLimitRule(
            name="database_operations",
            max_requests=20,
            window_seconds=60,
            scope="user",
            capability_pattern=".*database.*|.*query.*"
        ))
    
    def add_rule(self, rule: RateLimitRule):
        """Add a rate limiting rule."""
        self.rules.append(rule)
        logger.info(f"Added rate limit rule: {rule.name}")
    
    def _get_key(self, rule: RateLimitRule, context: Dict[str, Any]) -> str:
        """Generate rate limiting key for a rule and context."""
        if rule.scope == "global":
            return f"global:{rule.name}"
        elif rule.scope == "ip":
            return f"ip:{rule.name}:{context.get('source_ip', 'unknown')}"
        elif rule.scope == "user":
            return f"user:{rule.name}:{context.get('user_id', 'anonymous')}"
        elif rule.scope == "agent":
            return f"agent:{rule.name}:{context.get('agent_id', 'unknown')}"
        else:
            return f"custom:{rule.name}:{rule.scope}"
    
    def _cleanup_old_requests(self, key: str, window_seconds: int):
        """Remove old requests outside the window."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        while self.requests[key] and self.requests[key][0] < cutoff_time:
            self.requests[key].popleft()
    
    async def is_allowed(self, capability: str, context: Dict[str, Any]) -> bool:
        """Check if a request is allowed under rate limiting rules."""
        if not settings.security.ENABLE_RATE_LIMITING:
            return True
        
        async with self.lock:
            current_time = time.time()
            
            for rule in self.rules:
                # Check if rule applies to this capability
                if rule.capability_pattern:
                    if not re.search(rule.capability_pattern, capability, re.IGNORECASE):
                        continue
                
                key = self._get_key(rule, context)
                
                # Clean up old requests
                self._cleanup_old_requests(key, rule.window_seconds)
                
                # Check if limit exceeded
                if len(self.requests[key]) >= rule.max_requests:
                    logger.warning(f"Rate limit exceeded for rule {rule.name}, key: {key}")
                    return False
                
                # Add current request
                self.requests[key].append(current_time)
            
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        stats = {
            "rules_count": len(self.rules),
            "active_keys": len(self.requests),
            "total_requests": sum(len(queue) for queue in self.requests.values())
        }
        
        # Per-rule stats
        rule_stats = {}
        for rule in self.rules:
            matching_keys = [key for key in self.requests.keys() 
                           if key.startswith(f"{rule.scope}:{rule.name}:")]
            rule_stats[rule.name] = {
                "active_keys": len(matching_keys),
                "total_requests": sum(len(self.requests[key]) for key in matching_keys),
                "max_requests": rule.max_requests,
                "window_seconds": rule.window_seconds
            }
        
        stats["rules"] = rule_stats
        return stats


class AccessController:
    """Controls access to MCP capabilities based on permissions."""
    
    def __init__(self):
        self.permissions: Dict[str, Set[str]] = {}
        self.role_permissions: Dict[str, Set[str]] = {}
        self.user_roles: Dict[str, Set[str]] = {}
        
        # Default roles and permissions
        self._setup_default_permissions()
    
    def _setup_default_permissions(self):
        """Setup default roles and permissions."""
        # Admin role - can do everything
        self.role_permissions["admin"] = {
            "*"  # Wildcard for all capabilities
        }
        
        # User role - limited access
        self.role_permissions["user"] = {
            "read_file", "list_directory", "search_files",
            "record_audio", "analyze_spectrum",
            "web_search"
        }
        
        # Service role - for automated services
        self.role_permissions["service"] = {
            "read_file", "write_file", "list_directory",
            "execute_query", "create_table", "insert_data"
        }
        
        # Guest role - very limited
        self.role_permissions["guest"] = {
            "web_search"
        }
        
        # Assign default user role to anonymous users
        self.user_roles["anonymous"] = {"guest"}
        
        logger.info("Default permissions configured")
    
    def add_user_role(self, user_id: str, role: str):
        """Add a role to a user."""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()
        self.user_roles[user_id].add(role)
        logger.info(f"Added role {role} to user {user_id}")
    
    def add_role_permission(self, role: str, capability: str):
        """Add a capability permission to a role."""
        if role not in self.role_permissions:
            self.role_permissions[role] = set()
        self.role_permissions[role].add(capability)
        logger.info(f"Added permission {capability} to role {role}")
    
    def check_permission(self, user_id: str, capability: str) -> bool:
        """Check if a user has permission for a capability."""
        # Get user roles
        user_roles = self.user_roles.get(user_id, {"guest"})
        
        # Check permissions for each role
        for role in user_roles:
            role_perms = self.role_permissions.get(role, set())
            
            # Check for wildcard permission
            if "*" in role_perms:
                return True
            
            # Check for exact capability match
            if capability in role_perms:
                return True
            
            # Check for pattern matches (simple wildcards)
            for perm in role_perms:
                if perm.endswith("*") and capability.startswith(perm[:-1]):
                    return True
        
        logger.warning(f"Access denied: user {user_id} lacks permission for {capability}")
        return False


class SecurityAuditor:
    """Audits and logs security events."""
    
    def __init__(self):
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.event_counts: Dict[str, int] = defaultdict(int)
        self.lock = asyncio.Lock()
    
    async def log_event(self, event: SecurityEvent):
        """Log a security event."""
        async with self.lock:
            self.events.append(event)
            self.event_counts[event.event_type] += 1
            
            # Log based on severity
            log_msg = f"Security event: {event.event_type} - {event.details}"
            
            if event.severity == "critical":
                logger.critical(log_msg)
            elif event.severity == "error":
                logger.error(log_msg)
            elif event.severity == "warning":
                logger.warning(log_msg)
            else:
                logger.info(log_msg)
    
    def get_recent_events(self, limit: int = 100, event_type: str = None) -> List[SecurityEvent]:
        """Get recent security events."""
        events = list(self.events)
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get security audit statistics."""
        return {
            "total_events": len(self.events),
            "event_types": dict(self.event_counts),
            "recent_events_count": len(self.events)
        }


class MCPSecurityManager:
    """Main security manager for MCP operations."""
    
    def __init__(self):
        self.validator = InputValidator()
        self.rate_limiter = RateLimiter()
        self.access_controller = AccessController()
        self.auditor = SecurityAuditor()
        self.enabled = settings.security.ENABLE_REQUEST_VALIDATION
    
    async def validate_request(
        self,
        agent_id: str,
        capability: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Validate an MCP request for security."""
        if not self.enabled:
            return True
        
        try:
            # Input validation
            self.validator.validate_arguments(arguments)
            
            # Rate limiting
            if not await self.rate_limiter.is_allowed(capability, context):
                await self.auditor.log_event(SecurityEvent(
                    timestamp=time.time(),
                    event_type="rate_limit_exceeded",
                    source_ip=context.get("source_ip"),
                    user_id=context.get("user_id"),
                    agent_id=agent_id,
                    capability=capability,
                    severity="warning"
                ))
                return False
            
            # Access control
            user_id = context.get("user_id", "anonymous")
            if not self.access_controller.check_permission(user_id, capability):
                await self.auditor.log_event(SecurityEvent(
                    timestamp=time.time(),
                    event_type="access_denied",
                    source_ip=context.get("source_ip"),
                    user_id=user_id,
                    agent_id=agent_id,
                    capability=capability,
                    severity="warning"
                ))
                return False
            
            # Log successful validation
            await self.auditor.log_event(SecurityEvent(
                timestamp=time.time(),
                event_type="request_validated",
                source_ip=context.get("source_ip"),
                user_id=user_id,
                agent_id=agent_id,
                capability=capability,
                severity="info"
            ))
            
            return True
            
        except Exception as e:
            # Log validation failure
            await self.auditor.log_event(SecurityEvent(
                timestamp=time.time(),
                event_type="validation_error",
                source_ip=context.get("source_ip"),
                user_id=context.get("user_id"),
                agent_id=agent_id,
                capability=capability,
                details={"error": str(e)},
                severity="error"
            ))
            return False
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get overall security status."""
        return {
            "enabled": self.enabled,
            "rate_limiter": self.rate_limiter.get_stats(),
            "auditor": self.auditor.get_stats(),
            "validation_enabled": True,
            "access_control_enabled": True
        }
    
    # Convenience methods for common operations
    def add_user_role(self, user_id: str, role: str):
        """Add a role to a user."""
        self.access_controller.add_user_role(user_id, role)
    
    def add_rate_limit_rule(self, rule: RateLimitRule):
        """Add a rate limiting rule."""
        self.rate_limiter.add_rule(rule)
    
    async def get_recent_security_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent security events as dictionaries."""
        events = self.auditor.get_recent_events(limit)
        return [
            {
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "source_ip": event.source_ip,
                "user_id": event.user_id,
                "agent_id": event.agent_id,
                "capability": event.capability,
                "details": event.details,
                "severity": event.severity
            }
            for event in events
        ]


# Global security manager instance
_security_manager: Optional[MCPSecurityManager] = None


def get_security_manager() -> MCPSecurityManager:
    """Get the global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = MCPSecurityManager()
    return _security_manager


def require_permission(capability: str):
    """Decorator to require permission for a function."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract context from kwargs or create default
            context = kwargs.get('context', {})
            user_id = context.get('user_id', 'anonymous')
            
            security_manager = get_security_manager()
            if not security_manager.access_controller.check_permission(user_id, capability):
                raise PermissionError(f"Access denied for capability: {capability}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(max_requests: int, window_seconds: int = 60, scope: str = "global"):
    """Decorator to apply rate limiting to a function."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            context = kwargs.get('context', {})
            capability = func.__name__
            
            security_manager = get_security_manager()
            if not await security_manager.rate_limiter.is_allowed(capability, context):
                raise Exception(f"Rate limit exceeded for {capability}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator