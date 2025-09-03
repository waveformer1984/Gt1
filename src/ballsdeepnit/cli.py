"""
High-performance CLI interface for ballsDeepnit framework.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Optional

import click

from .core.config import settings
from .monitoring.performance import (
    performance_monitor,
    optimize_memory_usage,
    get_memory_usage,
    setup_performance_monitoring
)
from .utils.logging import get_logger, perf_logger


@click.group()
@click.version_option(version=settings.VERSION)
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config-file', type=click.Path(exists=True), help='Path to configuration file')
def cli(debug: bool, config_file: Optional[str]) -> None:
    """ballsDeepnit - The Deepest, Most Savage Bot Framework in the Game."""
    if debug:
        settings.DEBUG = True
    
    # Setup performance monitoring
    setup_performance_monitoring()
    
    logger = get_logger(__name__)
    logger.info(f"ballsDeepnit v{settings.VERSION} starting up")


@cli.command()
@click.option('--host', default=settings.HOST, help='Host to bind to')
@click.option('--port', default=settings.PORT, help='Port to bind to')
@click.option('--workers', default=settings.performance.MAX_WORKERS, help='Number of worker processes')
@click.option('--enable-mcp/--disable-mcp', default=settings.mcp.ENABLE_MCP, help='Enable/disable MCP support')
def run(host: str, port: int, workers: int, enable_mcp: bool) -> None:
    """Run the main ballsDeepnit framework."""
    logger = get_logger(__name__)
    
    try:
        # Update MCP setting
        settings.mcp.ENABLE_MCP = enable_mcp
        
        # Import here for lazy loading
        from .core.framework import BallsDeepnitFramework
        
        framework = BallsDeepnitFramework()
        
        logger.info(f"Starting framework on {host}:{port} with {workers} workers")
        
        # Run with performance optimizations
        asyncio.run(framework.run_async(host=host, port=port, workers=workers))
        
    except KeyboardInterrupt:
        logger.info("Framework stopped by user")
    except Exception as e:
        logger.error(f"Framework error: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option('--host', default=settings.HOST, help='Host to bind to')
@click.option('--port', default=settings.DASHBOARD_PORT, help='Port to bind to')
def dashboard(host: str, port: int) -> None:
    """Run the performance-optimized dashboard."""
    logger = get_logger(__name__)
    
    try:
        from .dashboard.app import DashboardApp
        
        dashboard_app = DashboardApp()
        
        logger.info(f"Starting dashboard on {host}:{port}")
        dashboard_app.run(host=host, port=port)
        
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        sys.exit(1)


@cli.group()
def performance() -> None:
    """Performance monitoring and optimization commands."""
    pass


@performance.command('monitor')
@click.option('--duration', default=60, help='Monitoring duration in seconds')
@click.option('--interval', default=1.0, help='Collection interval in seconds')
@click.option('--output', type=click.Path(), help='Output file for metrics')
def monitor_performance(duration: int, interval: float, output: Optional[str]) -> None:
    """Monitor system performance for a specified duration."""
    logger = get_logger(__name__)
    
    async def monitor():
        logger.info(f"Starting performance monitoring for {duration} seconds")
        
        # Configure monitoring interval
        performance_monitor.collection_interval = interval
        
        # Start monitoring
        await performance_monitor.start_monitoring()
        
        try:
            # Monitor for specified duration
            await asyncio.sleep(duration)
            
            # Generate report
            report = performance_monitor.get_performance_report()
            
            if output:
                import json
                with open(output, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                logger.info(f"Performance report saved to {output}")
            else:
                # Print summary to console
                _print_performance_summary(report)
                
        finally:
            await performance_monitor.stop_monitoring()
    
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        logger.info("Performance monitoring stopped by user")


@performance.command('optimize')
@click.option('--memory', is_flag=True, help='Optimize memory usage')
@click.option('--cache', is_flag=True, help='Clear and optimize cache')
def optimize_system(memory: bool, cache: bool) -> None:
    """Optimize system performance."""
    logger = get_logger(__name__)
    
    if memory:
        logger.info("Optimizing memory usage...")
        before = get_memory_usage()
        optimize_memory_usage()
        after = get_memory_usage()
        
        freed_mb = before.get("rss_mb", 0) - after.get("rss_mb", 0)
        click.echo(f"Memory optimization completed - freed {freed_mb:.2f}MB")
    
    if cache:
        async def clear_cache():
            from .utils.cache import get_global_cache
            cache_manager = await get_global_cache()
            await cache_manager.clear()
            stats = await cache_manager.get_stats()
            return stats
        
        stats = asyncio.run(clear_cache())
        click.echo(f"Cache cleared - hit rate was {stats.get('hit_rate', 0):.2%}")


@performance.command('report')
@click.option('--format', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.option('--output', type=click.Path(), help='Output file')
def performance_report(format: str, output: Optional[str]) -> None:
    """Generate a comprehensive performance report."""
    logger = get_logger(__name__)
    
    async def get_report():
        # Start monitoring briefly to get current metrics
        await performance_monitor.start_monitoring()
        await asyncio.sleep(2)  # Collect some data
        
        report = performance_monitor.get_performance_report()
        await performance_monitor.stop_monitoring()
        return report
    
    try:
        report = asyncio.run(get_report())
        
        if format == 'json':
            import json
            output_text = json.dumps(report, indent=2, default=str)
        else:
            output_text = _format_performance_table(report)
        
        if output:
            with open(output, 'w') as f:
                f.write(output_text)
            click.echo(f"Performance report saved to {output}")
        else:
            click.echo(output_text)
            
    except Exception as e:
        logger.error(f"Failed to generate performance report: {e}")
        sys.exit(1)


@cli.group()
def cache() -> None:
    """Cache management commands."""
    pass


@cache.command('stats')
def cache_stats() -> None:
    """Show cache statistics."""
    async def get_stats():
        from .utils.cache import get_global_cache
        cache_manager = await get_global_cache()
        return await cache_manager.get_stats()
    
    try:
        stats = asyncio.run(get_stats())
        _print_cache_stats(stats)
    except Exception as e:
        click.echo(f"Error getting cache stats: {e}", err=True)
        sys.exit(1)


@cache.command('clear')
@click.confirmation_option(prompt='Are you sure you want to clear all cache data?')
def clear_cache() -> None:
    """Clear all cache data."""
    async def clear():
        from .utils.cache import get_global_cache
        cache_manager = await get_global_cache()
        success = await cache_manager.clear()
        return success
    
    try:
        success = asyncio.run(clear())
        if success:
            click.echo("Cache cleared successfully")
        else:
            click.echo("Failed to clear cache", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error clearing cache: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--plugin-name', required=True, help='Name of the plugin to create')
@click.option('--template', default='basic', help='Plugin template to use')
def create_plugin(plugin_name: str, template: str) -> None:
    """Create a new plugin with performance optimizations."""
    logger = get_logger(__name__)
    
    try:
        from .core.plugin_scaffold import PluginScaffold
        
        scaffold = PluginScaffold()
        plugin_path = scaffold.create_plugin(plugin_name, template)
        
        click.echo(f"Plugin '{plugin_name}' created at: {plugin_path}")
        click.echo("Remember to register it in pyproject.toml under [project.entry-points.'ballsdeepnit.plugins']")
        
    except Exception as e:
        logger.error(f"Failed to create plugin: {e}")
        sys.exit(1)


@cli.command()
def health() -> None:
    """Check system health and performance."""
    logger = get_logger(__name__)
    
    try:
        # Get system info
        memory = get_memory_usage()
        
        async def get_cache_health():
            try:
                from .utils.cache import get_global_cache
                cache_manager = await get_global_cache()
                return await cache_manager.get_stats()
            except Exception:
                return {"available": False}
        
        cache_stats = asyncio.run(get_cache_health())
        
        # Display health information
        click.echo("🍑 ballsDeepnit Health Check")
        click.echo("=" * 40)
        
        # System health
        click.echo(f"Memory Usage: {memory.get('percent', 0):.1f}%")
        click.echo(f"Memory RSS: {memory.get('rss_mb', 0):.1f}MB")
        click.echo(f"Available Memory: {memory.get('available_mb', 0):.1f}MB")
        
        # Cache health
        if cache_stats.get("available", True):
            hit_rate = cache_stats.get("hit_rate", 0)
            click.echo(f"Cache Hit Rate: {hit_rate:.2%}")
            click.echo(f"Cache Operations/sec: {cache_stats.get('operations_per_second', 0):.1f}")
        else:
            click.echo("Cache: Not available")
        
        # Performance recommendations
        recommendations = []
        
        if memory.get('percent', 0) > 80:
            recommendations.append("⚠️  High memory usage - consider optimizing")
        
        if cache_stats.get("hit_rate", 1) < 0.7:
            recommendations.append("⚠️  Low cache hit rate - consider cache tuning")
        
        if recommendations:
            click.echo("\nRecommendations:")
            for rec in recommendations:
                click.echo(f"  {rec}")
        else:
            click.echo("\n✅ System health looks good!")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        sys.exit(1)


def _print_performance_summary(report: dict) -> None:
    """Print a formatted performance summary."""
    click.echo("🍑 Performance Summary")
    click.echo("=" * 40)
    
    system = report.get("system", {}).get("current", {})
    click.echo(f"CPU Usage: {system.get('cpu_percent', 0):.1f}%")
    click.echo(f"Memory Usage: {system.get('memory_percent', 0):.1f}%")
    click.echo(f"Memory RSS: {system.get('memory_rss_mb', 0):.1f}MB")
    click.echo(f"Active Threads: {system.get('active_threads', 0)}")
    
    functions = report.get("functions", {})
    if functions:
        click.echo(f"\nTop Functions by Call Count:")
        sorted_funcs = sorted(functions.items(), key=lambda x: x[1].get('call_count', 0), reverse=True)
        for func_name, metrics in sorted_funcs[:5]:
            click.echo(f"  {func_name}: {metrics.get('call_count', 0)} calls, {metrics.get('avg_time_ms', 0):.2f}ms avg")
    
    recommendations = report.get("recommendations", [])
    if recommendations:
        click.echo(f"\nRecommendations:")
        for rec in recommendations:
            click.echo(f"  • {rec}")


def _format_performance_table(report: dict) -> str:
    """Format performance report as a table."""
    from datetime import datetime
    
    lines = []
    lines.append("ballsDeepnit Performance Report")
    lines.append("=" * 50)
    lines.append(f"Generated: {datetime.fromtimestamp(report.get('timestamp', time.time()))}")
    lines.append("")
    
    # System metrics
    system = report.get("system", {}).get("current", {})
    lines.append("System Metrics:")
    lines.append("-" * 20)
    lines.append(f"CPU Usage:      {system.get('cpu_percent', 0):>8.1f}%")
    lines.append(f"Memory Usage:   {system.get('memory_percent', 0):>8.1f}%")
    lines.append(f"Memory RSS:     {system.get('memory_rss_mb', 0):>8.1f}MB")
    lines.append(f"Active Threads: {system.get('active_threads', 0):>8d}")
    lines.append(f"Open Files:     {system.get('open_files', 0):>8d}")
    lines.append("")
    
    # Function metrics
    functions = report.get("functions", {})
    if functions:
        lines.append("Function Performance:")
        lines.append("-" * 30)
        lines.append(f"{'Function':<30} {'Calls':<8} {'Avg(ms)':<10} {'Total(s)':<10}")
        lines.append("-" * 60)
        
        sorted_funcs = sorted(functions.items(), key=lambda x: x[1].get('total_time_s', 0), reverse=True)
        for func_name, metrics in sorted_funcs[:10]:
            short_name = func_name.split('.')[-1][:29]
            lines.append(f"{short_name:<30} {metrics.get('call_count', 0):<8d} "
                        f"{metrics.get('avg_time_ms', 0):<10.2f} {metrics.get('total_time_s', 0):<10.2f}")
        lines.append("")
    
    # Recommendations
    recommendations = report.get("recommendations", [])
    if recommendations:
        lines.append("Optimization Recommendations:")
        lines.append("-" * 35)
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
    
    return "\n".join(lines)


def _print_cache_stats(stats: dict) -> None:
    """Print formatted cache statistics."""
    click.echo("🍑 Cache Statistics")
    click.echo("=" * 30)
    
    click.echo(f"Hit Rate: {stats.get('hit_rate', 0):.2%}")
    click.echo(f"Operations/sec: {stats.get('operations_per_second', 0):.1f}")
    click.echo(f"Total Hits: {stats.get('hits', 0)}")
    click.echo(f"Total Misses: {stats.get('misses', 0)}")
    click.echo(f"Total Sets: {stats.get('sets', 0)}")
    click.echo(f"Errors: {stats.get('errors', 0)}")
    
    redis_stats = stats.get("redis", {})
    if redis_stats.get("connected"):
        click.echo(f"\nRedis:")
        click.echo(f"  Used Memory: {redis_stats.get('used_memory_mb', 0):.1f}MB")
        click.echo(f"  Connected Clients: {redis_stats.get('connected_clients', 0)}")
    
    disk_stats = stats.get("disk", {})
    if disk_stats.get("available", True):
        click.echo(f"\nDisk Cache:")
        click.echo(f"  Size: {disk_stats.get('size_mb', 0):.1f}MB")
        click.echo(f"  Items: {disk_stats.get('count', 0)}")


@cli.group(name='mcp')
def mcp_group() -> None:
    """Model Context Protocol (MCP) management commands."""
    pass


@mcp_group.command(name='status')
def mcp_status() -> None:
    """Show MCP system status and performance metrics."""
    import asyncio
    
    async def _get_status():
        from .core.framework import get_framework
        
        framework = get_framework()
        await framework.initialize()
        
        try:
            status = await framework.get_mcp_status()
            
            click.echo("=== MCP System Status ===")
            click.echo(f"MCP Enabled: {status.get('mcp_enabled', False)}")
            
            if status.get('mcp_enabled'):
                click.echo(f"Active Servers: {status.get('servers_count', 0)}")
                click.echo(f"Recent Operations: {status.get('recent_operations', 0)}")
                click.echo(f"Registered Agents: {status.get('agents_count', 0)}")
                click.echo(f"Total Capabilities: {status.get('total_capabilities', 0)}")
                
                cache_stats = status.get('cache_stats', {})
                if cache_stats:
                    click.echo(f"\n=== Cache Statistics ===")
                    click.echo(f"Hit Rate: {cache_stats.get('hit_rate', 0):.2%}")
                    click.echo(f"Cache Size: {cache_stats.get('cache_size', 0)}")
                    click.echo(f"Hit Count: {cache_stats.get('hit_count', 0)}")
                    click.echo(f"Miss Count: {cache_stats.get('miss_count', 0)}")
                
                framework_stats = status.get('framework_stats', {})
                if framework_stats:
                    click.echo(f"\n=== Framework Statistics ===")
                    click.echo(f"Requests Processed: {framework_stats.get('requests_processed', 0)}")
                    click.echo(f"Average Response Time: {framework_stats.get('average_response_time', 0):.3f}s")
                    click.echo(f"Error Count: {framework_stats.get('error_count', 0)}")
            else:
                click.echo("MCP is disabled. Use --enable-mcp to enable it.")
                
        finally:
            await framework.shutdown()
    
    try:
        asyncio.run(_get_status())
    except Exception as e:
        logger.error(f"Error getting MCP status: {e}")
        raise click.ClickException(str(e))


@mcp_group.command(name='capabilities')
@click.option('--function-type', help='Filter by function type (audio_processing, file_operations, etc.)')
@click.option('--agent-id', help='Show capabilities for specific agent')
def mcp_capabilities(function_type: Optional[str], agent_id: Optional[str]) -> None:
    """List available agent capabilities and MCP servers."""
    import asyncio
    
    async def _get_capabilities():
        from .core.framework import get_framework
        
        framework = get_framework()
        await framework.initialize()
        
        try:
            capabilities = framework.get_available_capabilities(function_type)
            
            click.echo("=== Available Agent Capabilities ===")
            
            for agent, caps in capabilities.items():
                if agent_id and agent != agent_id:
                    continue
                    
                click.echo(f"\n{agent.upper()}:")
                for cap in caps:
                    click.echo(f"  • {cap['name']} ({cap['function_type']})")
                    click.echo(f"    Description: {cap['description']}")
                    click.echo(f"    Priority: {cap['priority']}")
                    if cap['parameters']:
                        params = ', '.join([f"{k}: {v}" for k, v in cap['parameters'].items()])
                        click.echo(f"    Parameters: {params}")
                    click.echo()
                    
        finally:
            await framework.shutdown()
    
    try:
        asyncio.run(_get_capabilities())
    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        raise click.ClickException(str(e))


@mcp_group.command(name='test-audio')
@click.option('--duration', default=2.0, help='Recording duration in seconds')
@click.option('--sample-rate', default=44100, help='Audio sample rate')
def mcp_test_audio(duration: float, sample_rate: int) -> None:
    """Test audio processing capabilities via MCP."""
    import asyncio
    
    async def _test_audio():
        from .core.framework import execute_audio_task
        
        click.echo(f"Testing audio recording for {duration}s at {sample_rate}Hz...")
        
        try:
            result = await execute_audio_task(
                "record_audio",
                {"duration": duration, "sample_rate": sample_rate}
            )
            
            click.echo("Audio recording completed successfully!")
            click.echo(f"Recorded {result.get('samples', 0)} samples")
            
        except Exception as e:
            click.echo(f"Audio test failed: {e}")
            raise
    
    try:
        asyncio.run(_test_audio())
    except Exception as e:
        logger.error(f"Error in audio test: {e}")
        raise click.ClickException(str(e))


@mcp_group.command(name='test-file')
@click.option('--test-dir', default='test_mcp', help='Directory for file operation tests')
def mcp_test_file(test_dir: str) -> None:
    """Test file operation capabilities via MCP."""
    import asyncio
    
    async def _test_file():
        from .core.framework import execute_file_task
        
        click.echo(f"Testing file operations in {test_dir}/...")
        
        try:
            # Create test directory
            await execute_file_task(
                "create_directory",
                {"directory_path": test_dir}
            )
            click.echo(f"Created directory: {test_dir}")
            
            # Write test file
            test_content = "Hello from MCP file operations!\nThis is a test file."
            await execute_file_task(
                "write_file",
                {"file_path": f"{test_dir}/test.txt", "content": test_content}
            )
            click.echo("Created test file")
            
            # Read test file
            result = await execute_file_task(
                "read_file",
                {"file_path": f"{test_dir}/test.txt"}
            )
            click.echo(f"Read file content: {len(result.get('content', ''))} characters")
            
        except Exception as e:
            click.echo(f"File test failed: {e}")
            raise
    
    try:
        asyncio.run(_test_file())
    except Exception as e:
        logger.error(f"Error in file test: {e}")
        raise click.ClickException(str(e))


def main() -> None:
    """Main CLI entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()