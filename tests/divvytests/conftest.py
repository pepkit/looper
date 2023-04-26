import os
import glob
import divvy
import pytest


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(THIS_DIR, "data/divcfg-master")
FILES = glob.glob(DATA_DIR + "/*.yaml")
DCC_ATTRIBUTES = divvy.ComputingConfiguration().keys()


@pytest.fixture
def empty_dcc():
    """Provide the empty/default ComputingConfiguration object"""
    return divvy.ComputingConfiguration()


@pytest.fixture(params=FILES)
def dcc(request):
    """Provide ComputingConfiguration objects for all files in divcfg repository"""
    return divvy.ComputingConfiguration(filepath=request.param)


@pytest.fixture
def mock_env_missing(monkeypatch):
    [
        monkeypatch.delenv(env_var, raising=False)
        for env_var in divvy.const.COMPUTE_SETTINGS_VARNAME
    ]
