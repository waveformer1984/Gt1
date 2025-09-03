"""
Performance-optimized configuration management with caching and validation.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PerformanceSettings(BaseSettings):
    """Performance-related configuration settings."""
    
    # Core performance settings
    MAX_WORKERS: int = Field(default_factory=lambda: min(32, (os.cpu_count() or 1) + 4))
    ASYNC_POOL_SIZE: int = Field(default=100)
    EVENT_LOOP_POLICY: str = Field(default="uvloop")  # uvloop, asyncio
    
    # Memory optimization
    MAX_MEMORY_MB: int = Field(default=1024)
    GARBAGE_COLLECTION_THRESHOLD: int = Field(default=1000)
    ENABLE_MEMORY_PROFILING: bool = Field(default=False)
    
    # Caching configuration
    ENABLE_REDIS_CACHE: bool = Field(default=False)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CACHE_TTL_SECONDS: int = Field(default=3600)
    DISK_CACHE_SIZE_MB: int = Field(default=100)
    
    # Plugin optimization
    PLUGIN_LOAD_TIMEOUT: float = Field(default=5.0)
    MAX_PLUGIN_MEMORY_MB: int = Field(default=256)
    ENABLE_PLUGIN_SANDBOXING: bool = Field(default=True)
    
    # Hot reload performance
    FILE_WATCH_DEBOUNCE_MS: int = Field(default=100)
    MAX_RELOAD_QUEUE_SIZE: int = Field(default=50)
    
    @validator("MAX_WORKERS")
    def validate_max_workers(cls, v: int) -> int:
        """Ensure worker count is reasonable."""
        return max(1, min(v, 64))
    
    @validator("ASYNC_POOL_SIZE")
    def validate_pool_size(cls, v: int) -> int:
        """Ensure pool size is positive."""
        return max(1, v)


class SecuritySettings(BaseSettings):
    """Security-related settings that may impact performance."""
    
    ENABLE_RATE_LIMITING: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    ENABLE_REQUEST_VALIDATION: bool = Field(default=True)
    MAX_REQUEST_SIZE_MB: int = Field(default=10)


class MonitoringSettings(BaseSettings):
    """Performance monitoring configuration."""
    
    ENABLE_PERFORMANCE_MONITORING: bool = Field(default=True)
    METRICS_COLLECTION_INTERVAL: float = Field(default=1.0)
    ENABLE_PROFILING: bool = Field(default=False)
    PROFILING_SAMPLE_RATE: float = Field(default=0.01)
    
    # Prometheus metrics
    ENABLE_PROMETHEUS: bool = Field(default=False)
    PROMETHEUS_PORT: int = Field(default=8090)
    
    # Logging performance
    LOG_LEVEL: str = Field(default="INFO")
    ENABLE_STRUCTURED_LOGGING: bool = Field(default=True)
    LOG_BUFFER_SIZE: int = Field(default=1000)


class Settings(BaseSettings):
    """Main application settings with performance optimizations."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore unknown env vars for performance
    )
    
    # Basic application settings
    APP_NAME: str = Field(default="ballsDeepnit")
    DEBUG: bool = Field(default=False)
    VERSION: str = Field(default="0.1.0")
    
    # Server configuration
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    DASHBOARD_PORT: int = Field(default=8001)
    
    # Directory paths (cached for performance)
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    PLUGINS_DIR: Path = Field(default_factory=lambda: Path("plugins"))
    LOGS_DIR: Path = Field(default_factory=lambda: Path("logs"))
    CACHE_DIR: Path = Field(default_factory=lambda: Path(".cache"))
    
    # Audio/MIDI settings
    AUDIO_DEVICE_INDEX: Optional[int] = Field(default=None)
    MIDI_INPUT_DEVICE: Optional[str] = Field(default=None)
    MIDI_OUTPUT_DEVICE: Optional[str] = Field(default=None)
    AUDIO_SAMPLE_RATE: int = Field(default=44100)
    AUDIO_BUFFER_SIZE: int = Field(default=1024)
    
    # Speech recognition
    SPEECH_RECOGNITION_ENGINE: str = Field(default="google")
    SPEECH_TIMEOUT: float = Field(default=5.0)
    
    # Communication settings
    DISCORD_WEBHOOK_URL: Optional[str] = Field(default=None)
    EMAIL_SMTP_SERVER: Optional[str] = Field(default=None)
    EMAIL_PORT: int = Field(default=587)
    EMAIL_USERNAME: Optional[str] = Field(default=None)
    EMAIL_PASSWORD: Optional[str] = Field(default=None)
    
    # Feature flags for performance tuning
    ENABLE_HOT_RELOAD: bool = Field(default=True)
    ENABLE_VOICE_TRIGGERS: bool = Field(default=True)
    ENABLE_MIDI_TRIGGERS: bool = Field(default=True)
    ENABLE_WEB_DASHBOARD: bool = Field(default=True)
    ENABLE_API_ENDPOINTS: bool = Field(default=True)
    
    # Performance settings
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Create directories if they don't exist
        for directory in [self.PLUGINS_DIR, self.LOGS_DIR, self.CACHE_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    @lru_cache(maxsize=1)
    def enabled_features(self) -> Set[str]:
        """Get a cached set of enabled features for fast lookup."""
        features = set()
        if self.ENABLE_HOT_RELOAD:
            features.add("hot_reload")
        if self.ENABLE_VOICE_TRIGGERS:
            features.add("voice_triggers")
        if self.ENABLE_MIDI_TRIGGERS:
            features.add("midi_triggers")
        if self.ENABLE_WEB_DASHBOARD:
            features.add("web_dashboard")
        if self.ENABLE_API_ENDPOINTS:
            features.add("api_endpoints")
        return features
    
    @property
    @lru_cache(maxsize=1)
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG and os.getenv("ENVIRONMENT") == "production"
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get optimized cache configuration."""
        config = {
            "disk_cache_dir": self.CACHE_DIR / "disk",
            "max_size_mb": self.performance.DISK_CACHE_SIZE_MB,
            "ttl_seconds": self.performance.CACHE_TTL_SECONDS,
        }
        
        if self.performance.ENABLE_REDIS_CACHE:
            config.update({
                "redis_url": self.performance.REDIS_URL,
                "redis_ttl": self.performance.CACHE_TTL_SECONDS,
            })
        
        return config


# Create global settings instance with caching
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance for optimal performance."""
    return Settings()


# Global settings instance
settings = get_settings()

# Performance-related constants
SUPPORTED_AUDIO_FORMATS = frozenset(["wav", "mp3", "flac", "ogg"])
SUPPORTED_MIDI_MESSAGES = frozenset(["note_on", "note_off", "control_change", "program_change"])
DEFAULT_ENCODING = "utf-8"

# Export performance settings for easy access
ENABLE_PERFORMANCE_MONITORING = settings.monitoring.ENABLE_PERFORMANCE_MONITORING
MAX_WORKERS = settings.performance.MAX_WORKERS
ASYNC_POOL_SIZE = settings.performance.ASYNC_POOL_SIZE