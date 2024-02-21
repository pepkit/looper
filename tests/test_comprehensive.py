import pytest
from peppy.const import *
from yaml import dump

from looper.const import *
from looper.project import Project
from tests.conftest import *
from looper.utils import *
from looper.cli_looper import main

CMD_STRS = ["string", " --string", " --sjhsjd 212", "7867#$@#$cc@@"]


def test_comprehensive_looper_no_pipestat(prep_temp_pep):
    tp = prep_temp_pep

    x = test_args_expansion(tp, "run")
    try:
        main(test_args=x)
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))


def test_comprehensive_looper_pipestat(prep_temp_pep_pipestat):
    tp = prep_temp_pep_pipestat
    cmd = "run"

    x = [cmd, "-d", "--looper-config", tp]

    try:
        result = main(test_args=x)
        if cmd == "run":
            assert result["Pipestat compatible"] is True
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))