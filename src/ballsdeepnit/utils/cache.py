"""
High-performance caching system with Redis and disk cache fallback.
"""

import asyncio
import hashlib
import pickle
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import diskcache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False

try:
    import orjson as json
except ImportError:
    import json

from ..core.config import settings
from ..utils.logging import get_logger, perf_logger


class CacheKey:
    """Utility for generating consistent cache keys."""
    
    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_parts = []
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                # Hash complex objects
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        # Add keyword arguments
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
            key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest()[:8])
        
        return ":".join(key_parts)
    
    @staticmethod
    def namespace_key(namespace: str, key: str) -> str:
        """Add namespace to a cache key."""
        return f"{namespace}:{key}"


class CacheStats:
    """Track cache performance statistics."""
    
    def __init__(self) -> None:
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.total_time = 0.0
        self.start_time = time.time()
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def operations_per_second(self) -> float:
        """Calculate operations per second."""
        elapsed = time.time() - self.start_time
        total_ops = self.hits + self.misses + self.sets + self.deletes
        return total_ops / elapsed if elapsed > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": self.hit_rate,
            "operations_per_second": self.operations_per_second,
            "total_time": self.total_time,
            "uptime_seconds": time.time() - self.start_time,
        }


class CacheManager:
    """High-performance cache manager with Redis and disk cache fallback."""
    
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.stats = CacheStats()
        self.redis_client: Optional[redis.Redis] = None
        self.disk_cache: Optional[diskcache.Cache] = None
        self.config = settings.get_cache_config()
        
        # Cache warming configuration
        self._warm_cache_enabled = True
        self._warm_cache_keys: List[str] = []
    
    async def initialize(self) -> None:
        """Initialize cache backends."""
        # Initialize Redis if available and enabled
        if REDIS_AVAILABLE and settings.performance.ENABLE_REDIS_CACHE:
            try:
                self.redis_client = redis.from_url(
                    settings.performance.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                
                # Test connection
                await self.redis_client.ping()
                self.logger.info("Redis cache initialized successfully")
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize Redis cache: {e}")
                self.redis_client = None
        
        # Initialize disk cache
        if DISKCACHE_AVAILABLE:
            try:
                cache_dir = self.config["disk_cache_dir"]
                cache_dir.mkdir(parents=True, exist_ok=True)
                
                self.disk_cache = diskcache.Cache(
                    str(cache_dir),
                    size_limit=self.config["max_size_mb"] * 1024 * 1024,
                    eviction_policy="least-recently-used",
                    timeout=1.0,
                )
                
                self.logger.info(f"Disk cache initialized at {cache_dir}")
                
            except Exception as e:
                self.logger.warning(f"Failed to initialize disk cache: {e}")
                self.disk_cache = None
        
        if not self.redis_client and not self.disk_cache:
            self.logger.warning("No cache backends available - caching disabled")
    
    async def close(self) -> None:
        """Close cache connections."""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.disk_cache:
            self.disk_cache.close()
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with fallback chain."""
        start_time = time.perf_counter()
        
        try:
            # Try Redis first (fastest)
            if self.redis_client:
                try:
                    value = await self.redis_client.get(key)
                    if value is not None:
                        self.stats.hits += 1
                        result = json.loads(value)
                        
                        # Log cache hit for performance tracking
                        duration = time.perf_counter() - start_time
                        self.stats.total_time += duration
                        
                        perf_logger.log_metric("cache_get", duration * 1000, "ms",
                            cache_type="redis", hit=True, key_prefix=key.split(":")[0]
                        )
                        
                        return result
                        
                except Exception as e:
                    self.logger.debug(f"Redis cache error for key {key}: {e}")
                    self.stats.errors += 1
            
            # Try disk cache as fallback
            if self.disk_cache:
                try:
                    value = self.disk_cache.get(key)
                    if value is not None:
                        self.stats.hits += 1
                        
                        # Promote to Redis if available
                        if self.redis_client:
                            asyncio.create_task(self._promote_to_redis(key, value))
                        
                        duration = time.perf_counter() - start_time
                        self.stats.total_time += duration
                        
                        perf_logger.log_metric("cache_get", duration * 1000, "ms",
                            cache_type="disk", hit=True, key_prefix=key.split(":")[0]
                        )
                        
                        return value
                        
                except Exception as e:
                    self.logger.debug(f"Disk cache error for key {key}: {e}")
                    self.stats.errors += 1
            
            # Cache miss
            self.stats.misses += 1
            duration = time.perf_counter() - start_time
            self.stats.total_time += duration
            
            perf_logger.log_metric("cache_get", duration * 1000, "ms",
                cache_type="miss", hit=False, key_prefix=key.split(":")[0]
            )
            
            return default
            
        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            self.stats.errors += 1
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL."""
        start_time = time.perf_counter()
        ttl = ttl or self.config["ttl_seconds"]
        success = False
        
        try:
            # Store in Redis
            if self.redis_client:
                try:
                    serialized = json.dumps(value)
                    await self.redis_client.setex(key, ttl, serialized)
                    success = True
                except Exception as e:
                    self.logger.debug(f"Redis cache set error for key {key}: {e}")
                    self.stats.errors += 1
            
            # Store in disk cache
            if self.disk_cache:
                try:
                    # Calculate expiration time for disk cache
                    expire_time = time.time() + ttl
                    self.disk_cache.set(key, value, expire=expire_time)
                    success = True
                except Exception as e:
                    self.logger.debug(f"Disk cache set error for key {key}: {e}")
                    self.stats.errors += 1
            
            if success:
                self.stats.sets += 1
                
                # Track warm cache keys
                if self._warm_cache_enabled:
                    if key not in self._warm_cache_keys:
                        self._warm_cache_keys.append(key)
                        # Limit warm cache key tracking
                        if len(self._warm_cache_keys) > 1000:
                            self._warm_cache_keys = self._warm_cache_keys[-500:]
            
            duration = time.perf_counter() - start_time
            self.stats.total_time += duration
            
            perf_logger.log_metric("cache_set", duration * 1000, "ms",
                success=success, key_prefix=key.split(":")[0]
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            self.stats.errors += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        success = False
        
        try:
            # Delete from Redis
            if self.redis_client:
                try:
                    deleted = await self.redis_client.delete(key)
                    success = deleted > 0
                except Exception as e:
                    self.logger.debug(f"Redis cache delete error for key {key}: {e}")
                    self.stats.errors += 1
            
            # Delete from disk cache
            if self.disk_cache:
                try:
                    deleted = self.disk_cache.delete(key)
                    success = success or deleted
                except Exception as e:
                    self.logger.debug(f"Disk cache delete error for key {key}: {e}")
                    self.stats.errors += 1
            
            if success:
                self.stats.deletes += 1
                
                # Remove from warm cache keys
                if key in self._warm_cache_keys:
                    self._warm_cache_keys.remove(key)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            self.stats.errors += 1
            return False
    
    async def clear(self) -> bool:
        """Clear all cache data."""
        success = False
        
        try:
            # Clear Redis
            if self.redis_client:
                try:
                    await self.redis_client.flushdb()
                    success = True
                except Exception as e:
                    self.logger.debug(f"Redis cache clear error: {e}")
                    self.stats.errors += 1
            
            # Clear disk cache
            if self.disk_cache:
                try:
                    self.disk_cache.clear()
                    success = True
                except Exception as e:
                    self.logger.debug(f"Disk cache clear error: {e}")
                    self.stats.errors += 1
            
            # Clear warm cache keys
            self._warm_cache_keys.clear()
            
            self.logger.info("Cache cleared successfully")
            return success
            
        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")
            self.stats.errors += 1
            return False
    
    async def _promote_to_redis(self, key: str, value: Any) -> None:
        """Promote disk cache value to Redis cache."""
        if not self.redis_client:
            return
        
        try:
            serialized = json.dumps(value)
            await self.redis_client.setex(key, self.config["ttl_seconds"], serialized)
        except Exception as e:
            self.logger.debug(f"Failed to promote key {key} to Redis: {e}")
    
    async def warm_cache(self, warm_data: Dict[str, Any]) -> None:
        """Pre-warm cache with frequently accessed data."""
        if not warm_data:
            return
        
        self.logger.info(f"Warming cache with {len(warm_data)} entries")
        
        # Use asyncio.gather for concurrent cache warming
        tasks = []
        for key, value in warm_data.items():
            task = self.set(key, value, ttl=self.config["ttl_seconds"])
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful = sum(1 for result in results if result is True)
            self.logger.info(f"Cache warming completed: {successful}/{len(warm_data)} successful")
        except Exception as e:
            self.logger.error(f"Cache warming error: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = self.stats.to_dict()
        
        # Add backend-specific stats
        if self.redis_client:
            try:
                info = await self.redis_client.info()
                stats["redis"] = {
                    "connected": True,
                    "used_memory_mb": info.get("used_memory", 0) / 1024 / 1024,
                    "connected_clients": info.get("connected_clients", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
            except Exception as e:
                stats["redis"] = {"connected": False, "error": str(e)}
        else:
            stats["redis"] = {"connected": False}
        
        if self.disk_cache:
            try:
                stats["disk"] = {
                    "size_bytes": self.disk_cache.volume(),
                    "size_mb": self.disk_cache.volume() / 1024 / 1024,
                    "count": len(self.disk_cache),
                }
            except Exception as e:
                stats["disk"] = {"error": str(e)}
        else:
            stats["disk"] = {"available": False}
        
        return stats


def cached(ttl: int = 3600, namespace: str = "default", key_func: Optional[Callable] = None):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = CacheKey.make_key(func.__name__, *args, **kwargs)
            
            namespaced_key = CacheKey.namespace_key(namespace, cache_key)
            
            # Try to get from cache
            cache_manager = CacheManager()
            await cache_manager.initialize()
            
            try:
                cached_result = await cache_manager.get(namespaced_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await cache_manager.set(namespaced_key, result, ttl=ttl)
                
                return result
                
            finally:
                await cache_manager.close()
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run in asyncio
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global cache manager instance
global_cache_manager: Optional[CacheManager] = None


async def get_global_cache() -> CacheManager:
    """Get or create global cache manager."""
    global global_cache_manager
    
    if global_cache_manager is None:
        global_cache_manager = CacheManager()
        await global_cache_manager.initialize()
    
    return global_cache_manager


# Utility functions for common caching patterns
async def cache_or_compute(
    key: str,
    compute_func: Callable,
    ttl: int = 3600,
    namespace: str = "default",
    *args,
    **kwargs
) -> Any:
    """Cache result of expensive computation."""
    cache = await get_global_cache()
    namespaced_key = CacheKey.namespace_key(namespace, key)
    
    # Try cache first
    result = await cache.get(namespaced_key)
    if result is not None:
        return result
    
    # Compute and cache
    if asyncio.iscoroutinefunction(compute_func):
        result = await compute_func(*args, **kwargs)
    else:
        result = compute_func(*args, **kwargs)
    
    await cache.set(namespaced_key, result, ttl=ttl)
    return result


async def invalidate_cache_pattern(pattern: str, namespace: str = "default") -> int:
    """Invalidate all cache keys matching a pattern."""
    cache = await get_global_cache()
    
    # This is a simplified implementation
    # In production, you'd want to use Redis SCAN for better performance
    count = 0
    
    if cache.redis_client:
        try:
            keys = await cache.redis_client.keys(f"{namespace}:{pattern}")
            if keys:
                deleted = await cache.redis_client.delete(*keys)
                count += deleted
        except Exception as e:
            cache.logger.error(f"Failed to invalidate Redis pattern {pattern}: {e}")
    
    return count