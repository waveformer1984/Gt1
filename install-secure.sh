#!/bin/bash
# Secure Local Installation for ballsDeepnit + Hydi REPL
# This script installs the system in a secure, local-only configuration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="$HOME/.ballsdeepnit"
BACKUP_DIR="$HOME/.ballsdeepnit-backup-$(date +%Y%m%d-%H%M%S)"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Java is installed
check_java() {
    if ! command -v java &> /dev/null; then
        log_error "Java is not installed. Please install Java 11+ first."
        exit 1
    fi
    
    if ! command -v javac &> /dev/null; then
        log_error "Java compiler (javac) is not installed. Please install JDK 11+ first."
        exit 1
    fi
    
    local java_version=$(java -version 2>&1 | head -n1 | cut -d'"' -f2 | cut -d'.' -f1)
    if [[ "$java_version" -lt 11 ]]; then
        log_error "Java 11+ is required. Current version: $java_version"
        exit 1
    fi
    
    log_success "Java $java_version detected"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.10+ first."
        exit 1
    fi
    
    local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    local major=$(echo "$python_version" | cut -d'.' -f1)
    local minor=$(echo "$python_version" | cut -d'.' -f2)
    
    if [[ "$major" -lt 3 || ("$major" -eq 3 && "$minor" -lt 10) ]]; then
        log_error "Python 3.10+ is required. Current version: $python_version"
        exit 1
    fi
    
    log_success "Python $python_version detected"
}

# Create secure directory structure
create_directories() {
    log_info "Creating secure directory structure..."
    
    # Backup existing installation if it exists
    if [[ -d "$INSTALL_DIR" ]]; then
        log_warning "Existing installation found. Creating backup..."
        mv "$INSTALL_DIR" "$BACKUP_DIR"
        log_success "Backup created at $BACKUP_DIR"
    fi
    
    # Create new directory structure
    mkdir -p "$INSTALL_DIR"/{config,data/{cache,logs,plugins},java/{bin,db,src},temp,venv,bin}
    
    # Set secure permissions
    chmod 700 "$INSTALL_DIR"
    chmod 700 "$INSTALL_DIR/config"
    chmod 755 "$INSTALL_DIR/data"
    chmod 700 "$INSTALL_DIR/java"
    chmod 755 "$INSTALL_DIR/bin"
    
    log_success "Secure directory structure created"
}

# Install Java components
install_java() {
    log_info "Installing Java REPL components..."
    
    # Copy Java source files
    if [[ -d "src" && -n "$(find src -name '*.java' -type f)" ]]; then
        cp src/*.java "$INSTALL_DIR/java/src/"
        
        # Compile Java files
        cd "$INSTALL_DIR/java"
        if javac -d bin src/*.java; then
            log_success "Java components compiled successfully"
        else
            log_error "Java compilation failed"
            exit 1
        fi
        cd - > /dev/null
    else
        log_error "Java source files not found in src/ directory"
        exit 1
    fi
    
    # Create secure REPL launcher
    cat > "$INSTALL_DIR/bin/secure-repl.sh" << 'EOF'
#!/bin/bash
# Secure Java REPL launcher with sandboxing

set -euo pipefail

HYDI_HOME="$HOME/.ballsdeepnit"
JAVA_OPTS="-Djava.security.manager -Djava.security.policy=$HYDI_HOME/java/security.policy"

cd "$HYDI_HOME/java"
exec java $JAVA_OPTS -cp bin CommandREPL "$@"
EOF
    
    chmod +x "$INSTALL_DIR/bin/secure-repl.sh"
    
    # Create Java security policy
    cat > "$INSTALL_DIR/java/security.policy" << 'EOF'
grant {
    permission java.io.FilePermission "${user.home}/.ballsdeepnit/data/-", "read,write,delete";
    permission java.io.FilePermission "${java.io.tmpdir}/-", "read,write,delete";
    permission java.util.PropertyPermission "*", "read";
    permission java.lang.RuntimePermission "accessDeclaredMembers";
    permission java.net.SocketPermission "localhost:0", "listen,resolve";
    permission java.net.SocketPermission "127.0.0.1:0", "listen,resolve";
};
EOF
    
    log_success "Java REPL installed with security sandbox"
}

# Install Python components
install_python() {
    log_info "Installing Python framework components..."
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install basic requirements
    if [[ -f "requirements-basic.txt" ]]; then
        pip install --no-cache-dir -r requirements-basic.txt
    elif [[ -f "requirements.txt" ]]; then
        pip install --no-cache-dir -r requirements.txt
    else
        log_warning "No requirements file found. Installing minimal dependencies..."
        pip install --no-cache-dir fastapi uvicorn click pydantic pydantic-settings
    fi
    
    # Install ballsdeepnit package if available
    if [[ -d "src/ballsdeepnit" ]]; then
        pip install -e .
        log_success "ballsDeepnit Python package installed"
    else
        log_warning "ballsdeepnit Python package not found, skipping..."
    fi
    
    deactivate
    log_success "Python virtual environment created and configured"
}

# Create secure configuration
create_config() {
    log_info "Creating secure configuration files..."
    
    # Create secure YAML config
    cat > "$INSTALL_DIR/config/secure.yaml" << 'EOF'
network:
  host: "127.0.0.1"
  port: 8000
  allow_external: false
  cors_origins: ["http://127.0.0.1:3000"]

security:
  enable_authentication: true
  local_only_mode: true
  disable_external_plugins: true
  sandbox_java_execution: true

performance:
  max_memory_mb: 512
  enable_profiling: false
  max_workers: 4

logging:
  level: INFO
  file: ~/.ballsdeepnit/logs/ballsdeepnit.log
  max_size: 10MB
  backup_count: 5

cache:
  enable_redis: false
  disk_cache_size_mb: 50
  ttl_seconds: 3600
EOF
    
    # Create environment file
    cat > "$INSTALL_DIR/config/local.env" << 'EOF'
BALLSDEEPNIT_HOST=127.0.0.1
BALLSDEEPNIT_PORT=8000
BALLSDEEPNIT_DEBUG=false
BALLSDEEPNIT_LOCAL_ONLY=true
BALLSDEEPNIT_CONFIG_FILE=~/.ballsdeepnit/config/secure.yaml
EOF
    
    # Create SQLite config
    cat > "$INSTALL_DIR/config/sqlite.conf" << 'EOF'
PRAGMA temp_store = memory;
PRAGMA secure_delete = on;
PRAGMA foreign_keys = on;
PRAGMA journal_mode = WAL;
EOF
    
    # Set secure permissions
    chmod 600 "$INSTALL_DIR/config"/*
    
    log_success "Secure configuration files created"
}

# Create startup scripts
create_scripts() {
    log_info "Creating secure startup scripts..."
    
    # Main startup script
    cat > "$INSTALL_DIR/bin/ballsdeepnit-start.sh" << 'EOF'
#!/bin/bash
# Secure startup script for ballsDeepnit

set -euo pipefail

HYDI_HOME="$HOME/.ballsdeepnit"
source "$HYDI_HOME/venv/bin/activate"
export BALLSDEEPNIT_CONFIG="$HYDI_HOME/config/secure.yaml"

cd "$HYDI_HOME"
exec python -m ballsdeepnit run "$@"
EOF
    
    # Dashboard startup script
    cat > "$INSTALL_DIR/bin/ballsdeepnit-dashboard.sh" << 'EOF'
#!/bin/bash
# Secure dashboard startup script

set -euo pipefail

HYDI_HOME="$HOME/.ballsdeepnit"
source "$HYDI_HOME/venv/bin/activate"
export BALLSDEEPNIT_CONFIG="$HYDI_HOME/config/secure.yaml"

cd "$HYDI_HOME"
exec python -m ballsdeepnit dashboard "$@"
EOF
    
    # Status check script
    cat > "$INSTALL_DIR/bin/ballsdeepnit-status.sh" << 'EOF'
#!/bin/bash
# System status check script

echo "🔍 ballsDeepnit System Status"
echo "================================"

# Check Java
if command -v java &> /dev/null; then
    echo "✅ Java: $(java -version 2>&1 | head -n1)"
else
    echo "❌ Java: Not installed"
fi

# Check Python
if [[ -f "$HOME/.ballsdeepnit/venv/bin/python" ]]; then
    echo "✅ Python venv: $($HOME/.ballsdeepnit/venv/bin/python --version)"
else
    echo "❌ Python venv: Not found"
fi

# Check compiled Java classes
if [[ -f "$HOME/.ballsdeepnit/java/bin/CommandREPL.class" ]]; then
    echo "✅ Java REPL: Compiled"
else
    echo "❌ Java REPL: Not compiled"
fi

# Check network bindings
echo ""
echo "🌐 Network Status:"
if netstat -tlpn 2>/dev/null | grep -q ":8000.*127.0.0.1"; then
    echo "✅ ballsDeepnit server: Running (localhost only)"
elif netstat -tlpn 2>/dev/null | grep -q ":8000"; then
    echo "⚠️  ballsDeepnit server: Running (check binding)"
else
    echo "ℹ️  ballsDeepnit server: Not running"
fi

# Check permissions
echo ""
echo "🔒 Security Status:"
if [[ $(stat -c %a "$HOME/.ballsdeepnit") == "700" ]]; then
    echo "✅ Directory permissions: Secure (700)"
else
    echo "⚠️  Directory permissions: $(stat -c %a "$HOME/.ballsdeepnit")"
fi
EOF
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/bin"/*.sh
    
    log_success "Startup scripts created"
}

# Create desktop shortcut
create_shortcuts() {
    log_info "Creating desktop shortcuts..."
    
    # Create desktop entry if desktop environment is available
    if [[ -d "$HOME/Desktop" || -d "$HOME/.local/share/applications" ]]; then
        local desktop_dir="$HOME/.local/share/applications"
        mkdir -p "$desktop_dir"
        
        cat > "$desktop_dir/ballsdeepnit.desktop" << 'EOF'
[Desktop Entry]
Name=ballsDeepnit Framework
Comment=High-performance automation framework
Exec=/home/%u/.ballsdeepnit/bin/ballsdeepnit-start.sh
Icon=applications-development
Terminal=true
Type=Application
Categories=Development;
EOF
        
        log_success "Desktop entry created"
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    local errors=0
    
    # Check directory structure
    for dir in config data java bin venv; do
        if [[ ! -d "$INSTALL_DIR/$dir" ]]; then
            log_error "Missing directory: $dir"
            ((errors++))
        fi
    done
    
    # Check Java compilation
    if [[ ! -f "$INSTALL_DIR/java/bin/CommandREPL.class" ]]; then
        log_error "Java REPL not compiled"
        ((errors++))
    fi
    
    # Check Python virtual environment
    if [[ ! -f "$INSTALL_DIR/venv/bin/python" ]]; then
        log_error "Python virtual environment not created"
        ((errors++))
    fi
    
    # Check permissions
    local dir_perms=$(stat -c %a "$INSTALL_DIR")
    if [[ "$dir_perms" != "700" ]]; then
        log_warning "Directory permissions: $dir_perms (should be 700)"
    fi
    
    if [[ $errors -eq 0 ]]; then
        log_success "Installation verification passed"
        return 0
    else
        log_error "Installation verification failed with $errors errors"
        return 1
    fi
}

# Print usage instructions
print_usage() {
    echo ""
    echo -e "${GREEN}🎉 ballsDeepnit + Hydi REPL installation complete!${NC}"
    echo ""
    echo "📂 Installation directory: $INSTALL_DIR"
    echo ""
    echo "🚀 Quick Start Commands:"
    echo "  Start Python framework:  $INSTALL_DIR/bin/ballsdeepnit-start.sh"
    echo "  Start web dashboard:     $INSTALL_DIR/bin/ballsdeepnit-dashboard.sh"
    echo "  Start Java REPL:         $INSTALL_DIR/bin/secure-repl.sh"
    echo "  Check system status:     $INSTALL_DIR/bin/ballsdeepnit-status.sh"
    echo ""
    echo "🔒 Security Features:"
    echo "  ✅ Localhost-only bindings (127.0.0.1)"
    echo "  ✅ Java security manager enabled"
    echo "  ✅ Isolated Python virtual environment"
    echo "  ✅ Secure file permissions (700/600)"
    echo "  ✅ No external network dependencies"
    echo ""
    echo "📖 Documentation:"
    echo "  Security guide:    SECURITY_LOCKDOWN.md"
    echo "  Setup guide:       SETUP_GUIDE.md"
    echo ""
    echo "⚠️  Remember to read SECURITY_LOCKDOWN.md for important security information!"
}

# Main installation flow
main() {
    echo -e "${BLUE}"
    echo "🔒 ballsDeepnit + Hydi REPL Secure Local Installation"
    echo "===================================================="
    echo -e "${NC}"
    echo "This script will install ballsDeepnit in a secure, local-only configuration."
    echo ""
    
    # Check dependencies
    check_java
    check_python
    
    # Install components
    create_directories
    install_java
    install_python
    create_config
    create_scripts
    create_shortcuts
    
    # Verify and finish
    if verify_installation; then
        print_usage
        log_success "Installation completed successfully!"
        exit 0
    else
        log_error "Installation failed. Check the errors above."
        exit 1
    fi
}

# Run with error handling
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    trap 'log_error "Installation failed on line $LINENO"' ERR
    main "$@"
fi