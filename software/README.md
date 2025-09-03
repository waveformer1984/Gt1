# Software - REZONATE

## Overview
Performance UI, Bluetooth orchestration, and MIDI mapping software for cross-platform deployment.

## Components

### 📱 Performance UI (`/performance-ui/`)
- **Multi-Platform Support**: Phone apps, car stereo screens, tablets
- **Real-time Visualization**: Live performance metrics and waveforms
- **Touch Controls**: Intuitive gesture-based interface
- **Preset Management**: Save/load performance configurations
- **Live Mixing**: Real-time audio parameter control

**Supported Platforms:**
- iOS (Swift UI)
- Android (Kotlin/Compose)
- Car Audio Systems (Android Auto/CarPlay)
- Web Browser (Progressive Web App)

### 🔗 Bluetooth Orchestration (`/bluetooth-orchestration/`)
- **Device Discovery**: Automatic detection of REZONATE components
- **Pairing Management**: Secure multi-device connection handling
- **Network Topology**: Dynamic mesh network for drone coordination
- **Latency Optimization**: Bluetooth LE audio with minimal delay
- **Failover Systems**: Automatic reconnection and error recovery

### 🎵 MIDI Mapping (`/midi-mapping/`)
- **Custom Mapping Engine**: Flexible input-to-parameter assignment
- **DAW Integration**: Ableton Live, Logic Pro, Reaper compatibility
- **VST Support**: Direct plugin parameter control
- **Macro Systems**: Complex mapping relationships
- **Template Library**: Pre-built mapping configurations

## Technology Stack

### Frontend (Performance UI)
```
React Native / Flutter
- Cross-platform mobile development
- Native performance on iOS/Android
- Web deployment capability
- Bluetooth API integration
```

### Backend (Orchestration)
```
Node.js / Python FastAPI
- WebSocket real-time communication
- Bluetooth Low Energy libraries
- MIDI protocol handling
- SQLite for local data storage
```

### MIDI Engine
```
Python + RTMidi
- Cross-platform MIDI I/O
- Real-time parameter mapping
- OSC protocol support
- Plugin integration APIs
```

## Development Setup

### Prerequisites
```bash
# Install Node.js and Python
node --version  # v18+
python --version  # 3.10+

# Install mobile development tools
# iOS: Xcode Command Line Tools
# Android: Android Studio + SDK
```

### Quick Start
```bash
# Performance UI
cd software/performance-ui/
npm install
npm run dev

# Bluetooth Orchestration
cd software/bluetooth-orchestration/
pip install -r requirements.txt
python app.py

# MIDI Mapping
cd software/midi-mapping/
pip install -r requirements.txt
python mapping_engine.py
```

## Features

### Real-time Performance Dashboard
- Live audio waveforms and spectrum analysis
- Device status monitoring (battery, connection quality)
- Performance metrics (latency, packet loss)
- Touch-responsive controls with haptic feedback

### Advanced MIDI Mapping
- **Gesture-to-Parameter**: Motion input → DAW controls
- **Voice Control**: "Increase reverb" → parameter adjustment
- **Context Awareness**: Different mappings per song/project
- **Learning Mode**: AI-assisted mapping suggestions

### Bluetooth Network Management
- **Auto-Discovery**: Find all REZONATE devices in range
- **Priority Routing**: Critical audio data first
- **Mesh Resilience**: Alternative paths when devices disconnect
- **Bandwidth Optimization**: Adaptive quality based on connection

## Integration Points

### With Hardware
- Real-time sensor data visualization
- Firmware update delivery
- Configuration synchronization
- Health monitoring

### With Hydi AI
- Voice command processing
- Intelligent mapping suggestions
- Performance analysis and feedback
- Automated optimization

### With External DAWs
- Plugin parameter automation
- Transport control synchronization
- Project-specific mapping profiles
- Session recording integration

## Testing Strategy
```bash
# Unit tests
npm test  # UI components
pytest  # Python backend

# Integration tests
npm run test:integration
python -m pytest tests/integration/

# End-to-end testing
npm run test:e2e
```

## Contributing
- Follow React/React Native best practices for UI
- Use TypeScript for type safety
- Include automated tests for all features
- Document API endpoints and data structures
- Test on real devices before submission

---
*REZONATE Software - Cross-Platform Performance Interface*