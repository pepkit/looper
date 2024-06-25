import os.path

import pytest
from peppy import Project

from looper.exceptions import PipestatConfigurationException, MisconfigurationException
from tests.conftest import *
from looper.cli_pydantic import main
import pandas as pd


def _make_flags_pipestat(cfg, type, pipeline_name):
    """This makes flags for projects where pipestat is configured and used"""

    # get flag dir from .looper.yaml
    with open(cfg, "r") as f:
        looper_cfg_data = safe_load(f)
        flag_dir = looper_cfg_data[PIPESTAT_KEY]["flag_file_dir"]

    flag_dir = os.path.join(os.path.dirname(cfg), flag_dir)
    # get samples from the project config via Peppy
    project_config_path = get_project_config_path(cfg)
    p = Project(project_config_path)

    for s in p.samples:
        sf = flag_dir
        if not os.path.exists(sf):
            os.makedirs(sf)
        flag_path = os.path.join(
            sf, pipeline_name + "_" + s.sample_name + "_" + type + ".flag"
        )
        with open(flag_path, "w") as f:
            f.write(type)


def _make_flags(cfg, type, pipeline_name):
    """This makes flags for projects where pipestat is NOT configured"""

    # get flag dir from .looper.yaml
    with open(cfg, "r") as f:
        looper_cfg_data = safe_load(f)
        output_dir = looper_cfg_data[OUTDIR_KEY]

    output_dir = os.path.join(os.path.dirname(cfg), output_dir)
    # get samples from the project config via Peppy
    project_config_path = get_project_config_path(cfg)
    p = Project(project_config_path)

    for s in p.samples:
        # Make flags in sample subfolder, e.g /tmp/tmphqxdmxnl/advanced/results/results_pipeline/sample1
        sf = os.path.join(output_dir, "results_pipeline", s.sample_name)
        if not os.path.exists(sf):
            os.makedirs(sf)
        flag_path = os.path.join(
            sf, pipeline_name + "_" + s.sample_name + "_" + type + ".flag"
        )
        with open(flag_path, "w") as f:
            f.write(type)


class TestLooperPipestat:

    @pytest.mark.parametrize("cmd", ["report", "table", "check"])
    def test_fail_no_pipestat_config(self, prep_temp_pep, cmd):
        "report, table, and check should fail if pipestat is NOT configured."
        tp = prep_temp_pep
        x = [cmd, "--config", tp]
        with pytest.raises(PipestatConfigurationException):
            main(test_args=x)

    @pytest.mark.parametrize("cmd", ["run", "runp", "report", "table", "check"])
    def test_pipestat_configured(self, prep_temp_pep_pipestat, cmd):
        tp = prep_temp_pep_pipestat

        if cmd in ["run", "runp"]:
            x = [cmd, "--config", tp, "--dry-run"]
        else:
            # Not every command supports dry run
            x = [cmd, "--config", tp]

        try:
            result = main(test_args=x)
            if cmd == "run":
                assert result["Pipestat compatible"] is True
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))


class TestLooperRerun:
    @pytest.mark.parametrize(
        "flags", [FLAGS[2], FLAGS[3]]
    )  # Waiting and Failed flags should work
    @pytest.mark.parametrize("pipeline_name", ["example_pipestat_pipeline"])
    def test_pipestat_rerun(self, prep_temp_pep_pipestat, pipeline_name, flags):
        """Verify that rerun works with either failed or waiting flags"""
        tp = prep_temp_pep_pipestat
        _make_flags_pipestat(tp, flags, pipeline_name)
        path_to_looper_config = prep_temp_pep_pipestat
        pipestat_dir = os.path.dirname(path_to_looper_config)

        # open up the project config and replace the derived attributes with the path to the data. In a way, this simulates using the environment variables.
        pipestat_project_file = get_project_config_path(path_to_looper_config)

        pipestat_pipeline_interface_file = os.path.join(
            pipestat_dir, "pipeline_pipestat/pipeline_interface.yaml"
        )

        with open(pipestat_project_file, "r") as f:
            pipestat_project_data = safe_load(f)

        pipestat_project_data["sample_modifiers"]["derive"]["sources"]["source1"] = (
            os.path.join(pipestat_dir, "data/{sample_name}.txt")
        )

        with open(pipestat_pipeline_interface_file, "r") as f:
            pipestat_piface_data = safe_load(f)

        pipeline_name = pipestat_piface_data["pipeline_name"]

        with open(pipestat_project_file, "w") as f:
            dump(pipestat_project_data, f)

        x = ["rerun", "--config", tp]
        try:
            result = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        assert result["Jobs submitted"] == 2

    @pytest.mark.parametrize(
        "flags", [FLAGS[2], FLAGS[3]]
    )  # Waiting and Failed flags should work
    @pytest.mark.parametrize("pipeline_name", ["PIPELINE1"])
    def test_rerun_no_pipestat(self, prep_temp_pep, pipeline_name, flags):
        """Verify that rerun works with either failed or waiting flags"""
        tp = prep_temp_pep
        _make_flags(tp, flags, pipeline_name)

        x = ["rerun", "--config", tp]
        try:
            result = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        # Only 3 failed flags exist for PIPELINE1, so only 3 samples should be submitted
        assert result["Jobs submitted"] == 3


class TestLooperCheck:
    @pytest.mark.parametrize("flag_id", FLAGS)
    @pytest.mark.parametrize(
        "pipeline_name", ["example_pipestat_pipeline"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_check_works(self, prep_temp_pep_pipestat, flag_id, pipeline_name):
        """Verify that checking works"""
        tp = prep_temp_pep_pipestat
        _make_flags_pipestat(tp, flag_id, pipeline_name)

        x = ["check", "--config", tp]

        try:
            results = main(test_args=x)
            result_key = list(results.keys())[0]
            for k, v in results[result_key].items():
                assert v == flag_id
            print(results)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    @pytest.mark.parametrize("flag_id", FLAGS)
    @pytest.mark.parametrize("pipeline_name", ["example_pipestat_pipeline"])
    def test_check_multi(self, prep_temp_pep_pipestat, flag_id, pipeline_name):
        """Verify that checking works when multiple flags are created"""
        tp = prep_temp_pep_pipestat
        _make_flags_pipestat(tp, flag_id, pipeline_name)
        _make_flags_pipestat(tp, FLAGS[1], pipeline_name)

        x = ["check", "--config", tp]
        # Multiple flag files SHOULD cause pipestat to throw an assertion error
        if flag_id != FLAGS[1]:
            with pytest.raises(AssertionError):
                main(test_args=x)

    @pytest.mark.parametrize("flag_id", ["3333", "tonieflag", "bogus", "ms"])
    @pytest.mark.parametrize("pipeline_name", ["example_pipestat_pipeline"])
    def test_check_bogus(self, prep_temp_pep_pipestat, flag_id, pipeline_name):
        """Verify that checking works when bogus flags are created"""
        tp = prep_temp_pep_pipestat
        _make_flags_pipestat(tp, flag_id, pipeline_name)

        x = ["check", "--config", tp]
        try:
            results = main(test_args=x)
            result_key = list(results.keys())[0]
            for k, v in results[result_key].items():
                assert v == flag_id
            print(results)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))


class TestSelector:
    @pytest.mark.parametrize("flag_id", ["completed"])
    @pytest.mark.parametrize(
        "pipeline_name", ["example_pipestat_pipeline"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_selecting_flags_works(
        self, prep_temp_pep_pipestat, flag_id, pipeline_name
    ):
        """Verify selecting on a single flag"""
        tp = prep_temp_pep_pipestat
        project_config_path = get_project_config_path(tp)
        p = Project(project_config_path)

        # get flag dir from .looper.yaml
        with open(tp, "r") as f:
            looper_cfg_data = safe_load(f)
            flag_dir = looper_cfg_data[PIPESTAT_KEY]["flag_file_dir"]

        flag_dir = os.path.join(os.path.dirname(tp), flag_dir)

        count = 0
        for s in p.samples:
            sf = flag_dir
            if not os.path.exists(sf):
                os.makedirs(sf)
            flag_path = os.path.join(
                sf, pipeline_name + "_" + s.sample_name + "_" + FLAGS[count] + ".flag"
            )
            with open(flag_path, "w") as f:
                f.write(FLAGS[count])
            count += 1

        x = ["run", "--config", tp, "--sel-flag", "completed", "--dry-run"]

        try:
            results = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]
        assert len(subs_list) == 1

    @pytest.mark.parametrize("flag_id", ["completed"])
    @pytest.mark.parametrize(
        "pipeline_name", ["example_pipestat_pipeline"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_excluding_flags_works(
        self, prep_temp_pep_pipestat, flag_id, pipeline_name
    ):
        """Verify that excluding a single flag works"""
        tp = prep_temp_pep_pipestat
        project_config_path = get_project_config_path(tp)
        p = Project(project_config_path)

        # get flag dir from .looper.yaml
        with open(tp, "r") as f:
            looper_cfg_data = safe_load(f)
            flag_dir = looper_cfg_data[PIPESTAT_KEY]["flag_file_dir"]

        flag_dir = os.path.join(os.path.dirname(tp), flag_dir)
        count = 0
        for s in p.samples:
            sf = flag_dir
            if not os.path.exists(sf):
                os.makedirs(sf)
            flag_path = os.path.join(
                sf, pipeline_name + "_" + s.sample_name + "_" + FLAGS[count] + ".flag"
            )
            with open(flag_path, "w") as f:
                f.write(FLAGS[count])
            count += 1

        x = ["run", "--config", tp, "--exc-flag", "running", "--dry-run"]

        try:
            results = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]

        assert len(subs_list) == 1

    @pytest.mark.parametrize("flag_id", ["completed"])
    @pytest.mark.parametrize(
        "pipeline_name", ["example_pipestat_pipeline"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_excluding_multi_flags_works(
        self, prep_temp_pep_pipestat, flag_id, pipeline_name
    ):
        """Verify excluding multi flags"""
        tp = prep_temp_pep_pipestat
        project_config_path = get_project_config_path(tp)
        p = Project(project_config_path)

        # get flag dir from .looper.yaml
        with open(tp, "r") as f:
            looper_cfg_data = safe_load(f)
            flag_dir = looper_cfg_data[PIPESTAT_KEY]["flag_file_dir"]

        flag_dir = os.path.join(os.path.dirname(tp), flag_dir)

        count = 0
        for s in p.samples:
            sf = flag_dir
            if not os.path.exists(sf):
                os.makedirs(sf)
            flag_path = os.path.join(
                sf, pipeline_name + "_" + s.sample_name + "_" + FLAGS[count] + ".flag"
            )
            with open(flag_path, "w") as f:
                f.write(FLAGS[count])
            count += 1

        x = [
            "run",
            "--config",
            tp,
            "--exc-flag",
            "completed",
            "running",
            "--dry-run",
        ]

        try:
            results = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        # No submission directory will exist because both samples are excluded.
        sd = os.path.join(get_outdir(tp), "submission")
        assert os.path.exists(sd) is False

    @pytest.mark.parametrize("flag_id", ["completed"])
    @pytest.mark.parametrize(
        "pipeline_name", ["example_pipestat_pipeline"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_selecting_multi_flags_works(
        self, prep_temp_pep_pipestat, flag_id, pipeline_name
    ):
        """Verify selecting multiple flags"""
        tp = prep_temp_pep_pipestat
        project_config_path = get_project_config_path(tp)
        p = Project(project_config_path)

        # get flag dir from .looper.yaml
        with open(tp, "r") as f:
            looper_cfg_data = safe_load(f)
            flag_dir = looper_cfg_data[PIPESTAT_KEY]["flag_file_dir"]

        flag_dir = os.path.join(os.path.dirname(tp), flag_dir)
        count = 0
        for s in p.samples:
            sf = flag_dir
            if not os.path.exists(sf):
                os.makedirs(sf)
            flag_path = os.path.join(
                sf, pipeline_name + "_" + s.sample_name + "_" + FLAGS[count] + ".flag"
            )
            with open(flag_path, "w") as f:
                f.write(FLAGS[count])
            count += 1

        x = [
            "run",
            "--dry-run",
            "--config",
            tp,
            "--sel-flag",
            "completed",
            "running",
        ]

        try:
            results = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]

        assert len(subs_list) == 2

    @pytest.mark.parametrize("flag_id", ["completed"])
    @pytest.mark.parametrize(
        "pipeline_name", ["example_pipestat_pipeline"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_selecting_attr_and_flags_works(
        self, prep_temp_pep_pipestat_advanced, flag_id, pipeline_name
    ):
        """Verify selecting via attr and flags"""

        tp = prep_temp_pep_pipestat_advanced
        project_config_path = get_project_config_path(tp)
        p = Project(project_config_path)

        # get flag dir from .looper.yaml
        with open(tp, "r") as f:
            looper_cfg_data = safe_load(f)
            flag_dir = looper_cfg_data[PIPESTAT_KEY]["flag_file_dir"]

        flag_dir = os.path.join(os.path.dirname(tp), flag_dir)
        count = 0
        for s in p.samples:
            sf = flag_dir
            if not os.path.exists(sf):
                os.makedirs(sf)
            flag_path = os.path.join(
                sf, pipeline_name + "_" + s.sample_name + "_" + FLAGS[count] + ".flag"
            )
            with open(flag_path, "w") as f:
                f.write(FLAGS[count])
            count += 1

        x = [
            "run",
            "--dry-run",
            "--config",
            tp,
            "--sel-flag",
            "completed",
            "--sel-attr",
            "protocol",
            "--sel-incl",
            "PROTO1",
        ]

        try:
            results = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]

        assert len(subs_list) == 1

    @pytest.mark.parametrize("flag_id", ["completed"])
    @pytest.mark.parametrize(
        "pipeline_name", ["example_pipestat_pipeline"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_excluding_attr_and_flags_works(
        self, prep_temp_pep_pipestat_advanced, flag_id, pipeline_name
    ):
        """Verify excluding via attr and flags"""
        tp = prep_temp_pep_pipestat_advanced
        project_config_path = get_project_config_path(tp)
        p = Project(project_config_path)

        # get flag dir from .looper.yaml
        with open(tp, "r") as f:
            looper_cfg_data = safe_load(f)
            flag_dir = looper_cfg_data[PIPESTAT_KEY]["flag_file_dir"]

        flag_dir = os.path.join(os.path.dirname(tp), flag_dir)
        count = 0
        for s in p.samples:
            sf = flag_dir
            if not os.path.exists(sf):
                os.makedirs(sf)
            flag_path = os.path.join(
                sf, pipeline_name + "_" + s.sample_name + "_" + FLAGS[count] + ".flag"
            )
            with open(flag_path, "w") as f:
                f.write(FLAGS[count])
            count += 1

        x = [
            "run",
            "--dry-run",
            "--config",
            tp,
            "--exc-flag",
            "completed",
            "--sel-attr",
            "protocol",
            "--sel-incl",
            "PROTO1",
            "PROTO2",
        ]

        try:
            results = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]

        assert len(subs_list) == 2

    @pytest.mark.parametrize("flag_id", ["completed"])
    @pytest.mark.parametrize(
        "pipeline_name", ["example_pipestat_pipeline"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_excluding_toggle_attr(
        self, prep_temp_pep_pipestat_advanced, flag_id, pipeline_name
    ):
        """Verify excluding based on toggle attr"""
        tp = prep_temp_pep_pipestat_advanced
        project_config_path = get_project_config_path(tp)
        p = Project(project_config_path)

        # get flag dir from .looper.yaml
        with open(tp, "r") as f:
            looper_cfg_data = safe_load(f)
            flag_dir = looper_cfg_data[PIPESTAT_KEY]["flag_file_dir"]

        # Manually add a toggle column to the PEP for this specific test
        sample_csv = os.path.join(
            os.path.dirname(project_config_path), "annotation_sheet.csv"
        )
        df = pd.read_csv(sample_csv)
        df["toggle"] = 1
        df.to_csv(sample_csv, index=False)

        flag_dir = os.path.join(os.path.dirname(tp), flag_dir)
        count = 0
        for s in p.samples:
            sf = flag_dir
            if not os.path.exists(sf):
                os.makedirs(sf)
            flag_path = os.path.join(
                sf, pipeline_name + "_" + s.sample_name + "_" + FLAGS[count] + ".flag"
            )
            with open(flag_path, "w") as f:
                f.write(FLAGS[count])
            count += 1

        x = [
            "run",
            "--dry-run",
            "--config",
            tp,
            "--sel-attr",
            "toggle",
            "--sel-excl",
            "1",
        ]

        try:
            results = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        with pytest.raises(FileNotFoundError):
            # No samples submitted, thus no sub dir
            sd = os.path.join(get_outdir(tp), "submission")
            subs_list = [
                os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")
            ]

    @pytest.mark.parametrize("flag_id", ["completed"])
    @pytest.mark.parametrize(
        "pipeline_name", ["example_pipestat_pipeline"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_including_toggle_attr(
        self, prep_temp_pep_pipestat_advanced, flag_id, pipeline_name
    ):
        """Verify including based on toggle attr"""

        tp = prep_temp_pep_pipestat_advanced
        project_config_path = get_project_config_path(tp)
        p = Project(project_config_path)

        # get flag dir from .looper.yaml
        with open(tp, "r") as f:
            looper_cfg_data = safe_load(f)
            flag_dir = looper_cfg_data[PIPESTAT_KEY]["flag_file_dir"]

        # Manually add a toggle column to the PEP for this specific test
        sample_csv = os.path.join(
            os.path.dirname(project_config_path), "annotation_sheet.csv"
        )
        df = pd.read_csv(sample_csv)
        df["toggle"] = 1
        df.to_csv(sample_csv, index=False)

        flag_dir = os.path.join(os.path.dirname(tp), flag_dir)
        count = 0
        for s in p.samples:
            sf = flag_dir
            if not os.path.exists(sf):
                os.makedirs(sf)
            flag_path = os.path.join(
                sf, pipeline_name + "_" + s.sample_name + "_" + FLAGS[count] + ".flag"
            )
            with open(flag_path, "w") as f:
                f.write(FLAGS[count])
            count += 1

        x = [
            "run",
            "--dry-run",
            "--config",
            tp,
            "--sel-attr",
            "toggle",
            "--sel-incl",
            "1",
        ]

        try:
            results = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        sd = os.path.join(get_outdir(tp), "submission")
        subs_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".sub")]

        assert len(subs_list) == 3


class TestLooperInspect:
    @pytest.mark.parametrize("cmd", ["inspect"])
    def test_inspect_config(self, prep_temp_pep, cmd):
        "Checks inspect command"
        tp = prep_temp_pep
        x = [cmd, "--config", tp]
        try:
            results = main(test_args=x)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    @pytest.mark.parametrize("cmd", ["inspect"])
    def test_inspect_no_config_found(self, cmd):
        "Checks inspect command"
        x = [cmd]
        with pytest.raises(MisconfigurationException):
            results = main(test_args=x)
