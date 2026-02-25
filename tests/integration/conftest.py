"""Integration test configuration with environment variable gating."""

import os
import shutil
import socket
from contextlib import contextmanager
from shutil import copyfile
from typing import Iterable

import peppy
import pytest
from yaml import dump, safe_load

from looper.const import LOOPER_DOTFILE_NAME, OUTDIR_KEY


# Skip all integration tests unless explicitly enabled
def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless RUN_INTEGRATION_TESTS=true."""
    if os.getenv("RUN_INTEGRATION_TESTS") == "true":
        return
    skip_marker = pytest.mark.skip(
        reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=true to run."
    )
    for item in items:
        # Only skip tests in the integration directory that aren't marked as fast
        if "integration" in str(item.fspath):
            if not any(mark.name == "integration_fast" for mark in item.iter_markers()):
                item.add_marker(skip_marker)


# File constants
CFG = "project_config.yaml"
PIPESTAT_CONFIG = "global_pipestat_config.yaml"
PROJECT_CFG_PIPESTAT = "project_config_pipestat.yaml"
LOOPER_CFG = "looper_config_pipestat.yaml"
PIPESTAT_OS = "pipestat_output_schema.yaml"
PIPESTAT_PI = "pipeline_interface1_sample_pipestat.yaml"
PIPESTAT_PI_PRJ = "pipeline_interface1_project_pipestat.yaml"
ST = "annotation_sheet.csv"
PIP = "pipeline_interface{}_project.yaml"
PIS = "pipeline_interface{}_sample.yaml"
OS = "output_schema.yaml"
RES = "resources-{}.tsv"


@pytest.fixture(scope="function")
def dotfile_path():
    """Fixture for looper dotfile path with cleanup."""
    path = os.path.join(os.getcwd(), LOOPER_DOTFILE_NAME)
    yield path
    if os.path.isfile(path):
        os.remove(path)


def get_outdir(pth):
    """Get output directory from a config file."""
    with open(pth, "r") as conf_file:
        config_data = safe_load(conf_file)
    output_path = config_data[OUTDIR_KEY]
    dirname = os.path.dirname(pth)
    return os.path.join(dirname, output_path)


def get_project_config_path(looper_config_pth):
    """Get project config file path from a looper config file path."""
    dirname = os.path.dirname(looper_config_pth)
    return os.path.join(dirname, "project/project_config.yaml")


def _assert_content_in_files(fs: str | Iterable[str], query: str, negate: bool):
    """Check file content for presence or absence of query string."""
    if isinstance(fs, str):
        fs = [fs]
    check = (lambda doc: query not in doc) if negate else (lambda doc: query in doc)
    for f in fs:
        with open(f, "r") as fh:
            contents = fh.read()
        assert check(contents)


def assert_content_in_all_files(fs: str | Iterable[str], query: str):
    """Verify that string is in files content."""
    _assert_content_in_files(fs, query, negate=False)


def assert_content_not_in_any_files(fs: str | Iterable[str], query: str):
    """Verify that string is not in files' content."""
    _assert_content_in_files(fs, query, negate=True)


def print_standard_stream(text: str | bytes) -> None:
    """Print bytes or str to stdout."""
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    if not isinstance(text, str):
        raise TypeError(f"Stream to print is neither str nor bytes, but {type(text)}")
    for line in text.split("\n"):
        print(line)


def test_args_expansion(pth=None, cmd=None, appendix=None, dry=True):
    """Create list of strings to pass to looper.main() as test_args."""
    if appendix is None:
        appendix = []
    x = []
    if cmd:
        x.append(cmd)
    if pth:
        x.append("--config")
        x.append(pth)
    if dry:
        x.append("--dry-run")
    x.extend(appendix)
    return x


def verify_filecount_in_dir(dirpath, pattern, count):
    """Check if expected number of files matching pattern exist in directory."""
    assert os.path.isdir(dirpath)
    subm_err = IOError(
        f"Expected {count} files matching '{pattern}' pattern in "
        f"'{dirpath}'. Listdir: \n{os.listdir(dirpath)}"
    )
    assert sum([f.endswith(pattern) for f in os.listdir(dirpath)]) == count, subm_err


def is_connected():
    """Determines if local machine can connect to the internet."""
    try:
        host = socket.gethostbyname("www.databio.org")
        socket.create_connection((host, 80), 2)
        return True
    except Exception:
        pass
    return False


@contextmanager
def mod_yaml_data(path):
    """Context manager to modify YAML formatted data."""
    with open(path, "r") as f:
        yaml_data = safe_load(f)
    print(f"\nInitial YAML data: \n{yaml_data}\n")
    yield yaml_data
    print(f"\nModified YAML data: \n{yaml_data}\n")
    with open(path, "w") as f:
        dump(yaml_data, f)


@pytest.fixture
def example_pep_piface_path():
    """Path to test data directory."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )


@pytest.fixture
def example_pep_piface_path_cfg(example_pep_piface_path):
    """Path to test project config."""
    return os.path.join(example_pep_piface_path, CFG)


@pytest.fixture
def prep_temp_pep(example_pep_piface_path, tmp_path):
    """Prepare a temporary PEP for testing."""
    hello_looper_dir_path = os.path.join(example_pep_piface_path, "hello_looper-dev")
    d = tmp_path / "pep"
    shutil.copytree(hello_looper_dir_path, d, dirs_exist_ok=True)
    advanced_dir = d / "pytesting" / "advanced_test"
    path_to_looper_config = str(advanced_dir / ".looper.yaml")
    return path_to_looper_config


@pytest.fixture
def prep_temp_pep_basic(example_pep_piface_path, tmp_path):
    """Prepare a basic temporary PEP for testing."""
    hello_looper_dir_path = os.path.join(example_pep_piface_path, "hello_looper-dev")
    d = tmp_path / "pep"
    shutil.copytree(hello_looper_dir_path, d, dirs_exist_ok=True)
    advanced_dir = d / "pytesting" / "intermediate_test"
    path_to_looper_config = str(advanced_dir / ".looper.yaml")
    return path_to_looper_config


@pytest.fixture
def prep_temp_pep_csv(example_pep_piface_path, tmp_path):
    """Prepare a CSV-based PEP for testing."""
    hello_looper_dir_path = os.path.join(example_pep_piface_path, "hello_looper-dev")
    d = tmp_path / "pep"
    shutil.copytree(hello_looper_dir_path, d, dirs_exist_ok=True)
    advanced_dir = d / "looper_csv_example"
    path_to_looper_config = str(advanced_dir / ".looper.yaml")
    return path_to_looper_config


@pytest.fixture
def prep_temp_config_with_pep(example_pep_piface_path, tmp_path):
    """Prepare temp config with PEP project dict."""
    td = tmp_path / "cfg"
    td.mkdir()
    cfg_path = os.path.join(example_pep_piface_path, CFG)
    sample_table_path = os.path.join(example_pep_piface_path, ST)
    piface1s_path = os.path.join(example_pep_piface_path, PIS.format("1"))
    temp_path_cfg = str(td / CFG)
    temp_path_sample_table = str(td / ST)
    temp_path_piface1s = str(td / PIS.format("1"))
    copyfile(cfg_path, temp_path_cfg)
    copyfile(sample_table_path, temp_path_sample_table)
    copyfile(piface1s_path, temp_path_piface1s)
    return peppy.Project(temp_path_cfg).to_dict(extended=True), temp_path_piface1s


@pytest.fixture
def prep_temp_pep_pipestat(example_pep_piface_path, tmp_path):
    """Prepare a pipestat-enabled PEP for testing."""
    hello_looper_dir_path = os.path.join(example_pep_piface_path, "hello_looper-dev")
    d = tmp_path / "pep"
    shutil.copytree(hello_looper_dir_path, d, dirs_exist_ok=True)
    advanced_dir = d / "pytesting" / "pipestat_test"
    path_to_looper_config = str(advanced_dir / ".looper.yaml")
    return path_to_looper_config


@pytest.fixture
def prep_temp_pep_pipestat_advanced(example_pep_piface_path, tmp_path):
    """Prepare an advanced pipestat-enabled PEP for testing."""
    hello_looper_dir_path = os.path.join(example_pep_piface_path, "hello_looper-dev")
    d = tmp_path / "pep"
    shutil.copytree(hello_looper_dir_path, d, dirs_exist_ok=True)
    advanced_dir = d / "pytesting" / "advanced_test"
    path_to_looper_config = str(advanced_dir / ".looper_advanced_pipestat.yaml")
    return path_to_looper_config


@pytest.fixture
def prep_temp_pep_pephub(example_pep_piface_path, tmp_path):
    """Prepare a PEPhub PEP for testing."""
    hello_looper_dir_path = os.path.join(example_pep_piface_path, "hello_looper-dev")
    d = tmp_path / "pep"
    shutil.copytree(hello_looper_dir_path, d, dirs_exist_ok=True)
    advanced_dir = d / "pephub"
    path_to_looper_config = str(advanced_dir / ".looper.yaml")
    return path_to_looper_config
