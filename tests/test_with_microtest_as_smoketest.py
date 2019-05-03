""" Use microtest for smoketesting the looper CLI. """

import os
import subprocess
import pytest
from ubiquerg import build_cli_extra

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


REPO_NAME = "microtest"
REPO_URL = "https://github.com/databio/{}".format(REPO_NAME)
SAMPLE_SELECTOR_OPTION = "--selector-attribute"
INCLUSION_OPTION = "--selector-include"


@pytest.mark.remote_data
@pytest.fixture
def data_root(tmpdir):
    """ Clone data repo and return path to it. """
    tmp = tmpdir.strpath
    cmd = "git clone {}".format(REPO_URL)
    try:
        subprocess.check_call(cmd, cwd=tmp, shell=True)
    except subprocess.CalledProcessError:
        raise Exception("Failed to pull data ()".format(cmd))
    root = os.path.join(tmp, REPO_NAME)
    assert os.path.isdir(root)
    return root


@pytest.fixture
def data_conf_file(data_root):
    """ Clone data repo and return path to project config file. """
    f = os.path.join(data_root, "config", "microtest_config.yaml")
    assert os.path.isfile(f), "Contents: {}".format(os.listdir(data_root))
    return f


@pytest.fixture(scope="function")
def temp_chdir_home(tmpdir):
    """ Temporarily (for a test case) change home and working directories. """
    key = "HOME"
    prev_home = os.environ[key]
    prev_work = os.environ["PWD"]
    curr_home = tmpdir.strpath
    os.environ[key] = curr_home
    os.chdir(curr_home)
    yield
    os.environ[key] = prev_home
    os.chdir(prev_work)
    assert os.getcwd() == prev_work
    assert os.getenv(key) == prev_home
    assert os.environ[key] == prev_home


@pytest.mark.remote_data
@pytest.mark.usefixtures("temp_chdir_home")
@pytest.mark.parametrize("cli_extra",
    [build_cli_extra(kvs) for kvs in
     [{SAMPLE_SELECTOR_OPTION: "protocol", INCLUSION_OPTION: "ATAC-seq"}]])
def test_cli_microtest_smoke(cli_extra, data_conf_file):
    """ Using microtest as project, test CLI for failure on specific cases. """
    cmd = "looper run -d {} {}".format(data_conf_file, cli_extra)
    try:
        subprocess.check_call(cmd, shell=True)
    except Exception as e:
        print("Exception: {}".format(e))
        pytest.fail("Failed command: {}".format(cmd))
