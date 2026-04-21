#!/bin/bash
# Run load tests with proper environment setup

set -euo pipefail

# Configuration
API_BASE_URL=${API_BASE_URL:-"http://localhost:8000"}
AUTH_TOKEN=${AUTH_TOKEN:-""}
TEST_TYPE=${TEST_TYPE:-"smoke"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "GraftAI Load Test Runner"
echo "========================================"
echo ""

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo -e "${RED}Error: k6 is not installed${NC}"
    echo "Please install k6: https://k6.io/docs/getting-started/installation"
    exit 1
fi

echo -e "${GREEN}✓ k6 found${NC}"

# Verify API is reachable
echo "Checking API health..."
if ! curl --fail --silent --show-error --max-time 10 "${API_BASE_URL}/health" > /dev/null; then
    echo -e "${RED}Error: API is not reachable at ${API_BASE_URL}${NC}"
    echo "Please start the API server or update API_BASE_URL"
    exit 1
fi

echo -e "${GREEN}✓ API is healthy${NC}"
echo ""

# Set test script based on type
case $TEST_TYPE in
    "api")
        TEST_SCRIPT="api-load-test.js"
        ;;
    "workflow")
        TEST_SCRIPT="workflow-load-test.js"
        ;;
    "smoke")
        TEST_SCRIPT="api-load-test.js"
        EXTRA_ARGS="--tag test_type=smoke"
        ;;
    *)
        echo -e "${RED}Error: Unknown test type: $TEST_TYPE${NC}"
        echo "Valid types: api, workflow, smoke"
        exit 1
        ;;
esac

echo "Test Configuration:"
echo "  Type: $TEST_TYPE"
echo "  Script: $TEST_SCRIPT"
echo "  API URL: $API_BASE_URL"
if [ -n "$AUTH_TOKEN" ]; then
    echo "  Auth Token: ${AUTH_TOKEN:0:4}..."
else
    echo "  Auth Token: <none>"
fi
 echo ""

# Run the test
echo "Starting load test..."
echo "========================================"

k6 run \
    --env API_BASE_URL="$API_BASE_URL" \
    --env AUTH_TOKEN="$AUTH_TOKEN" \
    $EXTRA_ARGS \
    "$TEST_SCRIPT"

TEST_EXIT_CODE=$?

echo ""
echo "========================================"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Load test completed successfully${NC}"
else
    echo -e "${RED}✗ Load test failed (exit code: $TEST_EXIT_CODE)${NC}"
fi

exit $TEST_EXIT_CODE
