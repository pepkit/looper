import pytest
from peppy import Project

from looper.const import FLAGS
from looper.exceptions import PipestatConfigurationException
from tests.conftest import *
from looper.cli_looper import main


def _make_flags(cfg, type, pipeline_name):
    p = Project(cfg)
    out_dir = p[CONFIG_KEY][LOOPER_KEY][OUTDIR_KEY]
    print(p.samples)
    for s in p.samples:
        sf = os.path.join(out_dir, "results_pipeline")
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
        x = test_args_expansion(tp, cmd)
        with pytest.raises(PipestatConfigurationException):
            main(test_args=x)

    @pytest.mark.parametrize("cmd", ["run", "runp", "report", "table", "check"])
    def test_pipestat_configured(self, prep_temp_pep_pipestat, cmd):
        tp = prep_temp_pep_pipestat

        x = [cmd, "-d", "--looper-config", tp]

        try:
            result = main(test_args=x)
            if cmd == "run":
                assert result["Pipestat compatible"] is True
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))


class TestLooperCheck:
    @pytest.mark.parametrize("flag_id", FLAGS)
    @pytest.mark.parametrize(
        "pipeline_name", ["test_pipe"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_check_works(self, prep_temp_pep_pipestat, flag_id, pipeline_name):
        """Verify that checking works"""
        tp = prep_temp_pep_pipestat
        _make_flags(tp, flag_id, pipeline_name)

        x = ["check", "-d", "--looper-config", tp]

        try:
            results = main(test_args=x)
            result_key = list(results.keys())[0]
            for k, v in results[result_key].items():
                assert v == flag_id
            print(results)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

    @pytest.mark.parametrize("flag_id", FLAGS)
    @pytest.mark.parametrize("pipeline_name", ["test_pipe"])
    def test_check_multi(self, prep_temp_pep_pipestat, flag_id, pipeline_name):
        """Verify that checking works when multiple flags are created"""
        tp = prep_temp_pep_pipestat
        _make_flags(tp, flag_id, pipeline_name)
        _make_flags(tp, FLAGS[1], pipeline_name)

        x = ["check", "-d", "--looper-config", tp]
        # Multiple flag files SHOULD cause pipestat to throw an assertion error
        if flag_id != FLAGS[1]:
            with pytest.raises(AssertionError):
                main(test_args=x)

    @pytest.mark.parametrize("flag_id", ["3333", "tonieflag", "bogus", "ms"])
    @pytest.mark.parametrize("pipeline_name", ["test_pipe"])
    def test_check_bogus(self, prep_temp_pep_pipestat, flag_id, pipeline_name):
        """Verify that checking works when bogus flags are created"""
        tp = prep_temp_pep_pipestat
        _make_flags(tp, flag_id, pipeline_name)

        x = ["check", "-d", "--looper-config", tp]
        try:
            results = main(test_args=x)
            result_key = list(results.keys())[0]
            for k, v in results[result_key].items():
                assert v == flag_id
            print(results)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

class TestSelector:
    @pytest.mark.parametrize("flag_id", FLAGS)
    @pytest.mark.parametrize(
        "pipeline_name", ["PIPELINE1"]
    )  # This is given in the pipestat_output_schema.yaml
    def test_selecting_works(self, prep_temp_pep_pipestat, flag_id, pipeline_name):
        """Verify that checking works"""
        tp = prep_temp_pep_pipestat
        #_make_flags(tp, flag_id, pipeline_name)
        p = Project(tp)
        out_dir = p[CONFIG_KEY][LOOPER_KEY][OUTDIR_KEY]
        count = 0
        for s in p.samples:
            sf = os.path.join(out_dir, "results_pipeline")
            if not os.path.exists(sf):
                os.makedirs(sf)
            flag_path = os.path.join(
                sf, pipeline_name + "_" + s.sample_name + "_" + FLAGS[count] + ".flag"
            )
            with open(flag_path, "w") as f:
                f.write(FLAGS[count])
            count += 1

        # SAMPLE_SELECTION_FLAG_OPTNAME = "sel-flag"
        # SAMPLE_EXCLUSION_FLAG_OPTNAME = "exc-flag"
        x = ["run", "-d", "--looper-config", tp, "--sel-flag", ['failed']]

        try:
            results = main(test_args=x)
            # result_key = list(results.keys())[0]
            # for k, v in results[result_key].items():
            #     assert v == flag_id
            print(results)
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))