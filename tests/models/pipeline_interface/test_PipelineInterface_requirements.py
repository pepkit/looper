""" Tests for declaration of requirements in pipeline interface """

import os
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


TOP_LEVEL_KEY = "top-level"
PIPE_LEVEL_KEY = "pipeline"


def pytest_generate_tests(metafunc):
    """ Dynamic test case generation/parameterization local to this module. """
    if "from_file" in metafunc.fixturenames:
        metafunc.parametrize("from_file", [False, True])


def randn():
    """ Singly random integer from a huge interval """
    import random, sys
    return random.randint(-sys.maxsize, sys.maxsize)


def _make_from_data(from_file, folder, data):
    """
    Homogenize PipelineInterface build over both in-memory and on-disk data.

    :param bool from_file: whether to route the construction through disk
    :param str folder: folder in which to create config file if via disk
    :param Mapping data: raw PI config data
    :return looper.PipelineInterface: the new PipelineInterface instance
    """
    assert type(from_file) is bool
    if from_file:
        fp = os.path.join(folder, "pipeline_interface.yaml")
        with open(fp, 'w') as f:
            yaml.dump(data, f)
        data = fp
    return PipelineInterface(data)


@pytest.mark.parametrize(["observe", "expected"], [
    (lambda pi, pk: pi.validate(pk), True),
    (lambda pi, pk: pi.missing_requirements(pk), {})
])
def test_no_requirements_successfully_validates(
        observe, expected, from_file, atac_pipe_name, atacseq_piface_data, tmpdir):
    """ PipelineInterface declaring no requirements successfully validates. """

    # Pretest--check that we're keying the data as expected.
    assert [atac_pipe_name] == list(atacseq_piface_data.keys())
    assert ATAC_PIPE_NAME == atacseq_piface_data[atac_pipe_name]["name"]

    pi = _make_from_data(from_file, tmpdir.strpath, {
        PROTOMAP_KEY: {ATAC_PROTOCOL_NAME: atac_pipe_name},
        PL_KEY: {atac_pipe_name: atacseq_piface_data}
    })

    with pytest.raises(KeyError):
        pi[PIPELINE_REQUIREMENTS_KEY]
    assert expected == observe(pi, atac_pipe_name)


@pytest.mark.parametrize(["observe", "expected"], [
    (lambda pi, pk: pi.validate(pk), True),
    (lambda pi, pk: pi.missing_requirements(pk), {})
])
@pytest.mark.parametrize("reqs_data", [None, {}])
@pytest.mark.parametrize("placement", ["top-level", "pipeline"])
def test_empty_requirements_successfully_validates(
        observe, expected, from_file, tmpdir, reqs_data,
        atac_pipe_name, atacseq_piface_data, placement):
    """ Null value or empty mapping for requirements still validates. """

    # Pretest--check that we're keying the data as expected.
    assert [atac_pipe_name] == list(atacseq_piface_data.keys())
    assert ATAC_PIPE_NAME == atacseq_piface_data[atac_pipe_name]["name"]

    data = {
        PROTOMAP_KEY: {ATAC_PROTOCOL_NAME: atac_pipe_name},
        PL_KEY: {atac_pipe_name: atacseq_piface_data}
    }

    if placement == "top-level":
        data[PIPELINE_REQUIREMENTS_KEY] = reqs_data
    elif placement == "pipeline":
        data[PL_KEY][atac_pipe_name][PIPELINE_REQUIREMENTS_KEY] = reqs_data
    else:
        raise ValueError("Unexpected reqs placement spec: {}".format(placement))

    pi = _make_from_data(from_file, tmpdir.strpath, data)
    assert expected == observe(pi, atac_pipe_name)


class IllegalPipelineRequirementsSpecificationTests:
    """ Test expected behavior of various invalid reqs specs. """

    @pytest.mark.parametrize(["reqs_data", "expected"], [
        (randn(), TypeError),
        ({"ls": "not-a-valid-check-type"}, PipelineInterfaceRequirementsError)])
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
    def test_bad_reqs_specific_pipeline(self, reqs_data, expected, atac_pipe_name,
                                atacseq_piface_data, from_file, tmpdir):
        """ Invalid requirements within a specific pipeline section is exceptional. """
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

    @pytest.mark.parametrize("init_reqs_data", [None, {}])
    @pytest.mark.parametrize(["new_bad_reqs_data", "expected"], [
        (randn(), TypeError),
        ({"ls": "not-a-valid-check-type"}, PipelineInterfaceRequirementsError)
    ])
    @pytest.mark.parametrize(["init_place", "pretest"], [
        ("top-level", lambda pi, _, init: PIPELINE_REQUIREMENTS_KEY not in pi
            if init is None else pi[PIPELINE_REQUIREMENTS_KEY] == PathExAttMap()),
        ("pipeline", lambda pi, pipe_name, init: PIPELINE_REQUIREMENTS_KEY
                                                 not in pi[PL_KEY][pipe_name]
            if init is None else pi[PL_KEY][pipe_name][PIPELINE_REQUIREMENTS_KEY] == PathExAttMap())])
    @pytest.mark.parametrize("post_place_loc", ["top-level", "pipeline"])
    @pytest.mark.parametrize("post_place_fun", [
        lambda obj, data: setattr(obj, PIPELINE_REQUIREMENTS_KEY, data),
        lambda obj, data: obj.__setitem__(PIPELINE_REQUIREMENTS_KEY, data)
    ])
    def test_bad_reqs_post_construction(
            self, init_place, pretest, from_file, tmpdir, atac_pipe_name,
            atacseq_piface_data, init_reqs_data, new_bad_reqs_data,
            post_place_loc, post_place_fun, expected):
        """ Modification of requirements in invalid way is exceptional. """

        data = {
            PROTOMAP_KEY: {ATAC_PROTOCOL_NAME: atac_pipe_name},
            PL_KEY: {atac_pipe_name: atacseq_piface_data}
        }

        if init_place == "top-level":
            data[PIPELINE_REQUIREMENTS_KEY] = init_reqs_data
        elif init_place == "pipeline":
            data[PL_KEY][atac_pipe_name][PIPELINE_REQUIREMENTS_KEY] = init_reqs_data
        else:
            raise ValueError("Unexpected reqs placement spec: {}".format(init_place))

        pi = _make_from_data(from_file, tmpdir.strpath, data)
        pretest(pi, atac_pipe_name, init_reqs_data)

        if post_place_loc == "top-level":
            with ExpectContext(expected, post_place_fun) as try_bad_reqs_placement:
                try_bad_reqs_placement(pi, new_bad_reqs_data)
        elif post_place_loc == "pipeline":
            with ExpectContext(expected, post_place_fun) as try_bad_reqs_placement:
                try_bad_reqs_placement(pi, new_bad_reqs_data)
        else:
            raise ValueError("Unexpected reqs placement spec: {}".format(post_place_loc))


@pytest.mark.parametrize(
    "reqs", [{}, ["ls", "date"], {"ls": "executable", "date": "executable"}])
def test_top_level_requirements_do_not_literally_propagate(
        reqs, from_file, tmpdir, atac_pipe_name, atacseq_piface_data):
    """ Don't literally store universal requirements in each pipeline. """
    data = {
        PROTOMAP_KEY: {ATAC_PROTOCOL_NAME: atac_pipe_name},
        PL_KEY: {atac_pipe_name: atacseq_piface_data},
        PIPELINE_REQUIREMENTS_KEY: reqs
    }
    pi = _make_from_data(from_file, tmpdir.strpath, data)
    assert reqs == pi[PIPELINE_REQUIREMENTS_KEY]
    assert all(map(lambda d: PIPELINE_REQUIREMENTS_KEY not in d, pi[PL_KEY].values()))


@pytest.mark.parametrize(["reqs", "expected"], [
    ("nonexec", ["nonexec"]), (["not-on-path", "ls"], ["not-on-path"]),
    ({"nonexec": "executable", "$HOME": "folder"}, ["nonexec"])])
def test_top_level_requirements_functionally_propagate(
        reqs, from_file, tmpdir, atac_pipe_name, atacseq_piface_data, expected):
    """ The universal requirements do functionally apply to each pipeline. """
    data = {
        PROTOMAP_KEY: {ATAC_PROTOCOL_NAME: atac_pipe_name},
        PL_KEY: {atac_pipe_name: atacseq_piface_data},
        PIPELINE_REQUIREMENTS_KEY: reqs
    }
    pi = _make_from_data(from_file, tmpdir.strpath, data)
    assert set(reqs.keys()) == set(pi[PIPELINE_REQUIREMENTS_KEY].keys())
    assert PIPELINE_REQUIREMENTS_KEY not in pi[PL_KEY][atac_pipe_name]
    assert expected == pi.missing_requirements(atac_pipe_name)
    assert not pi.validate(atac_pipe_name)


@pytest.mark.skip("not implemented")
def test_pipeline_specific_requirements_remain_local():
    """ A single pipeline's requirements don't pollute others'. """
    pass
