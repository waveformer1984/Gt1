#!/bin/bash

# Frank Bot Standalone Launcher
# Desktop AI System for HYDI, RAID, and ProtoForge Integration

FRANK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRANK_CONFIG="$FRANK_DIR/config.json"
FRANK_PID="$FRANK_DIR/frank.pid"
FRANK_LOG="$FRANK_DIR/logs/frank.log"
FRANK_NODE="$FRANK_DIR/frank_core.cjs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_banner() {
    echo -e "${BLUE}"
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║                         FRANK BOT                            ║"
    echo "  ║                    Standalone Desktop AI                     ║"
    echo "  ║                                                              ║"
    echo "  ║  HYDI Integration  •  RAID Processing  •  ProtoForge Core    ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_dependencies() {
    echo -e "${BLUE}[Frank]${NC} Checking dependencies..."
    
    if ! command -v node &> /dev/null; then
        echo -e "${RED}[Error]${NC} Node.js is required but not installed"
        echo "Please install Node.js 18+ to run Frank Bot"
        exit 1
    fi
    
    if [ ! -f "$FRANK_CONFIG" ]; then
        echo -e "${YELLOW}[Setup]${NC} Creating default configuration..."
        create_default_config
    fi
    
    echo -e "${GREEN}[Frank]${NC} Dependencies check complete"
}

create_default_config() {
    cat > "$FRANK_CONFIG" << 'EOF'
{
  "frank": {
    "name": "Frank Bot Standalone",
    "version": "1.0.0",
    "mode": "desktop",
    "autoStart": true,
    "port": 3001
  },
  "capabilities": {
    "lexiconAnalyzer": {
      "enabled": true,
      "model": "advanced",
      "raidIntegration": true
    },
    "systemIntegrator": {
      "enabled": true,
      "hydiSync": true,
      "protoforgeSync": true
    },
    "automationOrchestrator": {
      "enabled": true,
      "workflowOptimization": true
    },
    "communicationHub": {
      "enabled": true,
      "nlpProcessing": true
    },
    "systemMonitor": {
      "enabled": true,
      "realTimeMetrics": true,
      "alerting": true
    }
  },
  "integration": {
    "hydi": {
      "autopilotSync": true,
      "voiceLogProcessing": true,
      "syncInterval": 30000
    },
    "raid": {
      "lexiconSync": true,
      "vocabularyAnalysis": true,
      "syncInterval": 60000
    },
    "protoforge": {
      "divisionSync": true,
      "automationRules": true,
      "syncInterval": 120000
    }
  },
  "logging": {
    "level": "info",
    "file": "./logs/frank.log",
    "console": true
  }
}
EOF
}

start_frank() {
    if is_running; then
        echo -e "${YELLOW}[Frank]${NC} Already running (PID: $(cat $FRANK_PID))"
        return 0
    fi
    
    print_banner
    check_dependencies
    
    echo -e "${BLUE}[Frank]${NC} Starting Frank Bot..."
    echo -e "${BLUE}[Frank]${NC} Configuration: $FRANK_CONFIG"
    echo -e "${BLUE}[Frank]${NC} Logs: $FRANK_LOG"
    
    # Start Frank in background
    nohup node "$FRANK_NODE" > "$FRANK_LOG" 2>&1 &
    local frank_pid=$!
    echo $frank_pid > "$FRANK_PID"
    
    # Wait a moment to check if it started successfully
    sleep 2
    
    if is_running; then
        echo -e "${GREEN}[Frank]${NC} Started successfully (PID: $frank_pid)"
        echo -e "${GREEN}[Frank]${NC} Frank Bot is now operational"
        echo ""
        echo -e "${BLUE}Commands:${NC}"
        echo "  $0 status    - Check Frank status"
        echo "  $0 stop      - Stop Frank Bot"
        echo "  $0 logs      - View logs"
        echo "  $0 config    - Edit configuration"
    else
        echo -e "${RED}[Error]${NC} Failed to start Frank Bot"
        echo -e "${RED}[Error]${NC} Check logs: $FRANK_LOG"
        exit 1
    fi
}

stop_frank() {
    if ! is_running; then
        echo -e "${YELLOW}[Frank]${NC} Not running"
        return 0
    fi
    
    local pid=$(cat "$FRANK_PID")
    echo -e "${BLUE}[Frank]${NC} Stopping Frank Bot (PID: $pid)..."
    
    kill "$pid" 2>/dev/null
    sleep 2
    
    if is_running; then
        echo -e "${YELLOW}[Frank]${NC} Force stopping..."
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi
    
    rm -f "$FRANK_PID"
    echo -e "${GREEN}[Frank]${NC} Stopped"
}

status_frank() {
    print_banner
    
    if is_running; then
        local pid=$(cat "$FRANK_PID")
        local uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
        echo -e "${GREEN}[Status]${NC} Frank Bot is running"
        echo -e "${GREEN}[PID]${NC}    $pid"
        echo -e "${GREEN}[Uptime]${NC} $uptime"
        echo -e "${GREEN}[Config]${NC} $FRANK_CONFIG"
        echo -e "${GREEN}[Logs]${NC}   $FRANK_LOG"
        
        if [ -f "$FRANK_LOG" ]; then
            echo ""
            echo -e "${BLUE}[Recent Activity]${NC}"
            tail -5 "$FRANK_LOG" | sed 's/^/  /'
        fi
    else
        echo -e "${RED}[Status]${NC} Frank Bot is not running"
    fi
}

is_running() {
    [ -f "$FRANK_PID" ] && kill -0 $(cat "$FRANK_PID") 2>/dev/null
}

show_help() {
    print_banner
    echo -e "${BLUE}Usage:${NC} $0 [command]"
    echo ""
    echo -e "${BLUE}Commands:${NC}"
    echo "  start     Start Frank Bot"
    echo "  stop      Stop Frank Bot"
    echo "  restart   Restart Frank Bot"
    echo "  status    Show Frank Bot status"
    echo "  logs      View Frank Bot logs"
    echo "  config    Edit configuration"
    echo "  help      Show this help"
}

case "$1" in
    start)
        start_frank
        ;;
    stop)
        stop_frank
        ;;
    restart)
        stop_frank
        sleep 2
        start_frank
        ;;
    status)
        status_frank
        ;;
    logs)
        [ -f "$FRANK_LOG" ] && tail -f "$FRANK_LOG" || echo "No log file found"
        ;;
    config)
        [ -f "$FRANK_CONFIG" ] && nano "$FRANK_CONFIG" || echo "Config file not found"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            start_frank
        else
            echo -e "${RED}[Error]${NC} Unknown command: $1"
            echo "Use '$0 help' for available commands"
            exit 1
        fi
        ;;
esac