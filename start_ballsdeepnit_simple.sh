#!/bin/bash
# Simple BallsDeepnit Startup Script
# Works with system Python when virtual environment is not available

echo "🍑 Starting BallsDeepnit MCP Framework (Simple Mode)"
echo "=================================================="

# Set Python path
export PYTHONPATH="/workspace/src:$PYTHONPATH"

# Check if we have dependencies
echo "🔍 Checking system status..."

# Function to check if a Python module is available
check_module() {
    python3 -c "import $1" 2>/dev/null && echo "✅ $1" || echo "❌ $1 (missing)"
}

echo "📦 Dependency Status:"
check_module "fastapi"
check_module "uvicorn" 
check_module "pydantic"
check_module "click"
check_module "asyncio"

echo ""
echo "📁 MCP Components:"
if [ -f "/workspace/src/ballsdeepnit/core/mcp_manager.py" ]; then
    echo "✅ MCP Manager"
else
    echo "❌ MCP Manager"
fi

if [ -f "/workspace/src/ballsdeepnit/core/framework.py" ]; then
    echo "✅ Agent Framework"
else
    echo "❌ Agent Framework"
fi

if [ -f "/workspace/setup_mcp.py" ]; then
    echo "✅ MCP Setup Script"
else
    echo "❌ MCP Setup Script"
fi

echo ""
echo "🚀 Starting Options:"
echo "1. Install dependencies and start full system"
echo "2. Start with minimal dependencies (structure verification only)"
echo "3. Show MCP status (if dependencies available)"
echo "4. Exit"
echo ""

read -p "Choose option (1-4): " choice

case $choice in
    1)
        echo "🔧 Installing dependencies with --break-system-packages..."
        python3 -m pip install --break-system-packages -r requirements.txt
        if [ $? -eq 0 ]; then
            echo "✅ Dependencies installed!"
            echo "🚀 Starting full MCP system..."
            python3 setup_mcp.py
            python3 -m ballsdeepnit.cli run --enable-mcp
        else
            echo "❌ Dependency installation failed. Try option 2 for minimal start."
        fi
        ;;
    2)
        echo "🔍 Starting minimal verification..."
        python3 -c "
import sys
sys.path.insert(0, '/workspace/src')

print('🧪 Testing MCP structure...')
try:
    # Test basic imports
    from pathlib import Path
    print('✅ Basic Python modules available')
    
    # Test MCP file structure
    mcp_files = [
        'src/ballsdeepnit/core/mcp_manager.py',
        'src/ballsdeepnit/core/mcp_servers.py', 
        'src/ballsdeepnit/core/mcp_security.py',
        'src/ballsdeepnit/core/framework.py'
    ]
    
    missing_files = []
    for file_path in mcp_files:
        full_path = Path('/workspace') / file_path
        if full_path.exists():
            print(f'✅ {file_path}')
            # Test basic syntax
            try:
                with open(full_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
                print(f'   ✅ Syntax valid')
            except SyntaxError as e:
                print(f'   ❌ Syntax error: {e}')
        else:
            print(f'❌ {file_path} - Missing')
            missing_files.append(file_path)
    
    if not missing_files:
        print('🎉 All MCP files present and syntactically valid!')
        print('💡 Install dependencies to enable full functionality')
    else:
        print(f'⚠️ Missing files: {missing_files}')
        
except Exception as e:
    print(f'❌ Error during verification: {e}')
"
        ;;
    3)
        echo "📊 Checking MCP status..."
        python3 -c "
import sys
sys.path.insert(0, '/workspace/src')

try:
    from ballsdeepnit.core.framework import get_framework
    import asyncio
    
    async def show_status():
        framework = get_framework()
        print('✅ Framework loaded successfully!')
        print(f'🤖 MCP Manager available: {hasattr(framework, \"mcp_manager\")}')
        
        # Try to get basic status
        try:
            await framework.initialize()
            status = await framework.get_mcp_status()
            print(f'📊 MCP Status: {status}')
        except Exception as e:
            print(f'⚠️ MCP initialization needs dependencies: {e}')
        finally:
            await framework.shutdown()
    
    asyncio.run(show_status())
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('💡 This usually means dependencies are missing')
    print('   Try: python3 -m pip install --break-system-packages -r requirements.txt')
except Exception as e:
    print(f'❌ Error: {e}')
"
        ;;
    4)
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "📝 For full setup instructions, see:"
echo "   📖 MCP_SETUP_README.md"
echo "   📊 REPOSITORY_STATUS.md"
echo ""
echo "🍑 BallsDeepnit MCP Framework Ready!"