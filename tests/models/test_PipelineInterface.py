""" Tests for PipelineInterface ADT. """

import copy
import inspect
import itertools
import logging
import os
import random
import sys
import warnings

import pytest
import yaml

from attmap import PathExAttMap
from looper.const import *
from looper.pipeline_interface import PipelineInterface, PL_KEY, PROTOMAP_KEY, \
    RESOURCES_KEY
from looper.project import Project
from looper.exceptions import InvalidResourceSpecificationException, \
    MissingPipelineConfigurationException, PipelineInterfaceConfigError
from peppy import Project, Sample
from peppy.const import *
from .conftest import ATAC_PROTOCOL_NAME, write_config_data
from tests.helpers import powerset


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


_LOGGER = logging.getLogger(__name__)


# Values with which to build pipeline interface keys and names
PIPELINE_NAMES = ["ATACseq", "WGBS"]
EXTENSIONS = [".py", ".sh", ".R"]


def pytest_generate_tests(metafunc):
    """ Customization specific to test cases in this module. """
    try:
        parameters = metafunc.cls.PARAMETERS
    except AttributeError:
        _LOGGER.debug("No indirect parameterization for test class: '{}'".
                      format(metafunc.cls))
    else:
        for name, values in parameters.items():
            metafunc.parametrize(argnames=name, argvalues=values)


@pytest.fixture(scope="function")
def basic_pipe_iface_data(request):
    """ Minimal PipelineInterface configuration data. """
    extension = request.getfixturevalue("extension") \
            if "extension" in request.fixturenames else ".py"
    return {pipe_name + extension: {"name": pipe_name}
            for pipe_name in PIPELINE_NAMES}


@pytest.fixture
def bundled_piface(request):
    """ Provide an essentially minimal collection of PI config data. """
    pipelines = request.getfixturevalue("basic_pipe_iface_data")
    return {PROTOMAP_KEY: {"ATAC": "ATACSeq.py"}, PL_KEY: pipelines}


@pytest.fixture(scope="function")
def pi_with_resources(request, bundled_piface, resources):
    """ Add resource bundle data to each config section. """
    if "use_new_file_size" in request.fixturenames:
        file_size_name = "min_file_size" if \
                request.getfixturevalue("use_new_file_size") else "file_size"
        for rp_data in resources.values():
            size1 = rp_data.pop("file_size", None)
            size2 = rp_data.pop("min_file_size", None)
            size = size1 or size2
            if size:
                rp_data[file_size_name] = size
    pipe_iface_config = PipelineInterface(bundled_piface)
    for pipe_data in pipe_iface_config.pipelines.values():
        pipe_data[RESOURCES_KEY] = resources
    return pipe_iface_config


@pytest.mark.parametrize(argnames="from_file", argvalues=[False, True])
def test_basic_construction(tmpdir, from_file, bundled_piface):
    """ PipelineInterface constructor handles Mapping or filepath. """

    if from_file:
        pipe_iface_config = tmpdir.join("pipe-iface-conf.yaml").strpath
        with open(tmpdir.join("pipe-iface-conf.yaml").strpath, 'w') as f:
            yaml.safe_dump(bundled_piface, f)
    else:
        pipe_iface_config = bundled_piface

    pi = PipelineInterface(pipe_iface_config)

    # Check for the protocol mapping and pipeline interface keys.
    assert PL_KEY in pi, "Missing pipeline key ({})".format(PL_KEY)
    assert PROTOMAP_KEY in pi, \
        "Missing protocol mapping key: ({})".format(PROTOMAP_KEY)

    assert pi.pipe_iface_file == (pipe_iface_config if from_file else None)
    if from_file:
        assert pi.pipelines_path == tmpdir.strpath
    else:
        assert pi.pipelines_path is None

    # Validate protocol mapping and interfaces contents.
    assert PathExAttMap(bundled_piface[PL_KEY]) == pi[PL_KEY]
    assert PathExAttMap(bundled_piface[PROTOMAP_KEY]) == pi[PROTOMAP_KEY]

    # Certain access modes should agree with one another.
    assert pi.pipelines == pi[PL_KEY]
    assert list(pi.pipelines.keys()) == pi.pipeline_names


def test_iterpipes(pi_with_resources):
    """ Test iteration over pipeline keys and interface data. """

    missing, unequal = [], []
    seen = 0

    known = pi_with_resources[PL_KEY]
    assert len(known) > 0

    def get_err_msg(obs, context):
        return "{} of {} known pipeline(s) {}: {}".format(
            len(obs), len(known), context, ", ".join(obs))

    for pipe, data in pi_with_resources.iterpipes():
        seen += 1
        if pipe not in known:
            missing.append(pipe)
        elif data != pi_with_resources.select_pipeline(pipe):
            unequal.append(pipe)

    assert len(known) == seen
    assert [] == missing, get_err_msg(missing, "missing")
    try:
        assert [] == unequal
    except AssertionError:
        print(get_err_msg(unequal, "with unmatched data"))
        print("KNOWN: {}".format(known))
        print("ITERPIPES: {}".format(", ".join(pi_with_resources.iterpipes())))
        raise


@pytest.mark.parametrize(
    "exclude", powerset(PipelineInterface.REQUIRED_SECTIONS))
def test_requires_pipelines_and_protocol_mapping(
        basic_pipe_iface_data, bundled_piface, exclude):
    """ Check PipelineInterface's requirement for important sections. """
    pipe_iface_config = copy.deepcopy(bundled_piface)
    missing = [s for s in PipelineInterface.REQUIRED_SECTIONS if s not in pipe_iface_config]
    assert [] == missing, \
        "Missing PI config section(s): {}".format(", ".join(missing))
    pipe_iface_config = {
        k: v for k, v in pipe_iface_config.items() if k not in exclude}
    assert [] == [s for s in exclude if s in pipe_iface_config]
    # For < 3.3 compat., no contextlib specialization here
    if exclude:
        with pytest.raises(PipelineInterfaceConfigError):
            PipelineInterface(pipe_iface_config)
    else:
        PipelineInterface(pipe_iface_config)


@pytest.mark.parametrize(
        argnames="funcname_and_kwargs",
        argvalues=[("choose_resource_package", {"file_size": 4}),
                   ("get_arg_string",
                    {"sample": Sample(
                            {"sample_name": "arbitrary-sample-name"})}),
                   ("get_attribute",
                    {"attribute_key": "irrelevant-attr-name"}),
                   ("get_pipeline_name", {})])
@pytest.mark.parametrize(argnames="use_resources", argvalues=[False, True])
def test_unconfigured_pipeline_exception(
        funcname_and_kwargs, use_resources, pi_with_resources):
    """ Each public function throws same exception given unmapped pipeline. """
    pi = pi_with_resources
    if not use_resources:
        for pipeline in pi.pipelines.values():
            try:
                del pipeline[RESOURCES_KEY][DEFAULT_COMPUTE_RESOURCES_NAME]
            except KeyError:
                # Already no default resource package.
                pass

    def parse_param_names(f):
        return inspect.getargspec(f).args if sys.version_info < (3, 0) \
            else [p for p in inspect.signature(f).parameters.keys()]

    # Each of the functions being tested should take pipeline_name arg,
    # and we want to test behavior for the call on an unknown pipeline.
    funcname, kwargs = funcname_and_kwargs
    func = getattr(pi, funcname)
    required_parameters = parse_param_names(func)
    for parameter in ["pipeline_name", "pipeline"]:
        if parameter in required_parameters and parameter not in kwargs:
            kwargs[parameter] = "missing-pipeline"
    with pytest.raises(MissingPipelineConfigurationException):
        func.__call__(**kwargs)


@pytest.mark.parametrize(
    argnames=["pipe_name", "extension"],
    argvalues=list(itertools.product(PIPELINE_NAMES, EXTENSIONS)))
def test_prohibition_of_direct_pipeline_access(
        recwarn, pipe_name, extension, pi_with_resources):
    """ Specific pipeline access is granted via getitem but is deprecated. """

    # Pipeline key is name + extension; ensure it's present.
    pk = pipe_name + extension
    assert pk in pi_with_resources.pipelines

    warnings.simplefilter('always')    # Capture DeprecationWarning with recwarn
    assert 0 == len(recwarn)           # Start fresh

    # Modern access pattern doesn't warn.
    _ = pi_with_resources.select_pipeline(pk)
    assert 0 == len(recwarn)

    # Old access pattern is an exception.
    with pytest.raises(KeyError):
        pi_with_resources[pk]


class PipelineInterfaceNameResolutionTests:
    """ Name is explicit or inferred from key. """

    @pytest.mark.parametrize(
            argnames="name_and_ext_pairs",
            argvalues=itertools.combinations(
                    itertools.product(PIPELINE_NAMES, EXTENSIONS), 2))
    def test_get_pipeline_name_explicit(self, name_and_ext_pairs):
        """ Configuration can directly specify pipeline name. """
        names, extensions = zip(*name_and_ext_pairs)
        pipelines = [name + ext for name, ext in name_and_ext_pairs]
        pi_conf_data = {pipeline: {"name": name}
                        for pipeline, name in zip(pipelines, names)}
        pi = PipelineInterface({PROTOMAP_KEY: {"ATAC": "ATACSeq.py"},
                                PL_KEY: pi_conf_data})
        for pipeline, expected_name in zip(pipelines, names):
            assert expected_name == pi.get_pipeline_name(pipeline)


class PipelineInterfaceResourcePackageTests:
    """ Tests for pipeline's specification of compute resources. """

    PARAMETERS = {"use_new_file_size": [False, True]}

    def test_requires_default(
            self, use_new_file_size, pi_with_resources, huge_resources):
        """ If provided, resources specification needs 'default.' """
        pi = pi_with_resources
        for name, pipeline in pi.iterpipes():
            try:
                del pipeline[RESOURCES_KEY][DEFAULT_COMPUTE_RESOURCES_NAME]
            except KeyError:
                # Already no default resource package.
                pass
            assert "default" not in pipeline[RESOURCES_KEY]
            with pytest.raises(InvalidResourceSpecificationException):
                pi.choose_resource_package(
                        name, file_size=huge_resources["file_size"] + 1)

    def test_negative_file_size_request(
            self, use_new_file_size, pi_with_resources):
        """ Negative file size is prohibited. """
        pi = pi_with_resources
        for pipeline_name in pi.pipeline_names:
            negative_file_size = -10 * random.random()
            with pytest.raises(ValueError):
                pi.choose_resource_package(
                        pipeline_name, file_size=negative_file_size)

    @pytest.mark.parametrize(argnames="file_size", argvalues=[0, 10, 101])
    def test_resources_not_required(
            self, use_new_file_size, file_size, pi_with_resources):
        """ Compute resource specification is optional. """
        pi = pi_with_resources
        for pipe_data in pi.pipelines.values():
            del pipe_data[RESOURCES_KEY]
        for pipe_name in pi.pipeline_names:
            assert {} == pi.choose_resource_package(pipe_name, int(file_size))
            assert {} == pi.choose_resource_package(pipe_name, float(file_size))

    @pytest.mark.parametrize(
            argnames=["file_size", "expected_package_name"],
            argvalues=[(0, "default"), (4, "default"),
                       (16, "midsize"), (64, "huge")])
    def test_selects_proper_resource_package(
            self, use_new_file_size, pi_with_resources,
            file_size, expected_package_name, midsize_resources):
        """ Minimal resource package sufficient for pipeline and file size. """
        for pipe_data in pi_with_resources.pipelines.values():
            pipe_data[RESOURCES_KEY].update(
                    {"midsize": copy.deepcopy(midsize_resources)})
        for pipe_name, pipe_data in pi_with_resources.iterpipes():
            observed_package = pi_with_resources.choose_resource_package(
                pipe_name, file_size)
            expected_package = copy.deepcopy(
                    pipe_data[RESOURCES_KEY][expected_package_name])
            assert expected_package == observed_package

    def test_negative_file_size_prohibited(
            self, use_new_file_size, pi_with_resources):
        """ Negative min file size in resource package spec is prohibited. """
        file_size_attr = "min_file_size" if use_new_file_size else "file_size"
        for pipe_data in pi_with_resources.pipelines.values():
            for package_data in pipe_data[RESOURCES_KEY].values():
                package_data[file_size_attr] = -5 * random.random()
        for pipe_name in pi_with_resources.pipeline_names:
            file_size_request = random.randrange(1, 11)
            with pytest.raises(ValueError):
                pi_with_resources.choose_resource_package(
                        pipe_name, file_size_request)

    def test_file_size_spec_not_required_for_default(
            self, use_new_file_size, bundled_piface, 
            default_resources, huge_resources, midsize_resources):
        """ Default package implies minimum file size of zero. """

        def clear_file_size(resource_package):
            for fs_var_name in ("file_size", "min_file_size"):
                if fs_var_name in resource_package:
                    del resource_package[fs_var_name]

        # Create the resource package specification data.
        resources_data = dict(zip(
                ["default", "midsize", "huge"],
                [copy.deepcopy(data) for data in
                 [default_resources, midsize_resources, huge_resources]]))
        for pack_name, pack_data in resources_data.items():
            # Use file size spec name as appropriate; clean default package.
            if pack_name == "default":
                clear_file_size(pack_data)
            elif use_new_file_size:
                pack_data["min_file_size"] = pack_data.pop("file_size")

        # Add resource package spec data and create PipelineInterface.
        pipe_iface_data = copy.deepcopy(bundled_piface)
        for pipe_data in pipe_iface_data[PL_KEY].values():
            pipe_data[RESOURCES_KEY] = resources_data
        pi = PipelineInterface(pipe_iface_data)

        # We should always get default resource package for mini file.
        for pipe_name, pipe_data in pi.iterpipes():
            default_resource_package = \
                    pipe_data[RESOURCES_KEY][DEFAULT_COMPUTE_RESOURCES_NAME]
            clear_file_size(default_resource_package)
            assert default_resource_package == \
                   pi.choose_resource_package(pipe_name, 0.001)

    @pytest.mark.parametrize(
            argnames="min_file_size", argvalues=[-1, 1])
    def test_default_package_new_name_zero_size(
            self, use_new_file_size, min_file_size, pi_with_resources):
        """ Default resource package sets minimum file size to zero. """

        for pipe_name, pipe_data in pi_with_resources.iterpipes():
            # Establish faulty default package setting for file size.
            default_resource_package = pipe_data[RESOURCES_KEY]["default"]
            if use_new_file_size:
                if "file_size" in default_resource_package:
                    del default_resource_package["file_size"]
                default_resource_package["min_file_size"] = min_file_size
            else:
                if "min_file_size" in default_resource_package:
                    del default_resource_package["min_file_size"]
                default_resource_package["file_size"] = min_file_size

            # Get the resource package to validate.
            # Requesting file size of 0 should always trigger default package.
            observed_resource_package = \
                    pi_with_resources.choose_resource_package(pipe_name, 0)

            # Default package is an early adopter of the new file size name.
            expected_resource_package = copy.deepcopy(default_resource_package)
            if "file_size" in expected_resource_package:
                del expected_resource_package["file_size"]
            # Default packages forces its file size value to 0.
            expected_resource_package["min_file_size"] = 0

            assert expected_resource_package == observed_resource_package

    def test_file_size_spec_required_for_non_default_packages(
            self, use_new_file_size, bundled_piface, 
            default_resources, huge_resources):
        """ Resource packages besides default require file size. """

        # Establish the resource specification.
        resource_package_data = {
                "default": copy.deepcopy(default_resources),
                "huge": copy.deepcopy(huge_resources)}

        # Remove file size for non-default; set it for default.
        del resource_package_data["huge"]["file_size"]
        if use_new_file_size:
            resource_package_data["default"]["min_file_size"] = \
                    resource_package_data["default"].pop("file_size")

        # Create the PipelineInterface.
        for pipe_data in bundled_piface[PL_KEY].values():
            pipe_data[RESOURCES_KEY] = resource_package_data
        pi = PipelineInterface(bundled_piface)

        # Attempt to select resource package should fail for each pipeline,
        # regardless of the file size specification; restrict to nonnegative
        # file size requests to avoid collision with ValueError that should
        # arise if requesting resource package for a negative file size value.
        for pipe_name in pi.pipeline_names:
            with pytest.raises(KeyError):
                pi.choose_resource_package(pipe_name, random.randrange(0, 10))


class ConstructorPathParsingTests:
    """ The constructor is responsible for expanding pipeline path(s). """

    ADD_PATH = [True, False]
    PIPELINE_KEYS = ["ATACSeq.py", "no_path.py"]
    RELATIVE_PATH_DATA = [
            ("./arbitrary-test-pipelines",
             {},
             "./arbitrary-test-pipelines"),
            ("path/to/$TEMP_PIPE_LOCS",
             {"TEMP_PIPE_LOCS": "validation-value"},
             "path/to/validation-value")]
    ABSOLUTE_PATHS = [
            os.path.join("~", "code_home", "bioinformatics"),
            os.path.join("$TEMP_TEST_HOME", "subfolder"),
            os.path.join("~", "$TEMPORARY_SUBFOLDER", "leaf")]
    ABSPATH_ENVVARS = {"TEMP_TEST_HOME": "tmptest-home-folder",
                       "TEMPORARY_SUBFOLDER": "temp-subfolder"}
    EXPECTED_PATHS_ABSOLUTE = [
            os.path.join(os.path.expanduser("~"), "code_home",
                         "bioinformatics"),
            os.path.join("tmptest-home-folder", "subfolder"),
            os.path.join(os.path.expanduser("~"), "temp-subfolder", "leaf")]

    @pytest.fixture(scope="function")
    def pipe_iface_data(self, piface_config_bundles):
        return dict(zip(self.PIPELINE_KEYS, piface_config_bundles))

    @pytest.fixture(scope="function")
    def bundled_piface(self, pipe_iface_data):
        return {PROTOMAP_KEY: {"ATAC": "ATACSeq.py"},
                PL_KEY: pipe_iface_data}

    @pytest.fixture(scope="function", autouse=True)
    def apply_envvars(self, request):
        """ Use environment variables temporarily. """

        if "envvars" not in request.fixturenames:
            # We're autousing, so check for the relevant fixture.
            return

        original_envvars = {}
        new_envvars = request.getfixturevalue("envvars")

        # Remember values that are replaced as variables are updated.
        for name, value in new_envvars.items():
            try:
                original_envvars[name] = os.environ[name]
            except KeyError:
                pass
            os.environ[name] = value

        def restore():
            # Restore swapped variables and delete added ones.
            for k, v in new_envvars.items():
                try:
                    os.environ[k] = original_envvars[k]
                except KeyError:
                    del os.environ[k]
        request.addfinalizer(restore)

    def test_no_path(self, config_bundles, piface_config_bundles,
                     bundled_piface):
        """ PipelineInterface config sections need not specify path. """
        pi = PipelineInterface(bundled_piface)
        for pipe_key in self.PIPELINE_KEYS:
            piface_config = pi.select_pipeline(pipe_key)
            # Specific negative test of interest.
            assert "path" not in piface_config
            # Positive control validation.
            assert pi.select_pipeline(pipe_key) == piface_config

    @pytest.mark.parametrize(
            argnames=["pipe_path", "envvars", "expected"],
            argvalues=RELATIVE_PATH_DATA)
    def test_relative_path(
            self, config_bundles, piface_config_bundles, bundled_piface,
            pipe_path, envvars, expected, apply_envvars):
        """
        PipelineInterface construction expands pipeline path.

        Environment variable(s) expand(s), but the path remains relative
        if specified as such, deferring the joining with pipelines location,
        which makes the path absolute, until the path is actually used.

        """
        for add_path, pipe_key in zip(self.ADD_PATH, self.PIPELINE_KEYS):
            if add_path:
                bundled_piface[PL_KEY][pipe_key]["path"] = pipe_path
        pi = PipelineInterface(bundled_piface)
        for add_path, pipe_key in zip(self.ADD_PATH, self.PIPELINE_KEYS):
            if add_path:
                assert expected == pi.select_pipeline(pipe_key)["path"]
            else:
                assert "path" not in pi.select_pipeline(pipe_key)

    @pytest.mark.parametrize(
            argnames=["pipe_path", "envvars", "expected"],
            argvalues=zip(ABSOLUTE_PATHS,
                          len(ABSOLUTE_PATHS) * [ABSPATH_ENVVARS],
                          EXPECTED_PATHS_ABSOLUTE))
    def test_path_expansion(
            self, pipe_path, envvars, expected,
            config_bundles, piface_config_bundles, bundled_piface):
        """ User/environment variables are expanded. """
        for piface_data in bundled_piface[PL_KEY].values():
            piface_data["path"] = pipe_path
        pi = PipelineInterface(bundled_piface)
        for piface_data in pi.pipelines.values():
            assert expected == piface_data["path"]


class PipelinePathResolutionTests:
    """ Project requests pipeline information via an interface key. """

    def test_no_path(self, atacseq_piface_data,
                     path_config_file, atac_pipe_name):
        """ Without explicit path, pipeline is assumed parallel to config. """

        piface = PipelineInterface(path_config_file)

        # The pipeline is assumed to live alongside its configuration file.
        config_dirpath = os.path.dirname(path_config_file)
        expected_pipe_path = os.path.join(config_dirpath, atac_pipe_name)

        _, full_pipe_path, _ = \
                piface.finalize_pipeline_key_and_paths(atac_pipe_name)
        assert expected_pipe_path == full_pipe_path

    def test_relpath_with_dot_becomes_absolute(
            self, tmpdir, atac_pipe_name, atacseq_piface_data):
        """ Leading dot drops from relative path, and it's made absolute. """
        path_parts = ["relpath", "to", "pipelines", atac_pipe_name]
        sans_dot_path = os.path.join(*path_parts)
        pipe_path = os.path.join(".", sans_dot_path)
        atacseq_piface_data[atac_pipe_name]["path"] = pipe_path

        exp_path = os.path.join(tmpdir.strpath, sans_dot_path)

        path_config_file = write_config_data(
                protomap={ATAC_PROTOCOL_NAME: atac_pipe_name},
                conf_data=atacseq_piface_data, dirpath=tmpdir.strpath)
        piface = PipelineInterface(path_config_file)
        _, obs_path, _ = piface.finalize_pipeline_key_and_paths(atac_pipe_name)
        # Dot may remain in path, so assert equality of absolute paths.
        assert os.path.abspath(exp_path) == os.path.abspath(obs_path)

    @pytest.mark.parametrize(
            argnames="pipe_path", argvalues=["relative/pipelines/path"])
    def test_non_dot_relpath_becomes_absolute(
            self, atacseq_piface_data, path_config_file,
            tmpdir, pipe_path, atac_pipe_name):
        """ Relative pipeline path is made absolute when requested by key. """
        # TODO: constant-ify "path" and "ATACSeq.py", as well as possibly "pipelines"
        # and "protocol_mapping" section names of PipelineInterface
        exp_path = os.path.join(
                tmpdir.strpath, pipe_path, atac_pipe_name)
        piface = PipelineInterface(path_config_file)
        _, obs_path, _ = piface.finalize_pipeline_key_and_paths(atac_pipe_name)
        assert exp_path == obs_path

    @pytest.mark.parametrize(
            argnames=["pipe_path", "expected_path_base"],
            argvalues=[(os.path.join("$HOME", "code-base-home", "biopipes"),
                        os.path.join(os.path.expandvars("$HOME"),
                                "code-base-home", "biopipes")),
                       (os.path.join("~", "bioinformatics-pipelines"),
                        os.path.join(os.path.expanduser("~"),
                                     "bioinformatics-pipelines"))])
    def test_absolute_path(
            self, atacseq_piface_data, path_config_file, tmpdir, pipe_path,
            expected_path_base, atac_pipe_name):
        """ Absolute path regardless of variables works as pipeline path. """
        exp_path = os.path.join(
                tmpdir.strpath, expected_path_base, atac_pipe_name)
        piface = PipelineInterface(path_config_file)
        _, obs_path, _ = piface.finalize_pipeline_key_and_paths(atac_pipe_name)
        assert exp_path == obs_path


@pytest.mark.usefixtures("write_project_files", "pipe_iface_config_file")
class BasicPipelineInterfaceTests:
    """ Test cases specific to PipelineInterface """

    def test_missing_input_files(self, proj):
        """ We're interested here in lack of exception, not return value. """
        proj.samples[0].get_attr_values("all_input_files")


@pytest.mark.skip("Not implemented")
class PipelineInterfaceArgstringTests:
    """  """
    pass


@pytest.mark.skip("Not implemented")
class PipelineInterfaceLooperArgsTests:
    """  """
    pass


@pytest.mark.skip("Not implemented")
class GenericProtocolMatchTests:
    """ Pipeline interface may support 'all-other' protocols notion. """

    NAME_ANNS_FILE = "annotations.csv"

    @pytest.fixture
    def prj_data(self):
        """ Provide basic Project data. """
        return {
            METADATA_KEY: {
                OUTDIR_KEY: "output",
                RESULTS_SUBDIR_KEY: "results_pipeline",
                SUBMISSION_SUBDIR_KEY: "submission"
            }
        }

    @pytest.fixture
    def sheet_lines(self):
        """ Provide sample annotations sheet lines. """
        return ["{},{}".format(SAMPLE_NAME_COLNAME, "basic_sample")]

    @pytest.fixture
    def sheet_file(self, tmpdir, sheet_lines):
        """ Write annotations sheet file and provide path. """
        anns_file = tmpdir.join(self.NAME_ANNS_FILE)
        anns_file.write(os.linesep.join(sheet_lines))
        return anns_file.strpath

    @pytest.fixture
    def iface_paths(self, tmpdir):
        """ Write basic pipeline interfaces and provide paths. """
        pass

    @pytest.fixture
    def prj(self, tmpdir, prj_data, anns_file, iface_paths):
        """ Provide basic Project. """
        prj_data[PIPELINE_INTERFACES_KEY] = iface_paths
        prj_data[METADATA_KEY][SAMPLE_ANNOTATIONS_KEY] = anns_file
        prj_file = tmpdir.join("pconf.yaml").strpath
        with open(prj_file, 'w') as f:
            yaml.dump(prj_data, f)
        return Project(prj_file)

    @pytest.mark.skip("Not implemented")
    def test_specific_protocol_match_lower_priority_interface(self):
        """ Generic protocol mapping doesn't preclude specific ones. """
        pass

    @pytest.mark.skip("Not implemented")
    def test_no_specific_protocol_match(self):
        """ Protocol match in no pipeline interface allows generic match. """
        pass
