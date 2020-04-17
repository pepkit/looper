import pytest
from tests.smoketests.conftest import *
from peppy.const import *
from looper.const import *
import subprocess
from yaml import safe_load, dump

def subp_run(pth):
    """
    looper run in a subprocess, example cfg
    """
    proc = subprocess.Popen(["looper", "run", "-d", pth],
                            stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return str(stdout), str(stderr), proc.returncode


class LooperRunTests:
    def test_looper_run_basic(self, example_pep_piface_path_cfg):
        """ Verify looper runs in a basic case and return code is 0 """
        stdout, stderr, rc = subp_run(example_pep_piface_path_cfg)
        assert rc == 0

    def test_looper_multi_pipeline(self, example_pep_piface_path_cfg):
        stdout, stderr, rc = subp_run(example_pep_piface_path_cfg)
        assert "Commands submitted: 6 of 6" in stderr

    def test_looper_single_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        # print("\nconfig_data: \n{}\n".format(config_data))
        pifaces = config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY]
        config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY] = pifaces[1]
        # print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = subp_run(tp)
        assert rc == 0
        assert "Commands submitted: 6 of 6" not in stderr