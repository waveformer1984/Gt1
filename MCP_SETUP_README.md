# 🍑 BallsDeepnit MCP (Model Context Protocol) Setup

**The Most Savage AI Agent Framework with Optimized MCP Integration**

This README provides comprehensive documentation for the Model Context Protocol (MCP) integration in the BallsDeepnit framework, featuring per-function optimization, advanced security, and high-performance agent capabilities.

## 🌟 What is MCP?

Model Context Protocol (MCP) is an open standard that enables Large Language Models (LLMs) and AI agents to securely connect with external data sources and tools. Think of it as "USB-C for AI" - a universal connector that allows your agents to interact with files, databases, APIs, audio systems, and more through a standardized interface.

## 🚀 Features

### 🔥 **Per-Function Optimization**
- **Audio Processing**: Optimized for real-time audio with specialized caching and priority handling
- **File Operations**: Secure file access with path validation and efficient caching
- **API Calls**: Smart retry logic and response caching for external services
- **Database Queries**: Connection pooling and query optimization
- **Real-time Data**: Ultra-low latency for time-sensitive operations

### 🛡️ **Advanced Security Framework**
- **Input Validation**: XSS, injection, and malicious pattern detection
- **Rate Limiting**: Configurable per-IP, per-user, and per-capability limits
- **Access Control**: Role-based permissions with fine-grained capability control
- **Security Auditing**: Comprehensive logging and event tracking
- **Path Sandboxing**: Prevents directory traversal and unauthorized file access

### ⚡ **High-Performance Architecture**
- **Connection Pooling**: Efficient MCP server connection management
- **Intelligent Caching**: Multi-layer caching with TTL and invalidation
- **Async Processing**: Full async/await support for maximum throughput
- **Load Balancing**: Automatic failover and health checking
- **Performance Monitoring**: Real-time metrics and bottleneck detection

### 🤖 **Agent Specialization**
- **Audio Agent**: Record, analyze, filter, and process audio in real-time
- **File Agent**: Read, write, search, and manage files with security
- **API Agent**: Web search, GitHub operations, and external service integration
- **Database Agent**: SQL queries, table management, and data operations
- **Universal Agent**: Jack-of-all-trades that can handle any capability

## 📦 Installation

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** (for official MCP servers)
- **Git** (for repository management)

### Quick Setup

1. **Clone and Navigate**
   ```bash
   git clone <your-repo-url>
   cd ballsdeepnit
   ```

2. **Run Automated Setup**
   ```bash
   python setup_mcp.py
   ```

3. **Configure API Keys**
   Edit `.env` file with your API keys:
   ```bash
   BRAVE_API_KEY=your_brave_search_api_key_here
   GITHUB_TOKEN=your_github_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Start the Framework**
   ```bash
   # Unix/Linux/macOS
   ./start_ballsdeepnit.sh
   
   # Windows
   start_ballsdeepnit.bat
   ```

### Manual Setup (Advanced)

1. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Unix
   # or
   .venv\Scripts\activate.bat  # Windows
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install MCP Servers**
   ```bash
   npm install -g @modelcontextprotocol/server-filesystem
   npm install -g @modelcontextprotocol/server-brave-search
   npm install -g @modelcontextprotocol/server-github
   ```

## 🎯 Usage

### CLI Commands

#### **Check MCP Status**
```bash
python -m ballsdeepnit.cli mcp status
```

#### **List Available Capabilities**
```bash
# All capabilities
python -m ballsdeepnit.cli mcp capabilities

# Filter by function type
python -m ballsdeepnit.cli mcp capabilities --function-type audio_processing

# Filter by agent
python -m ballsdeepnit.cli mcp capabilities --agent-id audio_agent
```

#### **Test Audio Processing**
```bash
python -m ballsdeepnit.cli mcp test-audio --duration 3.0 --sample-rate 44100
```

#### **Test File Operations**
```bash
python -m ballsdeepnit.cli mcp test-file --test-dir my_test_folder
```

### Python API

#### **Basic Framework Usage**
```python
import asyncio
from ballsdeepnit.core.framework import framework_context

async def main():
    async with framework_context() as framework:
        # Execute audio recording
        result = await framework.execute_task(
            "record_audio",
            "audio_processing",
            {"duration": 2.0, "sample_rate": 44100}
        )
        print(f"Recorded {result.get('samples')} audio samples")

asyncio.run(main())
```

#### **Direct Agent Execution**
```python
from ballsdeepnit.core.framework import execute_file_task, execute_audio_task

async def demo():
    # File operations
    await execute_file_task("write_file", {
        "file_path": "test.txt",
        "content": "Hello MCP!"
    })
    
    result = await execute_file_task("read_file", {
        "file_path": "test.txt"
    })
    print(f"File content: {result['content']}")
    
    # Audio analysis
    audio_data = [0.1, 0.5, -0.2, 0.8, -0.3]  # Sample data
    spectrum = await execute_audio_task("analyze_spectrum", {
        "audio_data": audio_data,
        "sample_rate": 44100
    })
    print(f"Dominant frequencies: {spectrum['dominant_frequencies'][:3]}")

asyncio.run(demo())
```

#### **Custom Capability Execution**
```python
from ballsdeepnit.core.framework import get_framework

async def advanced_usage():
    framework = get_framework()
    await framework.initialize()
    
    try:
        # Execute with specific agent and context
        result = await framework.execute_capability(
            agent_id="file_agent",
            capability_name="search_files",
            arguments={
                "pattern": "*.py",
                "directory": "src",
                "recursive": True
            },
            use_cache=True
        )
        
        print(f"Found {len(result['matches'])} Python files")
        
        # Get performance metrics
        status = await framework.get_mcp_status()
        print(f"Cache hit rate: {status['cache_stats']['hit_rate']:.2%}")
        
    finally:
        await framework.shutdown()

asyncio.run(advanced_usage())
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# MCP Core Settings
ENABLE_MCP=true
MCP_MAX_CONNECTIONS=10
MCP_CACHE_TTL=300

# Performance Settings
MAX_WORKERS=8
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_REDIS_CACHE=false

# Security Settings
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=60
ENABLE_REQUEST_VALIDATION=true

# Audio Settings
AUDIO_SAMPLE_RATE=44100
AUDIO_BUFFER_SIZE=1024

# API Keys
BRAVE_API_KEY=your_api_key
GITHUB_TOKEN=your_token
OPENAI_API_KEY=your_key
```

### MCP Server Configurations

Server configurations are stored in `mcp_configs/` directory:

- **filesystem.json**: File operations server
- **websearch.json**: Web search capabilities
- **github.json**: GitHub integration
- **database.json**: SQLite database operations
- **audio.json**: Audio processing server

## 🛡️ Security

### Access Control

The system uses role-based access control:

- **Admin**: Full access to all capabilities
- **User**: Limited access (read files, audio recording, web search)
- **Service**: Automated service access (files, database)
- **Guest**: Minimal access (web search only)

#### **Adding User Roles**
```python
from ballsdeepnit.core.mcp_security import get_security_manager

security_manager = get_security_manager()
security_manager.add_user_role("alice", "user")
security_manager.add_user_role("service_bot", "service")
```

### Rate Limiting

Built-in rate limiting protects against abuse:

- **Global**: 60 requests/minute by default
- **Per-IP**: 100 requests/minute
- **File Operations**: 30 requests/minute per IP
- **Database Operations**: 20 requests/minute per user

#### **Custom Rate Limits**
```python
from ballsdeepnit.core.mcp_security import RateLimitRule

rule = RateLimitRule(
    name="api_calls_strict",
    max_requests=10,
    window_seconds=60,
    scope="user",
    capability_pattern=".*api.*"
)

security_manager.add_rate_limit_rule(rule)
```

### Security Monitoring

#### **View Security Events**
```python
security_manager = get_security_manager()
events = await security_manager.get_recent_security_events(limit=20)

for event in events:
    print(f"{event['timestamp']}: {event['event_type']} - {event['severity']}")
```

## 📊 Performance Monitoring

### Real-time Metrics

```python
from ballsdeepnit.core.framework import get_framework

framework = get_framework()
status = await framework.get_mcp_status()

print(f"Servers: {status['servers_count']}")
print(f"Cache Hit Rate: {status['cache_stats']['hit_rate']:.2%}")
print(f"Avg Response Time: {status['framework_stats']['average_response_time']:.3f}s")
```

### Performance Optimization Tips

1. **Enable Redis Caching**: Set `ENABLE_REDIS_CACHE=true` for high-traffic scenarios
2. **Adjust Cache TTL**: Longer TTL for stable data, shorter for dynamic data
3. **Connection Pooling**: Increase `MCP_MAX_CONNECTIONS` for concurrent usage
4. **Function-Specific Optimization**: Different timeout and cache settings per function type

## 🔧 Advanced Usage

### Custom MCP Servers

Create custom servers for specialized functionality:

```python
from ballsdeepnit.core.mcp_servers import MCPServerFactory

# Register a custom server type
class CustomMCPServer:
    def __init__(self):
        self.server = Server("custom-operations")
        self.setup_tools()
    
    def setup_tools(self):
        @self.server.list_tools()
        async def list_tools():
            return [/* your tools */]

# Register with factory
MCPServerFactory._servers["custom_operations"] = CustomMCPServer
```

### Custom Agents

Register specialized agents:

```python
from ballsdeepnit.core.framework import AgentCapability

capabilities = [
    AgentCapability(
        name="custom_analysis",
        function_type="data_analysis",
        description="Perform custom data analysis",
        mcp_servers=["custom-operations"],
        priority=2,
        parameters={"data": "array", "algorithm": "string"}
    )
]

framework.agent_registry.register_agent("analysis_agent", capabilities)
```

## 🧪 Testing

### Run Full Test Suite
```bash
python test_mcp.py
```

### Component Tests
```bash
# Test specific agents
python -m ballsdeepnit.cli mcp test-audio
python -m ballsdeepnit.cli mcp test-file

# Test security
python -c "
from ballsdeepnit.core.mcp_security import get_security_manager
sm = get_security_manager()
print('Security Status:', sm.get_security_status())
"
```

## 🐛 Troubleshooting

### Common Issues

#### **MCP Servers Not Starting**
```bash
# Check Node.js installation
node --version

# Reinstall MCP servers
npm install -g @modelcontextprotocol/server-filesystem
```

#### **Permission Errors**
```bash
# Check file permissions
ls -la setup_mcp.py
chmod +x setup_mcp.py

# Verify virtual environment
which python
```

#### **Audio Device Issues**
```python
# List available audio devices
import sounddevice as sd
print(sd.query_devices())
```

#### **Import Errors**
```bash
# Ensure proper Python path
export PYTHONPATH="/workspace/src:$PYTHONPATH"

# Check dependencies
pip list | grep mcp
```

### Debug Mode

Enable detailed logging:
```bash
export DEBUG=true
python -m ballsdeepnit.cli run --enable-mcp --debug
```

### Performance Issues

1. **Check Resource Usage**
   ```bash
   python -c "
   import psutil
   print(f'CPU: {psutil.cpu_percent()}%')
   print(f'Memory: {psutil.virtual_memory().percent}%')
   "
   ```

2. **Monitor Cache Performance**
   ```bash
   python -m ballsdeepnit.cli mcp status
   ```

3. **Analyze Security Events**
   ```python
   from ballsdeepnit.core.mcp_security import get_security_manager
   events = await get_security_manager().get_recent_security_events()
   print([e for e in events if e['severity'] in ['warning', 'error']])
   ```

## 📈 Scaling and Production

### Production Deployment

1. **Enable Redis**: For shared cache across instances
2. **Load Balancing**: Multiple framework instances
3. **Monitoring**: Prometheus metrics integration
4. **Security**: API keys, rate limiting, access logs
5. **Backup**: Database and configuration backup

### Performance Tuning

1. **Connection Pools**: Increase for high concurrency
2. **Cache Strategy**: Optimize TTL per function type
3. **Worker Processes**: Scale with CPU cores
4. **Memory Management**: Monitor and tune garbage collection

## 🤝 Contributing

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/amazing-mcp-feature`
3. **Add Tests**: Ensure your changes include tests
4. **Follow Standards**: Use black formatting and type hints
5. **Submit PR**: With detailed description

## 📜 License

MIT License - see LICENSE file for details.

## 🙌 Acknowledgments

- **Anthropic** - For creating the MCP standard
- **BallsDeepnit Community** - For pushing the boundaries of AI frameworks
- **Open Source Contributors** - For making this ecosystem possible

---

## 🔗 Quick Links

- [MCP Official Documentation](https://modelcontextprotocol.io/)
- [BallsDeepnit Framework Docs](./README.md)
- [Performance Optimization Guide](./PERFORMANCE_OPTIMIZATIONS.md)
- [Security Best Practices](./SECURITY_LOCKDOWN.md)

**Ready to go balls deep with MCP? Let's build something amazing! 🍑🚀**