import pytest
from peppy.const import *
from yaml import dump

from looper.const import *
from looper.project import Project
from tests.conftest import *
from looper.utils import *
from looper.cli_looper import main
from tests.smoketests.test_run import is_connected
from tempfile import TemporaryDirectory
from git import Repo

CMD_STRS = ["string", " --string", " --sjhsjd 212", "7867#$@#$cc@@"]

REPO_URL = "https://github.com/pepkit/hello_looper.git"


def test_comprehensive_looper_no_pipestat(prep_temp_pep):
    tp = prep_temp_pep

    x = test_args_expansion(tp, "run")
    try:
        main(test_args=x)
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))


@pytest.mark.skipif(not is_connected(), reason="Test needs an internet connection")
def test_comprehensive_looper_pipestat():
    """
    This test clones the hello_looper repository and runs the looper config file in the pipestat sub-directory
    """

    cmd = "run"

    with TemporaryDirectory() as d:
        repo = Repo.clone_from(REPO_URL, d)

        path_to_looper_config = os.path.join(d, "pipestat", ".looper.yaml")

        x = [cmd, "-d", "--looper-config", path_to_looper_config]

        try:
            result = main(test_args=x)
            if cmd == "run":
                assert result["Pipestat compatible"] is True
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))
