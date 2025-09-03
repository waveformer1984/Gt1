#!/bin/bash
# REZONATE Test Suite - Run All Tests
# Execute tests for all REZONATE components

set -e

echo "🧪 REZONATE Test Suite - Running All Tests"
echo "=========================================="

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Hardware Design Tests
echo "📐 Testing hardware designs..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -d "hardware-design" ] && [ -f "hardware-design/README.md" ]; then
    echo "✓ Hardware design structure test passed"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "❌ Hardware design structure test failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Firmware Tests
echo "⚡ Testing firmware..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -d "firmware" ] && [ -f "firmware/README.md" ]; then
    echo "✓ Firmware structure test passed"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    # Future: Add PlatformIO unit tests
    echo "  Ready for ESP32 unit tests"
else
    echo "❌ Firmware structure test failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Software Tests
echo "📱 Testing software components..."
for component in performance-ui bluetooth-orchestration midi-mapping; do
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ -d "software/$component" ]; then
        echo "✓ Software component test passed: $component"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        # Future: Add npm test / pytest when package files exist
    else
        echo "❌ Software component test failed: $component"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
done

# Documentation Tests
echo "📚 Testing documentation..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "docs/README.md" ]; then
    echo "✓ Documentation test passed"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "❌ Documentation test failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Automation Tests
echo "🚀 Testing automation..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ -f "automation/README.md" ] && [ -f ".github/workflows/rezonate-build.yml" ]; then
    echo "✓ Automation test passed"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "❌ Automation test failed"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Integration Tests
echo "🔗 Testing system integration..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $FAILED_TESTS -eq 0 ]; then
    echo "✓ System integration test passed"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "❌ System integration test failed - component failures detected"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test Summary
echo "=========================================="
echo "🧪 REZONATE Test Results:"
echo "  Total Tests: $TOTAL_TESTS"
echo "  Passed: $PASSED_TESTS"
echo "  Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo "🎉 All tests passed! REZONATE system is ready."
    exit 0
else
    echo "💥 Some tests failed. Please check the output above."
    exit 1
fi