# 🧠 Hydi Mobile - Advanced AI REPL & Automation Framework

![Hydi Mobile](https://user-images.githubusercontent.com/placeholder.png)

*A powerful React Native mobile application for controlling and monitoring the Hydi AI automation framework*

---

## 🚀 Features

### Core Functionality
- **🧠 AI REPL Interface** - Full-featured mobile REPL with command history and auto-completion
- **🔧 Module Management** - Toggle and monitor core and experimental modules in real-time
- **🎤 Voice Control** - Voice commands for hands-free operation
- **📊 System Monitoring** - Real-time system status, CPU, memory, and connection monitoring
- **🔔 Push Notifications** - Smart notifications for system events and module status changes

### Advanced Features
- **🔐 Biometric Authentication** - Touch ID / Face ID / Fingerprint login support
- **📱 Offline Mode** - Cached data and offline command queuing
- **🌙 Dark Theme** - Neural-inspired dark theme optimized for mobile
- **🔄 Real-time Sync** - WebSocket connection for instant updates
- **📈 Performance Monitoring** - System metrics visualization
- **🧪 Experimental Modules** - Safe testing environment for experimental features

### Security
- **🛡️ Secure Authentication** - JWT tokens with refresh capability
- **🔒 Keychain Storage** - Secure credential storage using device keychain
- **🔐 End-to-End Encryption** - Encrypted communication with Hydi backend
- **📱 Device-Specific Security** - Per-device authentication and permissions

---

## 📱 Screenshots

*Coming soon - Screenshots of the app in action*

---

## 🛠️ Installation

### Prerequisites

- **Node.js** 16.0 or higher
- **React Native CLI** or **Expo CLI**
- **Android Studio** (for Android development)
- **Xcode** (for iOS development)
- **A running Hydi backend system**

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/ballsdeepnit/hydi-mobile.git
   cd hydi-mobile
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **iOS Setup** (iOS only)
   ```bash
   cd ios && pod install && cd ..
   ```

4. **Configure Hydi Backend URL**
   
   Create a `.env` file in the project root:
   ```env
   HYDI_BACKEND_URL=http://your-hydi-server:8000
   HYDI_WS_URL=ws://your-hydi-server:8000/ws
   ```

5. **Run the application**
   
   For Android:
   ```bash
   npm run android
   ```
   
   For iOS:
   ```bash
   npm run ios
   ```

---

## 🏗️ Development Setup

### Environment Configuration

The app requires a running Hydi backend system. You can either:

1. **Use an existing Hydi installation**
2. **Set up Hydi locally** following the main repository instructions
3. **Use Docker** for quick setup:
   ```bash
   docker run -p 8000:8000 ballsdeepnit/hydi:latest
   ```

### Development Commands

```bash
# Start Metro bundler
npm start

# Run on Android emulator/device
npm run android

# Run on iOS simulator/device
npm run ios

# Run tests
npm test

# Lint code
npm run lint

# Build for production
npm run build:android  # Android APK
npm run build:ios      # iOS archive
```

### Project Structure

```
mobile/hydi-mobile/
├── src/
│   ├── components/        # Reusable UI components
│   ├── screens/          # Main application screens
│   │   ├── HomeScreen.tsx
│   │   ├── REPLScreen.tsx
│   │   ├── ModulesScreen.tsx
│   │   ├── VoiceScreen.tsx
│   │   └── SettingsScreen.tsx
│   ├── services/         # Backend integration services
│   │   ├── HydiService.ts
│   │   ├── AuthService.ts
│   │   └── NotificationService.ts
│   ├── context/          # React Context providers
│   │   └── HydiContext.tsx
│   ├── theme/            # Design system and theming
│   │   └── HydiTheme.ts
│   └── utils/            # Utility functions
├── android/              # Android-specific code
├── ios/                  # iOS-specific code
├── App.tsx              # Main application component
└── package.json         # Dependencies and scripts
```

---

## 🎯 Core Screens

### 🏠 Home Screen
- System overview dashboard
- Quick action buttons
- Real-time connection status
- Recent activity feed
- System metrics visualization

### 🧠 REPL Screen
- Full-featured AI REPL interface
- Command history and auto-completion
- Syntax highlighting for different command types
- Real-time command execution
- Export session functionality

### 🔧 Modules Screen
- Complete module management interface
- Toggle core and experimental modules
- Real-time status monitoring
- Module logs and error reporting
- Search and filter capabilities

### 🎤 Voice Screen
- Voice command interface
- Real-time speech recognition
- Voice feedback and confirmation
- Command history and favorites
- Customizable voice triggers

### ⚙️ Settings Screen
- Authentication preferences
- Biometric security settings
- Notification configuration
- Theme and appearance options
- Connection settings

---

## 🔌 API Integration

The mobile app communicates with the Hydi backend through:

### REST API Endpoints
- `POST /api/auth/login` - User authentication
- `GET /api/system/status` - System status and metrics
- `GET /api/modules` - Module list and status
- `POST /api/modules/{id}/toggle` - Toggle module state
- `POST /api/repl/execute` - Execute REPL commands
- `POST /api/voice/process` - Process voice commands

### WebSocket Connection
- Real-time system updates
- Module status changes
- REPL command responses
- System notifications
- Connection status monitoring

### Authentication
- JWT-based authentication with refresh tokens
- Biometric authentication support
- Secure credential storage
- Per-device permissions

---

## 🔔 Notifications

The app supports comprehensive notification system:

### Local Notifications
- System connection status
- Module state changes
- REPL command results
- Voice command feedback
- Error and warning alerts

### Push Notifications (Future)
- Remote system alerts
- Scheduled task notifications
- Security alerts
- System maintenance notifications

---

## 🛡️ Security Features

### Authentication
- **Multi-factor Authentication** - Username/password + biometrics
- **Session Management** - Automatic token refresh and expiration
- **Device Binding** - Per-device authentication tokens
- **Secure Storage** - Keychain/Keystore credential storage

### Data Protection
- **End-to-End Encryption** - All communication encrypted
- **Certificate Pinning** - Prevent man-in-the-middle attacks
- **Data Sanitization** - Secure data cleanup on logout
- **Offline Security** - Encrypted local data storage

---

## 🎨 Design System

### Theme
- **Neural-inspired color palette** - Dark theme optimized for AI interfaces
- **Material Design 3** - Modern, accessible design language
- **Consistent spacing** - Systematic spacing scale
- **Typography hierarchy** - Clear information architecture

### Components
- **Modular design** - Reusable, composable components
- **Accessibility first** - Screen reader and keyboard navigation support
- **Animation system** - Smooth, purposeful animations
- **Responsive layout** - Works on phones and tablets

---

## 🧪 Experimental Features

### Voice AI Integration
- **Natural language processing** - Advanced voice command understanding
- **Voice synthesis** - System response through speech
- **Conversation mode** - Extended voice interactions
- **Voice training** - Personalized voice recognition

### Advanced Monitoring
- **Predictive analytics** - System performance predictions
- **Anomaly detection** - Automatic problem identification
- **Historical analysis** - Trend analysis and reporting
- **Custom dashboards** - Personalized monitoring views

---

## 📊 Performance Optimization

### App Performance
- **Lazy loading** - On-demand screen and component loading
- **State management optimization** - Efficient React Context usage
- **Memory management** - Proactive cleanup and optimization
- **Bundle optimization** - Minimized app size and startup time

### Network Optimization
- **Request batching** - Efficient API usage
- **Caching strategy** - Smart data caching
- **Offline support** - Graceful offline degradation
- **Connection pooling** - Efficient WebSocket management

---

## 🔍 Troubleshooting

### Common Issues

**Connection Problems**
```bash
# Check Hydi backend is running
curl http://localhost:8000/api/health

# Verify network connectivity
ping your-hydi-server

# Check app logs
npx react-native log-android  # Android
npx react-native log-ios      # iOS
```

**Build Issues**
```bash
# Clean and rebuild
cd android && ./gradlew clean && cd ..
npm run android

# iOS clean build
cd ios && xcodebuild clean && cd ..
npm run ios
```

**Module Loading Issues**
- Ensure all dependencies are installed: `npm install`
- Check React Native version compatibility
- Verify Android/iOS setup is complete

### Debug Mode

Enable debug logging by setting:
```env
DEBUG=true
LOG_LEVEL=debug
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards
- **TypeScript** - Strict type checking
- **ESLint** - Code quality and consistency
- **Prettier** - Code formatting
- **Jest** - Unit and integration testing

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **React Native** - Cross-platform mobile framework
- **React Native Paper** - Material Design components
- **Hydi Team** - Core AI automation framework
- **Open Source Community** - Dependencies and inspiration

---

## 📞 Support

- **Documentation**: [docs.hydi.ai](https://docs.hydi.ai)
- **Issues**: [GitHub Issues](https://github.com/ballsdeepnit/hydi-mobile/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ballsdeepnit/hydi-mobile/discussions)
- **Email**: support@hydi.ai

---

*Built with ❤️ by the ballsDeepnit team*