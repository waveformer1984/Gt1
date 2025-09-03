#!/bin/bash

# Frank Bot Standalone Launcher - Optimized Version
# Desktop AI System for HYDI, RAID, and ProtoForge Integration
# Performance optimizations: Parallel startup, monitoring, caching

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Enable job control for parallel processing
set -m

FRANK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRANK_CONFIG="$FRANK_DIR/config.json"
FRANK_PID="$FRANK_DIR/frank.pid"
FRANK_LOG="$FRANK_DIR/logs/frank.log"
FRANK_NODE="$FRANK_DIR/frank_core.cjs"
FRANK_CACHE="$FRANK_DIR/.cache"
FRANK_METRICS="$FRANK_DIR/logs/metrics.log"

# Performance tuning
export NODE_OPTIONS="--max-old-space-size=512 --optimize-for-size"
export UV_THREADPOOL_SIZE=16  # Increase thread pool for better I/O

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[Frank]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$FRANK_LOG"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$FRANK_LOG"
}

log_error() {
    echo -e "${RED}[✗]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$FRANK_LOG" >&2
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$FRANK_LOG"
}

# Progress bar function
show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((width * current / total))
    
    printf "\r["
    printf "%${completed}s" | tr ' ' '='
    printf "%$((width - completed))s" | tr ' ' '-'
    printf "] %d%%" "$percentage"
}

print_banner() {
    echo -e "${BLUE}"
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║                      FRANK BOT OPTIMIZED                     ║"
    echo "  ║                    Standalone Desktop AI                     ║"
    echo "  ║                                                              ║"
    echo "  ║  HYDI Integration  •  RAID Processing  •  ProtoForge Core    ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Create necessary directories
init_directories() {
    local dirs=("$FRANK_DIR/logs" "$FRANK_CACHE" "$FRANK_DIR/data")
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
}

# Check system resources
check_system_resources() {
    log_info "Checking system resources..."
    
    local mem_total=$(free -m | awk 'NR==2{print $2}')
    local mem_available=$(free -m | awk 'NR==2{print $7}')
    local cpu_count=$(nproc)
    local disk_available=$(df -BG "$FRANK_DIR" | awk 'NR==2{print $4}' | sed 's/G//')
    
    echo -e "${CYAN}System Resources:${NC}"
    echo "  • CPU Cores: $cpu_count"
    echo "  • Total Memory: ${mem_total}MB"
    echo "  • Available Memory: ${mem_available}MB"
    echo "  • Disk Space: ${disk_available}GB available"
    
    # Warn if resources are low
    if [ "$mem_available" -lt 512 ]; then
        log_warning "Low memory available. Performance may be affected."
    fi
    
    if [ "$disk_available" -lt 1 ]; then
        log_warning "Low disk space. Please free up some space."
    fi
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    local deps=("node" "npm" "jq")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        echo "Please install the missing dependencies:"
        for dep in "${missing[@]}"; do
            case $dep in
                node) echo "  • Node.js 18+: https://nodejs.org" ;;
                npm) echo "  • npm (comes with Node.js)" ;;
                jq) echo "  • jq: sudo apt-get install jq (or brew install jq)" ;;
            esac
        done
        exit 1
    fi
    
    # Check Node.js version
    local node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$node_version" -lt 18 ]; then
        log_error "Node.js 18+ is required (current: v$node_version)"
        exit 1
    fi
    
    log_success "All dependencies satisfied"
}

# Optimized config creation with validation
create_default_config() {
    cat > "$FRANK_CONFIG" << 'EOF'
{
  "frank": {
    "name": "Frank Bot Standalone",
    "version": "1.0.0",
    "mode": "desktop",
    "autoStart": true,
    "port": 3001,
    "performance": {
      "maxWorkers": 4,
      "memoryLimit": 512,
      "enableCaching": true,
      "cacheSize": 100
    }
  },
  "capabilities": {
    "lexiconAnalyzer": {
      "enabled": true,
      "model": "advanced",
      "raidIntegration": true,
      "cacheResults": true
    },
    "systemIntegrator": {
      "enabled": true,
      "hydiSync": true,
      "protoforgeSync": true,
      "batchSize": 50
    },
    "automationOrchestrator": {
      "enabled": true,
      "workflowOptimization": true,
      "parallelExecution": true
    },
    "communicationHub": {
      "enabled": true,
      "nlpProcessing": true,
      "responseCache": true
    },
    "systemMonitor": {
      "enabled": true,
      "realTimeMetrics": true,
      "alerting": true,
      "metricsInterval": 30000
    }
  },
  "integration": {
    "hydi": {
      "autopilotSync": true,
      "voiceLogProcessing": true,
      "syncInterval": 30000,
      "batchProcessing": true
    },
    "raid": {
      "lexiconSync": true,
      "vocabularyAnalysis": true,
      "syncInterval": 60000,
      "incrementalSync": true
    },
    "protoforge": {
      "divisionSync": true,
      "automationRules": true,
      "syncInterval": 120000,
      "deltaSync": true
    }
  },
  "logging": {
    "level": "info",
    "file": "./logs/frank.log",
    "console": true,
    "maxFiles": 5,
    "maxSize": "10M"
  },
  "monitoring": {
    "enabled": true,
    "port": 3002,
    "collectInterval": 5000,
    "retentionDays": 7
  }
}
EOF
}

# Install dependencies with caching
install_dependencies() {
    log_info "Checking Node.js dependencies..."
    
    if [ ! -f "$FRANK_NODE" ]; then
        log_error "Frank core module not found: $FRANK_NODE"
        return 1
    fi
    
    # Check if package.json exists
    if [ -f "$FRANK_DIR/package.json" ]; then
        # Use npm ci for faster, more reliable installs
        if [ -f "$FRANK_DIR/package-lock.json" ]; then
            log_info "Installing dependencies with npm ci..."
            npm ci --prefix "$FRANK_DIR" --production
        else
            log_info "Installing dependencies with npm install..."
            npm install --prefix "$FRANK_DIR" --production
        fi
    else
        log_warning "No package.json found, skipping dependency installation"
    fi
    
    return 0
}

# Start Frank with performance monitoring
start_frank() {
    log_info "Starting Frank Bot..."
    
    # Check if already running
    if [ -f "$FRANK_PID" ] && kill -0 "$(cat "$FRANK_PID")" 2>/dev/null; then
        log_warning "Frank is already running (PID: $(cat "$FRANK_PID"))"
        return 0
    fi
    
    # Start the node process with monitoring
    nohup node "$FRANK_NODE" > "$FRANK_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$FRANK_PID"
    
    # Wait for startup
    local timeout=30
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        if kill -0 $pid 2>/dev/null; then
            show_progress $elapsed $timeout
            sleep 1
            elapsed=$((elapsed + 1))
            
            # Check if service is responsive
            if [ -f "$FRANK_LOG" ] && grep -q "Frank Bot ready" "$FRANK_LOG" 2>/dev/null; then
                printf "\n"
                log_success "Frank Bot started successfully (PID: $pid)"
                
                # Start performance monitor in background
                start_performance_monitor $pid &
                
                return 0
            fi
        else
            printf "\n"
            log_error "Frank Bot failed to start"
            [ -f "$FRANK_LOG" ] && tail -20 "$FRANK_LOG"
            return 1
        fi
    done
    
    printf "\n"
    log_error "Frank Bot startup timeout"
    return 1
}

# Performance monitoring function
start_performance_monitor() {
    local pid=$1
    
    while kill -0 $pid 2>/dev/null; do
        # Collect metrics
        local cpu=$(ps -p $pid -o %cpu= 2>/dev/null || echo "0")
        local mem=$(ps -p $pid -o %mem= 2>/dev/null || echo "0")
        local rss=$(ps -p $pid -o rss= 2>/dev/null || echo "0")
        
        # Log metrics
        echo "$(date '+%Y-%m-%d %H:%M:%S') CPU:${cpu}% MEM:${mem}% RSS:${rss}KB" >> "$FRANK_METRICS"
        
        # Check thresholds
        if (( $(echo "$cpu > 80" | bc -l) )); then
            log_warning "High CPU usage: ${cpu}%"
        fi
        
        if (( $(echo "$mem > 50" | bc -l) )); then
            log_warning "High memory usage: ${mem}%"
        fi
        
        sleep 30
    done
}

# Graceful stop with cleanup
stop_frank() {
    log_info "Stopping Frank Bot..."
    
    if [ ! -f "$FRANK_PID" ]; then
        log_warning "PID file not found"
        return 0
    fi
    
    local pid=$(cat "$FRANK_PID")
    
    if ! kill -0 $pid 2>/dev/null; then
        log_warning "Frank Bot is not running"
        rm -f "$FRANK_PID"
        return 0
    fi
    
    # Send SIGTERM for graceful shutdown
    kill -TERM $pid
    
    # Wait for process to exit
    local timeout=10
    local elapsed=0
    
    while [ $elapsed -lt $timeout ] && kill -0 $pid 2>/dev/null; do
        sleep 1
        elapsed=$((elapsed + 1))
    done
    
    if kill -0 $pid 2>/dev/null; then
        log_warning "Force killing Frank Bot"
        kill -KILL $pid
    fi
    
    rm -f "$FRANK_PID"
    log_success "Frank Bot stopped"
}

# Enhanced status with metrics
check_status() {
    echo -e "${CYAN}Frank Bot Status${NC}"
    echo "================="
    
    if [ -f "$FRANK_PID" ] && kill -0 "$(cat "$FRANK_PID")" 2>/dev/null; then
        local pid=$(cat "$FRANK_PID")
        echo -e "Status: ${GREEN}Running${NC} (PID: $pid)"
        
        # Show process info
        local cpu=$(ps -p $pid -o %cpu= 2>/dev/null || echo "N/A")
        local mem=$(ps -p $pid -o %mem= 2>/dev/null || echo "N/A")
        local etime=$(ps -p $pid -o etime= 2>/dev/null || echo "N/A")
        
        echo "CPU Usage: ${cpu}%"
        echo "Memory Usage: ${mem}%"
        echo "Uptime: $etime"
        
        # Show recent metrics
        if [ -f "$FRANK_METRICS" ]; then
            echo -e "\n${CYAN}Recent Performance:${NC}"
            tail -5 "$FRANK_METRICS"
        fi
        
        # Show configuration
        if [ -f "$FRANK_CONFIG" ]; then
            echo -e "\n${CYAN}Active Capabilities:${NC}"
            jq -r '.capabilities | to_entries[] | select(.value.enabled==true) | "  • " + .key' "$FRANK_CONFIG"
        fi
    else
        echo -e "Status: ${RED}Not Running${NC}"
    fi
    
    # Show logs
    if [ -f "$FRANK_LOG" ]; then
        echo -e "\n${CYAN}Recent Logs:${NC}"
        tail -10 "$FRANK_LOG"
    fi
}

# View logs with filtering
view_logs() {
    local filter="${1:-}"
    
    if [ ! -f "$FRANK_LOG" ]; then
        log_error "Log file not found"
        return 1
    fi
    
    if [ -n "$filter" ]; then
        log_info "Filtering logs for: $filter"
        grep -i "$filter" "$FRANK_LOG" | tail -50
    else
        # Use less for interactive viewing
        less +G "$FRANK_LOG"
    fi
}

# Clear cache and temporary files
clear_cache() {
    log_info "Clearing cache and temporary files..."
    
    if [ -d "$FRANK_CACHE" ]; then
        rm -rf "$FRANK_CACHE"/*
        log_success "Cache cleared"
    fi
    
    # Rotate logs if they're too large
    if [ -f "$FRANK_LOG" ]; then
        local log_size=$(stat -f%z "$FRANK_LOG" 2>/dev/null || stat -c%s "$FRANK_LOG" 2>/dev/null || echo 0)
        if [ "$log_size" -gt 10485760 ]; then  # 10MB
            mv "$FRANK_LOG" "$FRANK_LOG.$(date +%Y%m%d%H%M%S)"
            log_success "Log file rotated"
        fi
    fi
}

# Main function
main() {
    case "${1:-}" in
        start)
            print_banner
            init_directories
            check_system_resources
            check_dependencies
            
            if [ ! -f "$FRANK_CONFIG" ]; then
                log_warning "Creating default configuration..."
                create_default_config
            fi
            
            install_dependencies && start_frank
            ;;
            
        stop)
            stop_frank
            ;;
            
        restart)
            stop_frank
            sleep 2
            print_banner
            start_frank
            ;;
            
        status)
            check_status
            ;;
            
        logs)
            view_logs "${2:-}"
            ;;
            
        config)
            if [ -f "$FRANK_CONFIG" ]; then
                jq . "$FRANK_CONFIG"
            else
                log_error "Configuration file not found"
                exit 1
            fi
            ;;
            
        cache-clear)
            clear_cache
            ;;
            
        monitor)
            log_info "Starting real-time monitoring... (Press Ctrl+C to stop)"
            tail -f "$FRANK_LOG" "$FRANK_METRICS" 2>/dev/null
            ;;
            
        *)
            echo -e "${CYAN}Frank Bot Launcher - Optimized Edition${NC}"
            echo -e "${CYAN}Usage:${NC} $0 {start|stop|restart|status|logs [filter]|config|cache-clear|monitor}"
            echo ""
            echo "Commands:"
            echo "  start       - Start Frank Bot with optimizations"
            echo "  stop        - Stop Frank Bot gracefully"
            echo "  restart     - Restart Frank Bot"
            echo "  status      - Show status and metrics"
            echo "  logs        - View logs (optional filter)"
            echo "  config      - Display current configuration"
            echo "  cache-clear - Clear cache and rotate logs"
            echo "  monitor     - Real-time log monitoring"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"