#!/usr/bin/env python3
"""
Unified Cache Manager for ProtoForge Desktop Suite
Implements multi-layer caching with Redis, memory, and disk backends
Performance optimized with async support and automatic fallback
"""

import asyncio
import json
import time
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable, List
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Performance optimized imports
try:
    import orjson
    json_loads = orjson.loads
    json_dumps = lambda obj: orjson.dumps(obj).decode('utf-8')
except ImportError:
    json_loads = json.loads
    json_dumps = json.dumps

try:
    import redis.asyncio as redis
    from redis.asyncio.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from diskcache import Cache as DiskCache
    DISK_CACHE_AVAILABLE = True
except ImportError:
    DISK_CACHE_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    errors: int = 0
    evictions: int = 0
    total_time: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def avg_time(self) -> float:
        """Average operation time in milliseconds."""
        total = self.hits + self.misses
        return (self.total_time / total * 1000) if total > 0 else 0.0


class MemoryCache:
    """High-performance in-memory cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.access_count: Dict[str, int] = {}
        self.stats = CacheStats()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        start_time = time.time()
        
        async with self._lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                
                if time.time() < expiry:
                    self.access_count[key] = self.access_count.get(key, 0) + 1
                    self.stats.hits += 1
                    self.stats.total_time += time.time() - start_time
                    return value
                else:
                    # Expired
                    del self.cache[key]
                    del self.access_count[key]
            
            self.stats.misses += 1
            self.stats.total_time += time.time() - start_time
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL."""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        
        async with self._lock:
            # Evict least accessed if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                await self._evict_least_accessed()
            
            self.cache[key] = (value, expiry)
            self.access_count[key] = 0
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                del self.access_count[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self.cache.clear()
            self.access_count.clear()
    
    async def _evict_least_accessed(self) -> None:
        """Evict least recently accessed entry."""
        if not self.access_count:
            return
        
        # Find least accessed key
        min_key = min(self.access_count, key=self.access_count.get)
        del self.cache[min_key]
        del self.access_count[min_key]
        self.stats.evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "type": "memory",
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": f"{self.stats.hit_rate:.2f}%",
            "avg_time_ms": f"{self.stats.avg_time:.2f}",
            "evictions": self.stats.evictions
        }


class UnifiedCacheManager:
    """Unified cache manager with multi-layer caching support."""
    
    def __init__(self, config_path: str = "optimization_config.json"):
        self.config = self._load_config(config_path)
        self.memory_cache: Optional[MemoryCache] = None
        self.redis_client: Optional[redis.Redis] = None
        self.disk_cache: Optional[DiskCache] = None
        self._initialized = False
        self.stats = {
            "memory": CacheStats(),
            "redis": CacheStats(),
            "disk": CacheStats()
        }
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load optimization configuration."""
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "caching": {
                "memory": {"enabled": True, "max_size": 1000, "ttl_seconds": 300},
                "redis": {"enabled": False},
                "disk": {"enabled": True, "directory": ".cache", "size_limit": "100MB"}
            }
        }
    
    async def initialize(self) -> None:
        """Initialize cache backends."""
        if self._initialized:
            return
        
        cache_config = self.config.get("caching", {})
        
        # Initialize memory cache
        if cache_config.get("memory", {}).get("enabled", True):
            mem_config = cache_config["memory"]
            self.memory_cache = MemoryCache(
                max_size=mem_config.get("max_size", 1000),
                default_ttl=mem_config.get("ttl_seconds", 300)
            )
            logger.info("Memory cache initialized")
        
        # Initialize Redis cache
        if REDIS_AVAILABLE and cache_config.get("redis", {}).get("enabled", False):
            redis_config = cache_config["redis"]
            try:
                pool = ConnectionPool(
                    host=redis_config.get("host", "localhost"),
                    port=redis_config.get("port", 6379),
                    db=redis_config.get("db", 0),
                    password=redis_config.get("password"),
                    decode_responses=True,
                    max_connections=redis_config.get("max_connections", 50),
                    socket_keepalive=True,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                self.redis_client = redis.Redis(connection_pool=pool)
                await self.redis_client.ping()
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis: {e}")
                self.redis_client = None
        
        # Initialize disk cache
        if DISK_CACHE_AVAILABLE and cache_config.get("disk", {}).get("enabled", True):
            disk_config = cache_config["disk"]
            try:
                cache_dir = Path(disk_config.get("directory", ".cache"))
                cache_dir.mkdir(exist_ok=True)
                
                self.disk_cache = DiskCache(
                    str(cache_dir),
                    size_limit=self._parse_size(disk_config.get("size_limit", "100MB")),
                    shards=disk_config.get("shards", 8),
                    timeout=disk_config.get("timeout", 0.01),
                    statistics=disk_config.get("statistics", True)
                )
                logger.info("Disk cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize disk cache: {e}")
                self.disk_cache = None
        
        self._initialized = True
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes."""
        size_str = size_str.upper()
        if size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        return int(size_str)
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get value from cache with automatic fallback."""
        if not self._initialized:
            await self.initialize()
        
        full_key = f"{namespace}:{key}"
        start_time = time.time()
        
        # Try memory cache first (fastest)
        if self.memory_cache:
            value = await self.memory_cache.get(full_key)
            if value is not None:
                self.stats["memory"].hits += 1
                self.stats["memory"].total_time += time.time() - start_time
                return value
            self.stats["memory"].misses += 1
        
        # Try Redis cache (fast, distributed)
        if self.redis_client:
            try:
                value = await self.redis_client.get(full_key)
                if value:
                    # Deserialize and promote to memory cache
                    result = json_loads(value)
                    if self.memory_cache:
                        asyncio.create_task(self.memory_cache.set(full_key, result))
                    self.stats["redis"].hits += 1
                    self.stats["redis"].total_time += time.time() - start_time
                    return result
                self.stats["redis"].misses += 1
            except Exception as e:
                logger.debug(f"Redis get error: {e}")
                self.stats["redis"].errors += 1
        
        # Try disk cache (slower, persistent)
        if self.disk_cache:
            try:
                value = self.disk_cache.get(full_key)
                if value is not None:
                    # Promote to faster caches
                    if self.memory_cache:
                        asyncio.create_task(self.memory_cache.set(full_key, value))
                    if self.redis_client:
                        asyncio.create_task(
                            self.redis_client.set(full_key, json_dumps(value), ex=300)
                        )
                    self.stats["disk"].hits += 1
                    self.stats["disk"].total_time += time.time() - start_time
                    return value
                self.stats["disk"].misses += 1
            except Exception as e:
                logger.debug(f"Disk cache get error: {e}")
                self.stats["disk"].errors += 1
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default"
    ) -> bool:
        """Set value in all cache layers."""
        if not self._initialized:
            await self.initialize()
        
        full_key = f"{namespace}:{key}"
        ttl = ttl or self.config.get("caching", {}).get("memory", {}).get("ttl_seconds", 300)
        
        tasks = []
        
        # Set in memory cache
        if self.memory_cache:
            tasks.append(self.memory_cache.set(full_key, value, ttl))
        
        # Set in Redis cache
        if self.redis_client:
            tasks.append(
                self._set_redis(full_key, value, ttl)
            )
        
        # Set in disk cache
        if self.disk_cache:
            tasks.append(
                asyncio.get_event_loop().run_in_executor(
                    None, self.disk_cache.set, full_key, value, ttl
                )
            )
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return all(r is True or r is None for r in results)
        
        return False
    
    async def _set_redis(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in Redis with error handling."""
        try:
            await self.redis_client.set(key, json_dumps(value), ex=ttl)
            return True
        except Exception as e:
            logger.debug(f"Redis set error: {e}")
            self.stats["redis"].errors += 1
            return False
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete key from all cache layers."""
        if not self._initialized:
            await self.initialize()
        
        full_key = f"{namespace}:{key}"
        tasks = []
        
        if self.memory_cache:
            tasks.append(self.memory_cache.delete(full_key))
        
        if self.redis_client:
            tasks.append(self.redis_client.delete(full_key))
        
        if self.disk_cache:
            tasks.append(
                asyncio.get_event_loop().run_in_executor(
                    None, self.disk_cache.delete, full_key
                )
            )
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return any(r for r in results if r is True)
        
        return False
    
    async def clear(self, namespace: Optional[str] = None) -> None:
        """Clear cache entries."""
        if not self._initialized:
            await self.initialize()
        
        if namespace:
            # Clear specific namespace
            pattern = f"{namespace}:*"
            
            if self.redis_client:
                async for key in self.redis_client.scan_iter(match=pattern):
                    await self.redis_client.delete(key)
            
            # For memory and disk cache, we need to iterate
            # This is less efficient but works
            if self.memory_cache:
                keys_to_delete = [
                    k for k in self.memory_cache.cache.keys()
                    if k.startswith(f"{namespace}:")
                ]
                for key in keys_to_delete:
                    await self.memory_cache.delete(key)
        else:
            # Clear all caches
            if self.memory_cache:
                await self.memory_cache.clear()
            
            if self.redis_client:
                await self.redis_client.flushdb()
            
            if self.disk_cache:
                self.disk_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            "initialized": self._initialized,
            "backends": {}
        }
        
        if self.memory_cache:
            stats["backends"]["memory"] = self.memory_cache.get_stats()
        
        if self.redis_client:
            stats["backends"]["redis"] = {
                "type": "redis",
                "hits": self.stats["redis"].hits,
                "misses": self.stats["redis"].misses,
                "errors": self.stats["redis"].errors,
                "hit_rate": f"{self.stats['redis'].hit_rate:.2f}%",
                "avg_time_ms": f"{self.stats['redis'].avg_time:.2f}"
            }
        
        if self.disk_cache:
            stats["backends"]["disk"] = {
                "type": "disk",
                "hits": self.stats["disk"].hits,
                "misses": self.stats["disk"].misses,
                "errors": self.stats["disk"].errors,
                "hit_rate": f"{self.stats['disk'].hit_rate:.2f}%",
                "avg_time_ms": f"{self.stats['disk'].avg_time:.2f}"
            }
        
        return stats
    
    async def close(self) -> None:
        """Close all cache connections."""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.disk_cache:
            self.disk_cache.close()
        
        self._initialized = False


# Decorator for automatic caching
def cached(
    ttl: int = 300,
    namespace: str = "default",
    key_func: Optional[Callable] = None
):
    """Decorator for automatic function result caching."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Get cache manager instance
            cache_manager = await get_cache_manager()
            
            # Try to get from cache
            result = await cache_manager.get(cache_key, namespace)
            if result is not None:
                return result
            
            # Compute result
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_manager.set(cache_key, result, ttl, namespace)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run in event loop
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Global cache manager instance
_cache_manager: Optional[UnifiedCacheManager] = None


async def get_cache_manager() -> UnifiedCacheManager:
    """Get or create global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = UnifiedCacheManager()
        await _cache_manager.initialize()
    return _cache_manager


# Example usage
if __name__ == "__main__":
    import random
    
    async def demo():
        """Demonstrate cache functionality."""
        cache = await get_cache_manager()
        
        # Test set/get
        await cache.set("test_key", {"data": "test_value"}, ttl=60)
        result = await cache.get("test_key")
        print(f"Retrieved: {result}")
        
        # Test cached decorator
        @cached(ttl=30, namespace="demo")
        async def expensive_operation(n: int) -> int:
            """Simulate expensive operation."""
            await asyncio.sleep(1)  # Simulate work
            return n * n
        
        # First call - will be slow
        start = time.time()
        result1 = await expensive_operation(5)
        print(f"First call: {result1}, took {time.time() - start:.2f}s")
        
        # Second call - should be fast (cached)
        start = time.time()
        result2 = await expensive_operation(5)
        print(f"Second call: {result2}, took {time.time() - start:.2f}s")
        
        # Show statistics
        print("\nCache Statistics:")
        print(json.dumps(cache.get_stats(), indent=2))
        
        # Cleanup
        await cache.close()
    
    # Run demo
    asyncio.run(demo())