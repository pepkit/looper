import pytest
from peppy.const import *
from yaml import dump

from looper.const import *
from looper.project import Project
from tests.conftest import *
from looper.utils import *
from looper.cli_pydantic import main

CMD_STRS = ["string", " --string", " --sjhsjd 212", "7867#$@#$cc@@"]


def test_cli(prep_temp_pep):
    tp = prep_temp_pep

    x = ["run", "--looper-config", tp, "--dry-run"]
    try:
        main(test_args=x)
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))


def is_connected():
    """Determines if local machine can connect to the internet."""
    import socket

    try:
        host = socket.gethostbyname("www.databio.org")
        socket.create_connection((host, 80), 2)
        return True
    except:
        pass
    return False


class TestLooperBothRuns:
    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_cfg_invalid(self, cmd):
        """Verify looper does not accept invalid cfg paths"""

        x = test_args_expansion(
            cmd, "--looper-config", "jdfskfds/dsjfklds/dsjklsf.yaml"
        )
        with pytest.raises(SystemExit):
            result = main(test_args=x)
            print(result)

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_cfg_required(self, cmd):
        """Verify looper does not accept invalid cfg paths"""

        x = test_args_expansion("", cmd)
        with pytest.raises(SystemExit):
            ff = main(test_args=x)
            print(ff)

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

        x = test_args_expansion(tp, cmd, arg)
        try:
            main(test_args=x)
        except Exception as err:
            raise pytest.fail(f"DID RAISE {err}")

        sd = os.path.join(get_outdir(tp), "submission")

        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_in_all_files(subs_list, arg[1])

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_unrecognized_args_not_passing(self, prep_temp_pep, cmd):
        tp = prep_temp_pep

        x = test_args_expansion(tp, cmd, ["--unknown-arg", "4"])
        with pytest.raises(SystemExit):
            main(test_args=x)


@pytest.mark.skipif(not is_connected(), reason="Test needs an internet connection")
class TestLooperRunBehavior:
    def test_looper_run_basic(self, prep_temp_pep):
        """Verify looper runs in a basic case and return code is 0"""
        tp = prep_temp_pep
        x = test_args_expansion(tp, "run")
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    def test_looper_multi_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        x = test_args_expansion(tp, "run")
        try:
            result = main(test_args=x)
            assert result[DEBUG_COMMANDS] == "6 of 6"
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    def test_looper_single_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep

        with mod_yaml_data(tp) as config_data:
            pifaces = config_data[PIPELINE_INTERFACES_KEY]
            config_data[PIPELINE_INTERFACES_KEY]["sample"] = pifaces["sample"][1]
            del config_data[PIPELINE_INTERFACES_KEY]["project"]

        x = test_args_expansion(tp, "run")
        try:
            result = main(test_args=x)
            assert result[DEBUG_COMMANDS] != "6 of 6"
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    def test_looper_var_templates(self, prep_temp_pep):
        tp = prep_temp_pep
        x = test_args_expansion(tp, "run")
        x.pop(-1)  # remove the --dry-run argument for this specific test

        try:
            # Test that {looper.piface_dir} is correctly rendered to a path which will show up in the final .sub file
            results = main(test_args=x)
            sd = os.path.join(get_outdir(tp), "submission")
            subs_list = [
                os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")
            ]
            assert_content_not_in_any_files(subs_list, "looper.piface_dir")
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    def test_looper_cli_pipeline(self, prep_temp_pep):
        """CLI-specified pipelines overwrite ones from config"""
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            pifaces = config_data[PIPELINE_INTERFACES_KEY]
            pi_pth = pifaces["sample"][1]
        x = test_args_expansion(tp, "run", ["--sample-pipeline-interfaces", pi_pth])
        try:
            result = main(test_args=x)

            assert result[DEBUG_COMMANDS] != "3 of 3"
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    def test_looper_no_pipeline(self, prep_temp_pep):
        """
        No jobs are submitted and proper log is produced when there are no
        valid pifaces defined
        """
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            del config_data[PIPELINE_INTERFACES_KEY]
        x = test_args_expansion(tp, "run")
        try:
            result = main(test_args=x)
            assert result[DEBUG_JOBS] == 0
            assert "No pipeline interfaces defined" in list(result.keys())
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    def test_looper_pipeline_not_found(self, prep_temp_pep):
        """
        Piface is ignored when it does not exist
        """
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            config_data[PIPELINE_INTERFACES_KEY]["sample"] = ["bogus"]
        x = test_args_expansion(tp, "run")
        try:
            result = main(test_args=x)

            assert result[DEBUG_JOBS] == 0
            assert "No pipeline interfaces defined" in result.keys()
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    def test_looper_sample_name_whitespace(self, prep_temp_pep):
        """
        Piface is ignored when it does not exist
        """
        tp = prep_temp_pep

        imply_whitespace = [
            {
                IMPLIED_IF_KEY: {"sample_name": "sample1"},
                IMPLIED_THEN_KEY: {"sample_name": "sample whitespace"},
            }
        ]

        project_config_path = get_project_config_path(tp)

        with mod_yaml_data(project_config_path) as project_config_data:
            project_config_data[SAMPLE_MODS_KEY][IMPLIED_KEY] = imply_whitespace

        x = test_args_expansion(tp, "run")
        with pytest.raises(Exception):
            result = main(test_args=x)
            expected_prefix = "Short-circuiting due to validation error"
            assert expected_prefix in str(result[DEBUG_EIDO_VALIDATION])

    def test_looper_toggle(self, prep_temp_pep):
        """
        If all samples have toggle attr set to 0, no jobs are submitted
        """
        tp = prep_temp_pep
        project_config_path = get_project_config_path(tp)

        with mod_yaml_data(project_config_path) as project_config_data:
            project_config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][SAMPLE_TOGGLE_ATTR] = 0

        x = test_args_expansion(tp, "run")
        x.pop(-1)  # remove dry run for this test

        try:
            result = main(test_args=x)
            assert result[DEBUG_JOBS] == 0
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    @pytest.mark.parametrize("arg", CMD_STRS)
    def test_cmd_extra_sample(self, prep_temp_pep, arg):
        """
        string set by sample_modifiers in Sample.command_extra should be
        appended to the pipelinecommand
        """
        tp = prep_temp_pep
        project_config_path = get_project_config_path(tp)

        with mod_yaml_data(project_config_path) as project_config_data:
            project_config_data[SAMPLE_MODS_KEY][CONSTANT_KEY]["command_extra"] = arg
        x = test_args_expansion(tp, "run")
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
        sd = os.path.join(get_outdir(tp), "submission")
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
        project_config_path = get_project_config_path(tp)

        with mod_yaml_data(project_config_path) as project_config_data:
            project_config_data[SAMPLE_MODS_KEY][CONSTANT_KEY]["command_extra"] = arg

        x = test_args_expansion(tp, "run", ["--command-extra-override='different'"])
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_not_in_any_files(subs_list, arg)


@pytest.mark.skip(reason="prep_temp_pep needs to be rewritten")
class TestLooperRunpBehavior:
    def test_looper_runp_basic(self, prep_temp_pep):
        """Verify looper runps in a basic case and return code is 0"""
        tp = prep_temp_pep
        x = test_args_expansion(tp, "runp")
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    def test_looper_multi_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        x = test_args_expansion(tp, "runp")
        try:
            result = main(test_args=x)
            assert result[DEBUG_JOBS] == 2
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    def test_looper_single_pipeline(self, prep_temp_pep):
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            piface_path = os.path.join(os.path.dirname(tp), PIP.format("1"))
            config_data[LOOPER_KEY][CLI_KEY]["runp"][
                PIPELINE_INTERFACES_KEY
            ] = piface_path
        x = test_args_expansion(tp, "runp")
        try:
            result = main(test_args=x)
            assert result[DEBUG_JOBS] != 2
            assert result[DEBUG_JOBS] == 1
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    @pytest.mark.parametrize("arg", CMD_STRS)
    def test_cmd_extra_project(self, prep_temp_pep, arg):
        tp = prep_temp_pep
        with mod_yaml_data(tp) as config_data:
            config_data[LOOPER_KEY]["command_extra"] = arg
        x = test_args_expansion(tp, "runp")
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_in_all_files(subs_list, arg)


@pytest.mark.skip(reason="prep_temp_pep needs to be rewritten")
class TestLooperRunPreSubmissionHooks:
    def test_looper_basic_plugin(self, prep_temp_pep):
        tp = prep_temp_pep
        x = test_args_expansion(tp, "run")
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
        sd = os.path.join(get_outdir(tp), "submission")
        verify_filecount_in_dir(sd, ".yaml", 3)

    @pytest.mark.parametrize(
        "plugin,appendix",
        [
            ("looper.write_submission_yaml", "submission.yaml"),
            ("looper.write_sample_yaml_prj", "prj.yaml"),
            ("looper.write_sample_yaml_cwl", "cwl.yaml"),
        ],
    )
    @pytest.mark.skipif(not is_connected(), reason="Test needs an internet connection")
    def test_looper_other_plugins(self, prep_temp_pep, plugin, appendix):
        tp = prep_temp_pep
        for path in {
            piface.pipe_iface_file for piface in Project(tp).pipeline_interfaces
        }:
            with mod_yaml_data(path) as piface_data:
                piface_data[PRE_SUBMIT_HOOK_KEY][PRE_SUBMIT_PY_FUN_KEY] = [plugin]

        x = test_args_expansion(tp, "run")
        try:
            main(test_args=x)
        except Exception as err:
            raise pytest.fail(f"DID RAISE {err}")
        sd = os.path.join(get_outdir(tp), "submission")
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
        x = test_args_expansion(tp, "run")
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
        sd = os.path.join(get_outdir(tp), "submission")
        verify_filecount_in_dir(sd, "test.txt", 3)


@pytest.mark.skip(reason="prep_temp_pep needs to be rewritten")
class TestLooperRunSubmissionScript:
    def test_looper_run_produces_submission_scripts(self, prep_temp_pep):
        tp = prep_temp_pep
        with open(tp, "r") as conf_file:
            config_data = safe_load(conf_file)
        outdir = config_data[LOOPER_KEY][OUTDIR_KEY]
        x = test_args_expansion(tp, "run")
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
        sd = os.path.join(outdir, "submission")
        verify_filecount_in_dir(sd, ".sub", 6)

    def test_looper_lumping(self, prep_temp_pep):
        tp = prep_temp_pep
        x = test_args_expansion(tp, "run", ["--lump-n", "2"])
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
        sd = os.path.join(get_outdir(tp), "submission")
        verify_filecount_in_dir(sd, ".sub", 4)

    def test_looper_lumping_jobs(self, prep_temp_pep):
        tp = prep_temp_pep
        x = test_args_expansion(tp, "run", ["--lump-j", "1"])
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
        sd = os.path.join(get_outdir(tp), "submission")
        verify_filecount_in_dir(sd, ".sub", 2)

    def test_looper_lumping_jobs_negative(self, prep_temp_pep):
        tp = prep_temp_pep
        x = test_args_expansion(tp, "run", ["--lump-j", "-1"])

        with pytest.raises(ValueError):
            main(test_args=x)

    def test_looper_limiting(self, prep_temp_pep):
        tp = prep_temp_pep
        x = test_args_expansion(tp, "run", ["--limit", "2"])
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
        sd = os.path.join(get_outdir(tp), "submission")
        verify_filecount_in_dir(sd, ".sub", 4)


@pytest.mark.skip(reason="prep_temp_pep needs to be rewritten")
class TestLooperCompute:
    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_respects_pkg_selection(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        x = test_args_expansion(tp, cmd, ["--package", "local"])
        try:
            main(test_args=x)
        except Exception as err:
            raise pytest.fail(f"DID RAISE {err}")
        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_not_in_any_files(subs_list, "#SBATCH")

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_looper_uses_cli_compute_options_spec(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        x = test_args_expansion(
            tp, cmd, ["--compute", "mem=12345", "--package", "slurm"]
        )
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_in_all_files(subs_list, "#SBATCH --mem='12345'")

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_cli_yaml_settings_general(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        td = tempfile.mkdtemp()
        settings_file_path = os.path.join(td, "settings.yaml")
        with open(settings_file_path, "w") as sf:
            dump({"mem": "testin_mem"}, sf)
        x = test_args_expansion(tp, cmd, ["--settings", settings_file_path])
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_nonexistent_yaml_settings_disregarded(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        x = test_args_expansion(tp, cmd, ["--settings", "niema.yaml"])
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_cli_yaml_settings_passes_settings(self, prep_temp_pep, cmd):
        tp = prep_temp_pep
        td = tempfile.mkdtemp()
        settings_file_path = os.path.join(td, "settings.yaml")
        with open(settings_file_path, "w") as sf:
            dump({"mem": "testin_mem"}, sf)

        x = test_args_expansion(
            tp, cmd, ["--settings", settings_file_path, "-p", "slurm"]
        )
        try:
            main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
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
        x = test_args_expansion(
            tp,
            cmd,
            ["--settings", settings_file_path, "--compute", "mem=10", "-p", "slurm"],
        )
        try:
            main(test_args=x)
        except Exception as err:
            raise pytest.fail(f"DID RAISE {err}")

        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert_content_not_in_any_files(subs_list, "testin_mem")


class TestLooperConfig:
    @pytest.mark.skip(reason="prep_temp_pep needs to be rewritten")
    @pytest.mark.parametrize("cmd", ["run", "runp"])
    def test_init_config_file(self, prep_temp_pep, cmd, dotfile_path):
        tp = prep_temp_pep
        x = test_args_expansion(tp, "init")
        try:
            result = main(test_args=x)
        except Exception as err:
            raise pytest.fail(f"DID RAISE: {err}")
        assert result == 0
        assert_content_in_all_files(dotfile_path, tp)
        x = test_args_expansion(tp, cmd)
        try:
            result = main(test_args=x)
        except Exception as err:
            raise pytest.fail(f"DID RAISE {err}")


class TestLooperPEPhub:
    @pytest.mark.parametrize(
        "pep_path",
        [
            "pephub::some/registry:path",
            "different/registry:path",
            "default/tag",
        ],
    )
    def test_pephub_registry_path_recognition(self, pep_path):
        assert is_registry_path(pep_path) is True

    @pytest.mark.parametrize(
        "pep_path",
        [
            "some/path/to/pep.yaml",
            "different/path.yaml",
            "default/path/to/file/without/yaml",
            "file_in_folder.yaml",
            "not_yaml_file",
        ],
    )
    def test_config_recognition(self, pep_path):
        assert is_registry_path(pep_path) is False

    def test_init_project_using_dict(self, prep_temp_config_with_pep):
        """Verify looper runs using pephub in a basic case and return code is 0"""
        raw_pep, piface1s_path = prep_temp_config_with_pep
        init_project = Project(
            runp=True, project_dict=raw_pep, sample_pipeline_interfaces=piface1s_path
        )

        assert len(init_project.pipeline_interfaces) == 3
