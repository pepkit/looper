# content of test_pyconv.py
import pytest
import os
from peppy import Project
from tempfile import gettempdir as gtd
from shutil import copyfile as cpf
import subprocess

# we reuse a bit of pytest's own testing machinery, this should eventually come
# from a separatedly installable pytest-cli plugin.
pytest_plugins = ["pytester"]
EB = "cfg2"
CFG = "project_config.yaml"
ST = "annotation_sheet.csv"
PI = "pipeline_interface{}.yaml"
OS = "output_schema.yaml"


# @pytest.fixture
# def subp_run(example_pep_piface_path):
#     """
#     looper run in a subprocess, example cfg
#     """
#     pth = os.path.join(example_pep_piface_path, CFG)
#     proc = subprocess.Popen(["looper", "run", "-d", pth],
#                             stderr=subprocess.PIPE, stdout=subprocess.PIPE)
#     stdout, stderr = proc.communicate()
#     return str(stdout), str(stderr), proc.returncode
#
#
# @pytest.fixture
# def temp_subp_run(prep_temp_pep):
#     """
#     looper run in a subprocess, temp cfg
#     """
#     proc = subprocess.Popen(["looper", "run", "-d", prep_temp_pep],
#                             stderr=subprocess.PIPE, stdout=subprocess.PIPE)
#     stdout, stderr = proc.communicate()
#     return str(stdout), str(stderr), proc.returncode


@pytest.fixture
def example_pep_piface_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data/example_peps-{}/example_piface".format(EB)
    )


@pytest.fixture
def example_pep_piface_path_cfg(example_pep_piface_path):
    return os.path.join(example_pep_piface_path, CFG)


@pytest.fixture
def prep_temp_pep(example_pep_piface_path):
    # temp dir
    td = gtd()
    # ori paths
    cfg_path = os.path.join(example_pep_piface_path, CFG)
    sample_table_path = os.path.join(example_pep_piface_path, ST)
    piface1_path = os.path.join(example_pep_piface_path, PI.format("1"))
    piface2_path = os.path.join(example_pep_piface_path, PI.format("2"))
    schema_path = os.path.join(example_pep_piface_path, OS)
    # temp copies
    temp_path_cfg = os.path.join(td, CFG)
    temp_path_sample_table = os.path.join(td, ST)
    temp_path_piface1 = os.path.join(td, PI.format("1"))
    temp_path_piface2 = os.path.join(td, PI.format("2"))
    temp_path_schema = os.path.join(td, OS)
    # copying
    cpf(cfg_path, temp_path_cfg)
    cpf(sample_table_path, temp_path_sample_table)
    cpf(piface1_path, temp_path_piface1)
    cpf(piface2_path, temp_path_piface2)
    cpf(schema_path, temp_path_schema)
    return temp_path_cfg
