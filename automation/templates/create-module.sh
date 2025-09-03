#!/bin/bash
# REZONATE Template Generator - Create New Module Templates
# Automatically generate scaffolding for new hardware/MIDI mapping modules

set -e

echo "🎵 REZONATE Template Generator - New Module Creation"
echo "=================================================="

# Function to create hardware module template
create_hardware_module() {
    local module_name=$1
    local module_dir="hardware-design/modules/$module_name"
    
    echo "🔧 Creating hardware module: $module_name"
    
    mkdir -p "$module_dir/schematics"
    mkdir -p "$module_dir/pcb-layouts"
    mkdir -p "$module_dir/3d-models"
    mkdir -p "$module_dir/documentation"
    
    # Create module README
    cat > "$module_dir/README.md" << EOF
# $module_name - REZONATE Hardware Module

## Overview
Hardware module for the REZONATE modular wearable instrument system.

## Module Specifications
- **Type**: Hardware Component
- **Category**: [Audio/Control/Power/Communication]
- **Compatibility**: REZONATE v1.0+
- **Power Requirements**: [Voltage/Current specifications]

## Integration
This module integrates with:
- REZONATE main controller
- Power distribution system
- Communication bus
- User interface

## Development Status
- [ ] Schematic design
- [ ] PCB layout
- [ ] 3D modeling
- [ ] Prototyping
- [ ] Testing
- [ ] Documentation

---
*REZONATE $module_name - Hardware Module*
EOF

    echo "✓ Hardware module template created: $module_dir"
}

# Function to create MIDI mapping module template
create_midi_module() {
    local module_name=$1
    local module_dir="software/midi-mapping/modules/$module_name"
    
    echo "🎹 Creating MIDI mapping module: $module_name"
    
    mkdir -p "$module_dir/src"
    mkdir -p "$module_dir/presets"
    mkdir -p "$module_dir/tests"
    
    # Create module README
    cat > "$module_dir/README.md" << EOF
# $module_name - REZONATE MIDI Mapping Module

## Overview
MIDI mapping module for the REZONATE modular wearable instrument system.

## Module Specifications
- **Type**: MIDI Mapping
- **Input Types**: [Touch/Motion/Voice/External]
- **Output Types**: [MIDI Notes/CC/Program Change/SysEx]
- **Latency**: <5ms target
- **Compatibility**: REZONATE v1.0+

## Integration
This module integrates with:
- REZONATE hardware inputs
- MIDI output system
- Preset management
- Performance UI

---
*REZONATE $module_name - MIDI Mapping Module*
EOF

    echo "✓ MIDI mapping module template created: $module_dir"
}

# Main script logic
if [ $# -eq 0 ]; then
    echo "Usage: $0 <module_type> <module_name>"
    echo ""
    echo "Module types:"
    echo "  hardware   - Create hardware design module"
    echo "  midi       - Create MIDI mapping module"
    echo ""
    echo "Examples:"
    echo "  $0 hardware pressure-sensor"
    echo "  $0 midi touch-harp"
    exit 1
fi

MODULE_TYPE=$1
MODULE_NAME=$2

if [ -z "$MODULE_NAME" ]; then
    echo "❌ Module name required"
    exit 1
fi

case $MODULE_TYPE in
    "hardware")
        create_hardware_module "$MODULE_NAME"
        ;;
    "midi")
        create_midi_module "$MODULE_NAME"
        ;;
    *)
        echo "❌ Unknown module type: $MODULE_TYPE"
        echo "Available types: hardware, midi"
        exit 1
        ;;
esac

echo ""
echo "🎉 Module template created successfully!"
echo "Next steps:"
echo "  1. Review the generated files and documentation"
echo "  2. Implement the module-specific functionality"
echo "  3. Add tests and validation"
echo "  4. Update integration documentation"
echo ""
echo "Happy coding! 🎵"