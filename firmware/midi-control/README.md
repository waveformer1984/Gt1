# MIDI Control Firmware

## Overview
Real-time MIDI generation and control firmware for ESP32-S3.

## Features
- Touch-to-MIDI conversion (<5ms latency)
- Multi-channel MIDI output
- Velocity sensitivity
- USB MIDI and Bluetooth LE support

## Architecture
```
Touch Input → Sensor Processing → MIDI Generation → Output
```

## Implementation Status
- [ ] Touch sensor driver
- [ ] MIDI protocol stack  
- [ ] Bluetooth LE implementation
- [ ] USB MIDI implementation
- [ ] Velocity calculation algorithms

Ready for PlatformIO development.