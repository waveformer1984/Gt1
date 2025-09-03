#!/usr/bin/env python3
"""
TaskBot CLI
===========

Command-line interface for the TaskBot system, providing comprehensive task and bot management capabilities.
"""

import argparse
import asyncio
import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ballsdeepnit.core.task_bot import (
    TaskBot, Bot, BotType, BotStatus, BotCapability, TaskAssignment,
    get_task_bot, initialize_task_bot
)
from src.ballsdeepnit.core.overwatch import (
    Task, TaskType, TaskPriority, TaskStatus, TaskContext, TaskResult,
    get_overwatch, initialize_overwatch
)

logger = logging.getLogger(__name__)


class TaskBotCLI:
    """Command-line interface for TaskBot system."""
    
    def __init__(self):
        self.task_bot: Optional[TaskBot] = None
        self.overwatch = None
    
    async def initialize(self):
        """Initialize the TaskBot and Overwatch systems."""
        try:
            print("🔍 Initializing TaskBot CLI...")
            
            # Initialize overwatch first
            self.overwatch = initialize_overwatch()
            await self.overwatch.start()
            
            # Initialize task bot
            self.task_bot = initialize_task_bot(self.overwatch)
            await self.task_bot.start()
            
            print("✅ TaskBot CLI initialized successfully!")
            
        except Exception as e:
            print(f"❌ Failed to initialize TaskBot CLI: {e}")
            sys.exit(1)
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.task_bot:
            await self.task_bot.stop()
        if self.overwatch:
            await self.overwatch.stop()

    # Bot Management Commands
    
    async def register_bot(self, args):
        """Register a new bot."""
        try:
            capabilities = []
            
            # Parse capabilities from command line
            if args.capabilities:
                for cap_str in args.capabilities:
                    parts = cap_str.split(':')
                    if len(parts) >= 2:
                        name = parts[0]
                        task_types = [TaskType(tt.strip()) for tt in parts[1].split(',')]
                        priority_boost = int(parts[2]) if len(parts) > 2 else 0
                        
                        capability = BotCapability(
                            name=name,
                            description=f"{name} capability",
                            task_types=task_types,
                            priority_boost=priority_boost
                        )
                        capabilities.append(capability)
            
            # Parse priority preferences
            priority_preference = []
            if args.priority_preference:
                priority_preference = [TaskPriority(p.strip()) for p in args.priority_preference.split(',')]
            
            # Create bot
            bot = Bot(
                name=args.name,
                bot_type=BotType(args.bot_type),
                capabilities=capabilities,
                max_concurrent_tasks=args.max_concurrent,
                priority_preference=priority_preference,
                metadata={"cli_registered": True}
            )
            
            # Register with TaskBot system
            success = self.task_bot.register_bot(bot)
            
            if success:
                print(f"✅ Bot '{args.name}' registered successfully!")
                print(f"   • ID: {bot.id}")
                print(f"   • Type: {bot.bot_type.value}")
                print(f"   • Max Concurrent Tasks: {bot.max_concurrent_tasks}")
                print(f"   • Capabilities: {len(bot.capabilities)}")
            else:
                print(f"❌ Failed to register bot '{args.name}'")
                
        except ValueError as e:
            print(f"❌ Invalid value: {e}")
        except Exception as e:
            print(f"❌ Error registering bot: {e}")
    
    async def list_bots(self, args):
        """List all registered bots."""
        try:
            bots = list(self.task_bot.bots.values())
            
            if not bots:
                print("📋 No bots registered")
                return
            
            # Filter by status if specified
            if args.status:
                status_filter = BotStatus(args.status)
                bots = [b for b in bots if b.status == status_filter]
            
            # Filter by type if specified
            if args.bot_type:
                type_filter = BotType(args.bot_type)
                bots = [b for b in bots if b.bot_type == type_filter]
            
            print(f"📋 Registered Bots ({len(bots)} found)")
            print("=" * 60)
            
            for bot in bots:
                status_icon = self._get_status_icon(bot.status)
                print(f"\n{status_icon} {bot.name} ({bot.id[:8]})")
                print(f"   Type: {bot.bot_type.value}")
                print(f"   Status: {bot.status.value}")
                print(f"   Tasks: {len(bot.current_tasks)}/{bot.max_concurrent_tasks}")
                print(f"   Completed: {bot.completed_tasks} | Failed: {bot.failed_tasks}")
                
                if bot.capabilities:
                    cap_names = [cap.name for cap in bot.capabilities]
                    print(f"   Capabilities: {', '.join(cap_names)}")
                
                if bot.last_seen:
                    print(f"   Last Seen: {bot.last_seen.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"❌ Error listing bots: {e}")
    
    async def bot_status(self, args):
        """Show detailed bot status."""
        try:
            if args.bot_id not in self.task_bot.bots:
                print(f"❌ Bot '{args.bot_id}' not found")
                return
            
            bot = self.task_bot.bots[args.bot_id]
            stats = self.task_bot.get_bot_stats(args.bot_id)
            
            status_icon = self._get_status_icon(bot.status)
            print(f"\n{status_icon} Bot Status: {bot.name}")
            print("=" * 50)
            print(f"ID: {bot.id}")
            print(f"Name: {bot.name}")
            print(f"Type: {bot.bot_type.value}")
            print(f"Status: {bot.status.value}")
            print(f"Max Concurrent Tasks: {bot.max_concurrent_tasks}")
            print(f"Current Tasks: {len(bot.current_tasks)}")
            print(f"Completed Tasks: {bot.completed_tasks}")
            print(f"Failed Tasks: {bot.failed_tasks}")
            
            if stats:
                print(f"Success Rate: {stats['completed_assignments'] / max(stats['total_assignments'], 1) * 100:.1f}%")
                print(f"Utilization: {stats['utilization'] * 100:.1f}%")
            
            if bot.last_seen:
                print(f"Last Seen: {bot.last_seen.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if bot.last_task_completed:
                print(f"Last Task Completed: {bot.last_task_completed.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if bot.capabilities:
                print("\nCapabilities:")
                for cap in bot.capabilities:
                    task_types = [tt.value for tt in cap.task_types]
                    print(f"  • {cap.name}: {', '.join(task_types)}")
                    if cap.priority_boost > 0:
                        print(f"    Priority Boost: +{cap.priority_boost}")
            
            if bot.current_tasks:
                print(f"\nCurrent Tasks: {', '.join(bot.current_tasks)}")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error getting bot status: {e}")
    
    async def update_bot_status(self, args):
        """Update bot status."""
        try:
            status = BotStatus(args.status)
            success = self.task_bot.update_bot_status(args.bot_id, status)
            
            if success:
                print(f"✅ Bot status updated to '{status.value}'")
            else:
                print(f"❌ Bot '{args.bot_id}' not found")
                
        except ValueError:
            print(f"❌ Invalid status: {args.status}")
            print(f"Valid statuses: {[s.value for s in BotStatus]}")
        except Exception as e:
            print(f"❌ Error updating bot status: {e}")
    
    async def unregister_bot(self, args):
        """Unregister a bot."""
        try:
            if args.bot_id not in self.task_bot.bots:
                print(f"❌ Bot '{args.bot_id}' not found")
                return
            
            bot_name = self.task_bot.bots[args.bot_id].name
            
            # Confirm if not forced
            if not args.force:
                confirm = input(f"⚠️  Are you sure you want to unregister bot '{bot_name}'? (y/N): ")
                if confirm.lower() != 'y':
                    print("Cancelled")
                    return
            
            success = self.task_bot.unregister_bot(args.bot_id)
            
            if success:
                print(f"✅ Bot '{bot_name}' unregistered successfully")
            else:
                print(f"❌ Failed to unregister bot")
                
        except Exception as e:
            print(f"❌ Error unregistering bot: {e}")

    # Task Management Commands
    
    async def create_task(self, args):
        """Create a new task."""
        try:
            # Parse task type and priority
            task_type = TaskType(args.task_type)
            priority = TaskPriority(args.priority)
            
            # Create task context
            context = TaskContext(
                subsystem=args.subsystem,
                user_id=args.user_id,
                session_id=args.session_id,
                metadata={"cli_created": True}
            )
            
            # Create task
            task = Task(
                name=args.name,
                description=args.description or f"CLI-created {task_type.value} task",
                task_type=task_type,
                priority=priority,
                context=context,
                metadata={"created_by": "cli"}
            )
            
            # Queue the task
            success = self.task_bot.queue_task(task)
            
            if success:
                print(f"✅ Task '{args.name}' created and queued successfully!")
                print(f"   • ID: {task.id}")
                print(f"   • Type: {task.task_type.value}")
                print(f"   • Priority: {task.priority.value}")
                print(f"   • Subsystem: {task.context.subsystem}")
            else:
                print(f"❌ Failed to create task '{args.name}'")
                
        except ValueError as e:
            print(f"❌ Invalid value: {e}")
        except Exception as e:
            print(f"❌ Error creating task: {e}")
    
    async def assign_task(self, args):
        """Assign a task to a bot."""
        try:
            # Check if task exists in overwatch system
            task = self.overwatch.get_task(args.task_id)
            if not task:
                print(f"❌ Task '{args.task_id}' not found")
                return
            
            # Assign the task
            assignment = await self.task_bot.assign_task(task, bot_id=args.bot_id)
            
            if assignment:
                bot_name = self.task_bot.bots[assignment.bot_id].name
                print(f"✅ Task assigned successfully!")
                print(f"   • Assignment ID: {assignment.id}")
                print(f"   • Task: {task.name} ({task.id[:8]})")
                print(f"   • Bot: {bot_name} ({assignment.bot_id[:8]})")
                print(f"   • Assigned At: {assignment.assigned_at.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"❌ Failed to assign task - no suitable bot available")
                
        except Exception as e:
            print(f"❌ Error assigning task: {e}")
    
    async def list_assignments(self, args):
        """List task assignments."""
        try:
            assignments = list(self.task_bot.assignments.values())
            
            # Filter by status if specified
            if args.status:
                status_filter = TaskStatus(args.status)
                assignments = [a for a in assignments if a.status == status_filter]
            
            # Filter by bot if specified
            if args.bot_id:
                assignments = [a for a in assignments if a.bot_id == args.bot_id]
            
            if not assignments:
                print("📋 No assignments found")
                return
            
            print(f"📋 Task Assignments ({len(assignments)} found)")
            print("=" * 80)
            
            for assignment in assignments:
                status_icon = self._get_assignment_status_icon(assignment.status)
                bot_name = self.task_bot.bots.get(assignment.bot_id, {}).get('name', 'Unknown')
                
                print(f"\n{status_icon} Assignment {assignment.id[:8]}")
                print(f"   Task: {assignment.task_id[:8]}")
                print(f"   Bot: {bot_name} ({assignment.bot_id[:8]})")
                print(f"   Status: {assignment.status.value}")
                print(f"   Assigned: {assignment.assigned_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if assignment.started_at:
                    print(f"   Started: {assignment.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if assignment.completed_at:
                    print(f"   Completed: {assignment.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    duration = assignment.completed_at - assignment.assigned_at
                    print(f"   Duration: {duration.total_seconds():.1f}s")
                
                if assignment.notes:
                    print(f"   Notes: {assignment.notes}")
            
            print("\n" + "=" * 80)
            
        except Exception as e:
            print(f"❌ Error listing assignments: {e}")

    # System Management Commands
    
    async def system_status(self, args):
        """Show system status."""
        try:
            stats = self.task_bot.get_system_stats()
            
            print("🔍 TaskBot System Status")
            print("=" * 50)
            print(f"Total Bots: {stats['total_bots']}")
            print(f"Online Bots: {stats['online_bots']}")
            print(f"Busy Bots: {stats['busy_bots']}")
            print(f"Total Assignments: {stats['total_assignments']}")
            print(f"Pending Assignments: {stats['pending_assignments']}")
            print(f"Queue Size: {stats['queue_size']}")
            print(f"Assignment Strategy: {stats['assignment_strategy']}")
            
            # Task bot specific stats
            task_bot_stats = stats['task_bot_stats']
            print(f"\nTask Assignment Statistics:")
            print(f"  Total Assignments: {task_bot_stats['total_assignments']}")
            print(f"  Successful: {task_bot_stats['successful_assignments']}")
            print(f"  Failed: {task_bot_stats['failed_assignments']}")
            
            if task_bot_stats['total_assignments'] > 0:
                success_rate = task_bot_stats['successful_assignments'] / task_bot_stats['total_assignments'] * 100
                print(f"  Success Rate: {success_rate:.1f}%")
                print(f"  Average Assignment Time: {task_bot_stats['avg_assignment_time']:.2f}s")
            
            # Bot utilization
            if task_bot_stats['bot_utilization']:
                print(f"\nBot Utilization:")
                for bot_id, utilization in task_bot_stats['bot_utilization'].items():
                    bot_name = self.task_bot.bots.get(bot_id, {}).get('name', 'Unknown')
                    print(f"  {bot_name}: {utilization * 100:.1f}%")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error getting system status: {e}")
    
    async def system_health(self, args):
        """Check system health."""
        try:
            # Get basic health info
            stats = self.task_bot.get_system_stats()
            
            print("🏥 System Health Check")
            print("=" * 50)
            
            # Check for potential issues
            issues = []
            warnings = []
            
            if stats['online_bots'] == 0:
                issues.append("No bots are online")
            
            if stats['queue_size'] > 50:
                warnings.append(f"Large task queue ({stats['queue_size']} tasks)")
            
            if stats['pending_assignments'] > 20:
                warnings.append(f"Many pending assignments ({stats['pending_assignments']})")
            
            # Calculate overall health score
            health_score = 100
            health_score -= len(issues) * 30
            health_score -= len(warnings) * 10
            health_score = max(0, health_score)
            
            # Determine health status
            if health_score >= 80:
                status = "✅ HEALTHY"
            elif health_score >= 60:
                status = "⚠️  WARNING"
            else:
                status = "❌ CRITICAL"
            
            print(f"Overall Status: {status}")
            print(f"Health Score: {health_score}/100")
            
            if issues:
                print(f"\n❌ Critical Issues:")
                for issue in issues:
                    print(f"  • {issue}")
            
            if warnings:
                print(f"\n⚠️  Warnings:")
                for warning in warnings:
                    print(f"  • {warning}")
            
            if not issues and not warnings:
                print("\n✅ No issues detected")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error checking system health: {e}")
    
    async def set_strategy(self, args):
        """Set assignment strategy."""
        try:
            if args.strategy not in self.task_bot.assignment_strategies:
                print(f"❌ Invalid strategy: {args.strategy}")
                print(f"Available strategies: {list(self.task_bot.assignment_strategies.keys())}")
                return
            
            old_strategy = self.task_bot.current_strategy
            self.task_bot.current_strategy = args.strategy
            
            print(f"✅ Assignment strategy changed from '{old_strategy}' to '{args.strategy}'")
            
        except Exception as e:
            print(f"❌ Error setting strategy: {e}")

    # Utility Methods
    
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
    
    def _get_assignment_status_icon(self, status: TaskStatus) -> str:
        """Get icon for assignment status."""
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
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TaskBot CLI - Manage bots and assign tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Register a bot
  %(prog)s register-bot "My Bot" --bot-type worker --capabilities "coding:custom,system_health"
  
  # List all bots
  %(prog)s list-bots
  
  # Create a task
  %(prog)s create-task "Health Check" --task-type system_health --priority high
  
  # Check system status
  %(prog)s status
  
  # View system health
  %(prog)s health
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Bot management commands
    bot_parser = subparsers.add_parser('register-bot', help='Register a new bot')
    bot_parser.add_argument('name', help='Bot name')
    bot_parser.add_argument('--bot-type', default='worker', choices=[bt.value for bt in BotType], help='Bot type')
    bot_parser.add_argument('--max-concurrent', type=int, default=3, help='Max concurrent tasks')
    bot_parser.add_argument('--capabilities', nargs='*', help='Bot capabilities (format: name:task_type1,task_type2:priority_boost)')
    bot_parser.add_argument('--priority-preference', help='Preferred priorities (comma-separated)')
    
    list_bots_parser = subparsers.add_parser('list-bots', help='List registered bots')
    list_bots_parser.add_argument('--status', choices=[bs.value for bs in BotStatus], help='Filter by status')
    list_bots_parser.add_argument('--bot-type', choices=[bt.value for bt in BotType], help='Filter by type')
    
    bot_status_parser = subparsers.add_parser('bot-status', help='Show bot status')
    bot_status_parser.add_argument('bot_id', help='Bot ID')
    
    update_status_parser = subparsers.add_parser('update-bot-status', help='Update bot status')
    update_status_parser.add_argument('bot_id', help='Bot ID')
    update_status_parser.add_argument('status', choices=[bs.value for bs in BotStatus], help='New status')
    
    unregister_parser = subparsers.add_parser('unregister-bot', help='Unregister a bot')
    unregister_parser.add_argument('bot_id', help='Bot ID')
    unregister_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Task management commands
    create_task_parser = subparsers.add_parser('create-task', help='Create a new task')
    create_task_parser.add_argument('name', help='Task name')
    create_task_parser.add_argument('--description', help='Task description')
    create_task_parser.add_argument('--task-type', default='custom', choices=[tt.value for tt in TaskType], help='Task type')
    create_task_parser.add_argument('--priority', default='normal', choices=[tp.value for tp in TaskPriority], help='Task priority')
    create_task_parser.add_argument('--subsystem', default='cli', help='Subsystem name')
    create_task_parser.add_argument('--user-id', help='User ID')
    create_task_parser.add_argument('--session-id', help='Session ID')
    
    assign_task_parser = subparsers.add_parser('assign-task', help='Assign a task to a bot')
    assign_task_parser.add_argument('task_id', help='Task ID')
    assign_task_parser.add_argument('--bot-id', help='Specific bot ID (optional)')
    
    list_assignments_parser = subparsers.add_parser('list-assignments', help='List task assignments')
    list_assignments_parser.add_argument('--status', choices=[ts.value for ts in TaskStatus], help='Filter by status')
    list_assignments_parser.add_argument('--bot-id', help='Filter by bot ID')
    
    # System management commands
    subparsers.add_parser('status', help='Show system status')
    subparsers.add_parser('health', help='Check system health')
    
    strategy_parser = subparsers.add_parser('set-strategy', help='Set assignment strategy')
    strategy_parser.add_argument('strategy', choices=['round_robin', 'best_fit', 'load_balanced', 'priority_first'], help='Assignment strategy')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    log_level = logging.WARNING
    if args.verbose:
        log_level = logging.INFO
    elif args.quiet:
        log_level = logging.ERROR
    
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Initialize CLI and run command
    cli = TaskBotCLI()
    
    try:
        await cli.initialize()
        
        # Map commands to methods
        command_map = {
            'register-bot': cli.register_bot,
            'list-bots': cli.list_bots,
            'bot-status': cli.bot_status,
            'update-bot-status': cli.update_bot_status,
            'unregister-bot': cli.unregister_bot,
            'create-task': cli.create_task,
            'assign-task': cli.assign_task,
            'list-assignments': cli.list_assignments,
            'status': cli.system_status,
            'health': cli.system_health,
            'set-strategy': cli.set_strategy,
        }
        
        # Execute command
        if args.command in command_map:
            await command_map[args.command](args)
        else:
            print(f"❌ Unknown command: {args.command}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    asyncio.run(main())