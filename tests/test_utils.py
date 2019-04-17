""" Tests for utility functions """

import os
import random
import string
import pytest
from looper.utils import determine_config_path, DEFAULT_CONFIG_SUFFIX, \
    DEFAULT_METADATA_FOLDER

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


def randstr(pool, size):
    """ Generate random string of given size/length. """
    return "".join(random.choice(pool) for _ in range(size))


class ConfigPathDeterminationTests:
    """ Tests for config path determination function """

    @staticmethod
    @pytest.mark.parametrize("subfolder", [randstr(string.ascii_letters, 10)])
    def test_nonexistent_root(tmpdir, subfolder):
        """ The root path to the config filepath determination function must exist. """
        root = os.path.join(tmpdir.strpath, subfolder)
        assert not os.path.exists(root)
        with pytest.raises(Exception):
            determine_config_path(root)

    @staticmethod
    @pytest.mark.parametrize("filename",
        [randstr(string.ascii_letters + string.digits, 15)])
    def test_filepath_returns_filepath(tmpdir, filename):
        """ Path that's a file is simply returned. """
        root = os.path.join(tmpdir.strpath, filename)
        with open(root, 'w'):
            assert os.path.isfile(root)
        assert root == determine_config_path(root)

    @staticmethod
    @pytest.mark.parametrize("filename",
        [randstr(string.ascii_letters + string.digits, 10)])
    def test_default_args_no_matching_files(tmpdir, filename):
        """ When no matching file is found, null value is returned. """
        root = tmpdir.strpath
        fpath = os.path.join(root, filename)
        assert os.path.isdir(root)
        with open(fpath, 'w'):
            assert os.path.isfile(fpath)
        assert determine_config_path(root) is None

    @staticmethod
    @pytest.mark.skip("not implemented")
    def test_default_args_multiple_matching_files(tmpdir):
        pass

    @staticmethod
    @pytest.mark.skip("not implemented")
    def test_default_args_single_matching_file(tmpdir):
        pass
