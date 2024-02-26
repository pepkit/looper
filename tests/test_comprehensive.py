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
from pipestat import PipestatManager

from yaml import dump, safe_load

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
        repo = Repo.clone_from(REPO_URL, d, branch="dev_derive")
        pipestat_dir = os.path.join(d, "pipestat")

        path_to_looper_config = os.path.join(
            pipestat_dir, ".looper_pipestat_shell.yaml"
        )

        # open up the project config and replace the derived attributes with the path to the data. In a way, this simulates using the environment variables.
        pipestat_project_file = os.path.join(
            d, "pipestat/project", "project_config.yaml"
        )
        with open(pipestat_project_file, "r") as f:
            pipestat_project_data = safe_load(f)

        pipestat_project_data["sample_modifiers"]["derive"]["sources"]["source1"] = (
            os.path.join(pipestat_dir, "data/{sample_name}.txt")
        )

        with open(pipestat_project_file, "w") as f:
            dump(pipestat_project_data, f)

        # x = [cmd, "-d", "--looper-config", path_to_looper_config]
        x = [cmd, "--looper-config", path_to_looper_config]

        try:
            result = main(test_args=x)
            if cmd == "run":
                assert result["Pipestat compatible"] is True
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        # TODO TEST PROJECT LEVEL RUN
        # Must add this to hello_looper for pipestat example

        # TEST LOOPER CHECK

        # looper cannot create flags, the pipeline or pipestat does that
        # if you do not specify flag dir, pipestat places them in the same dir as config file
        path_to_pipestat_config = os.path.join(
            pipestat_dir, "looper_pipestat_config.yaml"
        )
        psm = PipestatManager(config_file=path_to_pipestat_config)
        psm.set_status(record_identifier="frog_1", status_identifier="completed")
        psm.set_status(record_identifier="frog_2", status_identifier="completed")

        # Now use looper check to get statuses
        x = ["check", "--looper-config", path_to_looper_config]

        try:
            result = main(test_args=x)
            assert result["example_pipestat_pipeline"]["frog_1"] == "completed"
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        # TEST LOOPER REPORT

        x = ["report", "--looper-config", path_to_looper_config]

        try:
            result = main(test_args=x)
            assert "report_directory" in result
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        # TEST LOOPER Table

        x = ["table", "--looper-config", path_to_looper_config]

        try:
            result = main(test_args=x)
            assert "example_pipestat_pipeline_stats_summary.tsv" in result[0]
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        # TEST LOOPER DESTROY
        # TODO add destroying individual samples via pipestat

        x = [
            "destroy",
            "--looper-config",
            path_to_looper_config,
            "--force-yes",
        ]  # Must force yes or pytest will throw an exception "OSError: pytest: reading from stdin while output is captured!"

        try:
            result = main(test_args=x)
            # assert "report_directory" in result
        except Exception:
            raise pytest.fail("DID RAISE {0}".format(Exception))

        # TODO TEST LOOPER INSPECT  -> I believe this moved to Eido?

        print(result)
