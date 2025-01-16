import os.path

import pytest
from peppy.const import *
from yaml import dump

from looper.const import *
from looper.project import Project
from tests.conftest import *
from looper.utils import *
from looper.cli_pydantic import main
from tests.smoketests.test_run import is_connected
from tempfile import TemporaryDirectory
from pipestat import PipestatManager
from pipestat.exceptions import RecordNotFoundError

from yaml import dump, safe_load

CMD_STRS = ["string", " --string", " --sjhsjd 212", "7867#$@#$cc@@"]


def test_comprehensive_advanced_looper_no_pipestat(prep_temp_pep):

    path_to_looper_config = prep_temp_pep

    x = ["run", "--config", path_to_looper_config]

    try:
        results = main(test_args=x)
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))


def test_comprehensive_looper_no_pipestat(prep_temp_pep_basic):

    path_to_looper_config = prep_temp_pep_basic
    basic_dir = os.path.dirname(path_to_looper_config)

    # open up the project config and replace the derived attributes with the path to the data. In a way, this simulates using the environment variables.
    basic_project_file = os.path.join(basic_dir, "project", "project_config.yaml")
    with open(basic_project_file, "r") as f:
        basic_project_data = safe_load(f)

    basic_project_data["sample_modifiers"]["derive"]["sources"]["source1"] = (
        os.path.join(basic_dir, "data/{sample_name}.txt")
    )

    with open(basic_project_file, "w") as f:
        dump(basic_project_data, f)

    x = ["run", "--config", path_to_looper_config]

    try:
        results = main(test_args=x)
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))


def test_comprehensive_looper_pipestat(prep_temp_pep_pipestat):

    cmd = "run"

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

    x = [cmd, "--config", path_to_looper_config]

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
        pipestat_dir, f"results/pipestat_config_{pipeline_name}.yaml"
    )

    psm = PipestatManager(config_file=path_to_pipestat_config)
    psm.set_status(record_identifier="frog_1", status_identifier="completed")
    psm.set_status(record_identifier="frog_2", status_identifier="completed")

    # Now use looper check to get statuses
    x = ["check", "--config", path_to_looper_config]

    try:
        result = main(test_args=x)
        assert result["example_pipestat_pipeline"]["frog_1"] == "completed"
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))

    # Now use looper check to get project level statuses
    x = ["check", "--config", path_to_looper_config, "--project"]

    try:
        result = main(test_args=x)
        assert result == {}

    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))

    # TEST LOOPER REPORT

    x = ["report", "--config", path_to_looper_config]

    try:
        result = main(test_args=x)
        assert "report_directory" in result
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))

    # TEST LOOPER Table

    x = ["table", "--config", path_to_looper_config]

    try:
        result = main(test_args=x)
        assert "example_pipestat_pipeline_stats_summary.tsv" in result[0]
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))

    # TEST LOOPER DESTROY
    # TODO add destroying individual samples via pipestat

    x = [
        "destroy",
        "--config",
        path_to_looper_config,
        "--force-yes",
    ]  # Must force yes or pytest will throw an exception "OSError: pytest: reading from stdin while output is captured!"

    try:
        result = main(test_args=x)
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))

    sd = os.path.dirname(path_to_looper_config)
    tsv_list = [os.path.join(sd, f) for f in os.listdir(sd) if f.endswith(".tsv")]
    assert len(tsv_list) == 0
    with pytest.raises(RecordNotFoundError):
        psm = PipestatManager(config_file=path_to_pipestat_config)
        retrieved_result = psm.retrieve_one(record_identifier="frog_2")


@pytest.mark.skipif(not is_connected(), reason="This test needs internet access.")
@pytest.mark.skip(reason="user must be logged into pephub otherwise this will fail.")
def test_comprehensive_looper_pephub(prep_temp_pep_pephub):
    """Basic test to determine if Looper can run a PEP from PEPHub"""
    # TODO need to add way to check if user is logged into pephub and then run test otherwise skip
    path_to_looper_config = prep_temp_pep_pephub

    x = ["run", "--config", path_to_looper_config]

    try:
        results = main(test_args=x)
    except Exception:
        raise pytest.fail("DID RAISE {0}".format(Exception))
