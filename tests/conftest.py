import shutil
from contextlib import contextmanager
import os
import subprocess
from shutil import copyfile, rmtree, copytree
import tempfile
from typing import *

import peppy
import pytest
from peppy.const import *
from yaml import dump, safe_load

from looper.const import *

REPO_URL = "https://github.com/pepkit/hello_looper.git"

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
    path = os.path.join(os.getcwd(), LOOPER_DOTFILE_NAME)
    yield path
    if os.path.isfile(path):
        os.remove(path)


def get_outdir(pth):
    """
    Get output directory from a config file

    :param str pth:
    :return str: output directory
    """
    with open(pth, "r") as conf_file:
        config_data = safe_load(conf_file)

    output_path = config_data[OUTDIR_KEY]
    dirname = os.path.dirname(pth)

    return os.path.join(dirname, output_path)


def get_project_config_path(looper_config_pth):
    """
    Get project config file path from a config file path since they are relative

    :param str pth:
    :return str: output directory
    """
    dirname = os.path.dirname(looper_config_pth)

    return os.path.join(dirname, "project/project_config.yaml")


def _assert_content_in_files(fs: Union[str, Iterable[str]], query: str, negate: bool):
    if isinstance(fs, str):
        fs = [fs]
    check = (lambda doc: query not in doc) if negate else (lambda doc: query in doc)
    for f in fs:
        with open(f, "r") as fh:
            contents = fh.read()
        assert check(contents)


def assert_content_in_all_files(fs: Union[str, Iterable[str]], query: str):
    """
    Verify that string is in files content.

    :param str | Iterable[str] fs: list of files
    :param str query: string to look for
    """
    _assert_content_in_files(fs, query, negate=False)


def assert_content_not_in_any_files(fs: Union[str, Iterable[str]], query: str):
    """
    Verify that string is not in files' content.

    :param str | Iterable[str] fs: list of files
    :param str query: string to look for
    """
    _assert_content_in_files(fs, query, negate=True)


def print_standard_stream(text: Union[str, bytes]) -> None:
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    if not isinstance(text, str):
        raise TypeError(f"Stream to print is neither str nor bytes, but {type(text)}")
    for line in text.split("\n"):
        print(line)


def subp_exec(
    pth=None, cmd=None, appendix=list(), dry=True
) -> Tuple[bytes, bytes, int]:
    """

    :param str pth: config path
    :param str cmd: looper subcommand
    :param Iterable[str] appendix: other args to pass to the cmd
    :param bool dry: whether to append dry run flag
    :return stdout, stderr, and return code
    """
    x = ["looper", cmd, "-d" if dry else ""]
    if pth:
        x.append(pth)
    x.extend(appendix)
    proc = subprocess.Popen(x, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return stdout, stderr, proc.returncode


def test_args_expansion(pth=None, cmd=None, appendix=list(), dry=True) -> List[str]:
    """
    This function takes a path, command, extra argument list and creates a list of
    strings to pass to looper.main() as test_args.

    :param str pth: config path
    :param str cmd: looper subcommand
    :param Iterable[str] appendix: other args to pass to the cmd
    :param bool dry: whether to append dry run flag
    :return list of strings to pass to looper.main for testing
    """
    # --looper-config .looper.yaml run --dry-run
    # x = [cmd, "-d" if dry else ""]
    x = []
    if cmd:
        x.append(cmd)
    if pth:
        x.append("--looper-config")
        x.append(pth)
    if dry:
        x.append("--dry-run")
    x.extend(appendix)
    return x


def verify_filecount_in_dir(dirpath, pattern, count):
    """
    Check if the expected number of files matching specified pattern
    exist in a directory

    :param str dirpath: path to the directory to investigate
    :param str pattern: string pattern, used in str.endswith
    :param int count: expected number of files
    :raise IOError: when the number of files does not meet the expectations
    """
    assert os.path.isdir(dirpath)
    subm_err = IOError(
        f"Expected {count} files mathing '{pattern}' pattern in "
        f"'{dirpath}'. Listdir: \n{os.listdir(dirpath)}"
    )
    assert sum([f.endswith(pattern) for f in os.listdir(dirpath)]) == count, subm_err


@contextmanager
def mod_yaml_data(path):
    """
    Context manager used to modify YAML formatted data

    :param str path: path to the file to modify
    """
    # TODO: use everywhere
    with open(path, "r") as f:
        yaml_data = safe_load(f)
    print(f"\nInitial YAML data: \n{yaml_data}\n")
    yield yaml_data
    print(f"\nModified YAML data: \n{yaml_data}\n")
    with open(path, "w") as f:
        dump(yaml_data, f)


@pytest.fixture
def example_pep_piface_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@pytest.fixture
def example_pep_piface_path_cfg(example_pep_piface_path):
    return os.path.join(example_pep_piface_path, CFG)


@pytest.fixture
def prep_temp_pep(example_pep_piface_path):

    # Get Path to local copy of hello_looper
    hello_looper_dir_path = os.path.join(
        example_pep_piface_path, "hello_looper-dev_derive"
    )

    # Make local temp copy of hello_looper
    d = tempfile.mkdtemp()
    shutil.copytree(hello_looper_dir_path, d, dirs_exist_ok=True)

    advanced_dir = os.path.join(d, "advanced")
    path_to_looper_config = os.path.join(advanced_dir, ".looper.yaml")

    return path_to_looper_config


@pytest.fixture
def prep_temp_pep_basic(example_pep_piface_path):

    # Get Path to local copy of hello_looper
    hello_looper_dir_path = os.path.join(
        example_pep_piface_path, "hello_looper-dev_derive"
    )

    # Make local temp copy of hello_looper
    d = tempfile.mkdtemp()
    shutil.copytree(hello_looper_dir_path, d, dirs_exist_ok=True)

    advanced_dir = os.path.join(d, "basic")
    path_to_looper_config = os.path.join(advanced_dir, ".looper.yaml")

    return path_to_looper_config


@pytest.fixture
def prep_temp_config_with_pep(example_pep_piface_path):
    # temp dir
    td = tempfile.mkdtemp()
    out_td = os.path.join(td, "output")
    # ori paths
    cfg_path = os.path.join(example_pep_piface_path, CFG)
    sample_table_path = os.path.join(example_pep_piface_path, ST)
    piface1s_path = os.path.join(example_pep_piface_path, PIS.format("1"))
    temp_path_cfg = os.path.join(td, CFG)
    temp_path_sample_table = os.path.join(td, ST)
    temp_path_piface1s = os.path.join(td, PIS.format("1"))

    # copying
    copyfile(cfg_path, temp_path_cfg)
    copyfile(sample_table_path, temp_path_sample_table)
    copyfile(piface1s_path, temp_path_piface1s)

    return peppy.Project(temp_path_cfg).to_dict(extended=True), temp_path_piface1s


@pytest.fixture
def prep_temp_pep_pipestat(example_pep_piface_path):

    # Get Path to local copy of hello_looper

    hello_looper_dir_path = os.path.join(
        example_pep_piface_path, "hello_looper-dev_derive"
    )

    # Make local temp copy of hello_looper
    d = tempfile.mkdtemp()
    shutil.copytree(hello_looper_dir_path, d, dirs_exist_ok=True)

    advanced_dir = os.path.join(d, "pipestat")
    path_to_looper_config = os.path.join(advanced_dir, ".looper.yaml")

    return path_to_looper_config
