""" Tests for declaration of requirements in pipeline interface """

from attmap import PathExAttMap
from looper.pipeline_interface import \
    PL_KEY, PROTOMAP_KEY, PIPELINE_REQUIREMENTS_KEY
from looper import PipelineInterface
import pytest
from tests.models.pipeline_interface.conftest import \
    ATAC_PIPE_NAME, ATAC_PROTOCOL_NAME

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.mark.parametrize(["observe", "expected"], [
    (lambda pi, pk: pi.validate(pk), True),
    (lambda pi, pk: pi.missing_requirements(pk), {})
])
def test_no_requirements_successfully_validates(
        atac_pipe_name, atacseq_piface_data, observe, expected):
    """ PipelineInterface declaring no requirements successfully validates. """

    # Pretest--check that we're keying the data as expected.
    assert [atac_pipe_name] == list(atacseq_piface_data.keys())
    assert ATAC_PIPE_NAME == atacseq_piface_data[atac_pipe_name]["name"]

    pi = PipelineInterface({
        PROTOMAP_KEY: {ATAC_PROTOCOL_NAME: atac_pipe_name},
        PL_KEY: {atac_pipe_name: atacseq_piface_data}
    })

    assert PathExAttMap({}) == pi[PIPELINE_REQUIREMENTS_KEY]
    assert expected == observe(pi, atac_pipe_name)


@pytest.mark.skip("not implemented")
def test_illegal_requirements_specification():
    pass


@pytest.mark.skip("not implemented")
def test_validity_iff_missing_reqs_return_is_false():
    pass


@pytest.mark.skip("not implemented")
def test_all_requirements_satisfied():
    pass


@pytest.mark.skip("not implemented")
def test_mixed_requirement_satisfaction():
    pass


@pytest.mark.skip("not implemented")
def test_no_requirements_satisfied():
    pass
