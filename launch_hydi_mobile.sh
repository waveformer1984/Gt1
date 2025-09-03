#!/bin/bash

# 🧠 Hydi Mobile - Launch Script
# Advanced AI REPL & Automation Framework Mobile App

set -e

echo "🧠 Starting Hydi Mobile setup and launch..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="mobile/hydi-mobile"
HYDI_BACKEND_URL="${HYDI_BACKEND_URL:-http://localhost:8000}"
PLATFORM="${1:-android}" # Default to android, can be 'ios' or 'android'

print_banner() {
    echo -e "${CYAN}"
    echo "  ██╗  ██╗██╗   ██╗██████╗ ██╗    ███╗   ███╗ ██████╗ ██████╗ ██╗██╗     ███████╗"
    echo "  ██║  ██║╚██╗ ██╔╝██╔══██╗██║    ████╗ ████║██╔═══██╗██╔══██╗██║██║     ██╔════╝"
    echo "  ███████║ ╚████╔╝ ██║  ██║██║    ██╔████╔██║██║   ██║██████╔╝██║██║     █████╗  "
    echo "  ██╔══██║  ╚██╔╝  ██║  ██║██║    ██║╚██╔╝██║██║   ██║██╔══██╗██║██║     ██╔══╝  "
    echo "  ██║  ██║   ██║   ██████╔╝██║    ██║ ╚═╝ ██║╚██████╔╝██████╔╝██║███████╗███████╗"
    echo "  ╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝    ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝╚══════╝╚══════╝"
    echo -e "${NC}"
    echo -e "${PURPLE}🚀 Advanced AI REPL & Automation Framework - Mobile App${NC}"
    echo -e "${BLUE}💜 Built by the ballsDeepnit team${NC}"
    echo ""
}

check_dependencies() {
    echo -e "${YELLOW}📋 Checking dependencies...${NC}"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed. Please install Node.js 16+ first.${NC}"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        echo -e "${RED}❌ Node.js version 16+ required. Current version: $(node --version)${NC}"
        exit 1
    fi
    
    # Check npm/yarn
    if ! command -v npm &> /dev/null && ! command -v yarn &> /dev/null; then
        echo -e "${RED}❌ npm or yarn is required.${NC}"
        exit 1
    fi
    
    # Check React Native CLI
    if ! command -v npx &> /dev/null; then
        echo -e "${RED}❌ npx is required (comes with npm 5.2+).${NC}"
        exit 1
    fi
    
    # Platform-specific checks
    if [ "$PLATFORM" = "android" ]; then
        if ! command -v java &> /dev/null; then
            echo -e "${YELLOW}⚠️  Java not found. Android development requires Java 11+.${NC}"
        fi
        
        if [ ! -d "$ANDROID_HOME" ] && [ ! -d "$ANDROID_SDK_ROOT" ]; then
            echo -e "${YELLOW}⚠️  Android SDK not found. Set ANDROID_HOME or ANDROID_SDK_ROOT.${NC}"
        fi
    elif [ "$PLATFORM" = "ios" ]; then
        if [ "$(uname)" != "Darwin" ]; then
            echo -e "${RED}❌ iOS development requires macOS.${NC}"
            exit 1
        fi
        
        if ! command -v xcodebuild &> /dev/null; then
            echo -e "${RED}❌ Xcode is required for iOS development.${NC}"
            exit 1
        fi
        
        if ! command -v pod &> /dev/null; then
            echo -e "${YELLOW}⚠️  CocoaPods not found. Installing...${NC}"
            sudo gem install cocoapods
        fi
    fi
    
    echo -e "${GREEN}✅ Dependencies check passed${NC}"
}

setup_project() {
    echo -e "${YELLOW}🏗️  Setting up Hydi Mobile project...${NC}"
    
    # Navigate to project directory
    if [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${RED}❌ Project directory not found: $PROJECT_DIR${NC}"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Install dependencies
    echo -e "${BLUE}📦 Installing dependencies...${NC}"
    if command -v yarn &> /dev/null; then
        yarn install
    else
        npm install
    fi
    
    # iOS-specific setup
    if [ "$PLATFORM" = "ios" ] && [ -d "ios" ]; then
        echo -e "${BLUE}🍎 Setting up iOS dependencies...${NC}"
        cd ios
        pod install --repo-update
        cd ..
    fi
    
    # Create environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        echo -e "${BLUE}⚙️  Creating environment configuration...${NC}"
        cat > .env << EOF
# Hydi Mobile Environment Configuration
HYDI_BACKEND_URL=${HYDI_BACKEND_URL}
HYDI_WS_URL=${HYDI_BACKEND_URL/http/ws}/ws
DEBUG=true
LOG_LEVEL=info
EOF
        echo -e "${GREEN}✅ Created .env file with default configuration${NC}"
    fi
    
    echo -e "${GREEN}✅ Project setup completed${NC}"
}

check_hydi_backend() {
    echo -e "${YELLOW}🔍 Checking Hydi backend connection...${NC}"
    
    # Try to reach the backend health endpoint
    if curl -f -s --max-time 5 "${HYDI_BACKEND_URL}/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Hydi backend is accessible at ${HYDI_BACKEND_URL}${NC}"
        
        # Get backend info if available
        BACKEND_INFO=$(curl -s --max-time 5 "${HYDI_BACKEND_URL}/api/health" 2>/dev/null || echo "{}")
        echo -e "${BLUE}ℹ️  Backend info: ${BACKEND_INFO}${NC}"
    else
        echo -e "${YELLOW}⚠️  Cannot reach Hydi backend at ${HYDI_BACKEND_URL}${NC}"
        echo -e "${YELLOW}   Make sure the Hydi backend is running and accessible.${NC}"
        echo -e "${YELLOW}   You can still run the mobile app, but it will be in offline mode.${NC}"
        
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ Aborted by user${NC}"
            exit 1
        fi
    fi
}

start_metro() {
    echo -e "${YELLOW}🚀 Starting Metro bundler...${NC}"
    
    # Start Metro bundler in background
    npx react-native start --reset-cache &
    METRO_PID=$!
    
    # Wait for Metro to start
    echo -e "${BLUE}⏳ Waiting for Metro to start...${NC}"
    sleep 10
    
    # Check if Metro is running
    if kill -0 $METRO_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Metro bundler started (PID: $METRO_PID)${NC}"
    else
        echo -e "${RED}❌ Failed to start Metro bundler${NC}"
        exit 1
    fi
}

run_app() {
    echo -e "${YELLOW}📱 Launching Hydi Mobile on ${PLATFORM}...${NC}"
    
    if [ "$PLATFORM" = "android" ]; then
        echo -e "${BLUE}🤖 Starting Android app...${NC}"
        npx react-native run-android --variant=debug
    elif [ "$PLATFORM" = "ios" ]; then
        echo -e "${BLUE}🍎 Starting iOS app...${NC}"
        npx react-native run-ios --configuration Debug
    else
        echo -e "${RED}❌ Unsupported platform: $PLATFORM${NC}"
        echo -e "${YELLOW}   Supported platforms: android, ios${NC}"
        exit 1
    fi
}

cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
    
    # Kill Metro bundler if it's running
    if [ ! -z "$METRO_PID" ] && kill -0 $METRO_PID 2>/dev/null; then
        echo -e "${BLUE}🛑 Stopping Metro bundler...${NC}"
        kill $METRO_PID
    fi
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

show_help() {
    echo -e "${CYAN}Hydi Mobile Launch Script${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [platform] [options]"
    echo ""
    echo -e "${YELLOW}Platforms:${NC}"
    echo "  android    Launch on Android (default)"
    echo "  ios        Launch on iOS (macOS only)"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --help, -h           Show this help message"
    echo "  --setup-only         Only setup the project, don't launch"
    echo "  --no-backend-check   Skip backend connectivity check"
    echo "  --clean              Clean build and restart"
    echo ""
    echo -e "${YELLOW}Environment Variables:${NC}"
    echo "  HYDI_BACKEND_URL     Hydi backend URL (default: http://localhost:8000)"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 android                    # Launch on Android"
    echo "  $0 ios                        # Launch on iOS"
    echo "  $0 android --setup-only       # Setup only, don't launch"
    echo "  HYDI_BACKEND_URL=http://192.168.1.100:8000 $0 android"
    echo ""
}

main() {
    # Parse arguments
    SETUP_ONLY=false
    NO_BACKEND_CHECK=false
    CLEAN_BUILD=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --setup-only)
                SETUP_ONLY=true
                shift
                ;;
            --no-backend-check)
                NO_BACKEND_CHECK=true
                shift
                ;;
            --clean)
                CLEAN_BUILD=true
                shift
                ;;
            android|ios)
                PLATFORM=$1
                shift
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Main execution flow
    print_banner
    check_dependencies
    
    # Clean build if requested
    if [ "$CLEAN_BUILD" = true ]; then
        echo -e "${YELLOW}🧹 Performing clean build...${NC}"
        cd "$PROJECT_DIR"
        
        if [ "$PLATFORM" = "android" ]; then
            cd android && ./gradlew clean && cd ..
        elif [ "$PLATFORM" = "ios" ]; then
            cd ios && xcodebuild clean && cd ..
        fi
        
        # Clean Metro cache
        npx react-native start --reset-cache --stop
        rm -rf node_modules/.cache
    fi
    
    setup_project
    
    # Check backend unless skipped
    if [ "$NO_BACKEND_CHECK" != true ]; then
        check_hydi_backend
    fi
    
    # Launch app unless setup-only
    if [ "$SETUP_ONLY" != true ]; then
        start_metro
        sleep 3
        run_app
        
        echo -e "\n${GREEN}🎉 Hydi Mobile launched successfully!${NC}"
        echo -e "${BLUE}📱 The app should now be running on your ${PLATFORM} device/emulator${NC}"
        echo -e "${YELLOW}💡 Press Ctrl+C to stop Metro bundler and exit${NC}"
        
        # Wait for user to stop
        wait $METRO_PID
    else
        echo -e "\n${GREEN}🎉 Hydi Mobile setup completed!${NC}"
        echo -e "${BLUE}📱 Run the app with: npx react-native run-${PLATFORM}${NC}"
    fi
}

# Run main function with all arguments
main "$@"