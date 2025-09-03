#!/bin/bash
# REZONATE Setup - Install Dependencies
# Initialize development environment for all REZONATE components

set -e

echo "🚀 REZONATE Setup - Installing Dependencies"
echo "=========================================="

# Check system requirements
echo "📋 Checking system requirements..."

# Check for required tools
REQUIRED_TOOLS=("git" "python3" "node" "pip")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING_TOOLS+=("$tool")
        echo "❌ Missing: $tool"
    else
        echo "✓ Found: $tool ($(command -v "$tool"))"
    fi
done

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo "💥 Missing required tools: ${MISSING_TOOLS[*]}"
    echo "Please install them and run this script again."
    exit 1
fi

# Python dependencies for automation
echo "🐍 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✓ Installed Python requirements"
fi

# Install development tools
pip install --user platformio black isort pytest
echo "✓ Installed development tools"

# Node.js dependencies (if package.json exists)
echo "📦 Checking for Node.js projects..."
find software/ -name "package.json" -exec dirname {} \; | while read -r dir; do
    echo "Installing dependencies in $dir..."
    (cd "$dir" && npm install)
done

# Hardware design tools check
echo "🔧 Checking hardware design tools..."
if command -v kicad &> /dev/null; then
    echo "✓ KiCad found: $(kicad --version | head -n1)"
else
    echo "⚠️ KiCad not found - install for hardware design"
    echo "   Visit: https://www.kicad.org/download/"
fi

# Firmware development check
echo "⚡ Setting up firmware development..."
if command -v pio &> /dev/null; then
    echo "✓ PlatformIO CLI ready"
    # Initialize basic ESP32 project structure if needed
else
    echo "⚠️ PlatformIO not in PATH - check installation"
fi

# Git hooks setup
echo "🔗 Setting up Git hooks..."
if [ -d ".git" ]; then
    # Create pre-commit hook for formatting
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# REZONATE pre-commit hook
echo "🔍 Running REZONATE pre-commit checks..."

# Format Python files
find . -name "*.py" -not -path "./venv/*" | xargs black --quiet
find . -name "*.py" -not -path "./venv/*" | xargs isort --quiet

# Check YAML syntax
find .github/workflows/ -name "*.yml" -exec python3 -c "import yaml; yaml.safe_load(open('{}'))" \;

echo "✓ Pre-commit checks passed"
EOF
    chmod +x .git/hooks/pre-commit
    echo "✓ Git pre-commit hook installed"
fi

# Create development environment file
cat > .env.development << 'EOF'
# REZONATE Development Environment
REZONATE_ENV=development
REZONATE_LOG_LEVEL=debug
REZONATE_BLUETOOTH_ENABLED=true
REZONATE_MIDI_ENABLED=true
REZONATE_AI_INTEGRATION=false
EOF

echo "✓ Created development environment file"

# Final validation
echo "🧪 Running validation tests..."
if [ -x "automation/test/run-all-tests.sh" ]; then
    ./automation/test/run-all-tests.sh
else
    echo "⚠️ Test script not executable"
fi

echo "=========================================="
echo "🎉 REZONATE setup completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Review component READMEs for specific setup"
echo "  2. Choose a component to start developing:"
echo "     - Hardware: cd hardware-design/ && # Add KiCad files"
echo "     - Firmware: cd firmware/ && pio init --board esp32-s3-devkitc-1"
echo "     - Software: cd software/performance-ui/ && npx react-native init"
echo "  3. Run './automation/build/build-all.sh' to validate"
echo ""
echo "Happy coding! 🎵"