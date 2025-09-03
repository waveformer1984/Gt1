# Documentation - REZONATE

## Overview
Comprehensive documentation for the REZONATE modular wearable instrument system.

## Quick Navigation
- [📋 Setup Guide](#setup-guide)
- [🛠️ Development](#development)
- [🎵 User Manual](#user-manual)
- [🔧 API Reference](#api-reference)
- [🤝 Contributing](#contributing)

## Setup Guide

### System Requirements
**Hardware:**
- REZONATE hardware components (harp, drones, power system)
- Mobile device (iOS 14+ / Android 10+)
- Computer with DAW software (optional)

**Software:**
- REZONATE mobile app
- Bluetooth 5.0+ support
- USB-C for charging and firmware updates

### Quick Start (5 Minutes)
1. **Power On**: Press and hold power button on main controller
2. **Pair Devices**: Open REZONATE app → "Add Device" → Select components
3. **Calibrate**: Follow in-app motion calibration (30 seconds)
4. **Play**: Start with preset "Ambient Harp" for immediate sound

### First Performance Setup
```
1. Wear the neck harp comfortably
2. Position drones 2-3 meters away
3. Open Performance UI on your device
4. Select "Performance Mode"
5. Begin playing - touch strings generate MIDI notes
6. Use gestures to control drone sounds
```

## Development

### Architecture Overview
```
REZONATE System Architecture:

Hardware Layer:
├── Neck Harp (MIDI Controller)
├── Motion Sensors (IMU)
├── Drone Modules (Speakers)
└── Power Management

Firmware Layer:
├── Real-time MIDI Generation
├── Motion Processing
├── Wireless Communication
└── Power Management

Software Layer:
├── Performance UI
├── Bluetooth Orchestration  
├── MIDI Mapping Engine
└── Integration APIs

Integration Layer:
├── Hydi AI Voice Control
├── External DAW Support
├── Cloud Sync (Optional)
└── OTA Updates
```

### Development Environment Setup
See individual module READMEs:
- [Hardware Design Setup](../hardware-design/README.md)
- [Firmware Development](../firmware/README.md)
- [Software Development](../software/README.md)
- [Automation Setup](../automation/README.md)

## User Manual

### Basic Operations

#### Power Management
- **Power On/Off**: Hold main button 3 seconds
- **Sleep Mode**: Automatic after 5 minutes idle
- **Charging**: USB-C port, 2-hour full charge
- **Battery Life**: 8+ hours typical use

#### Playing Techniques

**Harp Mode:**
- Light touch: Soft notes (velocity 40-60)
- Firm press: Strong notes (velocity 80-127)
- Slide: Pitch bend effects
- Multi-finger: Chord generation

**Motion Control:**
- Tilt left/right: Pan drone sounds
- Forward/back lean: Volume control
- Rotation: Filter cutoff
- Sharp movements: Trigger effects

#### Advanced Features

**Voice Commands (Hydi Integration):**
- "Start recording"
- "Change to minor key"
- "Increase drone volume"
- "Save this setting as preset"

**MIDI Integration:**
- Connect to DAW via Bluetooth or USB
- Map gestures to plugin parameters
- Sync tempo with external sequencer
- Record MIDI data for editing

## API Reference

### REST API Endpoints
```
GET    /api/devices           # List paired devices
POST   /api/devices/pair      # Pair new device
GET    /api/status            # System status
POST   /api/calibrate         # Start calibration
GET    /api/presets           # List presets
POST   /api/presets           # Save new preset
PUT    /api/presets/{id}      # Update preset
DELETE /api/presets/{id}      # Delete preset
```

### WebSocket Events
```javascript
// Device status updates
{
  "type": "device_status",
  "device_id": "harp_01",
  "battery": 85,
  "connected": true
}

// MIDI note events
{
  "type": "midi_note",
  "note": 60,
  "velocity": 120,
  "channel": 1
}

// Motion data
{
  "type": "motion",
  "accel": [0.1, -0.2, 9.8],
  "gyro": [0.05, 0.1, -0.02],
  "timestamp": 1640995200000
}
```

### MIDI Protocol
- **Channel 1**: Harp notes
- **Channel 2**: Drone control
- **Channel 3**: Motion-mapped parameters
- **Channel 4**: Voice commands
- **CC 1**: Modulation (gesture Y-axis)
- **CC 2**: Breath (gesture Z-axis)
- **CC 7**: Volume (gesture X-axis)

## Troubleshooting

### Common Issues

**Device Won't Pair:**
1. Ensure Bluetooth is enabled
2. Reset device: Hold power + calibrate buttons
3. Clear app cache and retry
4. Check device compatibility

**No Sound from Drones:**
1. Verify drone power status
2. Check Bluetooth connection strength
3. Adjust volume in Performance UI
4. Test with built-in sounds

**High Latency:**
1. Close other Bluetooth devices
2. Ensure devices are within 10m range
3. Update firmware to latest version
4. Use wired connection for critical timing

**Motion Control Unresponsive:**
1. Recalibrate motion sensors
2. Check for magnetic interference
3. Clean sensor surfaces
4. Verify mounting stability

### Support Resources
- [Community Forum](https://forum.rezonate.dev)
- [Discord Server](https://discord.gg/rezonate)
- [GitHub Issues](https://github.com/waveformer1984/ballsDeepnit/issues)
- [Email Support](mailto:support@rezonate.dev)

## Contributing

### Documentation Guidelines
- Use clear, concise language
- Include code examples for APIs
- Add screenshots for UI features
- Keep setup instructions up-to-date
- Test all procedures before publishing

### Content Structure
```
docs/
├── README.md (this file)
├── setup/
│   ├── hardware-setup.md
│   ├── software-installation.md
│   └── calibration.md
├── api/
│   ├── rest-api.md
│   ├── websocket-api.md
│   └── midi-protocol.md
├── guides/
│   ├── getting-started.md
│   ├── advanced-techniques.md
│   └── daw-integration.md
└── troubleshooting/
    ├── common-issues.md
    ├── hardware-problems.md
    └── software-problems.md
```

### Auto-Generation
Documentation is automatically updated when:
- Code comments change (API docs)
- README files are modified
- New features are merged
- Version releases are tagged

---
*REZONATE Documentation - Complete System Guide*

**Lead System**: Hydi  
**Design Protocol**: UDP:ACTIVE  
**Project Codename**: Rezonate