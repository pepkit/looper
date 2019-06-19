""" Tests for YAML rendition of Sample """

import os
import pytest
import yaml
from looper import Sample as LSample
from peppy import Sample as PSample, SAMPLE_NAME_COLNAME
from peppy.sample import SAMPLE_YAML_EXT, SAMPLE_YAML_FILE_KEY

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


TYPE_PARAM_NAME = "data_type"


def _assert_sample_file_exists(exp_filename, dirpath):
    """ Check that an expected file is in a folder. """
    contents = os.listdir(dirpath)
    assert exp_filename in dirpath, "Contents of {}: {}".format(dirpath, contents)


def _get_exp_basic_sample_filename(n, _):
    """ Get the expected name for a basic Sample YAML file. """
    return n + SAMPLE_YAML_EXT


def _get_exp_sample_subtype_filename(n, t):
    """ Get the expected name for a Sample subtype YAML file. """
    return n + "_" + t.__name__ + SAMPLE_YAML_EXT


class PeppySampleSubtype(PSample):
    """ Dummy class for subtyping Sample from peppy. """
    pass


class LooperSampleSubtype(LSample):
    """ Dummy class for subtyping LooperSample. """
    pass


@pytest.fixture
def sample(request):
    """ Build a Sample, perhaps parameterized in name and type. """
    name = request.getfixturevalue("name") \
        if "name" in request.fixturenames else "testsample"
    build = request.getfixturevalue(TYPE_PARAM_NAME) \
        if TYPE_PARAM_NAME in request.fixturenames else LSample
    return build({SAMPLE_NAME_COLNAME: name})


@pytest.mark.parametrize([TYPE_PARAM_NAME, "get_exp"], [
    (PSample, _get_exp_basic_sample_filename),
    (LSample, _get_exp_basic_sample_filename),
    (PeppySampleSubtype, _get_exp_sample_subtype_filename),
    (LooperSampleSubtype, _get_exp_sample_subtype_filename)
])
def test_sample_yaml_file_exists(tmpdir, data_type, get_exp, sample):
    """ Ensure Sample write-to-disk creates expected file. """
    folder = tmpdir.strpath
    exp_name = get_exp(sample.name, data_type)
    exp_path = os.path.join(folder, exp_name)
    assert not os.path.exists(exp_path)
    sample.to_yaml(subs_folder_path=folder)
    assert os.path.isfile(exp_path)


@pytest.mark.parametrize(TYPE_PARAM_NAME, [
    PSample, LSample, PeppySampleSubtype, LooperSampleSubtype])
def test_sample_yaml_includes_filepath(tmpdir, data_type, sample):
    """ A Sample's disk representation includes key-value for that path. """
    fp = sample.to_yaml(subs_folder_path=tmpdir.strpath)
    assert os.path.isfile(fp)
    with open(fp, 'r') as f:
        data = yaml.load(f, yaml.SafeLoader)
    assert SAMPLE_YAML_FILE_KEY in data
    assert fp == data[SAMPLE_YAML_FILE_KEY]
