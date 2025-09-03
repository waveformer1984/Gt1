#!/usr/bin/env python3
"""
TaskBot System Demo
==================

A comprehensive demonstration of the TaskBot system showing:
- Bot registration with different capabilities
- Task creation and assignment
- Real-time monitoring
- System health checks
- Different assignment strategies
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
import sys

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ballsdeepnit.core.task_bot import (
    TaskBot, Bot, BotType, BotStatus, BotCapability, 
    initialize_task_bot
)
from src.ballsdeepnit.core.overwatch import (
    Task, TaskType, TaskPriority, TaskContext, TaskResult,
    initialize_overwatch
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TaskBotDemo:
    """Comprehensive TaskBot system demonstration."""
    
    def __init__(self):
        self.task_bot = None
        self.overwatch = None
        self.demo_bots = []
        self.demo_tasks = []
        self.demo_assignments = []
    
    async def initialize(self):
        """Initialize the TaskBot system for demo."""
        print("🚀 Initializing TaskBot Demo System...")
        print("=" * 60)
        
        # Initialize overwatch
        self.overwatch = initialize_overwatch()
        await self.overwatch.start()
        print("✅ Overwatch system started")
        
        # Initialize task bot
        self.task_bot = initialize_task_bot(self.overwatch)
        await self.task_bot.start()
        print("✅ TaskBot system started")
        
        print("🎯 TaskBot Demo System ready!")
        print("=" * 60)
    
    async def register_demo_bots(self):
        """Register a variety of demo bots with different capabilities."""
        print("\n🤖 Registering Demo Bots...")
        print("-" * 40)
        
        # Bot 1: System Administrator Bot
        admin_bot = Bot(
            name="AdminBot Alpha",
            bot_type=BotType.SYSTEM,
            capabilities=[
                BotCapability(
                    name="System Health",
                    description="Performs system health checks and diagnostics",
                    task_types=[TaskType.SYSTEM_HEALTH, TaskType.PERFORMANCE_CHECK],
                    priority_boost=10
                ),
                BotCapability(
                    name="Maintenance",
                    description="Handles system maintenance tasks",
                    task_types=[TaskType.MAINTENANCE],
                    priority_boost=5
                )
            ],
            max_concurrent_tasks=2,
            priority_preference=[TaskPriority.CRITICAL, TaskPriority.HIGH]
        )
        
        # Bot 2: Data Processing Worker
        data_bot = Bot(
            name="DataWorker Beta",
            bot_type=BotType.WORKER,
            capabilities=[
                BotCapability(
                    name="Data Backup",
                    description="Handles data backup and archival operations",
                    task_types=[TaskType.DATA_BACKUP],
                    priority_boost=15
                ),
                BotCapability(
                    name="Performance Analysis",
                    description="Analyzes system performance metrics",
                    task_types=[TaskType.PERFORMANCE_CHECK],
                    priority_boost=8
                )
            ],
            max_concurrent_tasks=3,
            priority_preference=[TaskPriority.NORMAL, TaskPriority.HIGH]
        )
        
        # Bot 3: OBD2 Specialist
        obd2_bot = Bot(
            name="OBD2Specialist Gamma",
            bot_type=BotType.SPECIALIST,
            capabilities=[
                BotCapability(
                    name="OBD2 Diagnostics",
                    description="Specialized OBD2 vehicle diagnostic capabilities",
                    task_types=[TaskType.OBD2_DIAGNOSTIC],
                    priority_boost=20
                )
            ],
            max_concurrent_tasks=1,
            priority_preference=[TaskPriority.HIGH, TaskPriority.CRITICAL]
        )
        
        # Bot 4: Security Monitor
        security_bot = Bot(
            name="SecurityGuard Delta",
            bot_type=BotType.MONITOR,
            capabilities=[
                BotCapability(
                    name="Security Scanning",
                    description="Performs security scans and vulnerability assessments",
                    task_types=[TaskType.SECURITY_SCAN],
                    priority_boost=25
                ),
                BotCapability(
                    name="System Monitoring",
                    description="Continuous system monitoring",
                    task_types=[TaskType.SYSTEM_HEALTH],
                    priority_boost=5
                )
            ],
            max_concurrent_tasks=2,
            priority_preference=[TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.NORMAL]
        )
        
        # Bot 5: General Assistant
        assistant_bot = Bot(
            name="Assistant Echo",
            bot_type=BotType.ASSISTANT,
            capabilities=[
                BotCapability(
                    name="General Tasks",
                    description="Handles various general tasks",
                    task_types=[TaskType.USER_TASK, TaskType.CUSTOM],
                    priority_boost=0
                ),
                BotCapability(
                    name="Backup Assistant",
                    description="Can assist with backup operations",
                    task_types=[TaskType.DATA_BACKUP],
                    priority_boost=3
                )
            ],
            max_concurrent_tasks=4,
            priority_preference=[TaskPriority.NORMAL, TaskPriority.LOW]
        )
        
        # Register all bots
        demo_bots = [admin_bot, data_bot, obd2_bot, security_bot, assistant_bot]
        
        for bot in demo_bots:
            success = self.task_bot.register_bot(bot)
            if success:
                self.demo_bots.append(bot)
                print(f"✅ {bot.name} ({bot.bot_type.value}) - {len(bot.capabilities)} capabilities")
                for cap in bot.capabilities:
                    task_types = [tt.value for tt in cap.task_types]
                    print(f"   • {cap.name}: {', '.join(task_types)}")
            else:
                print(f"❌ Failed to register {bot.name}")
        
        print(f"\n🎉 Registered {len(self.demo_bots)} demo bots successfully!")
    
    async def create_demo_tasks(self):
        """Create a variety of demo tasks."""
        print("\n📋 Creating Demo Tasks...")
        print("-" * 40)
        
        demo_task_configs = [
            {
                "name": "System Health Check",
                "description": "Perform comprehensive system health diagnostics",
                "task_type": TaskType.SYSTEM_HEALTH,
                "priority": TaskPriority.HIGH,
                "subsystem": "health_monitor"
            },
            {
                "name": "Daily Data Backup",
                "description": "Backup critical system data to secure storage",
                "task_type": TaskType.DATA_BACKUP,
                "priority": TaskPriority.NORMAL,
                "subsystem": "backup_system"
            },
            {
                "name": "Vehicle Diagnostic Scan",
                "description": "Run OBD2 diagnostic scan for error codes",
                "task_type": TaskType.OBD2_DIAGNOSTIC,
                "priority": TaskPriority.HIGH,
                "subsystem": "vehicle_diagnostics"
            },
            {
                "name": "Security Vulnerability Scan",
                "description": "Scan system for security vulnerabilities",
                "task_type": TaskType.SECURITY_SCAN,
                "priority": TaskPriority.CRITICAL,
                "subsystem": "security_monitor"
            },
            {
                "name": "Performance Benchmarking",
                "description": "Run performance benchmarks and analysis",
                "task_type": TaskType.PERFORMANCE_CHECK,
                "priority": TaskPriority.NORMAL,
                "subsystem": "performance_monitor"
            },
            {
                "name": "System Maintenance",
                "description": "Perform routine system maintenance tasks",
                "task_type": TaskType.MAINTENANCE,
                "priority": TaskPriority.LOW,
                "subsystem": "maintenance_scheduler"
            },
            {
                "name": "User Request Processing",
                "description": "Process user-submitted custom request",
                "task_type": TaskType.USER_TASK,
                "priority": TaskPriority.NORMAL,
                "subsystem": "user_interface"
            },
            {
                "name": "Emergency System Check",
                "description": "Emergency system status verification",
                "task_type": TaskType.SYSTEM_HEALTH,
                "priority": TaskPriority.CRITICAL,
                "subsystem": "emergency_response"
            }
        ]
        
        for task_config in demo_task_configs:
            context = TaskContext(
                subsystem=task_config["subsystem"],
                user_id="demo_user",
                session_id="demo_session",
                metadata={
                    "demo": True,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            task = Task(
                name=task_config["name"],
                description=task_config["description"],
                task_type=task_config["task_type"],
                priority=task_config["priority"],
                context=context,
                metadata={"demo_task": True}
            )
            
            # Queue the task
            success = self.task_bot.queue_task(task)
            if success:
                self.demo_tasks.append(task)
                priority_icon = self._get_priority_icon(task.priority)
                print(f"✅ {priority_icon} {task.name} ({task.task_type.value})")
            else:
                print(f"❌ Failed to create task: {task.name}")
        
        print(f"\n🎯 Created {len(self.demo_tasks)} demo tasks!")
    
    async def demonstrate_assignment_strategies(self):
        """Demonstrate different assignment strategies."""
        print("\n🧠 Demonstrating Assignment Strategies...")
        print("-" * 40)
        
        strategies = ["best_fit", "load_balanced", "round_robin", "priority_first"]
        
        for strategy in strategies:
            print(f"\n🔄 Testing '{strategy}' strategy...")
            
            # Set the strategy
            old_strategy = self.task_bot.current_strategy
            self.task_bot.current_strategy = strategy
            
            # Create a test task
            test_task = Task(
                name=f"Test Task - {strategy}",
                description=f"Test task for {strategy} assignment strategy",
                task_type=TaskType.CUSTOM,
                priority=TaskPriority.NORMAL,
                context=TaskContext(subsystem="strategy_test"),
                metadata={"strategy_test": strategy}
            )
            
            # Try to assign it
            assignment = await self.task_bot.assign_task(test_task)
            
            if assignment:
                bot = self.task_bot.bots[assignment.bot_id]
                print(f"   ✅ Assigned to: {bot.name} (Score-based selection)")
                self.demo_assignments.append(assignment)
                
                # Simulate task completion
                result = TaskResult(
                    task_id=test_task.id,
                    status=TaskStatus.COMPLETED,
                    result_data={"strategy": strategy, "success": True},
                    execution_time=1.5
                )
                await self.task_bot.complete_assignment(assignment.id, result)
                print(f"   ✅ Task completed successfully")
            else:
                print(f"   ❌ No suitable bot found")
            
            # Restore original strategy
            self.task_bot.current_strategy = old_strategy
            
            # Small delay between tests
            await asyncio.sleep(0.5)
    
    async def monitor_system_status(self):
        """Monitor and display system status."""
        print("\n📊 System Status Monitoring...")
        print("-" * 40)
        
        stats = self.task_bot.get_system_stats()
        
        print(f"📈 System Overview:")
        print(f"   Total Bots: {stats['total_bots']}")
        print(f"   Online Bots: {stats['online_bots']}")
        print(f"   Busy Bots: {stats['busy_bots']}")
        print(f"   Total Assignments: {stats['total_assignments']}")
        print(f"   Pending Assignments: {stats['pending_assignments']}")
        print(f"   Queue Size: {stats['queue_size']}")
        print(f"   Current Strategy: {stats['assignment_strategy']}")
        
        # Bot utilization
        if stats['task_bot_stats']['bot_utilization']:
            print(f"\n🤖 Bot Utilization:")
            for bot_id, utilization in stats['task_bot_stats']['bot_utilization'].items():
                bot = self.task_bot.bots.get(bot_id)
                if bot:
                    print(f"   {bot.name}: {utilization * 100:.1f}%")
        
        # Assignment statistics
        task_stats = stats['task_bot_stats']
        if task_stats['total_assignments'] > 0:
            success_rate = task_stats['successful_assignments'] / task_stats['total_assignments'] * 100
            print(f"\n📊 Assignment Statistics:")
            print(f"   Total: {task_stats['total_assignments']}")
            print(f"   Successful: {task_stats['successful_assignments']}")
            print(f"   Failed: {task_stats['failed_assignments']}")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Avg Assignment Time: {task_stats['avg_assignment_time']:.2f}s")
    
    async def demonstrate_bot_capabilities(self):
        """Show how bots are matched to tasks based on capabilities."""
        print("\n🎯 Demonstrating Bot-Task Matching...")
        print("-" * 40)
        
        # Test each task type with available bots
        task_types_to_test = [
            TaskType.SYSTEM_HEALTH,
            TaskType.OBD2_DIAGNOSTIC,
            TaskType.SECURITY_SCAN,
            TaskType.DATA_BACKUP,
            TaskType.PERFORMANCE_CHECK
        ]
        
        for task_type in task_types_to_test:
            print(f"\n🔍 Task Type: {task_type.value}")
            
            # Find bots that can handle this task type
            available_bots = self.task_bot.get_available_bots(task_type)
            
            if available_bots:
                print(f"   Available Bots ({len(available_bots)}):")
                for bot in available_bots:
                    # Calculate score for this task type
                    test_task = Task(
                        name=f"Test {task_type.value}",
                        task_type=task_type,
                        priority=TaskPriority.NORMAL
                    )
                    score = bot.get_task_score(test_task)
                    
                    # Find relevant capabilities
                    relevant_caps = [cap for cap in bot.capabilities if task_type in cap.task_types]
                    cap_names = [cap.name for cap in relevant_caps]
                    
                    print(f"     • {bot.name}: Score {score} ({', '.join(cap_names)})")
            else:
                print(f"   ❌ No bots available for {task_type.value}")
    
    async def simulate_real_time_operations(self):
        """Simulate real-time task processing."""
        print("\n⚡ Simulating Real-Time Operations...")
        print("-" * 40)
        
        # Process remaining queued tasks
        print(f"📤 Processing {len(self.task_bot.task_queue)} queued tasks...")
        
        processed_count = 0
        while self.task_bot.task_queue and processed_count < 5:  # Limit for demo
            # Let the assignment loop process tasks naturally
            await asyncio.sleep(2)  # Give time for processing
            
            current_assignments = len([a for a in self.task_bot.assignments.values() 
                                     if a.status == TaskStatus.PENDING])
            print(f"   Assignments in progress: {current_assignments}")
            processed_count += 1
        
        # Show final results
        completed_assignments = [a for a in self.task_bot.assignments.values() 
                               if a.status == TaskStatus.COMPLETED]
        print(f"✅ Completed {len(completed_assignments)} assignments")
    
    async def show_detailed_results(self):
        """Show detailed results of the demonstration."""
        print("\n📋 Demo Results Summary...")
        print("=" * 60)
        
        # Bot summary
        print(f"🤖 Registered Bots: {len(self.demo_bots)}")
        for bot in self.demo_bots:
            status_icon = self._get_status_icon(bot.status)
            print(f"   {status_icon} {bot.name}: {bot.completed_tasks} completed, {bot.failed_tasks} failed")
        
        # Task summary
        print(f"\n📋 Created Tasks: {len(self.demo_tasks)}")
        task_by_type = {}
        for task in self.demo_tasks:
            task_type = task.task_type.value
            task_by_type[task_type] = task_by_type.get(task_type, 0) + 1
        
        for task_type, count in task_by_type.items():
            print(f"   • {task_type}: {count}")
        
        # Assignment summary
        print(f"\n🔄 Total Assignments: {len(self.task_bot.assignments)}")
        assignment_by_status = {}
        for assignment in self.task_bot.assignments.values():
            status = assignment.status.value
            assignment_by_status[status] = assignment_by_status.get(status, 0) + 1
        
        for status, count in assignment_by_status.items():
            status_icon = self._get_assignment_status_icon(status)
            print(f"   {status_icon} {status}: {count}")
        
        # Performance metrics
        stats = self.task_bot.get_system_stats()
        task_stats = stats['task_bot_stats']
        
        if task_stats['total_assignments'] > 0:
            success_rate = task_stats['successful_assignments'] / task_stats['total_assignments'] * 100
            print(f"\n📊 Performance Metrics:")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Average Assignment Time: {task_stats['avg_assignment_time']:.2f}s")
        
        print("\n🎉 TaskBot Demo Completed Successfully!")
        print("=" * 60)
    
    async def cleanup(self):
        """Clean up demo resources."""
        print("\n🧹 Cleaning up demo resources...")
        
        if self.task_bot:
            await self.task_bot.stop()
            print("✅ TaskBot stopped")
        
        if self.overwatch:
            await self.overwatch.stop()
            print("✅ Overwatch stopped")
        
        print("👋 Demo cleanup completed!")
    
    # Utility methods
    def _get_priority_icon(self, priority: TaskPriority) -> str:
        """Get icon for task priority."""
        icons = {
            TaskPriority.CRITICAL: "🔴",
            TaskPriority.HIGH: "🟡", 
            TaskPriority.NORMAL: "🟢",
            TaskPriority.LOW: "🔵",
            TaskPriority.BACKGROUND: "⚪"
        }
        return icons.get(priority, "❓")
    
    def _get_status_icon(self, status: BotStatus) -> str:
        """Get icon for bot status."""
        icons = {
            BotStatus.ONLINE: "🟢",
            BotStatus.OFFLINE: "🔴",
            BotStatus.BUSY: "🟡",
            BotStatus.IDLE: "⚪",
            BotStatus.ERROR: "🔴",
            BotStatus.MAINTENANCE: "🟣"
        }
        return icons.get(status, "❓")
    
    def _get_assignment_status_icon(self, status) -> str:
        """Get icon for assignment status."""
        if isinstance(status, str):
            status_map = {
                "pending": "⏳",
                "running": "🔄", 
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫",
                "retrying": "🔁"
            }
            return status_map.get(status, "❓")
        else:
            icons = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.RUNNING: "🔄",
                TaskStatus.COMPLETED: "✅", 
                TaskStatus.FAILED: "❌",
                TaskStatus.CANCELLED: "🚫",
                TaskStatus.RETRYING: "🔁"
            }
            return icons.get(status, "❓")


async def main():
    """Run the TaskBot demonstration."""
    print("🚀 TaskBot System Demonstration")
    print("=" * 60)
    print("This demo will showcase the comprehensive TaskBot system including:")
    print("• Bot registration with different capabilities")
    print("• Intelligent task assignment strategies") 
    print("• Real-time task processing")
    print("• System monitoring and health checks")
    print("• Performance metrics and analytics")
    print("=" * 60)
    
    demo = TaskBotDemo()
    
    try:
        # Run the complete demonstration
        await demo.initialize()
        await demo.register_demo_bots()
        await demo.create_demo_tasks()
        await demo.demonstrate_bot_capabilities()
        await demo.demonstrate_assignment_strategies()
        await demo.monitor_system_status()
        await demo.simulate_real_time_operations()
        await demo.show_detailed_results()
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())