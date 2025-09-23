"""Looper version of NGS project model."""

import itertools
import os

from yaml import safe_load

try:
    from functools import cached_property
except ImportError:
    # cached_property was introduced in python 3.8
    cached_property = property

from .divvy import ComputingConfiguration
from eido import PathAttrNotFoundError, read_schema
from jsonschema import ValidationError
from pandas.core.common import flatten
from peppy.utils import make_abs_via_cfg
from pipestat import PipestatManager

from .conductor import write_pipestat_config

from .exceptions import *
from .pipeline_interface import PipelineInterface
from .processed_project import populate_project_paths, populate_sample_paths
from .utils import *
from .const import PipelineLevel

__all__ = ["Project"]

_LOGGER = getLogger(__name__)


class ProjectContext(object):
    """Wrap a Project to provide protocol-specific Sample selection."""

    def __init__(
        self,
        prj,
        selector_attribute=None,
        selector_include=None,
        selector_exclude=None,
        selector_flag=None,
        exclusion_flag=None,
    ):
        """Project and what to include/exclude defines the context."""
        if not isinstance(selector_attribute, str):
            raise TypeError(
                "Name of attribute for sample selection isn't a string: {} "
                "({})".format(selector_attribute, type(selector_attribute))
            )
        self.prj = prj
        self.include = selector_include
        self.exclude = selector_exclude
        self.attribute = selector_attribute
        self.selector_flag = selector_flag
        self.exclusion_flag = exclusion_flag

    def __getattr__(self, item):
        """Samples are context-specific; other requests are handled
        locally or dispatched to Project."""
        if item == "samples":
            return fetch_samples(
                prj=self.prj,
                selector_attribute=self.attribute,
                selector_include=self.include,
                selector_exclude=self.exclude,
                selector_flag=self.selector_flag,
                exclusion_flag=self.exclusion_flag,
            )
        if item in ["prj", "include", "exclude"]:
            # Attributes requests that this context/wrapper handles
            return self.__dict__[item]
        else:
            # Dispatch attribute request to Project.
            if hasattr(self.prj, item):
                return getattr(self.prj, item)
            else:
                return self.prj.get(item)

    def __getitem__(self, item):
        """Provide the Mapping-like item access to the instance's Project."""
        return self.prj[item]

    def __enter__(self):
        """References pass through this instance as needed, so the context
        provided is the instance itself."""
        return self

    def __repr__(self):
        return self.prj.__repr__()

    def __exit__(self, *args):
        """Context teardown."""
        pass


class Project(peppyProject):
    """
    Looper-specific Project.

    :param str cfg: path to configuration file with data from
        which Project is to be built
    :param Iterable[str] amendments: name indicating amendment to use, optional
    :param str divcfg_path: path to an environment configuration YAML file
        specifying compute settings.
    :param bool permissive: Whether a error should be thrown if
        a sample input file(s) do not exist or cannot be open.
    :param str compute_env_file: Environment configuration YAML file specifying
        compute settings.
    """

    def __init__(self, cfg=None, amendments=None, divcfg_path=None, **kwargs):
        super(Project, self).__init__(cfg=cfg, amendments=amendments)
        prj_dict = kwargs.get("project_dict")
        pep_config = kwargs.get("pep_config", None)
        if pep_config:
            self["pep_config"] = pep_config

        # init project from pephub pep_config:
        if prj_dict is not None and cfg is None:
            self._from_dict(prj_dict)
            self["_config_file"] = os.getcwd()  # for finding pipeline interface
            self["pep_config"] = pep_config

        self[EXTRA_KEY] = {}

        try:
            # For loading PEPs via CSV, Peppy cannot infer project name.
            name = self.name
        except NotImplementedError:
            self.name = None

        # add sample pipeline interface to the project
        if kwargs.get(SAMPLE_PL_ARG):
            self.set_sample_piface(kwargs.get(SAMPLE_PL_ARG))

        for attr_name in CLI_PROJ_ATTRS:
            if attr_name in kwargs:
                self[EXTRA_KEY][attr_name] = kwargs[attr_name]
                # setattr(self[EXTRA_KEY], attr_name, kwargs[attr_name])
        self._samples_by_interface = self._samples_by_piface(self.piface_key)
        self._interfaces_by_sample = self._piface_by_samples()
        self.linked_sample_interfaces = self._get_linked_pifaces()
        if FILE_CHECKS_KEY in self[EXTRA_KEY]:
            setattr(self, "file_checks", not self[EXTRA_KEY][FILE_CHECKS_KEY])
        if DRY_RUN_KEY in self[EXTRA_KEY]:
            setattr(self, DRY_RUN_KEY, self[EXTRA_KEY][DRY_RUN_KEY])
        self.dcc = (
            None
            if divcfg_path is None
            else ComputingConfiguration.from_yaml_file(filepath=divcfg_path)
        )
        if DRY_RUN_KEY in self and not self[DRY_RUN_KEY]:
            _LOGGER.debug("Ensuring project directories exist")
            self.make_project_dirs()

    @property
    def piface_key(self):
        """
        Name of the pipeline interface attribute for this project

        :return str: name of the pipeline interface attribute
        """
        return self._extra_cli_or_cfg(PIFACE_KEY_SELECTOR) or PIPELINE_INTERFACES_KEY

    @property
    def selected_compute_package(self):
        """
        Compute package name specified in object constructor

        :return str: compute package name
        """
        return self._extra_cli_or_cfg(COMPUTE_PACKAGE_KEY)

    @property
    def cli_pifaces(self):
        """
        Collection of pipeline interface sources specified in object constructor

        :return list[str]: collection of pipeline interface sources
        """
        x = self._extra_cli_or_cfg(self.piface_key)
        return (
            list(flatten([x] if not isinstance(x, list) else x))
            if x is not None
            else None
        )

    @property
    def output_dir(self):
        """
        Output directory for the project, specified in object constructor

        :return str: path to the output directory
        """
        return self._extra_cli_or_cfg(OUTDIR_KEY, strict=True)

    def _extra_cli_or_cfg(self, attr_name, strict=False):
        """
        Get attribute value provided in kwargs in object constructor of from
        looper section in the configuration file

        :param str attr_name: name of the attribute to get value for
        :param bool strict: whether a non-existent attribute is exceptional
        :raise MisconfigurationException: in strict mode, when no attribute
         found
        """
        try:
            result = self[EXTRA_KEY][attr_name]
            # getattr(self[EXTRA_KEY], attr_name))
        except (AttributeError, KeyError):
            pass
        else:
            if result is not None:
                return result
        if (
            CONFIG_KEY in self
            and LOOPER_KEY in self[CONFIG_KEY]
            and attr_name in self[CONFIG_KEY][LOOPER_KEY]
        ):
            return self[CONFIG_KEY][LOOPER_KEY][attr_name]
        else:
            if strict:
                raise MisconfigurationException(
                    "'{}' is missing. Provide it in the '{}' section of the "
                    "project configuration file".format(attr_name, LOOPER_KEY)
                )
            return

    @property
    def results_folder(self):
        """
        Path to the results folder for the project

        :return str: path to the results folder in the output folder
        """
        return self._out_subdir_path(RESULTS_SUBDIR_KEY, default="results_pipeline")

    @property
    def submission_folder(self):
        """
        Path to the submission folder for the project

        :return str: path to the submission in the output folder
        """
        return self._out_subdir_path(SUBMISSION_SUBDIR_KEY, default="submission")

    def _out_subdir_path(self, key: str, default: str) -> str:
        """
        Create a system path relative to the project output directory.
        The values for the names of the subdirectories are sourced from
        kwargs passed to the object constructor.

        :param str key: name of the attribute mapped to the value of interest
        :param str default: if key not specified, a default to use
        :return str: path to the folder
        """
        parent = getattr(self, OUTDIR_KEY)
        child = getattr(self[EXTRA_KEY], key, default) or default
        return os.path.join(parent, child)

    def make_project_dirs(self):
        """
        Create project directory structure if it doesn't exist.
        """
        for folder_key in ["results_folder", "submission_folder"]:
            folder_path = getattr(self, folder_key)
            _LOGGER.debug("Ensuring project dir exists: '{}'".format(folder_path))
            if not os.path.exists(folder_path):
                _LOGGER.debug(
                    "Attempting to create project folder: '{}'".format(folder_path)
                )
                try:
                    os.makedirs(folder_path)
                except OSError as e:
                    _LOGGER.warning(
                        "Could not create project folder: '{}'".format(str(e))
                    )

    @cached_property
    def project_pipeline_interface_sources(self):
        """
        Get a list of all valid project-level pipeline interface sources
        associated with this project. Sources that are file paths are expanded

        :return list[str]: collection of valid pipeline interface sources:
        """
        return (
            [self._resolve_path_with_cfg(src) for src in self.cli_pifaces]
            if self.cli_pifaces is not None
            else []
        )

    @cached_property
    def project_pipeline_interfaces(self):
        """
        Flat list of all valid project-level interface objects associated
        with this Project

        Note that only valid pipeline interfaces will show up in the
        result (ones that exist on disk/remotely and validate successfully
        against the schema)

        :return list[looper.PipelineInterface]: list of pipeline interfaces
        """
        return [
            PipelineInterface(pi, pipeline_type=PipelineLevel.PROJECT.value)
            for pi in self.project_pipeline_interface_sources
        ]

    @cached_property
    def pipeline_interfaces(self):
        """
        Flat list of all valid interface objects associated with this Project

        Note that only valid pipeline interfaces will show up in the
        result (ones that exist on disk/remotely and validate successfully
        against the schema)

        :return list[looper.PipelineInterface]: list of pipeline interfaces
        """
        return [pi for ifaces in self._interfaces_by_sample.values() for pi in ifaces]

    @cached_property
    def pipeline_interface_sources(self):
        """
        Get a list of all valid pipeline interface sources associated
        with this project. Sources that are file paths are expanded

        :return list[str]: collection of valid pipeline interface sources
        """
        return self._samples_by_interface.keys()

    @cached_property
    def pipestat_configured(self):
        """
        Whether pipestat configuration is complete for all sample pipelines

        :return bool: whether pipestat configuration is complete
        """
        return self._check_if_pipestat_configured()

    @cached_property
    def pipestat_configured_project(self):
        """
        Whether pipestat configuration is complete for all project pipelines

        :return bool: whether pipestat configuration is complete
        """
        return self._check_if_pipestat_configured(
            pipeline_type=PipelineLevel.PROJECT.value
        )

    def get_sample_piface(self, sample_name):
        """
        Get a list of pipeline interfaces associated with the specified sample.

        Note that only valid pipeline interfaces will show up in the
        result (ones that exist on disk/remotely and validate successfully
        against the schema)

        :param str sample_name: name of the sample to retrieve list of
            pipeline interfaces for
        :return list[looper.PipelineInterface]: collection of valid
            pipeline interfaces associated with selected sample
        """
        try:
            return self._interfaces_by_sample[sample_name]
        except KeyError:
            return None

    @staticmethod
    def get_schemas(pifaces, schema_key=INPUT_SCHEMA_KEY):
        """
        Get the list of unique schema paths for a list of pipeline interfaces

        :param str | Iterable[str] pifaces: pipeline interfaces to search
            schemas for
        :param str schema_key: where to look for schemas in the piface
        :return Iterable[str]: unique list of schema file paths
        """
        if isinstance(pifaces, str):
            pifaces = [pifaces]
        schema_set = set()
        for piface in pifaces:
            schema_file = piface.get_pipeline_schemas(schema_key)
            if schema_file:
                schema_set.update([schema_file])
        return list(schema_set)

    def _check_if_pipestat_configured(self, pipeline_type=PipelineLevel.SAMPLE.value):

        # First check if pipestat key is in looper_config, if not return false

        if PIPESTAT_KEY not in self[EXTRA_KEY]:
            return False
        elif PIPESTAT_KEY in self[EXTRA_KEY]:
            if self[EXTRA_KEY][PIPESTAT_KEY] is None:
                return False
            else:
                # If pipestat key is available assume user desires pipestat usage
                # This should return True OR raise an exception at this point.
                return self._get_pipestat_configuration(pipeline_type)

    def _get_pipestat_configuration(self, pipeline_type=PipelineLevel.SAMPLE.value):

        # First check if it already exists

        if pipeline_type == PipelineLevel.SAMPLE.value:
            for piface in self.pipeline_interfaces:

                pipestat_config_path = self._check_for_existing_pipestat_config(piface)

                if not pipestat_config_path:
                    self._create_pipestat_config(piface, pipeline_type)
                else:
                    piface.psm = PipestatManager(
                        config_file=pipestat_config_path,
                        multi_pipelines=True,
                        pipeline_type="sample",
                    )

        elif pipeline_type == PipelineLevel.PROJECT.value:
            for prj_piface in self.project_pipeline_interfaces:
                pipestat_config_path = self._check_for_existing_pipestat_config(
                    prj_piface
                )

                if not pipestat_config_path:
                    self._create_pipestat_config(prj_piface, pipeline_type)
                else:
                    prj_piface.psm = PipestatManager(
                        config_file=pipestat_config_path,
                        multi_pipelines=True,
                        pipeline_type="project",
                    )
        else:
            _LOGGER.error(
                msg="No pipeline type specified during pipestat configuration"
            )

        return True

    def _check_for_existing_pipestat_config(self, piface):
        """

        config files should be in looper output directory and named as:

        pipestat_config_pipelinename.yaml

        """

        # Cannot do much if we cannot retrieve the pipeline_name
        try:
            pipeline_name = piface.data["pipeline_name"]
        except KeyError:
            raise Exception(
                "To use pipestat, a pipeline_name must be set in the pipeline interface."
            )

        config_file_name = f"pipestat_config_{pipeline_name}.yaml"
        output_dir = expandpath(self.output_dir)

        config_file_path = os.path.join(
            # os.path.dirname(output_dir), config_file_name
            output_dir,
            config_file_name,
        )

        if os.path.exists(config_file_path):
            return config_file_path
        else:
            return None

    def _create_pipestat_config(self, piface, pipeline_type):
        """
        Each piface needs its own config file and associated psm
        """

        if PIPESTAT_KEY in self[EXTRA_KEY]:
            pipestat_config_dict = self[EXTRA_KEY][PIPESTAT_KEY]
        else:
            _LOGGER.debug(
                f"'{PIPESTAT_KEY}' not found in '{LOOPER_KEY}' section of the "
                f"project configuration file."
            )
            # We cannot use pipestat without it being defined in the looper config file.
            raise ValueError

        # Expand paths in the event ENV variables were used in config files
        output_dir = expandpath(self.output_dir)

        pipestat_config_dict.update({"output_dir": output_dir})

        if "output_schema" in piface.data:
            schema_path = expandpath(piface.data["output_schema"])
            if not os.path.isabs(schema_path):
                # Get path relative to the pipeline_interface
                schema_path = os.path.join(
                    os.path.dirname(piface.pipe_iface_file), schema_path
                )
            pipestat_config_dict.update({"schema_path": schema_path})
            try:
                with open(schema_path, "r") as f:
                    output_schema_data = safe_load(f)
                    output_schema_pipeline_name = output_schema_data[
                        PIPELINE_INTERFACE_PIPELINE_NAME_KEY
                    ]
            except Exception:
                output_schema_pipeline_name = None
        else:
            output_schema_pipeline_name = None
        if "pipeline_name" in piface.data:
            pipeline_name = piface.data["pipeline_name"]
            pipestat_config_dict.update({"pipeline_name": piface.data["pipeline_name"]})
        else:
            pipeline_name = None

        # Warn user if there is a mismatch in pipeline_names from sources!!!
        if pipeline_name != output_schema_pipeline_name:
            _LOGGER.warning(
                msg=f"Pipeline name mismatch detected. Pipeline interface: {pipeline_name}  Output schema: {output_schema_pipeline_name}  Defaulting to pipeline_interface value."
            )

        try:
            results_file_path = expandpath(pipestat_config_dict["results_file_path"])

            if not os.path.isabs(results_file_path):
                # e.g. user configures "results.yaml" as results_file_path
                if "{record_identifier}" in results_file_path:
                    # this is specifically to check if the user wishes tro generate a file for EACH record
                    if not os.path.exists(os.path.dirname(results_file_path)):
                        results_file_path = os.path.join(output_dir, results_file_path)
                else:
                    if not os.path.exists(os.path.dirname(results_file_path)):
                        results_file_path = os.path.join(
                            output_dir, f"{pipeline_name}/", results_file_path
                        )
            else:
                # Do nothing because the user has given an absolute file path
                pass

            pipestat_config_dict.update({"results_file_path": results_file_path})
        except KeyError:
            results_file_path = None

        try:
            flag_file_dir = expandpath(pipestat_config_dict["flag_file_dir"])
            if not os.path.isabs(flag_file_dir):
                flag_file_dir = os.path.join(os.path.dirname(output_dir), flag_file_dir)
            pipestat_config_dict.update({"flag_file_dir": flag_file_dir})
        except KeyError:
            flag_file_dir = None

        try:
            pephub_path = expandpath(pipestat_config_dict["pephub_path"])
            if is_pephub_registry_path(pephub_path):
                pipestat_config_dict.update({"pephub_path": pephub_path})
            else:
                _LOGGER.warning(
                    msg=f"Warning: PEPhub path provided is NOT a PEPhub registry {pephub_path}"
                )
        except KeyError:
            pephub_path = None

        # Pipestat_dict_ is now updated from all sources and can be written to a yaml.
        pipestat_config_path = os.path.join(
            output_dir,
            f"pipestat_config_{pipeline_name}.yaml",
        )

        # Two end goals, create a config file
        write_pipestat_config(pipestat_config_path, pipestat_config_dict)

        piface.psm = PipestatManager(
            config_file=pipestat_config_path, multi_pipelines=True
        )

        return None

    def populate_pipeline_outputs(self):
        """
        Populate project and sample output attributes based on output schemas
        that pipeline interfaces point to.
        """
        # eido.read_schema always returns a list of schemas since it supports
        # imports in schemas. The output schemas can't have the import section,
        # hence it's safe to select the fist element after read_schema() call.
        for sample in self.samples:
            sample_piface = self.get_sample_piface(sample[self.sample_table_index])
            if sample_piface:
                paths = self.get_schemas(sample_piface, OUTPUT_SCHEMA_KEY)
                for path in paths:
                    populate_sample_paths(sample, read_schema(path)[0])
        schemas = self.get_schemas(self.project_pipeline_interfaces, OUTPUT_SCHEMA_KEY)
        for schema in schemas:
            populate_project_paths(self, read_schema(schema)[0])

    def _get_linked_pifaces(self):
        """
        Get linked sample pipeline interfaces by project pipeline interface.

        These are indicated in project pipeline interface by
        'linked_pipeline_interfaces' key. If a project pipeline interface
         does not have such key defined, an empty list is returned for that
         pipeline interface.

        :return dict[list[str]]: mapping of sample pipeline interfaces
            by project pipeline interfaces
        """

        def _process_linked_piface(p, piface, prj_piface):
            piface = make_abs_via_cfg(piface, prj_piface)
            if piface not in p.pipeline_interface_sources:
                raise PipelineInterfaceConfigError(
                    "Linked sample pipeline interface was not assigned "
                    f"to any sample in this project: {piface}"
                )
            return piface

        linked_pifaces = {}
        for prj_piface in self.project_pipeline_interfaces:
            pifaces = (
                prj_piface.linked_pipeline_interfaces
                if hasattr(prj_piface, "linked_pipeline_interfaces")
                else []
            )
            linked_pifaces[prj_piface.source] = list(
                {
                    _process_linked_piface(self, piface, prj_piface.source)
                    for piface in pifaces
                }
            )
        return linked_pifaces

    def _piface_by_samples(self):
        """
        Create a mapping of all defined interfaces in this Project by samples.

        :return dict[str, list[PipelineInterface]]: a collection of pipeline
            interfaces keyed by sample name
        """
        pifaces_by_sample = {}
        for source, sample_names in self._samples_by_interface.items():
            try:
                pi = PipelineInterface(source, pipeline_type=PipelineLevel.SAMPLE.value)
            except PipelineInterfaceConfigError as e:
                _LOGGER.debug(f"Skipping pipeline interface creation: {e}")
            else:
                for sample_name in sample_names:
                    pifaces_by_sample.setdefault(sample_name, []).append(pi)
        return pifaces_by_sample

    def _omit_from_repr(self, k, cls):
        """
        Exclude the interfaces from representation.

        :param str k: key of item to consider for omission
        :param type cls: placeholder to comply with superclass signature
        """
        return super(Project, self)._omit_from_repr(k, cls) or k == "interfaces"

    def _resolve_path_with_cfg(self, pth):
        """
        Expand provided path and make it absolute using project config path

        :param str pth: path, possibly including env vars and/or relative
        :return str: absolute path
        """
        if pth is None:
            return
        pth = expandpath(pth)
        if not os.path.isabs(pth):
            pth = os.path.realpath(os.path.join(os.path.dirname(self.config_file), pth))
            _LOGGER.debug("Relative path made absolute: {}".format(pth))
        return pth

    def _samples_by_piface(self, piface_key):
        """
        Create a collection of all samples with valid pipeline interfaces

        :param str piface_key: name of the attribute that holds pipeline
         interfaces
        :return list[str]: a collection of samples keyed by pipeline interface
            source
        """
        samples_by_piface = {}
        msgs = set()
        for sample in self.samples:
            if piface_key in sample and sample[piface_key]:
                piface_srcs = sample[piface_key]
                if isinstance(piface_srcs, str):
                    piface_srcs = [piface_srcs]
                for source in piface_srcs:
                    source = self._resolve_path_with_cfg(source)
                    try:
                        PipelineInterface(
                            source, pipeline_type=PipelineLevel.SAMPLE.value
                        )
                    except (
                        ValidationError,
                        IOError,
                        PipelineInterfaceConfigError,
                    ) as e:
                        msg = (
                            "Ignoring invalid pipeline interface source: "
                            "{}. Caught exception: {}".format(
                                source, getattr(e, "message", repr(e))
                            )
                        )
                        msgs.add(msg)
                        continue
                    else:
                        samples_by_piface.setdefault(source, set())
                        samples_by_piface[source].add(sample[self.sample_table_index])
        for msg in msgs:
            _LOGGER.warning(msg)
        return samples_by_piface

    def set_sample_piface(self, sample_piface: Union[List[str], str]) -> NoReturn:
        """
        Add sample pipeline interfaces variable to object

        :param list | str sample_piface: sample pipeline interface
        """
        self.config.setdefault("sample_modifiers", {})
        self.config["sample_modifiers"].setdefault("append", {})
        self.config["sample_modifiers"]["append"]["pipeline_interfaces"] = sample_piface

        self.modify_samples()


def fetch_samples(
    prj,
    selector_attribute=None,
    selector_include=None,
    selector_exclude=None,
    selector_flag=None,
    exclusion_flag=None,
):
    """
    Collect samples of particular protocol(s).

    Protocols can't be both positively selected for and negatively
    selected against. That is, it makes no sense and is not allowed to
    specify both selector_include and selector_exclude protocols. On the
    other hand, if
    neither is provided, all of the Project's Samples are returned.
    If selector_include is specified, Samples without a protocol will be
    excluded,
    but if selector_exclude is specified, protocol-less Samples will be
    included.

    :param Project prj: the Project with Samples to fetch
    :param str selector_attribute: name of attribute on which to base the
    fetch
    :param Iterable[str] | str selector_include: protocol(s) of interest;
        if specified, a Sample must
    :param Iterable[str] | str selector_exclude: protocol(s) to include
    :param Iterable[str] | str selector_flag: flag to select on, e.g. FAILED, COMPLETED
    :param Iterable[str] | str exclusion_flag: flag to exclude on, e.g. FAILED, COMPLETED
    :return list[Sample]: Collection of this Project's samples with
        protocol that either matches one of those in selector_include,
        or either
        lacks a protocol or does not match one of those in selector_exclude
    :raise TypeError: if both selector_include and selector_exclude
    protocols are
        specified; TypeError since it's basically providing two arguments
        when only one is accepted, so remain consistent with vanilla
        Python2;
        also possible if name of attribute for selection isn't a string
    """

    kept_samples = prj.samples

    if not selector_include and not selector_exclude:
        # Default case where user does not use selector_include or selector exclude.
        # Assume that user wants to exclude samples if toggle = 0.
        # if any([hasattr(s, "toggle") for s in prj.samples]):
        # if any("toggle" in s for s in prj.samples):
        if "toggle" in prj.samples[0]:  # assume the samples have the same schema
            selector_exclude = [0]

            def keep(s):
                return (
                    not hasattr(s, selector_attribute)
                    or getattr(s, selector_attribute) not in selector_exclude
                )

            kept_samples = list(filter(keep, prj.samples))
        else:
            kept_samples = prj.samples

    # Intersection between selector_include and selector_exclude is
    # nonsense user error.
    if selector_include and selector_exclude:
        raise TypeError(
            "Specify only selector_include or selector_exclude parameter, " "not both."
        )

    if not isinstance(selector_attribute, str):
        raise TypeError(
            "Name for attribute on which to base selection isn't string: "
            "{} "
            "({})".format(selector_attribute, type(selector_attribute))
        )

    # At least one of the samples has to have the specified attribute
    if prj.samples and not any([hasattr(s, selector_attribute) for s in prj.samples]):
        if selector_attribute == "toggle":
            # this is the default, so silently pass.
            pass
        else:
            raise AttributeError(
                "The Project samples do not have the attribute '{attr}'".format(
                    attr=selector_attribute
                )
            )

    if prj.samples:
        # Use the attr check here rather than exception block in case the
        # hypothetical AttributeError would occur; we want such
        # an exception to arise, not to catch it as if the Sample lacks
        # "protocol"
        if not selector_include:
            # Loose; keep all samples not in the selector_exclude.
            def keep(s):
                return not hasattr(s, selector_attribute) or getattr(
                    s, selector_attribute
                ) not in make_set(selector_exclude)

        else:
            # Strict; keep only samples in the selector_include.
            def keep(s):
                return hasattr(s, selector_attribute) and getattr(
                    s, selector_attribute
                ) in make_set(selector_include)

        kept_samples = list(filter(keep, kept_samples))

        if selector_flag and exclusion_flag:
            raise TypeError("Specify only selector_flag or exclusion_flag not both.")

        flags = selector_flag or exclusion_flag or None
        if flags:
            # Collect uppercase flags or error if not str
            if not isinstance(flags, list):
                flags = [str(flags)]
            for flag in flags:
                if not isinstance(flag, str):
                    raise TypeError(
                        f"Supplied flags must be a string! Flag:{flag} {type(flag)}"
                    )
                flags.remove(flag)
                flags.insert(0, flag.upper())
            # Look for flags
            # Is pipestat configured? Then, the user may have set the flag folder
            if prj.pipestat_configured:
                try:
                    flag_dir = expandpath(prj[EXTRA_KEY][PIPESTAT_KEY]["flag_file_dir"])
                    if not os.path.isabs(flag_dir):
                        flag_dir = os.path.join(
                            os.path.dirname(prj.output_dir), flag_dir
                        )
                except KeyError:
                    _LOGGER.warning(
                        "Pipestat is configured but no flag_file_dir supplied, defaulting to output_dir"
                    )
                    flag_dir = prj.output_dir
            else:
                # if pipestat not configured, check the looper output dir
                flag_dir = prj.output_dir

            # Using flag_dir, search for flags:
            for sample in kept_samples:
                sample_pifaces = prj.get_sample_piface(sample[prj.sample_table_index])
                pl_name = sample_pifaces[0].pipeline_name
                flag_files = fetch_sample_flags(prj, sample, pl_name, flag_dir)
                status = get_sample_status(sample.sample_name, flag_files)
                sample.update({"status": status})

            if not selector_flag:
                # Loose; keep all samples not in the exclusion_flag.
                def keep(s):
                    return not hasattr(s, "status") or getattr(
                        s, "status"
                    ) not in make_set(flags)

            else:
                # Strict; keep only samples in the selector_flag
                def keep(s):
                    return hasattr(s, "status") and getattr(s, "status") in make_set(
                        flags
                    )

            kept_samples = list(filter(keep, kept_samples))

    return kept_samples


def make_set(items):
    if isinstance(items, str):
        items = [items]
    elif len(items) == 1:
        items = list(map(str, items))  # list(int(items[0]))
    else:
        pass
    return items
