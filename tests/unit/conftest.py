"""Unit test configuration with minimal, fast fixtures (no file I/O)."""

import pytest


@pytest.fixture
def sample_piface_dict():
    """Sample pipeline interface dictionary for unit tests."""
    return {
        "pipeline_name": "test_pipeline",
        "pipeline_type": "sample",
        "command_template": "python pipeline.py {sample.sample_name}",
    }


@pytest.fixture
def sample_piface_with_output_schema():
    """Pipeline interface dict with output_schema for pipestat tests."""
    return {
        "pipeline_name": "test_pipeline",
        "pipeline_type": "sample",
        "output_schema": "schema.yaml",
        "command_template": "python pipeline.py --pipestat-config {pipestat.config_file}",
    }
