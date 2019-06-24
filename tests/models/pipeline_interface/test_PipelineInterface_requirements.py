""" Tests for declaration of requirements in pipeline interface """

from attmap import PathExAttMap
from looper import PipelineInterface
from looper.exceptions import PipelineInterfaceRequirementsError
from looper.pipeline_interface import \
    PL_KEY, PROTOMAP_KEY, PIPELINE_REQUIREMENTS_KEY
import pytest
import yaml
from tests.models.pipeline_interface.conftest import \
    ATAC_PIPE_NAME, ATAC_PROTOCOL_NAME
from veracitools import ExpectContext

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


def randn():
    import random, sys
    return random.randint(-sys.maxsize, sys.maxsize)


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


class IllegalPipelineRequirementsSpecificationTests:

    @pytest.mark.parametrize(["reqs_data", "expected"], [
        (randn(), TypeError),
        ({"ls": "not-a-valid-check-type"}, PipelineInterfaceRequirementsError)])
    @pytest.mark.parametrize("from_file", [False, True])
    def test_bad_reqs_top_level(self, reqs_data, expected, atac_pipe_name,
                                atacseq_piface_data, from_file, tmpdir):
        assert PIPELINE_REQUIREMENTS_KEY not in atacseq_piface_data[atac_pipe_name]
        pi_data = {PROTOMAP_KEY: {ATAC_PROTOCOL_NAME: atac_pipe_name},
                   PL_KEY: atacseq_piface_data,
                   PIPELINE_REQUIREMENTS_KEY: reqs_data}
        if from_file:
            src = tmpdir.join("pi.yaml").strpath
            with open(src, 'w') as f:
                yaml.dump(pi_data, f)
        else:
            src = pi_data
        with ExpectContext(expected, PipelineInterface) as build_iface:
            build_iface(src)

    @pytest.mark.parametrize(["reqs_data", "expected"], [
        (randn(), TypeError),
        ({"ls": "not-a-valid-check-type"}, PipelineInterfaceRequirementsError)])
    @pytest.mark.parametrize("from_file", [False, True])
    def test_bad_reqs_specific_pipeline(self, reqs_data, expected, atac_pipe_name,
                                atacseq_piface_data, from_file, tmpdir):
        assert PIPELINE_REQUIREMENTS_KEY not in atacseq_piface_data[atac_pipe_name]
        atacseq_piface_data[atac_pipe_name][PIPELINE_REQUIREMENTS_KEY] = reqs_data
        assert atacseq_piface_data[atac_pipe_name][PIPELINE_REQUIREMENTS_KEY] == reqs_data
        pi_data = {PROTOMAP_KEY: {ATAC_PROTOCOL_NAME: atac_pipe_name},
                   PL_KEY: atacseq_piface_data}
        print("DATA: {}".format(pi_data))
        if from_file:
            src = tmpdir.join("pi.yaml").strpath
            with open(src, 'w') as f:
                yaml.dump(pi_data, f)
        else:
            src = pi_data
        # DEBUG
        #pi = PipelineInterface(src)
        #print("PI: {}".format(pi[PL_KEY]))
        with ExpectContext(expected, PipelineInterface) as build_iface:
            print(build_iface(src))

    @pytest.mark.skip("not implemented")
    def test_bad_reqs_post_construction(self):
        pass

    @pytest.mark.skip("not implemented")
    def test_bad_reqs_specific_pipeline_post_construction(self):
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
