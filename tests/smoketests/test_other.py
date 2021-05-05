import pytest
from peppy import Project

from looper.const import FLAGS
from tests.smoketests.conftest import *


def _make_flags(cfg, type, count):
    p = Project(cfg)
    out_dir = p[CONFIG_KEY][LOOPER_KEY][OUTDIR_KEY]
    for s in p.samples[:count]:
        sf = os.path.join(out_dir, "results_pipeline", s[SAMPLE_NAME_ATTR])
        if not os.path.exists(sf):
            os.makedirs(sf)
        open(os.path.join(sf, type + ".flag"), "a").close()


class LooperCheckTests:
    @pytest.mark.parametrize("flag_id", FLAGS)
    @pytest.mark.parametrize("count", list(range(2)))
    def test_check_works(self, prep_temp_pep, flag_id, count):
        """Verify that checking works"""
        tp = prep_temp_pep
        _make_flags(tp, flag_id, count)
        stdout, stderr, rc = subp_exec(tp, "check")
        assert rc == 0
        print(stderr)
        assert "{}: {}".format(flag_id.upper(), str(count)) in stderr

    @pytest.mark.parametrize("flag_id", FLAGS)
    @pytest.mark.parametrize("count", list(range(2)))
    def test_check_multi(self, prep_temp_pep, flag_id, count):
        """Verify that checking works when multiple flags are created"""
        tp = prep_temp_pep
        _make_flags(tp, flag_id, count)
        _make_flags(tp, FLAGS[1], count)
        stdout, stderr, rc = subp_exec(tp, "check")
        assert rc == 0
        print(stderr)
        if flag_id != FLAGS[1]:
            assert "{}: {}".format(flag_id.upper(), str(count)) in stderr

    @pytest.mark.parametrize("flag_id", ["3333", "tonieflag", "bogus", "ms"])
    def test_check_bogus(self, prep_temp_pep, flag_id):
        """Verify that checking works when bogus flags are created"""
        tp = prep_temp_pep
        _make_flags(tp, flag_id, 1)
        stdout, stderr, rc = subp_exec(tp, "check")
        assert rc == 0
        print(stderr)
        for f in FLAGS:
            assert "{}: {}".format(f.upper(), "0") in stderr
