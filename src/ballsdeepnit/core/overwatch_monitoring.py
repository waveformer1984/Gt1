#!/usr/bin/env python3
"""
Overwatch Monitoring Integration
===============================

Integration between the overwatch system and existing monitoring infrastructure.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..monitoring.performance import performance_monitor
from .overwatch import get_overwatch, TaskType, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class OverwatchMonitoringIntegration:
    """Integration class that connects overwatch with monitoring systems."""
    
    def __init__(self):
        self.overwatch = get_overwatch()
        self.monitoring_active = False
        self.last_health_check = datetime.now()
        self.health_check_interval = timedelta(minutes=5)
        
        # Performance thresholds
        self.cpu_threshold = 80.0  # %
        self.memory_threshold = 85.0  # %
        self.disk_threshold = 90.0  # %
        
        # Alert history
        self.recent_alerts = []
        self.max_alert_history = 100
    
    async def start_monitoring(self):
        """Start the monitoring integration."""
        if self.monitoring_active:
            logger.warning("Overwatch monitoring is already active")
            return
        
        self.monitoring_active = True
        
        # Start overwatch system if not already running
        if not self.overwatch.running:
            await self.overwatch.start()
        
        # Add custom task generation rules
        self._add_monitoring_rules()
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        logger.info("Overwatch monitoring integration started")
    
    def stop_monitoring(self):
        """Stop the monitoring integration."""
        self.monitoring_active = False
        logger.info("Overwatch monitoring integration stopped")
    
    def _add_monitoring_rules(self):
        """Add custom task generation rules based on monitoring data."""
        
        def performance_alert_rule():
            """Generate tasks when performance thresholds are exceeded."""
            tasks = []
            
            # Get current performance data
            perf_data = performance_monitor.get_current_stats()
            
            if perf_data:
                cpu_usage = perf_data.get("cpu_percent", 0)
                memory_usage = perf_data.get("memory_percent", 0)
                
                # CPU alert
                if cpu_usage > self.cpu_threshold:
                    task = self._create_alert_task(
                        f"High CPU Usage Alert ({cpu_usage:.1f}%)",
                        f"CPU usage is at {cpu_usage:.1f}%, exceeding threshold of {self.cpu_threshold}%",
                        "high_cpu_usage",
                        TaskPriority.HIGH
                    )
                    tasks.append(task)
                
                # Memory alert
                if memory_usage > self.memory_threshold:
                    task = self._create_alert_task(
                        f"High Memory Usage Alert ({memory_usage:.1f}%)",
                        f"Memory usage is at {memory_usage:.1f}%, exceeding threshold of {self.memory_threshold}%",
                        "high_memory_usage",
                        TaskPriority.HIGH
                    )
                    tasks.append(task)
            
            return tasks
        
        def health_check_rule():
            """Generate periodic health checks."""
            tasks = []
            
            now = datetime.now()
            if (now - self.last_health_check) >= self.health_check_interval:
                task = self._create_health_check_task()
                tasks.append(task)
                self.last_health_check = now
            
            return tasks
        
        def system_maintenance_rule():
            """Generate maintenance tasks based on system state."""
            tasks = []
            
            system_state = self.overwatch.system_state
            uptime = system_state.get("uptime", 0)
            
            # Schedule maintenance every 24 hours
            if uptime > 86400 and uptime % 86400 < 300:  # Within 5 minutes of 24-hour mark
                task = self._create_maintenance_task()
                tasks.append(task)
            
            return tasks
        
        # Register the rules
        self.overwatch.add_task_generation_rule(performance_alert_rule)
        self.overwatch.add_task_generation_rule(health_check_rule)
        self.overwatch.add_task_generation_rule(system_maintenance_rule)
    
    def _create_alert_task(self, name: str, description: str, alert_type: str, priority: TaskPriority):
        """Create an alert task."""
        from .overwatch import Task, TaskContext, TaskType
        
        return Task(
            name=name,
            description=description,
            task_type=TaskType.CUSTOM,
            priority=priority,
            context=TaskContext(
                subsystem="monitoring",
                metadata={
                    "alert_type": alert_type,
                    "timestamp": datetime.now().isoformat(),
                    "source": "overwatch_monitoring"
                }
            )
        )
    
    def _create_health_check_task(self):
        """Create a health check task."""
        from .overwatch import Task, TaskContext, TaskType
        
        return Task(
            name="Scheduled Health Check",
            description="Automated system health monitoring check",
            task_type=TaskType.SYSTEM_HEALTH,
            priority=TaskPriority.NORMAL,
            context=TaskContext(
                subsystem="monitoring",
                metadata={
                    "automated": True,
                    "source": "overwatch_monitoring"
                }
            )
        )
    
    def _create_maintenance_task(self):
        """Create a maintenance task."""
        from .overwatch import Task, TaskContext, TaskType
        
        return Task(
            name="Automated System Maintenance",
            description="Automated system maintenance and cleanup",
            task_type=TaskType.MAINTENANCE,
            priority=TaskPriority.LOW,
            scheduled_at=datetime.now() + timedelta(minutes=30),  # Schedule for later
            context=TaskContext(
                subsystem="maintenance",
                metadata={
                    "automated": True,
                    "source": "overwatch_monitoring"
                }
            )
        )
    
    async def _monitoring_loop(self):
        """Main monitoring loop that checks system state and generates alerts."""
        while self.monitoring_active:
            try:
                await self._check_system_health()
                await self._check_task_performance()
                await self._cleanup_old_alerts()
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on errors
    
    async def _check_system_health(self):
        """Check overall system health and generate alerts if needed."""
        try:
            # Get performance data
            perf_data = performance_monitor.get_current_stats()
            
            if not perf_data:
                return
            
            # Check for critical conditions
            critical_conditions = []
            
            cpu_usage = perf_data.get("cpu_percent", 0)
            memory_usage = perf_data.get("memory_percent", 0)
            
            if cpu_usage > 95:
                critical_conditions.append(f"Critical CPU usage: {cpu_usage:.1f}%")
            
            if memory_usage > 95:
                critical_conditions.append(f"Critical memory usage: {memory_usage:.1f}%")
            
            # Generate critical alert if needed
            if critical_conditions:
                alert = {
                    "timestamp": datetime.now(),
                    "type": "critical_system_health",
                    "conditions": critical_conditions,
                    "severity": "critical"
                }
                
                await self._handle_critical_alert(alert)
        
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
    
    async def _check_task_performance(self):
        """Check overwatch task performance and identify issues."""
        try:
            scheduler = self.overwatch.task_scheduler
            stats = scheduler.get_stats()
            
            # Check for performance issues
            issues = []
            
            queue_size = stats.get("queue_size", 0)
            running_tasks = stats.get("running_tasks", 0)
            failed_tasks = len(scheduler.failed_tasks)
            
            if queue_size > 50:
                issues.append(f"Large task queue: {queue_size} tasks")
            
            if running_tasks == scheduler.max_concurrent_tasks:
                issues.append("All task slots occupied")
            
            if failed_tasks > 10:
                issues.append(f"High failure rate: {failed_tasks} recent failures")
            
            # Generate performance alert if needed
            if issues:
                alert = {
                    "timestamp": datetime.now(),
                    "type": "task_performance",
                    "issues": issues,
                    "severity": "warning",
                    "stats": stats
                }
                
                await self._handle_performance_alert(alert)
        
        except Exception as e:
            logger.error(f"Error checking task performance: {e}")
    
    async def _handle_critical_alert(self, alert: Dict[str, Any]):
        """Handle critical system alerts."""
        # Add to alert history
        self.recent_alerts.append(alert)
        
        # Log the alert
        logger.critical(f"CRITICAL ALERT: {alert['conditions']}")
        
        # Generate immediate diagnostic tasks
        diagnostic_task = self.overwatch.create_task(
            name="Critical System Diagnostic",
            description=f"Emergency diagnostic due to: {', '.join(alert['conditions'])}",
            task_type=TaskType.SYSTEM_HEALTH,
            priority=TaskPriority.CRITICAL
        )
        
        # Could also trigger external notifications here
        # e.g., send email, SMS, webhook, etc.
    
    async def _handle_performance_alert(self, alert: Dict[str, Any]):
        """Handle task performance alerts."""
        # Add to alert history
        self.recent_alerts.append(alert)
        
        # Log the alert
        logger.warning(f"PERFORMANCE ALERT: {alert['issues']}")
        
        # Generate performance optimization task
        optimization_task = self.overwatch.create_task(
            name="Performance Optimization",
            description=f"Optimize system performance due to: {', '.join(alert['issues'])}",
            task_type=TaskType.PERFORMANCE_CHECK,
            priority=TaskPriority.HIGH
        )
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts from history."""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        self.recent_alerts = [
            alert for alert in self.recent_alerts
            if alert.get("timestamp", datetime.now()) > cutoff_time
        ]
        
        # Keep only the most recent alerts
        if len(self.recent_alerts) > self.max_alert_history:
            self.recent_alerts = self.recent_alerts[-self.max_alert_history:]
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "monitoring_active": self.monitoring_active,
            "overwatch_running": self.overwatch.running,
            "last_health_check": self.last_health_check.isoformat(),
            "recent_alerts_count": len(self.recent_alerts),
            "thresholds": {
                "cpu": self.cpu_threshold,
                "memory": self.memory_threshold,
                "disk": self.disk_threshold
            },
            "system_state": self.overwatch.system_state
        }
    
    def get_recent_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        # Sort by timestamp (most recent first)
        sorted_alerts = sorted(
            self.recent_alerts,
            key=lambda x: x.get("timestamp", datetime.min),
            reverse=True
        )
        
        return sorted_alerts[:limit]
    
    def update_thresholds(self, 
                         cpu_threshold: Optional[float] = None,
                         memory_threshold: Optional[float] = None,
                         disk_threshold: Optional[float] = None):
        """Update monitoring thresholds."""
        if cpu_threshold is not None:
            self.cpu_threshold = cpu_threshold
        
        if memory_threshold is not None:
            self.memory_threshold = memory_threshold
        
        if disk_threshold is not None:
            self.disk_threshold = disk_threshold
        
        logger.info(f"Updated monitoring thresholds: CPU={self.cpu_threshold}%, "
                   f"Memory={self.memory_threshold}%, Disk={self.disk_threshold}%")


# Global monitoring integration instance
_monitoring_integration: Optional[OverwatchMonitoringIntegration] = None


def get_monitoring_integration() -> OverwatchMonitoringIntegration:
    """Get the global monitoring integration instance."""
    global _monitoring_integration
    if _monitoring_integration is None:
        _monitoring_integration = OverwatchMonitoringIntegration()
    return _monitoring_integration


async def start_overwatch_monitoring():
    """Start the overwatch monitoring integration."""
    integration = get_monitoring_integration()
    await integration.start_monitoring()


def stop_overwatch_monitoring():
    """Stop the overwatch monitoring integration."""
    integration = get_monitoring_integration()
    integration.stop_monitoring()


if __name__ == "__main__":
    # Example usage
    async def main():
        integration = get_monitoring_integration()
        await integration.start_monitoring()
        
        # Run for a while to see monitoring in action
        await asyncio.sleep(60)
        
        # Show monitoring status
        status = integration.get_monitoring_status()
        print(f"Monitoring Status: {status}")
        
        # Show recent alerts
        alerts = integration.get_recent_alerts()
        print(f"Recent Alerts: {len(alerts)}")
        
        integration.stop_monitoring()
    
    asyncio.run(main())