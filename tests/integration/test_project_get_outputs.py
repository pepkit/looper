""" Tests for interaction between Project and PipelineInterface """

import pytest
import yaml
from looper import Project as LP
from peppy.const import *


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


MAIN_META_KEY = "main_meta"
SUBS_META_KEY = "subs_meta"
SECTION_BY_FIXTURE = {
    MAIN_META_KEY: METADATA_KEY, SUBS_META_KEY: SUBPROJECTS_SECTION}


def get_conf_data(req):
    """
    Get Project config data for a test case.

    :param pytest.FixtureRequest req: test case requesting Project config data
    :return dict: Project config data
    """
    m = {key: req.getfixturevalue(fix) for fix, key
         in SECTION_BY_FIXTURE.items() if fix in req.fixturenames}
    return m


@pytest.fixture(scope="function")
def prj(request, tmpdir):
    """ Provide a test case with a Project instance. """
    conf_data = get_conf_data(request)
    conf_file = tmpdir.join("pc.yaml").strpath
    with open(conf_file, 'w') as f:
        yaml.dump(conf_data, f)
    return LP(conf_file)


@pytest.mark.parametrize(MAIN_META_KEY, [{OUTDIR_KEY: "arbitrary"}])
def test_no_pifaces(prj, main_meta):
    """ No pipeline interfaces --> the outputs data mapping is empty."""
    assert {} == prj.get_outputs()


@pytest.mark.skip("not implemented")
def test_no_outputs():
    pass


@pytest.mark.skip("not implemented")
def test_malformed_outputs():
    pass


@pytest.mark.skip("not implemented")
def test_only_subproject_has_pifaces():
    pass


@pytest.mark.skip("not implemented")
def test_only_subproject_has_outputs():
    pass


@pytest.mark.skip("not implemented")
def test_main_project_and_subproject_have_outputs():
    pass


@pytest.mark.skip("not implemented")
def test_no_samples_match_protocols_with_outputs():
    pass


@pytest.mark.skip("not implemented")
def test_pipeline_identifier_collision_same_data():
    pass


@pytest.mark.skip("not implemented")
def test_pipeline_identifier_collision_different_data():
    pass


@pytest.mark.skip("not implemented")
def test_sample_collection_accuracy():
    pass


@pytest.mark.skip("not implemented")
def test_protocol_collection_accuracy():
    pass
