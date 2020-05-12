import pytest
from tests.smoketests.conftest import *
from peppy.const import *
from looper.const import *
import subprocess
from yaml import safe_load, dump

CMD_STRS = ["string", " --string", " --sjhsjd 212", "7867#$@#$cc@@"]


def _subp_exec(pth=None, cmd=None, appendix=list(), dry=True):
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


def _is_in_file(fs, s, reverse=False):
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


def _get_outdir(pth):
    """
    Get output directory from a config file

    :param str pth:
    :return str: output directory
    """
    with open(pth, 'r') as conf_file:
        config_data = safe_load(conf_file)
    return config_data[LOOPER_KEY][ALL_SUBCMD_KEY][OUTDIR_KEY]


class LooperBothRunsTests:
    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_cfg_invalid(self, cmd):
        """ Verify looper does not accept invalid cfg paths """
        stdout, stderr, rc = _subp_exec("jdfskfds/dsjfklds/dsjklsf.yaml", cmd)
        print(stderr)
        assert rc != 0

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_cfg_required(self, cmd):
        """ Verify looper does not accept invalid cfg paths """
        stdout, stderr, rc = _subp_exec(pth="", cmd=cmd)
        print(stderr)
        assert rc != 0

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    @pytest.mark.parametrize("arg", [["--command-extra", CMD_STRS[0]],
                                     ["--command-extra", CMD_STRS[1]],
                                     ["--command-extra", CMD_STRS[2]],
                                     ["--command-extra", CMD_STRS[3]]])
    def test_cmd_extra_cli(self, prep_temp_pep, cmd, arg):
        """
        Argument passing functionality works only for the above
        configurations. Notably, it does not work for --command-extra '--arg'.

        See https://github.com/pepkit/looper/issues/245#issuecomment-621815222
        """
        tp = prep_temp_pep
        stdout, stderr, rc = _subp_exec(tp, cmd, arg)
        sd = os.path.join(_get_outdir(tp), "submission")
        print(stderr)
        assert rc == 0
        subs_list = \
            [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, arg[1])

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_unrecognized_args_not_passing(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        stdout, stderr, rc = _subp_exec(tp, cmd, ["--unknown-arg", "4"])
        sd = os.path.join(_get_outdir(tp), "submission")
        print(stderr)
        assert rc == 0
        subs_list = \
            [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, "--unknown-arg", reverse=True)

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_dotfile_general(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        dotfile_path = os.path.join(os.getcwd(), LOOPER_DOTFILE_NAME)
        with open(dotfile_path, 'w') as df:
            dump({LOOPER_KEY: {"package": "local"}}, df)
        stdout, stderr, rc = _subp_exec(tp, cmd)
        sd = os.path.join(_get_outdir(tp), "submission")
        print(stderr)
        assert rc == 0
        subs_list = \
            [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, "#SBATCH", reverse=True)
        os.remove(dotfile_path)

    # @pytest.mark.parametrize("cmd", ["run", "runp"])
    # def test_dotfile_config_file(self, prep_temp_pep, cmd):
    #     tp = prep_temp_pep
    #     dotfile_path = os.path.join(os.getcwd(), LOOPER_DOTFILE_NAME)
    #     with open(dotfile_path, 'w') as df:
    #         dump({LOOPER_KEY: {"config_file": tp}}, df)
    #     stdout, stderr, rc = _subp_exec(cmd=cmd)
    #     print(stderr)
    #     assert rc == 0
    #     os.remove(dotfile_path)

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_cli_overwrites_dotfile(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        dotfile_path = os.path.join(os.getcwd(), LOOPER_DOTFILE_NAME)
        with open(dotfile_path, 'w') as df:
            dump({LOOPER_KEY: {"package": "local"}}, df)
        stdout, stderr, rc = _subp_exec(tp, cmd, ["--package", "slurm"])
        sd = os.path.join(_get_outdir(tp), "submission")
        print(stderr)
        assert rc == 0
        subs_list = \
            [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, "#SBATCH")
        os.remove(dotfile_path)

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_run_after_init(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        dotfile_path = os.path.join(os.getcwd(), LOOPER_DOTFILE_NAME)
        stdout, stderr, rc = _subp_exec(tp, "init")
        print(stderr)
        print(stdout)
        assert rc == 0
        _is_in_file(dotfile_path, tp)
        stdout, stderr, rc = _subp_exec(cmd=cmd)
        print(stderr)
        print(stdout)
        assert rc == 0
        os.remove(dotfile_path)


class LooperRunBehaviorTests:
    def test_looper_run_basic(self, prep_temp_pep):
        """ Verify looper runs in a basic case and return code is 0 """
        tp = prep_temp_pep
        stdout, stderr, rc = _subp_exec(tp, "run")
        print(stderr)
        assert rc == 0

    def test_looper_multi_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        stdout, stderr, rc = _subp_exec(tp, "run")
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

    def test_looper_cli_pipeline(self, prep_temp_pep):
        """ CLI-specified pipelines overwrite ones from config """
        tp = prep_temp_pep
        pi_pth = os.path.join(os.path.dirname(tp), "pipeline_interface1.yaml")
        stdout, stderr, rc = _subp_exec(tp, "run",
                                        ["--pipeline-interfaces", pi_pth])
        print(stderr)
        assert rc == 0
        assert "Commands submitted: 3 of 3" not in stdout

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

    def test_looper_sample_name_whitespace(self, prep_temp_pep):
        """
        Piface is ignored when when it does not exist
        """
        tp = prep_temp_pep
        imply_whitespace = \
            [{IMPLIED_IF_KEY: {'sample_name': 'sample1'},
              IMPLIED_THEN_KEY: {'sample_name': 'sample whitespace'}}]
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        config_data[SAMPLE_MODS_KEY][IMPLIED_KEY] = imply_whitespace
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = _subp_exec(tp, "run")
        print(stderr)
        assert rc != 0

    def test_looper_toogle(self, prep_temp_pep):
        """
        If all samples have tooggle attr set to 0, no jobs are submitted
        """
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][SAMPLE_TOGGLE_ATTR] = 0
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = _subp_exec(tp, "run")
        print(stderr)
        assert rc == 0
        assert "Jobs submitted: 0" in stderr

    @pytest.mark.parametrize("arg", CMD_STRS)
    def test_cmd_extra_sample(self, prep_temp_pep, arg):
        """
        string set by sample_modifiers in Sample.command_extra shuld be
        appended to the pipelinecommand
        """
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        config_data[SAMPLE_MODS_KEY][CONSTANT_KEY]["command_extra"] = arg
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = _subp_exec(tp, "run")
        sd = os.path.join(_get_outdir(tp), "submission")
        print(stderr)
        assert rc == 0
        subs_list = \
            [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, arg)

    @pytest.mark.parametrize("arg", CMD_STRS)
    def test_cmd_extra_override_sample(self, prep_temp_pep, arg):
        """
        --command-extra-override should override the Sample.command_extra
        and Project.looper.command_extra attributes appeneded to the
        pipeline command
        """
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        config_data[SAMPLE_MODS_KEY][CONSTANT_KEY]["command_extra"] = arg
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = \
            _subp_exec(tp, "run", ["--command-extra-override='different'"])
        sd = os.path.join(_get_outdir(tp), "submission")
        print(stderr)
        assert rc == 0
        subs_list = \
            [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, arg, reverse=True)


class LooperRunpBehaviorTests:
    def test_looper_runp_basic(self, prep_temp_pep):
        """ Verify looper runps in a basic case and return code is 0 """
        tp = prep_temp_pep
        stdout, stderr, rc = _subp_exec(tp, "runp")
        print(stderr)
        assert rc == 0

    def test_looper_multi_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        stdout, stderr, rc = _subp_exec(tp, "runp")
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

    @pytest.mark.parametrize("arg", CMD_STRS)
    def test_cmd_extra_project(self, prep_temp_pep, arg):
        """
        """
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        config_data[LOOPER_KEY]["command_extra"] = arg
        print("\nconfig_data: \n{}\n".format(config_data))
        with open(tp, 'w') as conf_file:
            dump(config_data, conf_file)
        stdout, stderr, rc = _subp_exec(tp, "runp")
        sd = os.path.join(_get_outdir(tp), "submission")
        print(stderr)
        assert rc == 0
        subs_list = \
            [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, arg)


class LooperRunSubmissionScriptTests:
    def test_looper_run_produces_submission_scripts(self, prep_temp_pep):
        tp = prep_temp_pep
        with open(tp, 'r') as conf_file:
            config_data = safe_load(conf_file)
        print("\nconfig_data: \n{}\n".format(config_data))
        outdir = config_data[LOOPER_KEY][ALL_SUBCMD_KEY][OUTDIR_KEY]
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
        stdout, stderr, rc = _subp_exec(tp, "run", ["--lumpn", "2"])
        sd = os.path.join(_get_outdir(tp), "submission")
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
        stdout, stderr, rc = _subp_exec(tp, "run", ["--lumpn", "2"])
        sd = os.path.join(_get_outdir(tp), "submission")
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
        stdout, stderr, rc = _subp_exec(tp, "run", ["--limit", "2"])
        sd = os.path.join(_get_outdir(tp), "submission")
        subm_err = \
            IOError("Not found in submission directory ({}): 4 "
                    "submission scripts (2 per pipeline) and 2 sample "
                    "YAML representations. Listdir: \n{}".
                    format(sd, os.listdir(sd)))
        print(stderr)
        assert rc == 0
        assert os.path.isdir(sd)
        assert sum([f.endswith(".sub") for f in os.listdir(sd)]) == 4, subm_err
        assert sum([f.endswith(".yaml") for f in os.listdir(sd)]) == 2, subm_err


class LooperComputeTests:
    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_respects_pkg_selection(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        stdout, stderr, rc = _subp_exec(tp, cmd, ["--package", "local"])
        sd = os.path.join(_get_outdir(tp), "submission")
        print(stderr)
        assert rc == 0
        subs_list = \
            [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, "#SBATCH", reverse=True)

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_uses_cli_compute_options_spec(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        stdout, stderr, rc = _subp_exec(tp, cmd, ["--compute", "mem=12345",
                                                    "--package", "slurm"])
        sd = os.path.join(_get_outdir(tp), "submission")
        print(stderr)
        assert rc == 0
        subs_list = \
            [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, "#SBATCH --mem='12345'")

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_cli_yaml_settings_general(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        td = tempfile.mkdtemp()
        settings_file_path = os.path.join(td, "settings.yaml")
        with open(settings_file_path, 'w') as sf:
            dump({"mem": "testin_mem"}, sf)
        stdout, stderr, rc = \
            _subp_exec(tp, cmd, ["--settings", settings_file_path])
        print(stderr)
        assert rc == 0

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_nonexistent_yaml_settings_disregarded(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        stdout, stderr, rc = \
            _subp_exec(tp, cmd, ["--settings", "niema.yaml"])
        print(stderr)
        assert rc == 0

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_cli_yaml_settings_passes_settings(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        td = tempfile.mkdtemp()
        settings_file_path = os.path.join(td, "settings.yaml")
        with open(settings_file_path, 'w') as sf:
            dump({"mem": "testin_mem"}, sf)
        stdout, stderr, rc = \
            _subp_exec(tp, cmd, ["--settings", settings_file_path, "-p", "slurm"])
        print(stderr)
        assert rc == 0
        sd = os.path.join(_get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f)
                     for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, "testin_mem")

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_cli_compute_overwrites_yaml_settings_spec(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        td = tempfile.mkdtemp()
        settings_file_path = os.path.join(td, "settings.yaml")
        with open(settings_file_path, 'w') as sf:
            dump({"mem": "testin_mem"}, sf)
        stdout, stderr, rc = \
            _subp_exec(tp, cmd, ["--settings", settings_file_path,
                                 "--compute", "mem=10",
                                 "-p", "slurm"])
        print(stderr)
        assert rc == 0
        sd = os.path.join(_get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f)
                     for f in os.listdir(sd) if f.endswith(".sub")]
        _is_in_file(subs_list, "testin_mem", reverse=True)