# Z-areo OBD2 System Testing Guide

This guide explains how to set up your admin profile, test OBD2 bidirectional data gathering, integrate with Proto Yi, and verify the web services dashboard.

## 🚀 Quick Start

### 1. Run Complete Test Suite

Execute the comprehensive test suite that includes all components:

```bash
python run_complete_test.py
```

This will run:
- ✅ Admin profile setup and authentication
- ✅ OBD2 bidirectional data gathering tests
- ✅ Proto Yi integration testing
- ✅ Web dashboard verification
- ✅ Real-time monitoring validation

### 2. Start the Web Dashboard

```bash
python start_dashboard.py
```

The dashboard will be available at:
- **Main Interface**: http://localhost:8765
- **API Documentation**: http://localhost:8765/docs
- **Authentication**: http://localhost:8765/api/auth/login
- **OBD2 API**: http://localhost:8765/api/obd2/status

## 🔧 Individual Test Components

### Admin Profile Setup & Authentication

```bash
python setup_admin_and_test_obd2.py
```

This script:
- Creates an admin user with full OBD2 permissions
- Sets up authentication and session management
- Tests the OBD2 system initialization
- Verifies bidirectional scanner capabilities
- Generates a comprehensive test report

**Default Admin Credentials** (created during testing):
- Username: `zareo_admin`
- Password: `ZareoAdmin2024!`
- Email: `admin@zareo-test.local`

### Proto Yi Integration Testing

```bash
python proto_yi_integration.py
```

This script:
- Simulates a realistic vehicle (Proto Yi Test Vehicle)
- Tests idle, acceleration, diagnostic, and stress scenarios
- Verifies bidirectional communication
- Provides OBD2 protocol testing

### OBD2 Bidirectional Features

The system includes comprehensive bidirectional capabilities:

**Read Operations:**
- Real-time parameter monitoring (RPM, Speed, Coolant Temp, etc.)
- Diagnostic code scanning
- Vehicle readiness tests
- Manufacturer-specific data

**Write Operations:**
- Actuator testing (throttle control, etc.)
- ECU programming capabilities
- Diagnostic code clearing
- System configuration

**Permissions:**
- `read_data`: Basic OBD2 data access
- `write_data`: Parameter modification
- `bidirectional_access`: Full bidirectional communication
- `ecu_programming`: ECU modification capabilities
- `system_configuration`: System settings management
- `user_management`: User and profile management
- `audit_access`: Security audit logs

## 🌐 Web Dashboard Features

### Authentication Endpoints

**Login**
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "zareo_admin",
  "password": "ZareoAdmin2024!"
}
```

**Get Current User**
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### OBD2 Endpoints

**System Status**
```http
GET /api/obd2/status
Authorization: Bearer <token>
```

**Start Data Collection Session**
```http
POST /api/obd2/start-session
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_name": "test_session",
  "adapter_type": "ELM327_SERIAL",
  "port": "/dev/ttyUSB0"
}
```

**Perform Vehicle Diagnostic**
```http
POST /api/obd2/diagnostic
Authorization: Bearer <token>
```

**Bidirectional Actuator Test** (Admin Only)
```http
POST /api/obd2/bidirectional/actuator-test
Authorization: Bearer <token>
Content-Type: application/json

{
  "actuator_name": "throttle",
  "parameters": {"position": 25}
}
```

**Real-time Data WebSocket**
```
ws://localhost:8765/api/obd2/ws/live-data
```

### Admin Management Endpoints

**Create User** (Admin Only)
```http
POST /api/auth/admin/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "new_user",
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "role": "technician"
}
```

**Grant Bidirectional Access** (Admin Only)
```http
POST /api/auth/admin/grant-bidirectional/{user_id}
Authorization: Bearer <token>
```

**Update OBD2 Permissions** (Admin Only)
```http
PUT /api/auth/admin/obd2-permissions/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "permissions": {
    "bidirectional_access": true,
    "ecu_programming": false
  }
}
```

## 📊 Real-time Monitoring

The system provides real-time monitoring through:

### WebSocket Streaming
- Live OBD2 parameter updates
- Real-time diagnostic information
- System status monitoring

### CAN Bus Sniffer
- Virtual CAN interface monitoring
- Protocol analysis
- Message filtering and decoding

### Mobile Bridge
- Mobile device integration
- Cross-platform data streaming
- Remote monitoring capabilities

## 🔐 Security Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control
- Session management with automatic cleanup
- Multi-device session support

### Admin Profile Management
- Granular OBD2 permissions
- System access control
- Security audit logging
- Emergency contact management

### Data Protection
- Automatic data anonymization
- Compliance management
- Privacy controls
- Secure session handling

## 📁 Test Reports

After running tests, check these files for detailed results:

- `complete_test_report.json` - Comprehensive test results
- `zareo_test_report.json` - Admin setup and OBD2 test results
- `proto_yi_test_report.json` - Proto Yi integration results

## 🎯 Expected Test Results

When everything is working correctly, you should see:

```
Z-AREO OBD2 TEST SUMMARY
========================
Admin User: zareo_admin (ID: <user_id>)
Admin Profile: Level 3
OBD2 System: Running

Test Results:
  Authentication: ✅ PASS
  Obd2 Setup: ✅ PASS
  Bidirectional Scanner: ✅ PASS
  Data Collection: ✅ PASS
  Can Sniffer: ✅ PASS
  Mobile Bridge: ✅ PASS

Bidirectional Access: ✅ ENABLED
Proto Yi Integration: ✅ READY
Web Dashboard: ✅ AVAILABLE
```

## 🔧 Troubleshooting

### Common Issues

**Database Connection Errors**
- Ensure SQLite permissions are correct
- Check disk space
- Verify Python async SQLite support

**OBD2 Adapter Issues**
- Use virtual adapter for testing: `AdapterType.VIRTUAL`
- Check USB permissions: `sudo usermod -a -G dialout $USER`
- Verify adapter is connected: `ls /dev/ttyUSB*`

**Permission Errors**
- Check admin profile creation
- Verify OBD2 permissions are granted
- Review security audit logs

**Dashboard Access Issues**
- Ensure port 8765 is available
- Check firewall settings
- Verify authentication tokens

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python run_complete_test.py
```

## 🚀 Next Steps

After successful testing:

1. **Hardware Integration**: Connect real OBD2 adapter
2. **Production Database**: Configure PostgreSQL or similar
3. **Production Deployment**: Set up proper web server
4. **User Training**: Create user documentation
5. **Monitoring Setup**: Configure production monitoring

## 📞 Support

For issues or questions:
- Check the test reports for detailed error information
- Review the API documentation at `/docs`
- Examine security audit logs for authentication issues
- Verify admin profile permissions

---

**🎉 Congratulations!** You now have a fully functional Z-areo OBD2 system with admin profile management, bidirectional data gathering, Proto Yi integration, and a comprehensive web services dashboard ready for real-world testing!