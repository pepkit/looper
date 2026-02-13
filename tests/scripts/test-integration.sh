#!/bin/bash
# Integration Test Runner for Looper
# Runs full CLI integration tests that require temp directories and file I/O

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
cd "$PROJECT_ROOT"

export RUN_INTEGRATION_TESTS=true

echo "=== Running Looper Integration Tests ==="
python3 -m pytest tests/integration/ -v "$@"

echo "=== Integration tests completed successfully! ==="
