#!/bin/bash
# REZONATE Self-Heal - Fix YAML Files
# Automatically repair broken YAML syntax and structure

set -e

echo "🔧 REZONATE Self-Heal - Fixing YAML Files"
echo "=========================================="

# Check for yaml tools
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 required for YAML validation"
    exit 1
fi

# Install PyYAML if not available
python3 -c "import yaml" 2>/dev/null || pip install --user PyYAML

YAML_FILES_FOUND=0
YAML_FILES_FIXED=0
YAML_FILES_FAILED=0

# Find and validate YAML files
echo "🔍 Scanning for YAML files..."
find . -name "*.yml" -o -name "*.yaml" | grep -v node_modules | while read -r yaml_file; do
    YAML_FILES_FOUND=$((YAML_FILES_FOUND + 1))
    echo "Checking: $yaml_file"
    
    # Test YAML syntax
    if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
        echo "✓ $yaml_file - Valid YAML"
    else
        echo "🔧 $yaml_file - Attempting repair..."
        
        # Create backup
        cp "$yaml_file" "$yaml_file.backup"
        
        # Common YAML fixes
        sed -i 's/\t/  /g' "$yaml_file"                # Replace tabs with spaces
        sed -i 's/[[:space:]]*$//' "$yaml_file"        # Remove trailing whitespace
        sed -i '/^[[:space:]]*$/d' "$yaml_file"        # Remove empty lines with whitespace
        
        # Test again after fixes
        if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
            echo "✓ $yaml_file - Fixed successfully"
            rm "$yaml_file.backup"
            YAML_FILES_FIXED=$((YAML_FILES_FIXED + 1))
        else
            echo "❌ $yaml_file - Could not auto-fix"
            mv "$yaml_file.backup" "$yaml_file"
            YAML_FILES_FAILED=$((YAML_FILES_FAILED + 1))
        fi
    fi
done

# Fix GitHub Actions workflow issues
echo "🔧 Checking GitHub Actions workflows..."
WORKFLOW_DIR=".github/workflows"
if [ -d "$WORKFLOW_DIR" ]; then
    for workflow in "$WORKFLOW_DIR"/*.yml; do
        if [ -f "$workflow" ]; then
            echo "Validating workflow: $(basename "$workflow")"
            
            # Check for common workflow issues
            if ! grep -q "on:" "$workflow"; then
                echo "⚠️ Missing 'on:' trigger in $workflow"
            fi
            
            if ! grep -q "jobs:" "$workflow"; then
                echo "⚠️ Missing 'jobs:' section in $workflow"
            fi
            
            # Validate workflow syntax
            python3 -c "
import yaml
import sys
try:
    with open('$workflow', 'r') as f:
        content = yaml.safe_load(f)
    if 'on' not in content:
        print('⚠️ Workflow missing trigger configuration')
    if 'jobs' not in content:
        print('⚠️ Workflow missing jobs section')
    print('✓ Workflow syntax valid')
except Exception as e:
    print(f'❌ Workflow syntax error: {e}')
    sys.exit(1)
" || echo "❌ Workflow validation failed: $workflow"
        fi
    done
fi

# Fix documentation YAML frontmatter
echo "📚 Checking documentation YAML frontmatter..."
find . -name "*.md" | while read -r md_file; do
    if head -n 1 "$md_file" | grep -q "^---$"; then
        echo "Checking frontmatter in: $md_file"
        
        # Extract frontmatter for validation
        sed -n '2,/^---$/p' "$md_file" | head -n -1 > /tmp/frontmatter.yml 2>/dev/null || true
        
        if [ -s /tmp/frontmatter.yml ]; then
            if ! python3 -c "import yaml; yaml.safe_load(open('/tmp/frontmatter.yml'))" 2>/dev/null; then
                echo "🔧 Fixing frontmatter in $md_file"
                # Remove broken frontmatter for now
                sed -i '/^---$/,/^---$/d' "$md_file"
                echo "✓ Removed broken frontmatter from $md_file"
            fi
        fi
        
        rm -f /tmp/frontmatter.yml
    fi
done

# Generate summary report
echo "=========================================="
echo "🔧 YAML Self-Heal Summary:"
echo "  Files Scanned: $YAML_FILES_FOUND"
echo "  Files Fixed: $YAML_FILES_FIXED" 
echo "  Files Failed: $YAML_FILES_FAILED"

if [ $YAML_FILES_FAILED -eq 0 ]; then
    echo "🎉 All YAML files are healthy!"
    exit 0
else
    echo "⚠️ Some YAML files require manual attention"
    exit 1
fi