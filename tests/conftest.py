"""Root test configuration.

Test organization:
- tests/unit/ - Fast unit tests with no file I/O
- tests/integration/ - CLI integration tests (set RUN_INTEGRATION_TESTS=true to run)
- tests/divvytests/ - Divvy compute configuration tests

Run commands:
- pytest tests/unit tests/divvytests  # Fast tests (default)
- RUN_INTEGRATION_TESTS=true pytest tests/integration  # Integration tests
- ./tests/scripts/test-integration.sh  # Integration tests via script
"""



# Register custom markers
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (skipped by default)"
    )
