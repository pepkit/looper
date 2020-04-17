import pytest
import os
from tempfile import gettempdir as gtd
from shutil import copyfile as cpf

CFG = "project_config.yaml"
ST = "annotation_sheet.csv"
PI = "pipeline_interface{}.yaml"
OS = "output_schema.yaml"
RES = "resources-{}.tsv"

@pytest.fixture
def example_pep_piface_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data/example_peps/example_piface")


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
    res_proj_path = os.path.join(example_pep_piface_path, RES.format("project"))
    res_samp_path = os.path.join(example_pep_piface_path, RES.format("sample"))
    # temp copies
    temp_path_cfg = os.path.join(td, CFG)
    temp_path_sample_table = os.path.join(td, ST)
    temp_path_piface1 = os.path.join(td, PI.format("1"))
    temp_path_piface2 = os.path.join(td, PI.format("2"))
    temp_path_schema = os.path.join(td, OS)
    temp_path_res_proj = os.path.join(td, RES.format("project"))
    temp_path_res_samp = os.path.join(td, RES.format("sample"))
    # copying
    cpf(cfg_path, temp_path_cfg)
    cpf(sample_table_path, temp_path_sample_table)
    cpf(piface1_path, temp_path_piface1)
    cpf(piface2_path, temp_path_piface2)
    cpf(schema_path, temp_path_schema)
    cpf(res_proj_path, temp_path_res_proj)
    cpf(res_samp_path, temp_path_res_samp)
    return temp_path_cfg
