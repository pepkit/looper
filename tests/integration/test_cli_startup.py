"""Tests for CLI startup performance."""

import subprocess
import time

import pytest

# These tests are fast and should run by default (not require RUN_INTEGRATION_TESTS)
pytestmark = pytest.mark.integration_fast


def test_cli_help_startup_time():
    """Ensure --help responds quickly without loading heavy dependencies."""
    start = time.time()
    result = subprocess.run(
        ["python", "-m", "looper.cli_pydantic", "--help"],
        capture_output=True,
        text=True,
    )
    elapsed = time.time() - start

    assert result.returncode == 0, f"--help failed: {result.stderr}"
    assert elapsed < 0.5, f"CLI --help took {elapsed:.2f}s, should be < 0.5s"


def test_subcommand_help_startup_time():
    """Ensure subcommand --help also responds quickly."""
    start = time.time()
    result = subprocess.run(
        ["python", "-m", "looper.cli_pydantic", "run", "--help"],
        capture_output=True,
        text=True,
    )
    elapsed = time.time() - start

    assert result.returncode == 0, f"run --help failed: {result.stderr}"
    assert elapsed < 0.5, f"CLI run --help took {elapsed:.2f}s, should be < 0.5s"
