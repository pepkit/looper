""" Tests for utility functions """

import os
import random
import string
import pytest
from looper.utils import determine_config_path, DEFAULT_CONFIG_SUFFIX, \
    DEFAULT_METADATA_FOLDER
from oldtests.helpers import randstr, LETTERS_AND_DIGITS


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


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
    @pytest.mark.parametrize("filename", [randstr(LETTERS_AND_DIGITS, 15)])
    def test_filepath_returns_filepath(tmpdir, filename):
        """ Path that's a file is simply returned. """
        root = os.path.join(tmpdir.strpath, filename)
        with open(root, 'w'):
            assert os.path.isfile(root)
        assert root == determine_config_path(root)

    @staticmethod
    @pytest.mark.parametrize("filename", [randstr(LETTERS_AND_DIGITS, 10)])
    def test_default_args_no_matching_files(tmpdir, filename):
        """ When no matching file is found, null value is returned. """
        root = tmpdir.strpath
        fpath = os.path.join(root, filename)
        assert os.path.isdir(root)
        with open(fpath, 'w'):
            assert os.path.isfile(fpath)
        assert determine_config_path(root) is None

    @staticmethod
    @pytest.mark.parametrize("fnames", [[
        randstr(LETTERS_AND_DIGITS, 20) + DEFAULT_CONFIG_SUFFIX
        for _ in range(random.randint(2, 5))]])
    def test_default_args_multiple_matching_files_main_level(tmpdir, fnames):
        """ Multiple matches emits warning and returns first. """
        root = tmpdir.strpath
        paths = [os.path.join(root, fn) for fn in fnames]
        for fp in paths:
            with open(fp, 'w'):
                assert os.path.isfile(fp)
        with pytest.raises(ValueError):
            determine_config_path(root)

    @staticmethod
    @pytest.mark.parametrize("use_sub", [False, True])
    @pytest.mark.parametrize("filename",
        [randstr(LETTERS_AND_DIGITS, 15) + DEFAULT_CONFIG_SUFFIX])
    def test_default_args_single_matching_file_main_folder(tmpdir, filename, use_sub):
        """ Config in proper subfolder is correctly found. """
        root = tmpdir.strpath
        if use_sub:
            folder = os.path.join(root, DEFAULT_METADATA_FOLDER)
            os.makedirs(folder)
        else:
            folder = root
        fp = os.path.join(folder, filename)
        with open(fp, 'w'):
            assert os.path.isfile(fp)
        assert fp == determine_config_path(root)
