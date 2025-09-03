# Z-areo Non-Profit OBD2 Data Collection System Setup Guide

![Z-areo Logo](https://img.shields.io/badge/Z--areo-Non--Profit-blue) ![OBD2](https://img.shields.io/badge/OBD2-Data%20Collection-green) ![License](https://img.shields.io/badge/License-Research%20Only-orange)

## Overview

The Z-areo OBD2 Data Collection System is a comprehensive solution for non-profit vehicle diagnostics research. It combines advanced OBD2 scanning, virtual CAN bus monitoring, mobile integration, and strict privacy compliance features.

### Key Features

- ✅ **ELM327 & Bidirectional Scanner Support**
- ✅ **Virtual CAN Bus Sniffer with Protocol Analysis**
- ✅ **Real-time Mobile App Integration**
- ✅ **Research-grade Data Storage & Export**
- ✅ **Privacy & Compliance Management**
- ✅ **Multi-protocol Support (OBD2, UDS, J1939)**

---

## Prerequisites

### Hardware Requirements

1. **OBD2 Adapter**
   - ELM327 USB/Bluetooth adapter
   - STN1110 chipset (recommended for advanced features)
   - Or compatible bidirectional scanner

2. **Computing Platform**
   - Linux-based system (Ubuntu 20.04+ recommended)
   - Raspberry Pi 4+ for mobile deployments
   - 4GB+ RAM, 32GB+ storage

3. **Mobile Device**
   - Android or iOS device
   - React Native compatible (for app development)

### Software Requirements

- Python 3.10+
- Node.js 16+ (for mobile app)
- Git
- Virtual CAN interface support (`can-utils`)

---

## Installation

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv git can-utils

# Setup virtual CAN interface
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# Make virtual CAN persistent
echo 'vcan' | sudo tee -a /etc/modules
echo 'ip link add dev vcan0 type vcan && ip link set up vcan0' | sudo tee /etc/systemd/system/vcan-setup.service
```

### 2. Clone Repository

```bash
git clone https://github.com/zareo-nonprofit/obd2-data-collection.git
cd obd2-data-collection
```

### 3. Python Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import obd, can, structlog; print('Dependencies OK')"
```

### 4. Database Setup

```bash
# Initialize SQLite database (default)
python -c "
from src.ballsdeepnit.obd2.data_collector import Base, create_engine
engine = create_engine('sqlite:///zareo_vehicle_data.db')
Base.metadata.create_all(engine)
print('Database initialized')
"
```

### 5. Mobile App Setup (Optional)

```bash
cd mobile/hydi-mobile

# Install Node.js dependencies
npm install

# Install Expo CLI globally
npm install -g @expo/cli

# Start development server
expo start
```

---

## Configuration

### 1. OBD2 Adapter Configuration

Create `config/obd2_config.json`:

```json
{
  "adapter_type": "ELM327_SERIAL",
  "port": "/dev/ttyUSB0",
  "baudrate": 38400,
  "timeout": 30.0,
  "auto_connect": true,
  "fast_mode": true,
  "protocol": null
}
```

**Adapter Types:**
- `ELM327_SERIAL` - USB serial connection
- `ELM327_BLUETOOTH` - Bluetooth connection
- `ELM327_WIFI` - WiFi connection
- `STN1110` - Advanced STN1110 chipset
- `VIRTUAL` - Testing/simulation mode

### 2. System Configuration

Create `config/system_config.json`:

```json
{
  "organization_name": "Z-areo Non-Profit",
  "data_controller": "Z-areo Data Protection Officer",
  "enable_can_sniffer": true,
  "enable_mobile_bridge": true,
  "enable_compliance": true,
  "mobile_port": 8765,
  "database_url": "sqlite:///zareo_vehicle_data.db",
  "log_level": "INFO"
}
```

### 3. Privacy & Compliance Settings

```json
{
  "data_retention_days": 2555,
  "anonymization_after_days": 365,
  "auto_anonymization": true,
  "consent_required": true,
  "audit_logging": true,
  "research_purposes_only": true
}
```

---

## Quick Start

### 1. Basic OBD2 Scanning

```python
import asyncio
from src.ballsdeepnit.obd2.zareo_system import create_zareo_system

async def basic_scan():
    # Create system with your adapter
    system = create_zareo_system(
        adapter_type="ELM327_SERIAL",
        port="/dev/ttyUSB0",
        enable_can_sniffer=True,
        enable_mobile_bridge=True,
        enable_compliance=True
    )
    
    # Initialize and start
    if await system.initialize():
        if await system.start():
            print("✅ Z-areo system started successfully")
            
            # Start data collection session
            session_id = await system.start_data_collection_session(
                session_name="my_first_scan",
                participant_id="participant_001"
            )
            
            # Perform diagnostic scan
            diagnostic = await system.perform_vehicle_diagnostic()
            print(f"Found {len(diagnostic['diagnostic_codes'])} diagnostic codes")
            
            # Stop session and export data
            result = await system.stop_data_collection_session()
            if result['success']:
                export_path = await system.export_session_data(
                    session_id, 'json', anonymize=True
                )
                print(f"📁 Data exported to: {export_path}")
    
    await system.stop()

# Run the scan
asyncio.run(basic_scan())
```

### 2. Mobile App Connection

1. **Start the backend system:**
```bash
python examples/start_zareo_system.py
```

2. **Connect mobile app:**
   - Open the mobile app
   - Enter WebSocket URL: `ws://your-ip:8765`
   - Tap "Connect"
   - Start monitoring vehicle parameters

### 3. Virtual CAN Testing

```bash
# Generate test CAN messages
cangen vcan0 -v -n 100

# Monitor in separate terminal
candump vcan0

# Run Z-areo system with virtual interface
python examples/virtual_can_demo.py
```

---

## Advanced Usage

### 1. Bidirectional Scanner Operations

```python
from src.ballsdeepnit.obd2.scanner import BidirectionalScanner, ScannerMode

# Enable bidirectional mode
scanner.mode = ScannerMode.BIDIRECTIONAL

# Perform actuator test
result = await scanner.perform_actuator_test(
    'fuel_injector', 
    {'pulse_width': 1000}
)

# Read enhanced manufacturer parameters
enhanced_data = await scanner.read_enhanced_parameters()
```

### 2. Custom CAN Protocol Analysis

```python
from src.ballsdeepnit.obd2.can_sniffer import VirtualCANSniffer, CANFilter

# Setup custom CAN filters
sniffer = VirtualCANSniffer()
sniffer.add_filter(0x123, mask=0x7FF)  # Specific ID
sniffer.add_filter(0x700, mask=0x700)  # ID range

# Add custom protocol analyzer
async def custom_analyzer(can_msg):
    if can_msg.arbitration_id == 0x123:
        # Custom decoding logic
        decoded = decode_custom_protocol(can_msg.data)
        can_msg.decoded_data = decoded

sniffer.add_message_callback(custom_analyzer)
```

### 3. Data Export & Analysis

```python
# Export to different formats
csv_path = await data_collector.export_session_data(session_id, 'csv')
json_path = await data_collector.export_session_data(session_id, 'json')
excel_path = await data_collector.export_session_data(session_id, 'excel')

# Anonymize data
from src.ballsdeepnit.obd2.compliance import ComplianceManager

compliance = ComplianceManager()
anonymized_data = compliance.anonymize_data(raw_data, preserve_utility=True)
```

---

## API Reference

### Core Classes

#### `ZareoOBD2System`
Main integration class that orchestrates all components.

```python
system = ZareoOBD2System(config)
await system.initialize()
await system.start()
session_id = await system.start_data_collection_session()
diagnostic = await system.perform_vehicle_diagnostic()
await system.stop()
```

#### `OBD2Manager`
Manages OBD2 adapter communication and monitoring.

```python
manager = OBD2Manager(config)
await manager.connect()
await manager.start_monitoring(['RPM', 'SPEED'])
data = await manager.query_parameter('COOLANT_TEMP')
```

#### `VirtualCANSniffer`
Advanced CAN bus monitoring with protocol analysis.

```python
sniffer = VirtualCANSniffer()
await sniffer.start()
stats = sniffer.get_statistics()
recent_messages = sniffer.get_recent_messages(100)
```

### REST API Endpoints

Base URL: `http://localhost:8765/api`

- `GET /status` - System status
- `GET /parameters` - Available OBD2 parameters
- `POST /command` - Execute OBD2 command
- `GET /data/{parameter}` - Get parameter value

### WebSocket API

Connect to: `ws://localhost:8765`

**Message Types:**
- `subscribe` - Subscribe to parameter updates
- `command` - Execute system command
- `heartbeat` - Keep-alive message

---

## Privacy & Compliance

### Data Collection Consent

```python
# Register participant consent
consent_id = await compliance_manager.register_consent(
    participant_id="participant_001",
    purposes=[ProcessingPurpose.RESEARCH, ProcessingPurpose.SAFETY_ANALYSIS],
    data_types=['vehicle_data', 'diagnostic_codes'],
    retention_days=2555  # 7 years
)

# Withdraw consent
await compliance_manager.withdraw_consent(consent_id, participant_id)
```

### Data Anonymization

```python
# Anonymize while preserving research utility
anonymized = compliance_manager.anonymize_data(
    vehicle_data, 
    preserve_utility=True
)

# Generate privacy report
report = compliance_manager.generate_privacy_report(session_id)
```

### Audit Logging

All system activities are automatically logged for compliance:

- User consent registration/withdrawal
- Data collection start/stop
- Data access and export
- System configuration changes

---

## Troubleshooting

### Common Issues

1. **OBD2 Adapter Not Found**
   ```bash
   # Check USB devices
   lsusb
   
   # Check serial ports
   ls /dev/ttyUSB*
   
   # Check permissions
   sudo usermod -a -G dialout $USER
   ```

2. **Virtual CAN Interface Issues**
   ```bash
   # Reload CAN modules
   sudo modprobe -r vcan
   sudo modprobe vcan
   
   # Recreate interface
   sudo ip link delete vcan0
   sudo ip link add dev vcan0 type vcan
   sudo ip link set up vcan0
   ```

3. **Mobile App Connection Failed**
   - Check firewall settings
   - Verify IP address and port
   - Ensure WebSocket server is running

4. **Database Connection Error**
   ```bash
   # Check database file permissions
   ls -la zareo_vehicle_data.db
   
   # Reset database
   rm zareo_vehicle_data.db
   python scripts/init_database.py
   ```

### Debug Mode

Enable detailed logging:

```python
import structlog
structlog.configure(level="DEBUG")

# Or set environment variable
export LOG_LEVEL=DEBUG
```

### Performance Optimization

1. **High-frequency data collection:**
   - Increase buffer sizes
   - Reduce monitoring interval
   - Use faster storage (SSD)

2. **CAN message processing:**
   - Add specific message filters
   - Limit buffer size
   - Use separate threads for analysis

---

## Contributing

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/

# Code formatting
black src/
ruff check src/
```

### Research Ethics

This system is designed for **non-profit research only**. All contributions must:

- Respect participant privacy
- Follow research ethics guidelines
- Maintain data security standards
- Support open science principles

---

## Support

### Documentation
- 📚 [API Documentation](docs/api.md)
- 🔧 [Hardware Compatibility](docs/hardware.md)
- 📱 [Mobile App Guide](docs/mobile.md)
- 🔒 [Privacy Policy](docs/privacy.md)

### Community
- 💬 [Discussion Forum](https://github.com/zareo-nonprofit/discussions)
- 🐛 [Bug Reports](https://github.com/zareo-nonprofit/issues)
- 📧 Email: support@zareo-nonprofit.org

### Citation

If you use this system in research, please cite:

```bibtex
@software{zareo_obd2_2024,
  title={Z-areo Non-Profit OBD2 Data Collection System},
  author={Z-areo Non-Profit Research Team},
  year={2024},
  url={https://github.com/zareo-nonprofit/obd2-data-collection},
  note={Research-grade vehicle diagnostics platform}
}
```

---

## License

This software is licensed for **non-profit research use only**. Commercial use requires explicit permission.

```
Copyright (c) 2024 Z-areo Non-Profit
Licensed under Research-Only License
```

---

**⚠️ Important:** This system is designed for research purposes. Always ensure proper consent and compliance with local regulations when collecting vehicle data.