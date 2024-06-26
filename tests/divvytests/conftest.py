import os
import glob
import looper.divvy as divvy
import pytest

from looper.divvy import select_divvy_config, DEFAULT_CONFIG_SCHEMA


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(THIS_DIR, "data/divcfg-master")
FILES = glob.glob(DATA_DIR + "/*.yaml")


dcc_filepath = select_divvy_config(None)
DCC = divvy.ComputingConfiguration.from_yaml_file(filepath=dcc_filepath)
DCC_ATTRIBUTES = DCC.keys()


@pytest.fixture
def empty_dcc():
    """Provide the empty/default ComputingConfiguration object"""
    return divvy.ComputingConfiguration()


@pytest.fixture(params=FILES)
def dcc(request):
    """Provide ComputingConfiguration objects for all files in divcfg repository"""
    return divvy.ComputingConfiguration.from_yaml_file(filepath=request.param)


@pytest.fixture
def mock_env_missing(monkeypatch):
    [
        monkeypatch.delenv(env_var, raising=False)
        for env_var in divvy.COMPUTE_SETTINGS_VARNAME
    ]
