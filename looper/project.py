""" Looper version of NGS project model. """

import itertools
import os

try:
    from functools import cached_property
except ImportError:
    # cached_property was introduced in python 3.8
    cached_property = property
from logging import getLogger

from .divvy import ComputingConfiguration
from eido import PathAttrNotFoundError, read_schema
from jsonschema import ValidationError
from pandas.core.common import flatten
from peppy import CONFIG_KEY, OUTDIR_KEY
from peppy import Project as peppyProject
from peppy.utils import make_abs_via_cfg
from pipestat import PipestatError, PipestatManager
from ubiquerg import expandpath, is_command_callable
from yacman import YAMLConfigManager

from .exceptions import *
from .pipeline_interface import PipelineInterface
from .processed_project import populate_project_paths, populate_sample_paths
from .utils import *

__all__ = ["Project"]

_LOGGER = getLogger(__name__)


class ProjectContext(object):
    """Wrap a Project to provide protocol-specific Sample selection."""

    def __init__(
        self, prj, selector_attribute=None, selector_include=None, selector_exclude=None
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

    def __getattr__(self, item):
        """Samples are context-specific; other requests are handled
        locally or dispatched to Project."""
        if item == "samples":
            return fetch_samples(
                prj=self.prj,
                selector_attribute=self.attribute,
                selector_include=self.include,
                selector_exclude=self.exclude,
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

    def __init__(
        self, cfg=None, amendments=None, divcfg_path=None, runp=False, **kwargs
    ):
        super(Project, self).__init__(cfg=cfg, amendments=amendments)
        prj_dict = kwargs.get("project_dict")

        # init project from pephub:
        if prj_dict is not None and cfg is None:
            self.from_dict(prj_dict)
            self["_config_file"] = os.getcwd()

        self[EXTRA_KEY] = {}

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
            else ComputingConfiguration(filepath=divcfg_path)
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
            PipelineInterface(pi, pipeline_type="project")
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
        return self._check_if_pipestat_configured(project_level=True)

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

    def build_submission_bundles(self, protocol, priority=True):
        """
        Create pipelines to submit for each sample of a particular protocol.

        With the argument (flag) to the priority parameter, there's control
        over whether to submit pipeline(s) from only one of the project's
        known pipeline locations with a match for the protocol, or whether to
        submit pipelines created from all locations with a match for the
        protocol.

        :param str protocol: name of the protocol/library for which to
            create pipeline(s)
        :param bool priority: to only submit pipeline(s) from the first of the
            pipelines location(s) (indicated in the project config file) that
            has a match for the given protocol; optional, default True
        :return Iterable[(PipelineInterface, type, str, str)]:
        :raises AssertionError: if there's a failure in the attempt to
            partition an interface's pipeline scripts into disjoint subsets of
            those already mapped and those not yet mapped
        """

        if not priority:
            raise NotImplementedError(
                "Currently, only prioritized protocol mapping is supported "
                "(i.e., pipeline interfaces collection is a prioritized list, "
                "so only the first interface with a protocol match is used.)"
            )

        # Pull out the collection of interfaces (potentially one from each of
        # the locations indicated in the project configuration file) as a
        # sort of pool of information about possible ways in which to submit
        # pipeline(s) for sample(s) of the indicated protocol.
        pifaces = self.interfaces.get_pipeline_interface(protocol)
        if not pifaces:
            raise PipelineInterfaceConfigError(
                "No interfaces for protocol: {}".format(protocol)
            )

        # coonvert to a list, in the future we might allow to match multiple
        pifaces = pifaces if isinstance(pifaces, str) else [pifaces]

        job_submission_bundles = []
        new_jobs = []

        _LOGGER.debug("Building pipelines matched by protocol: {}".format(protocol))

        for pipe_iface in pifaces:
            # Determine how to reference the pipeline and where it is.
            path = pipe_iface["path"]
            if not (os.path.exists(path) or is_command_callable(path)):
                _LOGGER.warning("Missing pipeline script: {}".format(path))
                continue

            # Add this bundle to the collection of ones relevant for the
            # current PipelineInterface.
            new_jobs.append(pipe_iface)
            job_submission_bundles.append(new_jobs)
        return list(itertools.chain(*job_submission_bundles))

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

    def get_pipestat_managers(self, sample_name=None, project_level=False):
        """
        Get a collection of pipestat managers for the selected sample or project.

        The number of pipestat managers corresponds to the number of unique
        output schemas in the pipeline interfaces specified by the sample or project.

        :param str sample_name: sample name to get pipestat managers for
        :param bool project_level: whether the project PipestatManagers
            should be returned
        :return dict[str, pipestat.PipestatManager]: a mapping of pipestat
            managers by pipeline interface name
        """
        pipestat_configs = self._get_pipestat_configuration(
            sample_name=sample_name, project_level=project_level
        )
        return {
            pipeline_name: PipestatManager(**pipestat_vars)
            for pipeline_name, pipestat_vars in pipestat_configs.items()
        }

    def _check_if_pipestat_configured(self, project_level=False):
        """
        A helper method determining whether pipestat configuration is complete

        :param bool project_level: whether the project pipestat config should be checked
        :return bool: whether pipestat configuration is complete
        """
        try:
            if project_level:
                pipestat_configured = self._get_pipestat_configuration(
                    sample_name=None, project_level=project_level
                )
            else:
                for s in self.samples:
                    pipestat_configured = self._get_pipestat_configuration(
                        sample_name=s.sample_name
                    )
        except Exception as e:
            context = (
                f"Project '{self.name}'"
                if project_level
                else f"Sample '{s.sample_name}'"
            )
            _LOGGER.debug(
                f"Pipestat configuration incomplete for {context}; "
                f"caught exception: {getattr(e, 'message', repr(e))}"
            )
            return False
        else:
            if pipestat_configured is not None and pipestat_configured != {}:
                return True
            else:
                return False

    def _get_pipestat_configuration(self, sample_name=None, project_level=False):
        """
        Get all required pipestat configuration variables from looper_config file
        """

        def _get_val_from_attr(pipestat_sect, object, attr_name, default, no_err=False):
            """
            Get configuration value from an object's attribute or return default

            :param dict pipestat_sect: pipestat section for sample or project
            :param peppy.Sample | peppy.Project object: object to get the
                configuration values for
            :param str attr_name: attribute name with the value to retrieve
            :param str default: default attribute name
            :param bool no_err: do not raise error in case the attribute is missing,
                in order to use the values specified in a different way, e.g. in pipestat config
            :return str: retrieved configuration value
            """
            if pipestat_sect is not None and attr_name in pipestat_sect:
                return pipestat_sect[attr_name]
            try:
                return object[default]
            except KeyError:
                if no_err:
                    return None
                raise AttributeError(f"'{default}' attribute is missing")

        ret = {}
        if not project_level and sample_name is None:
            raise ValueError(
                "Must provide the sample_name to determine the "
                "sample to get the PipestatManagers for"
            )
        key = "project" if project_level else "sample"
        # self[EXTRA_KEY] pipestat is stored here on the project if added to looper config file.
        if DEFAULT_PIPESTAT_CONFIG_ATTR in self[EXTRA_KEY]:
            pipestat_config = self[EXTRA_KEY][DEFAULT_PIPESTAT_CONFIG_ATTR]
        else:
            _LOGGER.debug(
                f"'{PIPESTAT_KEY}' not found in '{LOOPER_KEY}' section of the "
                f"project configuration file."
            )
            # We can't use pipestat without the config file
            raise ValueError

        pipestat_config_path = self._resolve_path_with_cfg(pth=pipestat_config)

        pipestat_config = YAMLConfigManager(filepath=pipestat_config_path)
        try:
            results_file_path = pipestat_config.data["results_file_path"]
            if not os.path.exists(os.path.dirname(results_file_path)):
                results_file_path = os.path.join(
                    os.path.dirname(self.output_dir), results_file_path
                )
        except KeyError:
            results_file_path = None

        try:
            flag_file_dir = pipestat_config.data["flag_file_dir"]
            if not os.path.isabs(flag_file_dir):
                flag_file_dir = os.path.join(
                    os.path.dirname(self.output_dir), flag_file_dir
                )
        except KeyError:
            flag_file_dir = None

        try:
            output_schema_path = pipestat_config.data["schema_path"]
            if not os.path.isabs(output_schema_path):
                output_schema_path = os.path.join(
                    os.path.dirname(self.output_dir), output_schema_path
                )
        except KeyError:
            output_schema_path = None

        pifaces = (
            self.project_pipeline_interfaces
            if project_level
            else self._interfaces_by_sample[sample_name]
        )
        for piface in pifaces:
            rec_id = sample_name

            ret[piface.pipeline_name] = {
                "config_file": pipestat_config_path,
                "results_file_path": results_file_path,
                "flag_file_dir": flag_file_dir,
                "sample_name": rec_id,
                "schema_path": output_schema_path,
                "output_dir": self.output_dir,
            }
        return ret

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
                pi = PipelineInterface(source, pipeline_type="sample")
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
                        PipelineInterface(source, pipeline_type="sample")
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
    prj, selector_attribute=None, selector_include=None, selector_exclude=None
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

            return list(filter(keep, prj.samples))
        else:
            return list(prj.samples)

    if not isinstance(selector_attribute, str):
        raise TypeError(
            "Name for attribute on which to base selection isn't string: "
            "{} "
            "({})".format(selector_attribute, type(selector_attribute))
        )

    # At least one of the samples has to have the specified attribute
    if prj.samples and not any([hasattr(s, selector_attribute) for s in prj.samples]):
        raise AttributeError(
            "The Project samples do not have the attribute '{attr}'".format(
                attr=selector_attribute
            )
        )

    # Intersection between selector_include and selector_exclude is
    # nonsense user error.
    if selector_include and selector_exclude:
        raise TypeError(
            "Specify only selector_include or selector_exclude parameter, " "not both."
        )

    # Ensure that we're working with sets.
    def make_set(items):
        try:
            # Check if user input single integer value for inclusion/exclusion criteria
            if len(items) == 1:
                items = list(map(int, items))  # list(int(items[0]))
        except:
            if isinstance(items, str):
                items = [items]
        return items

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

    return list(filter(keep, prj.samples))
