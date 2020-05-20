import pytest
import os
import tempfile
from shutil import copyfile as cpf, rmtree
from looper.const import *
from peppy.const import *
from yaml import safe_load
import subprocess

CFG = "project_config.yaml"
ST = "annotation_sheet.csv"
PIP = "pipeline_interface{}_project.yaml"
PIS = "pipeline_interface{}_sample.yaml"
OS = "output_schema.yaml"
RES = "resources-{}.tsv"


def get_outdir(pth):
    """
    Get output directory from a config file

    :param str pth:
    :return str: output directory
    """
    with open(pth, 'r') as conf_file:
        config_data = safe_load(conf_file)
    return config_data[LOOPER_KEY][OUTDIR_KEY]


def is_in_file(fs, s, reverse=False):
    """
    Verify if string is in files content

    :param str | Iterable[str] fs: list of files
    :param str s: string to look for
    :param bool reverse: whether the reverse should be checked
    """
    if isinstance(fs, str):
        fs = [fs]
    for f in fs:
        with open(f, 'r') as fh:
            if reverse:
                assert s not in fh.read()
            else:
                assert s in fh.read()


def subp_exec(pth=None, cmd=None, appendix=list(), dry=True):
    """

    :param str pth: config path
    :param str cmd: looper subcommand
    :param Iterable[str] appendix: other args to pass to the cmd
    :return:
    """
    x = ["looper", cmd, "-d" if dry else ""]
    if pth:
        x.append(pth)
    x.extend(appendix)
    proc = subprocess.Popen(x, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return str(stdout), str(stderr), proc.returncode


@pytest.fixture
def example_pep_piface_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


@pytest.fixture
def example_pep_piface_path_cfg(example_pep_piface_path):
    return os.path.join(example_pep_piface_path, CFG)


@pytest.fixture
def prep_temp_pep(example_pep_piface_path):
    # temp dir
    td = tempfile.mkdtemp()
    out_td = os.path.join(td, "output")
    # ori paths
    cfg_path = os.path.join(example_pep_piface_path, CFG)
    sample_table_path = os.path.join(example_pep_piface_path, ST)
    piface1p_path = os.path.join(example_pep_piface_path, PIP.format("1"))
    piface2p_path = os.path.join(example_pep_piface_path, PIP.format("2"))
    piface1s_path = os.path.join(example_pep_piface_path, PIS.format("1"))
    piface2s_path = os.path.join(example_pep_piface_path, PIS.format("2"))
    output_schema_path = os.path.join(example_pep_piface_path, OS)
    res_proj_path = os.path.join(example_pep_piface_path, RES.format("project"))
    res_samp_path = os.path.join(example_pep_piface_path, RES.format("sample"))
    # temp copies
    temp_path_cfg = os.path.join(td, CFG)
    temp_path_sample_table = os.path.join(td, ST)
    temp_path_piface1s = os.path.join(td, PIS.format("1"))
    temp_path_piface2s = os.path.join(td, PIS.format("2"))
    temp_path_piface1p = os.path.join(td, PIP.format("1"))
    temp_path_piface2p = os.path.join(td, PIP.format("2"))
    temp_path_output_schema = os.path.join(td, OS)
    temp_path_res_proj = os.path.join(td, RES.format("project"))
    temp_path_res_samp = os.path.join(td, RES.format("sample"))
    # copying
    cpf(cfg_path, temp_path_cfg)
    cpf(sample_table_path, temp_path_sample_table)
    cpf(piface1s_path, temp_path_piface1s)
    cpf(piface2s_path, temp_path_piface2s)
    cpf(piface1p_path, temp_path_piface1p)
    cpf(piface2p_path, temp_path_piface2p)
    cpf(output_schema_path, temp_path_output_schema)
    cpf(res_proj_path, temp_path_res_proj)
    cpf(res_samp_path, temp_path_res_samp)
    # modififactions
    from yaml import safe_load, dump
    with open(temp_path_cfg, 'r') as f:
        piface_data = safe_load(f)
    piface_data[LOOPER_KEY][OUTDIR_KEY] = out_td
    piface_data[LOOPER_KEY][CLI_KEY] = {}
    piface_data[LOOPER_KEY][CLI_KEY]["runp"] = {}
    piface_data[LOOPER_KEY][CLI_KEY]["runp"][PIPELINE_INTERFACES_KEY] = \
        [temp_path_piface1p, temp_path_piface2p]
    piface_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY] = \
        [temp_path_piface1s, temp_path_piface2s]
    with open(temp_path_cfg, 'w') as f:
        dump(piface_data, f)
    return temp_path_cfg
