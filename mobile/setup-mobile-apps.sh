#!/bin/bash

# Mobile Apps Setup Script for ballsDeepnit and Z-AREO
# This script sets up both mobile applications with Hydi integration

set -e

echo "🚀 Setting up ballsDeepnit and Z-AREO Mobile Applications"
echo "======================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
check_nodejs() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 16+ first."
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        print_error "Node.js version 16+ is required. Current version: $(node --version)"
        exit 1
    fi
    
    print_success "Node.js $(node --version) detected"
}

# Check if React Native CLI is installed
check_react_native() {
    if ! command -v npx react-native &> /dev/null; then
        print_warning "React Native CLI not found. Installing..."
        npm install -g @react-native-community/cli
    fi
    print_success "React Native CLI is available"
}

# Check if Java and Android SDK are set up (for Android development)
check_android_setup() {
    if [ -z "$ANDROID_HOME" ]; then
        print_warning "ANDROID_HOME environment variable not set"
        print_warning "Android development will not be available without proper Android SDK setup"
    else
        print_success "Android SDK detected at $ANDROID_HOME"
    fi
}

# Setup ballsDeepnit mobile app
setup_ballsdeepnit_mobile() {
    print_status "Setting up ballsDeepnit Mobile App..."
    
    cd mobile/ballsdeepnit-mobile
    
    # Install dependencies
    print_status "Installing ballsDeepnit mobile dependencies..."
    npm install
    
    # Create necessary directories
    mkdir -p src/screens src/components src/services src/context src/theme src/utils src/types
    mkdir -p android/app/src/main/assets
    mkdir -p ios/BallsDeepnitMobile/Supporting\ Files
    mkdir -p scripts
    
    # Create metro.config.js
    cat > metro.config.js << 'EOF'
const {getDefaultConfig, mergeConfig} = require('@react-native/metro-config');

const defaultConfig = getDefaultConfig(__dirname);

const config = {
  resolver: {
    alias: {
      crypto: 'react-native-crypto-js',
      stream: 'stream-browserify',
      util: 'util',
    },
  },
  transformer: {
    getTransformOptions: async () => ({
      transform: {
        experimentalImportSupport: false,
        inlineRequires: true,
      },
    }),
  },
};

module.exports = mergeConfig(defaultConfig, config);
EOF

    # Create index.js
    cat > index.js << 'EOF'
import {AppRegistry} from 'react-native';
import App from './App';
import {name as appName} from './app.json';

AppRegistry.registerComponent(appName, () => App);
EOF

    # Create app.json
    cat > app.json << 'EOF'
{
  "name": "BallsDeepnitMobile",
  "displayName": "ballsDeepnit Mobile",
  "description": "Advanced Web Services & Automation with Hydi Integration"
}
EOF

    print_success "ballsDeepnit Mobile app structure created"
    cd ../..
}

# Setup Z-AREO mobile app
setup_zareo_mobile() {
    print_status "Setting up Z-AREO Mobile App..."
    
    cd mobile/zareo-mobile
    
    # Install dependencies
    print_status "Installing Z-AREO mobile dependencies..."
    npm install
    
    # Create necessary directories
    mkdir -p src/screens src/components src/services src/context src/theme src/utils src/types
    mkdir -p android/app/src/main/assets
    mkdir -p ios/ZareoMobile/Supporting\ Files
    mkdir -p scripts
    
    # Create metro.config.js
    cat > metro.config.js << 'EOF'
const {getDefaultConfig, mergeConfig} = require('@react-native/metro-config');

const defaultConfig = getDefaultConfig(__dirname);

const config = {
  resolver: {
    alias: {
      crypto: 'react-native-crypto-js',
      stream: 'stream-browserify',
      buffer: 'buffer',
      util: 'util',
    },
  },
  transformer: {
    getTransformOptions: async () => ({
      transform: {
        experimentalImportSupport: false,
        inlineRequires: true,
      },
    }),
  },
};

module.exports = mergeConfig(defaultConfig, config);
EOF

    # Create index.js
    cat > index.js << 'EOF'
import {AppRegistry} from 'react-native';
import App from './App';
import {name as appName} from './app.json';

AppRegistry.registerComponent(appName, () => App);
EOF

    # Create app.json
    cat > app.json << 'EOF'
{
  "name": "ZareoMobile",
  "displayName": "Z-AREO Mobile Research",
  "description": "Non-Profit OBD2 Data Collection with Hydi Integration"
}
EOF

    print_success "Z-AREO Mobile app structure created"
    cd ../..
}

# Update existing Hydi mobile app
update_hydi_mobile() {
    print_status "Updating existing Hydi Mobile App with web services integration..."
    
    cd mobile/hydi-mobile
    
    # Install additional dependencies for web services integration
    npm install socket.io-client axios uuid crypto-js lodash
    
    print_success "Hydi Mobile app updated with web services support"
    cd ../..
}

# Create shared mobile utilities
create_shared_utilities() {
    print_status "Creating shared mobile utilities..."
    
    mkdir -p mobile/shared/utils mobile/shared/types mobile/shared/services
    
    # Create shared Hydi bridge utility
    cat > mobile/shared/services/HydiBridge.ts << 'EOF'
import {EventEmitter} from 'events';

export interface HydiBridgeConfig {
  serverUrl: string;
  apiKey: string;
  enableAutoReconnect: boolean;
}

export class HydiBridge extends EventEmitter {
  private static instance: HydiBridge;
  private config: HydiBridgeConfig;
  private isConnected: boolean = false;

  private constructor() {
    super();
    this.config = {
      serverUrl: 'ws://localhost:8765',
      apiKey: 'hydi-mobile-bridge-2024',
      enableAutoReconnect: true,
    };
  }

  public static getInstance(): HydiBridge {
    if (!HydiBridge.instance) {
      HydiBridge.instance = new HydiBridge();
    }
    return HydiBridge.instance;
  }

  public async connect(): Promise<boolean> {
    try {
      // Connection logic here
      this.isConnected = true;
      this.emit('connected');
      return true;
    } catch (error) {
      this.emit('error', error);
      return false;
    }
  }

  public isConnectedToBridge(): boolean {
    return this.isConnected;
  }
}
EOF

    print_success "Shared mobile utilities created"
}

# Create build scripts
create_build_scripts() {
    print_status "Creating build and deployment scripts..."
    
    # Create build script for ballsDeepnit mobile
    cat > mobile/ballsdeepnit-mobile/scripts/build-release.sh << 'EOF'
#!/bin/bash

echo "Building ballsDeepnit Mobile Release..."

# Android build
if [ "$1" == "android" ] || [ "$1" == "both" ]; then
    echo "Building Android APK..."
    cd android
    ./gradlew assembleRelease
    echo "Android APK built: android/app/build/outputs/apk/release/app-release.apk"
    cd ..
fi

# iOS build (requires macOS and Xcode)
if [ "$1" == "ios" ] || [ "$1" == "both" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Building iOS Archive..."
        cd ios
        xcodebuild -workspace BallsDeepnitMobile.xcworkspace -scheme BallsDeepnitMobile -configuration Release archive
        echo "iOS archive created"
        cd ..
    else
        echo "iOS build requires macOS and Xcode"
    fi
fi
EOF

    # Create build script for Z-AREO mobile
    cat > mobile/zareo-mobile/scripts/build-release.sh << 'EOF'
#!/bin/bash

echo "Building Z-AREO Mobile Release..."

# Android build
if [ "$1" == "android" ] || [ "$1" == "both" ]; then
    echo "Building Android APK..."
    cd android
    ./gradlew assembleRelease
    echo "Android APK built: android/app/build/outputs/apk/release/app-release.apk"
    cd ..
fi

# iOS build (requires macOS and Xcode)
if [ "$1" == "ios" ] || [ "$1" == "both" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Building iOS Archive..."
        cd ios
        xcodebuild -workspace ZareoMobile.xcworkspace -scheme ZareoMobile -configuration Release archive
        echo "iOS archive created"
        cd ..
    else
        echo "iOS build requires macOS and Xcode"
    fi
fi
EOF

    # Make scripts executable
    chmod +x mobile/ballsdeepnit-mobile/scripts/build-release.sh
    chmod +x mobile/zareo-mobile/scripts/build-release.sh
    
    print_success "Build scripts created"
}

# Create development runner script
create_dev_runner() {
    cat > mobile/run-dev.sh << 'EOF'
#!/bin/bash

echo "🚀 Mobile Development Runner"
echo "==========================="

select app in "ballsDeepnit Mobile" "Z-AREO Mobile" "Hydi Mobile" "All Apps"; do
    case $app in
        "ballsDeepnit Mobile")
            echo "Starting ballsDeepnit Mobile development server..."
            cd ballsdeepnit-mobile && npm start
            break
            ;;
        "Z-AREO Mobile")
            echo "Starting Z-AREO Mobile development server..."
            cd zareo-mobile && npm start
            break
            ;;
        "Hydi Mobile")
            echo "Starting Hydi Mobile development server..."
            cd hydi-mobile && npm start
            break
            ;;
        "All Apps")
            echo "Starting all mobile development servers..."
            # This would require a process manager like PM2
            echo "Please start each app individually for now"
            break
            ;;
        *)
            echo "Invalid selection"
            ;;
    esac
done
EOF

    chmod +x mobile/run-dev.sh
    print_success "Development runner script created"
}

# Create README for mobile apps
create_mobile_readme() {
    cat > mobile/README.md << 'EOF'
# Mobile Applications Suite

This directory contains three React Native mobile applications with Hydi integration:

## Applications

### 1. ballsDeepnit Mobile (`ballsdeepnit-mobile/`)
- **Purpose**: Mobile interface for ballsDeepnit web services
- **Features**: 
  - Plugin management
  - Bot control and monitoring
  - Web services dashboard
  - Hydi AI integration
  - Real-time notifications

### 2. Z-AREO Mobile (`zareo-mobile/`)
- **Purpose**: Non-profit OBD2 research data collection
- **Features**:
  - Bluetooth OBD2 adapter connection
  - Real-time vehicle diagnostics
  - Research data collection
  - Privacy compliance
  - Hydi AI assistance

### 3. Hydi Mobile (`hydi-mobile/`)
- **Purpose**: Enhanced AI REPL and automation framework
- **Features**:
  - Voice-controlled commands
  - Advanced REPL interface
  - Module management
  - Web services integration

## Quick Start

1. **Setup all apps:**
   ```bash
   ./setup-mobile-apps.sh
   ```

2. **Run development server:**
   ```bash
   ./run-dev.sh
   ```

3. **Build releases:**
   ```bash
   cd <app-directory>
   ./scripts/build-release.sh android
   ```

## Development Requirements

- Node.js 16+
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development, macOS only)
- Hydi server running on localhost:8765

## Architecture

All apps share:
- Common Hydi integration layer
- Shared utilities and types
- Consistent UI/UX patterns
- Real-time WebSocket communication
- Local data storage with encryption

## Configuration

Each app can be configured through:
- AsyncStorage settings
- Environment variables
- Configuration files in `src/config/`

## Contributing

1. Follow React Native best practices
2. Use TypeScript for type safety
3. Maintain consistent code style
4. Test on both platforms when possible
5. Update documentation for new features

EOF

    print_success "Mobile README created"
}

# Main setup function
main() {
    print_status "Starting mobile applications setup..."
    
    # Pre-flight checks
    check_nodejs
    check_react_native
    check_android_setup
    
    # Create mobile directory if it doesn't exist
    mkdir -p mobile
    
    # Setup each app
    setup_ballsdeepnit_mobile
    setup_zareo_mobile
    update_hydi_mobile
    
    # Create shared utilities
    create_shared_utilities
    
    # Create build and development scripts
    create_build_scripts
    create_dev_runner
    
    # Create documentation
    create_mobile_readme
    
    print_success "Mobile applications setup completed!"
    
    echo
    echo "📱 Next Steps:"
    echo "=============="
    echo "1. Choose which app to develop:"
    echo "   - ballsDeepnit Mobile: cd mobile/ballsdeepnit-mobile && npm start"
    echo "   - Z-AREO Mobile: cd mobile/zareo-mobile && npm start"  
    echo "   - Hydi Mobile: cd mobile/hydi-mobile && npm start"
    echo
    echo "2. Start the Hydi server: python src/hydi_gui/hydi_server.py"
    echo
    echo "3. For Android development:"
    echo "   - Ensure Android emulator is running or device is connected"
    echo "   - Run: npx react-native run-android"
    echo
    echo "4. For iOS development (macOS only):"
    echo "   - Run: npx react-native run-ios"
    echo
    echo "5. Build releases using: ./scripts/build-release.sh [android|ios|both]"
    echo
    print_success "Setup complete! Happy coding! 🚀"
}

# Run main function
main "$@"