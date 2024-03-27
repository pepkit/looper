""" Assorted divvy tests """

import pytest
from yacman import YacAttMap, load_yaml
from looper.divvy import DEFAULT_COMPUTE_RESOURCES_NAME
from tests.divvytests.conftest import DCC_ATTRIBUTES, FILES, mock_env_missing


class TestDefaultDCC:
    """Tests the default divvy.ComputingConfiguration object creation"""

    def test_no_args(self, empty_dcc):
        """Lack of arguments does not cause failure"""
        empty_dcc

    @pytest.mark.parametrize(argnames="att", argvalues=DCC_ATTRIBUTES)
    def test_attrs_produced(self, att, empty_dcc):
        """Test if compute property is produced and is not empty"""
        empty_dcc[att]

    def test_no_env_var(self, mock_env_missing, empty_dcc):
        empty_dcc


class TestDCC:
    """Tests the divvy.ComputingConfiguration object creation"""

    def test_object_creation(self, dcc):
        """Test object creation for all the available compute files in divcfg repo"""
        dcc

    @pytest.mark.parametrize(argnames="att", argvalues=DCC_ATTRIBUTES)
    def test_attrs_produced(self, att, dcc):
        """Test if compute all properties are produced"""
        dcc[att]


class TestActivating:
    """Test for the activate_package method"""

    def test_activating_default_package(self, dcc):
        """Test if activating the default compute package works for every case"""
        assert dcc.activate_package(DEFAULT_COMPUTE_RESOURCES_NAME)

    @pytest.mark.parametrize(argnames="package_idx", argvalues=[0, 1])
    def test_activating_some_package(self, dcc, package_idx):
        """Test if activating the default compute package works for every case"""
        package = list(dcc["compute_packages"].keys())[package_idx]
        assert dcc.activate_package(package)

    @pytest.mark.parametrize(
        argnames="package", argvalues=["faulty_package", "another_one", 1]
    )
    def test_not_activating_faulty_package(self, dcc, package):
        """Test if the function returns False if faulty compute package provided"""
        assert not dcc.activate_package(package)


class TestGettingActivePackage:
    """Test for the get_active_package method"""

    def test_settings_nonempty(self, dcc):
        """Test if get_active_package produces a nonempty YacAttMap object"""
        settings = dcc.get_active_package()
        assert settings != YacAttMap()


class TestListingPackages:
    """Test for the list_compute_packages method"""

    def test_list_compute_packages_is_set(self, dcc):
        """Test if list_compute_packages returns a set"""
        assert isinstance(dcc.list_compute_packages(), set)

    def test_list_compute_packages_result_nonempty(self, dcc):
        """Test if result nonempty"""
        assert dcc.list_compute_packages() != set()


class TestResettingSettings:
    """ " Test for the reset_active_settings method"""

    def test_reset_active_settings(self, dcc):
        """Test if always succeeds -- returns True"""
        assert dcc.reset_active_settings()

    def test_reset_active_settings_works(self, dcc):
        """Test if the settings are cleared"""
        dcc.reset_active_settings()
        assert dcc.get_active_package() == YacAttMap({})


class UpdatingPackagesTests:
    """Test for the update_packages method"""

    @pytest.mark.parametrize(argnames="config_file", argvalues=FILES)
    def test_update_packages(self, dcc, config_file):
        """Test updating does not produce empty compute packages"""
        entries = load_yaml(config_file)
        dcc.update(entries)
        assert dcc["compute_packages"] != YacAttMap()
