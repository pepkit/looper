import pytest
from tests.smoketests.conftest import *
from peppy.const import *
from looper.const import *
import subprocess
from yaml import safe_load, dump


def _subp_exec(pth, cmd, appendix=list(), dry=True):
    """

    :param str pth: config path
    :param str cmd: looper subcommand
    :param Iterable[str] appendix: other args to pass to the cmd
    :return:
    """
    x = ["looper", cmd, "-d" if dry else "", pth]
    x.extend(appendix)
    proc = subprocess.Popen(x, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return str(stdout), str(stderr), proc.returncode


def _get_outdir(pth):
    """
    Get output directory from a config file

    :param str pth:
    :return str: output directory
    """
    with open(pth, 'r') as conf_file:
        config_data = safe_load(conf_file)
    return config_data[LOOPER_KEY][OUTDIR_KEY]


class LooperRunBehaviorTests:
    def test_looper_run_basic(self, example_pep_piface_path_cfg):
        """ Verify looper runs in a basic case and return code is 0 """
        stdout, stderr, rc = _subp_exec(example_pep_piface_path_cfg, "run")
        print(stderr)
        assert rc == 0

    def test_looper_multi_pipeline(self, example_pep_piface_path_cfg):
        stdout, stderr, rc = _subp_exec(example_pep_piface_path_cfg, "run")
        print(stderr)
        assert "Commands submitted: 6 of 6" in stderr

    def test_looper_single_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        pifaces = \
            config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY]
        config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY] = \
            pifaces[1]
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = _subp_exec(tp, "run")
        print(stderr)
        assert rc == 0
        assert "Commands submitted: 6 of 6" not in stderr

    def test_looper_no_pipeline(self, prep_temp_pep):
        """
        No jobs are submitted and proper log is produced when there are no
        valid pifaces defined
        """
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        del config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY]
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = _subp_exec(tp, "run")
        print(stderr)
        assert rc == 0
        assert "Jobs submitted: 0" in stderr
        assert "No pipeline interfaces defined"

    def test_looper_pipeline_not_found(self, prep_temp_pep):
        """
        Piface is ignored when when it does not exist
        """
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY] = \
            ["bogus"]
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = _subp_exec(tp, "run")
        print(stderr)
        assert rc == 0
        assert "Jobs submitted: 0" in stderr
        assert "Ignoring invalid pipeline interface source"

    def test_looper_pipeline_invalid(self, prep_temp_pep):
        """
        Pipeline is ignored when does not validate successfully
        agianst a schema
        """
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        pifaces = config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][
            PIPELINE_INTERFACES_KEY]
        config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY] = \
            pifaces[1]
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        piface_path = os.path.join(os.path.dirname(tp), pifaces[1])
        with open(piface_path, 'r') as piface_file:
            piface_data = safe_load(piface_file)
        del piface_data["pipeline_name"]
        with open(piface_path, 'w') as piface_file:
            dump(piface_data, piface_file)
        stdout, stderr, rc = _subp_exec(tp, "run")
        print(stderr)
        assert rc == 0
        assert "Jobs submitted: 0" in stderr
        assert "Ignoring invalid pipeline interface source"
        assert "'pipeline_name' is a required property"

    def test_looper_sample_attr_missing(self, prep_temp_pep):
        """
        Piface is ignored when when it does not exist
        """
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        del config_data[SAMPLE_MODS_KEY][CONSTANT_KEY]["attr"]
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = _subp_exec(tp, "run")
        print(stderr)
        assert rc == 0
        assert "Jobs submitted: 0" in stderr


class LooperRunpBehaviorTests:
    def test_looper_runp_basic(self, example_pep_piface_path_cfg):
        """ Verify looper runps in a basic case and return code is 0 """
        stdout, stderr, rc = _subp_exec(example_pep_piface_path_cfg, "runp")
        assert rc == 0

    def test_looper_multi_pipeline(self, example_pep_piface_path_cfg):
        stdout, stderr, rc = _subp_exec(example_pep_piface_path_cfg, "runp")
        assert "Jobs submitted: 2" in stderr

    def test_looper_single_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        pifaces = \
            config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY]
        config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY] = \
            pifaces[1]
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = _subp_exec(tp, "runp")
        print(stderr)
        assert rc == 0
        assert "Jobs submitted: 2" not in stderr
        assert "Jobs submitted: 1" in stderr


class LooperRunSubmissionScriptTests:
    def test_looper_run_produces_submission_scripts(self, prep_temp_pep):
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        outdir = config_data[LOOPER_KEY][OUTDIR_KEY]
        stdout, stderr, rc = _subp_exec(tp, "run")
        sd = os.path.join(outdir, "submission")
        subm_err = \
            IOError("Not found in submission directory ({}): 6 "
                              "submission scripts (3 per pipeline) and 3 sample"
                              " YAML representations".format(sd))
        print(stderr)
        assert rc == 0
        assert os.path.isdir(sd)
        assert len(os.listdir(sd)) == 9, subm_err
        assert sum([f.endswith(".sub") for f in os.listdir(sd)]) == 6, subm_err
        assert sum([f.endswith(".yaml") for f in os.listdir(sd)]) == 3, subm_err

    def test_looper_lumping(self, prep_temp_pep):
        tp = prep_temp_pep
        outdir = _get_outdir(tp)
        stdout, stderr, rc = _subp_exec(tp, "run", ["--lumpn", "2"])
        sd = os.path.join(outdir, "submission")
        subm_err = \
            IOError("Not found in submission directory ({}): 4 "
                              "submission scripts (2 per pipeline) and 3 sample"
                              " YAML representations. Listdir: \n{}".
                    format(sd, os.listdir(sd)))
        print(stderr)
        assert rc == 0
        assert os.path.isdir(sd)
        assert len(os.listdir(sd)) == 7, subm_err
        assert sum([f.endswith(".sub") for f in os.listdir(sd)]) == 4, subm_err
        assert sum([f.endswith(".yaml") for f in os.listdir(sd)]) == 3, subm_err

    def test_looper_lumping(self, prep_temp_pep):
        tp = prep_temp_pep
        outdir = _get_outdir(tp)
        stdout, stderr, rc = _subp_exec(tp, "run", ["--lumpn", "2"])
        sd = os.path.join(outdir, "submission")
        subm_err = \
            IOError("Not found in submission directory ({}): 4 "
                              "submission scripts (2 per pipeline) and 3 sample"
                              " YAML representations. Listdir: \n{}".
                    format(sd, os.listdir(sd)))
        print(stderr)
        assert rc == 0
        assert os.path.isdir(sd)
        assert sum([f.endswith(".sub") for f in os.listdir(sd)]) == 4, subm_err
        assert sum([f.endswith(".yaml") for f in os.listdir(sd)]) == 3, subm_err

    def test_looper_limiting(self, prep_temp_pep):
        tp = prep_temp_pep
        outdir = _get_outdir(tp)
        stdout, stderr, rc = _subp_exec(tp, "run", ["--limit", "2"])
        sd = os.path.join(outdir, "submission")
        subm_err = \
            IOError("Not found in submission directory ({}): 4 "
                              "submission scripts (2 per pipeline) and 2 sample"
                              " YAML representations. Listdir: \n{}".
                    format(sd, os.listdir(sd)))
        print(stderr)
        assert rc == 0
        assert os.path.isdir(sd)
        assert sum([f.endswith(".sub") for f in os.listdir(sd)]) == 4, subm_err
        assert sum([f.endswith(".yaml") for f in os.listdir(sd)]) == 2, subm_err















