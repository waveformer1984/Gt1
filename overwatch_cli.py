#!/usr/bin/env python3
"""
Overwatch System CLI
===================

Command-line interface for managing the overwatch task generation and dispatch system.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ballsdeepnit.core.overwatch import (
    get_overwatch, initialize_overwatch, TaskType, TaskPriority
)
from src.ballsdeepnit.core.overwatch_handlers import register_all_handlers
from src.ballsdeepnit.core.overwatch_monitoring import start_overwatch_monitoring, stop_overwatch_monitoring


async def start_overwatch(args):
    """Start the overwatch system."""
    print("🔍 Starting Overwatch System...")
    
    # Initialize overwatch with custom settings
    overwatch = initialize_overwatch(
        max_concurrent_tasks=args.max_tasks
    )
    
    # Register all handlers
    print("📝 Registering task handlers...")
    register_all_handlers(overwatch)
    
    # Start monitoring integration if requested
    if args.enable_monitoring:
        print("📊 Starting monitoring integration...")
        await start_overwatch_monitoring()
    
    # Start the overwatch system
    await overwatch.start()
    
    print("✅ Overwatch system started successfully!")
    print(f"   • Max concurrent tasks: {overwatch.task_scheduler.max_concurrent_tasks}")
    print(f"   • Task generation interval: {overwatch.generation_interval} seconds")
    print(f"   • Monitoring integration: {'enabled' if args.enable_monitoring else 'disabled'}")
    
    if args.daemon:
        print("🔄 Running in daemon mode... (Press Ctrl+C to stop)")
        try:
            await overwatch.run_forever()
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested")
        finally:
            overwatch.stop()
            if args.enable_monitoring:
                stop_overwatch_monitoring()
            print("✅ Overwatch system stopped")
    else:
        print("✅ Overwatch system started in background")


async def status_overwatch(args):
    """Show overwatch system status."""
    overwatch = get_overwatch()
    
    status = overwatch.get_status()
    
    print("🔍 Overwatch System Status")
    print("=" * 40)
    print(f"Running: {'✅ Yes' if status['running'] else '❌ No'}")
    print(f"Uptime: {status['system_state']['uptime']:.1f} seconds")
    print(f"Health: {status['system_state'].get('health_status', 'unknown')}")
    print(f"Last task generation: {status['last_generation']}")
    
    print("\n📊 Task Statistics")
    print("-" * 20)
    stats = status['scheduler_stats']
    print(f"Queue size: {stats['queue_size']}")
    print(f"Running tasks: {stats['running_tasks']}")
    print(f"Completed tasks: {stats['completed_tasks']}")
    print(f"Failed tasks: {stats['failed_tasks']}")
    print(f"Average execution time: {stats['average_execution_time']:.3f}s")
    
    if args.json:
        print("\n📄 Full Status (JSON)")
        print("-" * 25)
        print(json.dumps(status, indent=2, default=str))


async def create_task(args):
    """Create a new task."""
    overwatch = get_overwatch()
    
    # Parse task type
    try:
        task_type = TaskType(args.type)
    except ValueError:
        print(f"❌ Invalid task type: {args.type}")
        print(f"Valid types: {[t.value for t in TaskType]}")
        return
    
    # Parse priority
    try:
        priority = TaskPriority(args.priority)
    except ValueError:
        print(f"❌ Invalid priority: {args.priority}")
        print(f"Valid priorities: {[p.value for p in TaskPriority]}")
        return
    
    # Create the task
    task = overwatch.create_task(
        name=args.name,
        description=args.description or f"CLI-created {task_type.value} task",
        task_type=task_type,
        priority=priority,
        subsystem=args.subsystem
    )
    
    print(f"✅ Task created successfully!")
    print(f"   • ID: {task.id}")
    print(f"   • Name: {task.name}")
    print(f"   • Type: {task.task_type.value}")
    print(f"   • Priority: {task.priority.value}")
    print(f"   • Subsystem: {task.context.subsystem}")


async def list_tasks(args):
    """List tasks."""
    overwatch = get_overwatch()
    scheduler = overwatch.task_scheduler
    
    print("📋 Task List")
    print("=" * 60)
    
    # Running tasks
    if scheduler.running_tasks:
        print("\n🔄 Running Tasks")
        print("-" * 20)
        for task in scheduler.running_tasks.values():
            print(f"  {task.id[:8]} | {task.name[:30]:30} | {task.task_type.value:15} | {task.priority.value}")
    
    # Recent completed tasks
    recent_completed = list(scheduler.completed_tasks)[-args.limit:]
    if recent_completed:
        print("\n✅ Recent Completed Tasks")
        print("-" * 30)
        for task in recent_completed:
            execution_time = scheduler.execution_times.get(task.id, 0)
            print(f"  {task.id[:8]} | {task.name[:30]:30} | {execution_time:.3f}s")
    
    # Recent failed tasks
    recent_failed = list(scheduler.failed_tasks)[-args.limit:]
    if recent_failed:
        print("\n❌ Recent Failed Tasks")
        print("-" * 25)
        for task in recent_failed:
            print(f"  {task.id[:8]} | {task.name[:30]:30} | {task.task_type.value:15}")


async def generate_tasks(args):
    """Manually trigger task generation."""
    overwatch = get_overwatch()
    
    if not overwatch.running:
        print("❌ Overwatch system is not running")
        return
    
    print("🔄 Generating tasks...")
    await overwatch.generate_and_submit_tasks()
    print("✅ Task generation completed")


async def test_system(args):
    """Run system tests."""
    print("🧪 Testing Overwatch System...")
    
    overwatch = get_overwatch()
    register_all_handlers(overwatch)
    
    # Start system
    await overwatch.start()
    
    print("✅ System started")
    
    # Create test tasks
    test_tasks = [
        ("Health Check Test", TaskType.SYSTEM_HEALTH, TaskPriority.HIGH),
        ("Performance Test", TaskType.PERFORMANCE_CHECK, TaskPriority.NORMAL),
        ("Security Scan Test", TaskType.SECURITY_SCAN, TaskPriority.LOW),
    ]
    
    print("📝 Creating test tasks...")
    for name, task_type, priority in test_tasks:
        task = overwatch.create_task(
            name=name,
            description=f"Test task: {name}",
            task_type=task_type,
            priority=priority
        )
        print(f"   • Created: {name} ({task.id[:8]})")
    
    # Wait for tasks to complete
    print("⏳ Waiting for tasks to complete...")
    await asyncio.sleep(10)
    
    # Show results
    status = overwatch.get_status()
    stats = status['scheduler_stats']
    
    print(f"\n📊 Test Results")
    print("-" * 20)
    print(f"Completed: {stats['completed_tasks']}")
    print(f"Failed: {stats['failed_tasks']}")
    print(f"Average time: {stats['average_execution_time']:.3f}s")
    
    # Stop system
    overwatch.stop()
    print("✅ Test completed")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Overwatch System - Task Generation and Dispatch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start --daemon --enable-monitoring    # Start with monitoring
  %(prog)s status --json                         # Show status as JSON
  %(prog)s create-task "Backup Data" --type data_backup --priority high
  %(prog)s list-tasks --limit 10                # Show recent tasks
  %(prog)s test                                  # Run system tests
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the overwatch system')
    start_parser.add_argument('--daemon', action='store_true', 
                             help='Run in daemon mode (blocking)')
    start_parser.add_argument('--max-tasks', type=int, default=10,
                             help='Maximum concurrent tasks (default: 10)')
    start_parser.add_argument('--enable-monitoring', action='store_true',
                             help='Enable monitoring integration')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    status_parser.add_argument('--json', action='store_true',
                              help='Output status as JSON')
    
    # Create task command
    create_parser = subparsers.add_parser('create-task', help='Create a new task')
    create_parser.add_argument('name', help='Task name')
    create_parser.add_argument('--description', help='Task description')
    create_parser.add_argument('--type', default='user_task',
                              help='Task type (default: user_task)')
    create_parser.add_argument('--priority', default='normal',
                              help='Task priority (default: normal)')
    create_parser.add_argument('--subsystem', default='core',
                              help='Target subsystem (default: core)')
    
    # List tasks command
    list_parser = subparsers.add_parser('list-tasks', help='List tasks')
    list_parser.add_argument('--limit', type=int, default=20,
                            help='Maximum number of tasks to show (default: 20)')
    
    # Generate tasks command
    generate_parser = subparsers.add_parser('generate', help='Manually generate tasks')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run system tests')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run the appropriate command
    try:
        if args.command == 'start':
            asyncio.run(start_overwatch(args))
        elif args.command == 'status':
            asyncio.run(status_overwatch(args))
        elif args.command == 'create-task':
            asyncio.run(create_task(args))
        elif args.command == 'list-tasks':
            asyncio.run(list_tasks(args))
        elif args.command == 'generate':
            asyncio.run(generate_tasks(args))
        elif args.command == 'test':
            asyncio.run(test_system(args))
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()