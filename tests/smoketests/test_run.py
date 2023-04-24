import pytest
from peppy.const import *
from yaml import dump

from looper.const import *
from looper.project import Project
from tests.conftest import *

CMD_STRS = ["string", " --string", " --sjhsjd 212", "7867#$@#$cc@@"]


class TestsLooperBothRuns:
    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_cfg_invalid(self, cmd):
        """Verify looper does not accept invalid cfg paths"""
        stdout, stderr, rc = subp_exec("jdfskfds/dsjfklds/dsjklsf.yaml", cmd)
        print_standard_stream(stderr)
        assert rc != 0

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_cfg_required(self, cmd):
        """Verify looper does not accept invalid cfg paths"""
        stdout, stderr, rc = subp_exec(pth="", cmd=cmd)
        print_standard_stream(stderr)
        assert rc != 0

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    @pytest.mark.parametrize(
        "arg",
        [
            ["--command-extra", CMD_STRS[0]],
            ["--command-extra", CMD_STRS[1]],
            ["--command-extra", CMD_STRS[2]],
            ["--command-extra", CMD_STRS[3]],
        ],
    )
    def test_cmd_extra_cli(self, prep_temp_pep, cmd, arg):
        """
        Argument passing functionality works only for the above
        configurations. Notably, it does not work for --command-extra '--arg'.

        See https://github.com/pepkit/looper/issues/245#issuecomment-621815222
        """
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, cmd, arg)
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_in_all_files(subs_list, arg[1])

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_unrecognized_args_not_passing(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, cmd, ["--unknown-arg", "4"])
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_not_in_any_files(subs_list, "--unknown-arg")

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_run_after_init(self, prep_temp_pep, cmd, dotfile_path):
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, "init")
        print_standard_stream(stderr)
        print_standard_stream(stdout)
        assert rc == 0
        assert_content_in_all_files(dotfile_path, tp)
        stdout, stderr, rc = subp_exec(cmd=cmd)
        print_standard_stream(stderr)
        print_standard_stream(stdout)
        assert rc == 0


class TestsLooperRunBehavior:
    def test_looper_run_basic(self, prep_temp_pep):
        """Verify looper runs in a basic case and return code is 0"""
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, "run")
        print_standard_stream(stderr)
        assert rc == 0

    def test_looper_multi_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, "run")
        print_standard_stream(stderr)
        assert "Commands submitted: 6 of 6" in str(stderr)

    def test_looper_single_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            pifaces = config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][
                PIPELINE_INTERFACES_KEY
            ]
            config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][
                PIPELINE_INTERFACES_KEY
            ] = pifaces[1]

        stdout, stderr, rc = subp_exec(tp, "run")
        print_standard_stream(stderr)
        assert rc == 0
        assert "Commands submitted: 6 of 6" not in str(stderr)

    def test_looper_cli_pipeline(self, prep_temp_pep):
        """CLI-specified pipelines overwrite ones from config"""
        tp = prep_temp_pep
        pi_pth = os.path.join(os.path.dirname(tp), PIS.format("1"))
        stdout, stderr, rc = subp_exec(tp, "run", ["--pipeline-interfaces", pi_pth])
        print_standard_stream(stderr)
        assert rc == 0
        assert "Commands submitted: 3 of 3" not in str(stdout)

    def test_looper_no_pipeline(self, prep_temp_pep):
        """
        No jobs are submitted and proper log is produced when there are no
        valid pifaces defined
        """
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            del config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY]
        stdout, stderr, rc = subp_exec(tp, "run")
        print_standard_stream(stderr)
        assert rc == 0
        assert "Jobs submitted: 0" in str(stderr)
        assert "No pipeline interfaces defined"

    def test_looper_pipeline_not_found(self, prep_temp_pep):
        """
        Piface is ignored when it does not exist
        """
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][PIPELINE_INTERFACES_KEY] = [
                "bogus"
            ]
        stdout, stderr, rc = subp_exec(tp, "run")
        print_standard_stream(stderr)
        assert rc == 0
        assert "Jobs submitted: 0" in str(stderr)
        assert "Ignoring invalid pipeline interface source"

    def test_looper_pipeline_invalid(self, prep_temp_pep):
        """
        Pipeline is ignored when does not validate successfully
        against a schema
        """
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            pifaces = config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][
                PIPELINE_INTERFACES_KEY
            ]
            config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][
                PIPELINE_INTERFACES_KEY
            ] = pifaces[1]
        piface_path = os.path.join(os.path.dirname(tp), pifaces[1])
        with mod_yaml_data(piface_path) as piface_data:
            del piface_data["pipeline_name"]
        stdout, stderr, rc = subp_exec(tp, "run")
        print_standard_stream(stderr)
        assert rc == 0
        assert "Jobs submitted: 0" in str(stderr)
        assert "Ignoring invalid pipeline interface source"
        assert "'pipeline_name' is a required property"

    def test_looper_sample_attr_missing(self, prep_temp_pep):
        """
        Piface is ignored when it does not exist
        """
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            del config_data[SAMPLE_MODS_KEY][CONSTANT_KEY]["attr"]
        stdout, stderr, rc = subp_exec(tp, "run")
        print_standard_stream(stderr)
        assert rc == 0
        assert "Jobs submitted: 0" in str(stderr)

    def test_looper_sample_name_whitespace(self, prep_temp_pep):
        """
        Piface is ignored when it does not exist
        """
        pepfile = prep_temp_pep
        imply_whitespace = [
            {
                IMPLIED_IF_KEY: {"sample_name": "sample1"},
                IMPLIED_THEN_KEY: {"sample_name": "sample whitespace"},
            }
        ]
        with mod_yaml_data(pepfile) as config_data:
            config_data[SAMPLE_MODS_KEY][IMPLIED_KEY] = imply_whitespace
        stdout, stderr, rc = subp_exec(pepfile, "run")
        print_standard_stream(stderr)
        assert rc == 0
        expected_prefix = "Short-circuiting due to validation error"
        assert expected_prefix in str(stderr)

    def test_looper_toggle(self, prep_temp_pep):
        """
        If all samples have toggle attr set to 0, no jobs are submitted
        """
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][SAMPLE_TOGGLE_ATTR] = 0
        stdout, stderr, rc = subp_exec(tp, "run")
        print_standard_stream(stderr)
        assert rc == 0
        assert "Jobs submitted: 0" in str(stderr)

    @pytest.mark.parametrize("arg", CMD_STRS)
    def test_cmd_extra_sample(self, prep_temp_pep, arg):
        """
        string set by sample_modifiers in Sample.command_extra shuld be
        appended to the pipelinecommand
        """
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            config_data[SAMPLE_MODS_KEY][CONSTANT_KEY]["command_extra"] = arg
        stdout, stderr, rc = subp_exec(tp, "run")
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_in_all_files(subs_list, arg)

    @pytest.mark.parametrize("arg", CMD_STRS)
    def test_cmd_extra_override_sample(self, prep_temp_pep, arg):
        """
        --command-extra-override should override the Sample.command_extra
        and Project.looper.command_extra attributes appeneded to the
        pipeline command
        """
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            config_data[SAMPLE_MODS_KEY][CONSTANT_KEY]["command_extra"] = arg
        stdout, stderr, rc = subp_exec(
            tp, "run", ["--command-extra-override='different'"]
        )
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_not_in_any_files(subs_list, arg)


class TestsLooperRunpBehavior:
    def test_looper_runp_basic(self, prep_temp_pep):
        """Verify looper runps in a basic case and return code is 0"""
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, "runp")
        print_standard_stream(stderr)
        assert rc == 0

    def test_looper_multi_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, "runp")
        assert "Jobs submitted: 2" in str(stderr)

    def test_looper_single_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            piface_path = os.path.join(os.path.dirname(tp), PIP.format("1"))
            config_data[LOOPER_KEY][CLI_KEY]["runp"][
                PIPELINE_INTERFACES_KEY
            ] = piface_path
        stdout, stderr, rc = subp_exec(tp, "runp")
        print_standard_stream(stderr)
        assert rc == 0
        assert "Jobs submitted: 2" not in str(stderr)
        assert "Jobs submitted: 1" in str(stderr)

    @pytest.mark.parametrize("arg", CMD_STRS)
    def test_cmd_extra_project(self, prep_temp_pep, arg):
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            config_data[LOOPER_KEY]["command_extra"] = arg
        stdout, stderr, rc = subp_exec(tp, "runp")
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_in_all_files(subs_list, arg)


class TestsLooperRunPreSubmissionHooks:
    def test_looper_basic_plugin(self, prep_temp_pep):
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, "run")
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        verify_filecount_in_dir(sd, ".yaml", 3)

    @pytest.mark.parametrize(
        "plugin,appendix",
        [
            ("looper.write_submission_yaml", "submission.yaml"),
            ("looper.write_sample_yaml_prj", "prj.yaml"),
            ("looper.write_sample_yaml_cwl", "cwl.yaml"),
        ],
    )
    def test_looper_other_plugins(self, prep_temp_pep, plugin, appendix):
        tp = prep_temp_pep
        for path in {
            piface.pipe_iface_file for piface in Project(tp).pipeline_interfaces
        }:
            with mod_yaml_data(path) as piface_data:
                piface_data[PRE_SUBMIT_HOOK_KEY][PRE_SUBMIT_PY_FUN_KEY] = [plugin]
        stdout, stderr, rc = subp_exec(tp, "run")
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        verify_filecount_in_dir(sd, appendix, 3)

    @pytest.mark.parametrize(
        "cmd",
        [
            "touch {looper.output_dir}/submission/{sample.sample_name}_test.txt; "
            "{%raw%}echo {}{%endraw%}"
        ],
    )
    def test_looper_command_templates_hooks(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        for path in {
            piface.pipe_iface_file for piface in Project(tp).pipeline_interfaces
        }:
            with mod_yaml_data(path) as piface_data:
                piface_data[PRE_SUBMIT_HOOK_KEY][PRE_SUBMIT_CMD_KEY] = [cmd]
        stdout, stderr, rc = subp_exec(tp, "run")
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        verify_filecount_in_dir(sd, "test.txt", 3)


class TestsLooperRunSubmissionScript:
    def test_looper_run_produces_submission_scripts(self, prep_temp_pep):
        tp = prep_temp_pep
        with open(tp, "r") as conf_file:
            config_data = safe_load(conf_file)
        outdir = config_data[LOOPER_KEY][OUTDIR_KEY]
        stdout, stderr, rc = subp_exec(tp, "run")
        sd = os.path.join(outdir, "submission")
        print_standard_stream(stderr)
        assert rc == 0
        verify_filecount_in_dir(sd, ".sub", 6)

    def test_looper_lumping(self, prep_temp_pep):
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, "run", ["--lumpn", "2"])
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        verify_filecount_in_dir(sd, ".sub", 4)

    def test_looper_limiting(self, prep_temp_pep):
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, "run", ["--limit", "2"])
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        verify_filecount_in_dir(sd, ".sub", 4)


class TestsLooperCompute:
    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_respects_pkg_selection(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, cmd, ["--package", "local"])
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_not_in_any_files(subs_list, "#SBATCH")

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_uses_cli_compute_options_spec(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(
            tp, cmd, ["--compute", "mem=12345", "--package", "slurm"]
        )
        sd = os.path.join(get_outdir(tp), "submission")
        print_standard_stream(stderr)
        assert rc == 0
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_in_all_files(subs_list, "#SBATCH --mem='12345'")

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_cli_yaml_settings_general(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        td = tempfile.mkdtemp()
        settings_file_path = os.path.join(td, "settings.yaml")
        with open(settings_file_path, "w") as sf:
            dump({"mem": "testin_mem"}, sf)
        stdout, stderr, rc = subp_exec(tp, cmd, ["--settings", settings_file_path])
        print_standard_stream(stderr)
        assert rc == 0

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_nonexistent_yaml_settings_disregarded(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        stdout, stderr, rc = subp_exec(tp, cmd, ["--settings", "niema.yaml"])
        print_standard_stream(stderr)
        assert rc == 0

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_cli_yaml_settings_passes_settings(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        td = tempfile.mkdtemp()
        settings_file_path = os.path.join(td, "settings.yaml")
        with open(settings_file_path, "w") as sf:
            dump({"mem": "testin_mem"}, sf)
        stdout, stderr, rc = subp_exec(
            tp, cmd, ["--settings", settings_file_path, "-p", "slurm"]
        )
        print_standard_stream(stderr)
        assert rc == 0
        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_in_all_files(subs_list, "testin_mem")

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_cli_compute_overwrites_yaml_settings_spec(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        td = tempfile.mkdtemp()
        settings_file_path = os.path.join(td, "settings.yaml")
        with open(settings_file_path, "w") as sf:
            dump({"mem": "testin_mem"}, sf)
        stdout, stderr, rc = subp_exec(
            tp,
            cmd,
            ["--settings", settings_file_path, "--compute", "mem=10", "-p", "slurm"],
        )
        print_standard_stream(stderr)
        assert rc == 0
        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_not_in_any_files(subs_list, "testin_mem")
