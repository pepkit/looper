import pytest
from peppy import Project

from looper.const import FLAGS
from looper.exceptions import PipestatConfigurationException
from tests.conftest import *
from looper.cli_looper import main


def _make_flags(cfg, type, count):
    p = Project(cfg)
    out_dir = p[CONFIG_KEY][LOOPER_KEY][OUTDIR_KEY]
    for s in p.samples[:count]:
        sf = os.path.join(out_dir, "results_pipeline", s[SAMPLE_NAME_ATTR])
        if not os.path.exists(sf):
            os.makedirs(sf)
        open(os.path.join(sf, type + ".flag"), "a").close()


class TestLooperPipestat:
    @pytest.mark.parametrize("cmd", ["report", "table", "check"])
    def test_fail_no_pipestat_config(self, prep_temp_pep, cmd):
        "report, table, and check should fail if pipestat is NOT configured."
        tp = prep_temp_pep
        x = test_args_expansion(tp, cmd)
        with pytest.raises(PipestatConfigurationException):
            main(test_args=x)

    @pytest.mark.parametrize("cmd", ["run"])
    def test_pipestat_configured(self, prep_temp_pep_pipestat, cmd):
        tp = prep_temp_pep_pipestat
        #td = tempfile.mkdtemp()
        #looper_consettings_file_path = os.path.join(td, "settings.yaml")
        # with mod_yaml_data(tp) as config_data:
        #     pifaces = config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][
        #         PIPELINE_INTERFACES_KEY
        #     ]
        #     config_data[SAMPLE_MODS_KEY][CONSTANT_KEY][
        #         PIPELINE_INTERFACES_KEY
        #     ] = pifaces[1]

        x = test_args_expansion(tp, cmd)

        try:
            result = main(test_args=x)
            #assert result[DEBUG_COMMANDS] != "6 of 6"
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))


class TestLooperCheck:
    @pytest.mark.skip(reason="Wait to deprecate CheckerOld")
    @pytest.mark.parametrize("flag_id", FLAGS)
    @pytest.mark.parametrize("count", list(range(2)))
    def test_check_works(self, prep_temp_pep, flag_id, count):
        """Verify that checking works"""
        tp = prep_temp_pep
        _make_flags(tp, flag_id, count)
        stdout, stderr, rc = subp_exec(tp, "check")
        assert rc == 0
        print_standard_stream(stderr)
        assert "{}: {}".format(flag_id.upper(), str(count)) in str(stderr)

    @pytest.mark.skip(reason="Wait to deprecate CheckerOld ")
    @pytest.mark.parametrize("flag_id", FLAGS)
    @pytest.mark.parametrize("count", list(range(2)))
    def test_check_multi(self, prep_temp_pep, flag_id, count):
        """Verify that checking works when multiple flags are created"""
        tp = prep_temp_pep
        _make_flags(tp, flag_id, count)
        _make_flags(tp, FLAGS[1], count)
        stdout, stderr, rc = subp_exec(tp, "check")
        assert rc == 0
        print_standard_stream(stderr)
        if flag_id != FLAGS[1]:
            assert "{}: {}".format(flag_id.upper(), str(count)) in str(stderr)

    @pytest.mark.skip(reason="Wait to deprecate CheckerOld")
    @pytest.mark.parametrize("flag_id", ["3333", "tonieflag", "bogus", "ms"])
    def test_check_bogus(self, prep_temp_pep, flag_id):
        """Verify that checking works when bogus flags are created"""
        tp = prep_temp_pep
        _make_flags(tp, flag_id, 1)
        stdout, stderr, rc = subp_exec(tp, "check")
        assert rc == 0
        print_standard_stream(stderr)
        for f in FLAGS:
            assert "{}: {}".format(f.upper(), "0") in str(stderr)
