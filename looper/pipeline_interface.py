""" Model the connection between a pipeline and a project or executor. """

from collections import Iterable, Mapping, OrderedDict
import inspect
import logging
import os
import warnings
import pandas as pd
from logging import getLogger

from .const import PIPELINE_REQUIREMENTS_KEY
from .exceptions import InvalidResourceSpecificationException, \
    MissingPipelineConfigurationException, PipelineInterfaceConfigError, \
    PipelineInterfaceRequirementsError
from .pipereqs import create_pipeline_requirement, RequiredExecutable
from .sample import Sample
from .const import *
from peppy import CONFIG_KEY
from attmap import PathExAttMap as PXAM
from divvy import DEFAULT_COMPUTE_RESOURCES_NAME, NEW_COMPUTE_KEY as DIVVY_COMPUTE_KEY
from divvy.const import OLD_COMPUTE_KEY
from peppy import utils as peputil
from ubiquerg import expandpath, is_command_callable, is_url
from yacman import load_yaml

_LOGGER = getLogger(__name__)


PL_KEY = "pipelines"
PROTOMAP_KEY = "protocol_mapping"
RESOURCES_KEY = "resources"
SUBTYPE_MAPPING_SECTION = "sample_subtypes"


@peputil.copy
class PipelineInterface(PXAM):
    """
    This class parses, holds, and returns information for a yaml file that
    specifies how to interact with each individual pipeline. This
    includes both resources to request for cluster job submission, as well as
    arguments to be passed from the sample annotation metadata to the pipeline

    :param str | Mapping config: path to file from which to parse
        configuration data, or pre-parsed configuration data.
    """

    REQUIRED_SECTIONS = [PL_KEY, PROTOMAP_KEY]

    def __init__(self, config):
        super(PipelineInterface, self).__init__()

        if isinstance(config, Mapping):
            self.pipe_iface_file = None
            self.source = None
        else:
            _LOGGER.debug("Parsing '%s' for %s config data",
                          config, self.__class__.__name__)
            self.pipe_iface_file = config
            self.source = config
            config = load_yaml(config)
        # Check presence of 2 main sections (protocol mapping and pipelines).
        missing = [s for s in self.REQUIRED_SECTIONS if s not in config]
        if missing:
            raise PipelineInterfaceConfigError(missing)

        # Format and add the protocol mappings and individual interfaces.
        config = expand_pl_paths(config)
        assert PROTOMAP_KEY in config, \
            "For protocol mapping standardization, pipeline interface data " \
            "must contain key '{}'".format(PROTOMAP_KEY)

        for k, v in config.items():
            if k in ["pipe_iface_file", "source"]:
                continue
            assert k not in self, \
                "Interface key already mapped: {} ({})".format(k, self[k])
            self[k] = v

    def __str__(self):
        """ String representation """
        source = self.pipe_iface_file or "Mapping"
        pipelines = self.pipelines.keys()
        collators = self[COLLATORS_KEY].keys() \
            if COLLATORS_KEY in self else None
        txt = "{} from {}. Defines {} pipelines ({})".\
            format(self.__class__.__name__, source,
                   len(pipelines),
                   ", ".join(pipelines))
        if collators:
            txt += " and {} {} ({})".\
                format(len(collators), COLLATORS_KEY, ", ".join(collators))
        return txt

    def __setitem__(self, key, value):
        if key == PIPELINE_REQUIREMENTS_KEY:
            super(PipelineInterface, self).__setitem__(
                key, read_pipe_reqs(value), finalize=False)
        elif key == PL_KEY:
            assert isinstance(value, Mapping) or not value, \
                "If non-null, value for key '{}' in interface specification " \
                "must be a mapping; got {}".format(key, type(value).__name__)
            m = PXAM()
            for k, v in value.items():
                assert isinstance(v, Mapping), \
                    "Value for pipeline {} is {}, not mapping".\
                    format(k, type(v).__name__)
                m_sub = PXAM()
                for k_sub, v_sub in v.items():
                    if k_sub == PIPELINE_REQUIREMENTS_KEY:
                        m_sub.__setitem__(k_sub, read_pipe_reqs(v_sub),
                                          finalize=False)
                    else:
                        m_sub.__setitem__(k_sub, v_sub, finalize=True)
                m.__setitem__(k, m_sub, finalize=False)
            super(PipelineInterface, self).__setitem__(key, m)
        else:
            super(PipelineInterface, self).__setitem__(key, value)

    def choose_resource_package(self, pipeline_name, namespaces, file_size,
                                collate=False):
        """
        Select resource bundle for given input file size to given pipeline.

        :param str pipeline_name: Name of pipeline.
        :param float file_size: Size of input data (in gigabytes).
        :param Mapping[Mapping[str]] namespaces: namespaced variables to pass
            as a context for fluid attributes command rendering
        :param bool collate: Whether a collate job is to be submitted (runs on
            the project level, rather that on the sample level)
        :return MutableMapping: resource bundle appropriate for given pipeline,
            for given input file size
        :raises ValueError: if indicated file size is negative, or if the
            file size value specified for any resource package is negative
        :raises _InvalidResourceSpecificationException: if no default
            resource package specification is provided
        """

        # Ensure that we have a numeric value before attempting comparison.
        file_size = float(file_size)

        if file_size < 0:
            raise ValueError("Attempted selection of resource package for "
                             "negative file size: {}".format(file_size))

        def _file_size_ante(name, data):
            # Retrieve this package's minimum file size.
            # Retain backwards compatibility while enforcing key presence.
            fsize = float(data[FILE_SIZE_COLNAME])
            # Negative file size is illogical and problematic for comparison.
            if fsize < 0:
                raise InvalidResourceSpecificationException(
                    "Found negative value () in '{}' column; package '{}'".
                        format(fsize, FILE_SIZE_COLNAME, name)
                )
            return fsize

        def _notify(msg):
            msg += " for pipeline '{}'".format(pipeline_name)
            if self.pipe_iface_file is not None:
                msg += " in interface {}".format(self.pipe_iface_file)
            _LOGGER.debug(msg)

        def _load_fluid_attrs(pipeline, pipeline_name):
            """
            Render command string (jinja2 template), execute it in a subprocess
            and its result (JSON object) as a dict

            :param Mapping pipeline: pipeline dict
            :param str pipeline_name: pipeline name
            :return Mapping: a dict with attributes returned in the JSON
                by called command
            """
            def _log_raise_latest():
                """ Log error info and raise latest handled exception """
                _LOGGER.error(
                    "Could not retrieve JSON via command: '{}'".format(
                        pipeline[COMPUTE_KEY][FLUID_ATTRS_KEY]))
                raise
            json = None
            if COMPUTE_KEY in pipeline \
                    and FLUID_ATTRS_KEY in pipeline[COMPUTE_KEY]:
                from subprocess import check_output, CalledProcessError
                from json import loads
                from .utils import jinja_render_cmd_strictly
                try:
                    cmd = jinja_render_cmd_strictly(
                        cmd_template=pipeline[COMPUTE_KEY][FLUID_ATTRS_KEY],
                        namespaces=namespaces
                    )
                    json = loads(check_output(cmd, shell=True))
                except CalledProcessError as e:
                    print(e.output)
                    _log_raise_latest()
                except Exception:
                    _log_raise_latest()
                else:
                    _LOGGER.debug(
                        "Loaded resources from JSON returned by a command for"
                        " pipeline '{}':\n{}".format(pipeline_name, json))
            return json

        def _load_size_dep_vars(piface, pipeline, pipeline_name):
            """
            Read the resources from a TSV provided in the pipeline interface

            :param looper.PipelineInterface piface: currently processed piface
            :param Mapping pipeline: pipeline dict
            :param str pipeline_name: pipeline name
            :return pandas.DataFrame: resources
            """
            df = None
            if COMPUTE_KEY in pipeline \
                    and SIZE_DEP_VARS_KEY in pipeline[COMPUTE_KEY]:
                resources_tsv_path = pipeline[COMPUTE_KEY][SIZE_DEP_VARS_KEY]
                if not os.path.isabs(resources_tsv_path):
                    resources_tsv_path = os.path.join(
                        os.path.dirname(piface.pipe_iface_file),
                        resources_tsv_path)
                df = pd.read_csv(resources_tsv_path, sep='\t', header=0).fillna(0)
                df[ID_COLNAME] = df.index
                df.set_index(ID_COLNAME)
                _LOGGER.debug("Loaded resources ({}) for pipeline '{}':\n{}".
                              format(resources_tsv_path, pipeline_name, df))
            else:
                _notify("No '{}' defined".format(SIZE_DEP_VARS_KEY))
            return df
        pl = self.select_pipeline(pipeline_name, collate=collate)
        fluid_resources = _load_fluid_attrs(pl, pipeline_name)
        if fluid_resources is not None:
            return fluid_resources
        resources_df = _load_size_dep_vars(self, pl, pipeline_name)
        resources_data = {}
        if resources_df is not None:
            resources = resources_df.to_dict('index')
            try:
                # Sort packages by descending file size minimum to return first
                # package for which given file size satisfies the minimum.
                resource_packages = sorted(
                    resources.items(),
                    key=lambda name_and_data: _file_size_ante(*name_and_data),
                    reverse=True)
            except ValueError:
                _LOGGER.error("Unable to use file size to prioritize "
                              "resource packages: {}".format(resources))
                raise

            # choose minimally-sufficient package
            for rp_name, rp_data in resource_packages:
                size_ante = _file_size_ante(rp_name, rp_data)
                if file_size >= size_ante:
                    _LOGGER.debug(
                        "Selected '{}' package with file size {} Gb for file "
                        "of size {} Gb.".format(rp_name, size_ante, file_size))
                    _LOGGER.debug("Selected resource package data:\n{}".
                                  format(rp_data))
                    resources_data = rp_data
                    break

        if COMPUTE_KEY in pl and RESOURCES_KEY in pl[COMPUTE_KEY]:
            # overwrite possibly selected size dependent data with values
            # explicitly defined in the piface
            resources_data.update(pl[COMPUTE_KEY][RESOURCES_KEY])

        project = namespaces["project"]
        if COMPUTE_KEY in project[LOOPER_KEY] \
                and RESOURCES_KEY in project[LOOPER_KEY][COMPUTE_KEY]:
            # overwrite with values from project.looper.compute.resources
            resources_data.\
                update(project[LOOPER_KEY][COMPUTE_KEY][RESOURCES_KEY])

        return resources_data

    def finalize_pipeline_key_and_paths(self, pipeline_key):
        """
        Determine pipeline's full path, arguments, and strict key.

        This handles multiple ways in which to refer to a pipeline (by key)
        within the mapping that contains the data that defines a
        PipelineInterface. It also ensures proper handling of the path to the
        pipeline (i.e., ensuring that it's absolute), and that the text for
        the arguments are appropriately dealt parsed and passed.

        :param str pipeline_key: the key in the pipeline interface file used
            for the protocol_mappings section. Previously was the script name.
        :return (str, str, str): more precise version of input key, along with
            absolute path for pipeline script, and full script path + options

        """

        # The key may contain extra command-line flags; split key from flags.
        # The strict key was previously the script name itself, something like
        # "ATACseq.py", but now is typically just something like "atacseq".
        strict_pipeline_key, _, pipeline_key_args = pipeline_key.partition(' ')

        full_pipe_path = \
                self.get_attribute(strict_pipeline_key, "path")

        if full_pipe_path:
            script_path_only = os.path.expanduser(
                os.path.expandvars(full_pipe_path[0].strip()))
            if os.path.isdir(script_path_only):
                script_path_only = os.path.join(script_path_only, pipeline_key)
            script_path_with_flags = \
                    "{} {}".format(script_path_only, pipeline_key_args)
        else:
            # backwards compatibility w/ v0.5
            script_path_only = strict_pipeline_key
            script_path_with_flags = pipeline_key

        # Clear trailing whitespace.
        script_path_only = script_path_only.rstrip()

        # TODO: determine how to deal with pipelines_path (i.e., could be null)
        if not os.path.isabs(script_path_only) and not \
                is_command_callable(script_path_only):
            _LOGGER.debug("Expanding non-absolute script path: '%s'",
                            script_path_only)
            script_path_only = os.path.join(
                    self.pipelines_path, script_path_only)
            _LOGGER.debug("Absolute script path: '%s'", script_path_only)
            script_path_with_flags = os.path.join(
                    self.pipelines_path, script_path_with_flags)
            _LOGGER.debug("Absolute script path with flags: '%s'",
                            script_path_with_flags)

        return strict_pipeline_key, script_path_only, script_path_with_flags

    def absolutize_pipeline_path(self, pipeline_key):
        """
        Make the selected pipeline's path absolute

        :param str pipeline_key: key to identify the pipeline of interest
        """
        ori_path = self.get_attribute(pipeline_key, "path")
        if ori_path:
            script_path = \
                os.path.expanduser(os.path.expandvars(ori_path[0].strip()))
            if os.path.isdir(script_path):
                script_path = os.path.join(script_path, pipeline_key)
        else:
            script_path = pipeline_key

        if not os.path.isabs(script_path) \
                and not is_command_callable(script_path):
            _LOGGER.debug("Expanding pipeline path: '{}'".format(script_path))
            script_path = os.path.join(self.pipelines_path, script_path)
        try:
            setattr(self["pipelines"][pipeline_key], "path", script_path)
            _LOGGER.debug("'{}' pipeline path set to: {}"
                          .format(pipeline_key, script_path))
        except KeyError:
            _LOGGER.warning("Could not set '{}' pipeline path: {}"
                            .format(pipeline_key, script_path))

    def parse_mapped_pipelines(self, protocol):
        """
        Parse pipielines string mapped to a specified protocol
        in the specified pipeline interface

        :param str protocol: protocol to match pipelines against
        :return Iterable[str]: pipeline keys
        """
        this_protocol_pipelines = self.fetch_pipelines(protocol)
        if not this_protocol_pipelines:
            _LOGGER.debug("No pipelines; available: {}".format(
                ", ".join(self.protocol_mapping.keys())))
            return None

        pipeline_keys = this_protocol_pipelines.split(",")
        return [pk.strip() for pk in pipeline_keys]

    def fetch_pipelines(self, protocol):
        """
        Fetch the mapping for a particular protocol, null if unmapped.

        :param str protocol: name/key for the protocol for which to fetch the
            pipeline(s)
        :return str | Iterable[str] | NoneType: pipeline(s) to which the given
            protocol is mapped, otherwise null
        """
        if not self.protocol_mapping.get(protocol):
            if GENERIC_PROTOCOL_KEY in self.protocol_mapping.keys():
                protocol = GENERIC_PROTOCOL_KEY
        return self.protocol_mapping.get(protocol)

    def fetch_sample_subtype(
            self, protocol, strict_pipe_key, full_pipe_path):
        """
        Determine the interface and Sample subtype for a protocol and pipeline.

        :param str protocol: name of the relevant protocol
        :param str strict_pipe_key: key for specific pipeline in a pipeline
            interface mapping declaration; this must exactly match a key in
            the PipelineInterface (or the Mapping that represent it)
        :param str full_pipe_path: (absolute, expanded) path to the
            pipeline script
        :return type: Sample subtype to use for jobs for the given protocol,
            that use the pipeline indicated
        :raises KeyError: if given a pipeline key that's not mapped in the
            pipelines section of this PipelineInterface
        """

        subtype = None

        this_pipeline_data = self.pipelines[strict_pipe_key]

        try:
            subtypes = this_pipeline_data[SUBTYPE_MAPPING_SECTION]
        except KeyError:
            _LOGGER.debug("Configuration (from %s) doesn't define section '%s' "
                          "for pipeline '%s'", self.source,
                          SUBTYPE_MAPPING_SECTION, strict_pipe_key)
            # Without a subtypes section, if pipeline module defines a single
            # Sample subtype, we'll assume that type is to be used when in
            # this case, when the interface section for this pipeline lacks
            # an explicit subtypes section specification.
            subtype_name = None
        else:
            if subtypes is None:
                # Designate lack of need for import attempt and provide
                # class with name to format message below.
                subtype = Sample
                _LOGGER.debug("Null %s subtype(s) section specified for "
                              "pipeline: '%s'; using base %s type",
                              subtype.__name__, strict_pipe_key,
                              subtype.__name__)
            elif isinstance(subtypes, str):
                subtype_name = subtypes
                _LOGGER.debug("Single subtype name for pipeline '%s' "
                              "in interface from '%s': '%s'", subtype_name,
                              strict_pipe_key, self.source)
            else:
                try:
                    subtype_name = subtypes[protocol]
                except KeyError:
                    # Designate lack of need for import attempt and provide
                    # class with name to format message below.
                    subtype = Sample
                    _LOGGER.debug("No %s subtype specified in interface from "
                                  "'%s': '%s', '%s'; known: %s",
                                  subtype.__name__, self.source,
                                  strict_pipe_key, protocol,
                                  ", ".join(subtypes.keys()))

        # subtype_name is defined if and only if subtype remained null.
        # The import helper function can return null if the import attempt
        # fails, so provide the base Sample type as a fallback.
        subtype = subtype or \
                  _import_sample_subtype(full_pipe_path, subtype_name) or \
                  Sample
        _LOGGER.debug("Using Sample subtype: %s", subtype.__name__)
        return subtype

    def get_attribute(self, pipeline_name, attribute_key, path_as_list=True):
        """
        Return the value of the named attribute for the pipeline indicated.

        :param str pipeline_name: name of the pipeline of interest
        :param str attribute_key: name of the pipeline attribute of interest
        :param bool path_as_list: whether to ensure that a string attribute
            is returned as a list; this is useful for safe iteration over
            the returned value.
        """
        config = self.select_pipeline(pipeline_name)
        value = config.get(attribute_key)
        return [value] if isinstance(value, str) and path_as_list else value

    def get_pipeline_name(self, pipeline, collate=False):
        """
        Translate a pipeline name (e.g., stripping file extension).

        :param str pipeline: pipeline name or script (top-level key in
            pipeline interface mapping).
        :param bool collate: whether to get a project-level name (collator)
        :return str: translated pipeline name, as specified in config or by
            stripping the pipeline's file extension
        """
        config = self.select_pipeline(pipeline, collate)
        try:
            return config["name"]
        except KeyError:
            _LOGGER.debug("No 'name' for pipeline '{}'".format(pipeline))
            return os.path.splitext(pipeline)[0]

    def iterpipes(self):
        """
        Iterate over pairs of pipeline key and interface data.

        :return iterator of (str, Mapping): Iterator over pairs of pipeline
            key and interface data
        """
        return iter(self.pipelines.items())

    def missing_requirements(self, pipeline):
        """
        Determine which requirements--if any--declared by a pipeline are unmet.

        :param str pipeline: key for pipeline for which to determine unmet reqs
        :return Iterable[looper.PipelineRequirement]: unmet requirements
        """
        reqs_data = {name: req for name, req in
                     self.get(PIPELINE_REQUIREMENTS_KEY, {}).items()}
        reqs_data.update(self.select_pipeline(pipeline).
                         get(PIPELINE_REQUIREMENTS_KEY, {}))
        return [v.req for v in reqs_data.values() if not v.satisfied]

    @property
    def pipeline_names(self):
        """
        Names of pipelines about which this interface is aware.

        :return Iterable[str]: names of pipelines about which this
            interface is aware
        """
        # TODO: could consider keying on name.
        return list(self.pipelines.keys())

    @property
    def pipelines_path(self):
        """
        Path to pipelines folder.

        :return str | None: Path to pipelines folder, if configured with
            file rather than with raw mapping.
        """
        try:
            return os.path.dirname(self.pipe_iface_file)
        except (AttributeError, TypeError):
            return None

    @property
    def pipe_iface(self):
        """
        Old-way access to pipeline key-to-interface mapping

        :return Mapping: Binding between pipeline key and interface data
        """
        warnings.warn("On {} pi, use pi.pipelines instead of pi.pipe_iface "
                      "to access mapping from pipeline key to interface.".
                      format(self.__class__.__name__), DeprecationWarning)
        return self.pipelines

    @property
    def protomap(self):
        """
        Access protocol mapping portion of this composite interface.

        :return Mapping: binding between protocol name and pipeline key.
        """
        warnings.warn("Protomap access is deprecated; please use {}"
                      .format(PROTOMAP_KEY), DeprecationWarning)
        return self.protocol_mapping

    def get_pipeline_schema(self, pipeline_name, schema_key=SCHEMA_KEY):
        """
        Get path to the pipeline schema.

        :param str pipeline_name: pipeline name
        :param str schema_key: where to look for schemas in the pipeline iface
        :return str: absolute path to the pipeline schema file
        """
        schema_source = self.get_attribute(pipeline_name, schema_key,
                                           path_as_list=False)
        _LOGGER.debug("Got schema source: {}".format(schema_source))
        if schema_source:
            if is_url(schema_source):
                return schema_source
            elif not os.path.isabs(schema_source):
                schema_source = \
                    os.path.join(os.path.split(self.pipe_iface_file)[0], schema_source)
        return schema_source

    def select_pipeline(self, pipeline_name, collate=False):
        """
        Check to make sure that pipeline has an entry and if so, return it.

        :param str pipeline_name: Name of pipeline.
        :param bool collate: whether to select from collators.
        :return Mapping: configuration data for pipeline indicated
        :raises MissingPipelineConfigurationException: if there's no
            configuration data for the indicated pipeline
        """
        pl_key = COLLATORS_KEY if collate else PL_KEY
        try:
            # For unmapped pipeline, Return empty interface instead of None.
            return self[pl_key][pipeline_name] or dict()
        except KeyError:
            names = ["'{}'".format(p) for p in self[pl_key].keys()]
            _LOGGER.error(
                "Missing pipeline description: '{}' not found ({} known: {})".
                format(pipeline_name, len(names), ", ".join(names)))
            # TODO: use defaults or force user to define this?
            raise MissingPipelineConfigurationException(pipeline_name)

    def uses_looper_args(self, pipeline_name):
        """
        Determine whether indicated pipeline accepts looper arguments.

        :param str pipeline_name: Name of pipeline to check for looper
            argument acceptance.
        :return bool: Whether indicated pipeline accepts looper arguments.
        """
        config = self.select_pipeline(pipeline_name)
        return "looper_args" in config and config["looper_args"]

    def validate(self, pipeline):
        """
        Determine whether any declared requirements are unmet.

        :param str pipeline: key for the pipeline to validate
        :return bool: whether any declared requirements are unmet
        :raise MissingPipelineConfigurationException: if the requested pipeline
            is not defined in this interface
        """
        return not self.missing_requirements(pipeline)


def expand_pl_paths(piface):
    """
    Expand path to each pipeline in a declared mapping

    :param Mapping piface: Key-value mapping in which one value is a collection
        of pipeline manifests, i.e. in the pipelines section of a pipeline
        interface config file
    :return Mapping: Same as input, but with any pipeline path expanded
    """
    assert PL_KEY in piface, "For pipeline path expansion, pipeline interface" \
        "data must contain key '{}'".format(PL_KEY)
    for pipe_data in piface[PL_KEY].values():
        if "path" in pipe_data:
            pipe_path = pipe_data["path"]
            _LOGGER.debug("Expanding path: '%s'", pipe_path)
            pipe_path = expandpath(pipe_path)
            _LOGGER.debug("Expanded: '%s'", pipe_path)
            pipe_data["path"] = pipe_path
    return piface


def read_pipe_reqs(reqs_data):
    """
    Read/parse a requirements section or subsection of a pipeline interface config.

    :param Mapping reqs_data: the data to parse; this should be a collection
        of strings (names/paths of executables), or a mapping of requirements
        declarations, keyed on name/path with each key mapping to a string
        that indicates the kind of requirement (file, folder, executable).
        If nothing's specified (list rather than dict) of requirements, or if
        the value for a requirement is empty/null, the requirement is assumed
        to be the declaration of an executable.
    :return attmap.PathExAttMap[str, looper.pipereqs.PipelineRequirement]: a
        binding between requirement name/path and validation instance
    """
    reqs_data = reqs_data or {}
    if isinstance(reqs_data, str):
        reqs_data = [reqs_data]
    if isinstance(reqs_data, Mapping):
        newval, errors = OrderedDict(), {}
        for r, t in reqs_data.items():
            try:
                newval[r] = create_pipeline_requirement(r, typename=t)
            except ValueError:
                errors[r] = t
        if errors:
            raise PipelineInterfaceRequirementsError(errors)
    elif isinstance(reqs_data, Iterable):
        newval = OrderedDict([(r, RequiredExecutable(r)) for r in reqs_data])
    else:
        raise TypeError(
            "Non-iterable pipeline requirements (key '{}'): {}".
                format(PIPELINE_REQUIREMENTS_KEY, type(reqs_data).__name__))
    return PXAM(newval)


def _import_sample_subtype(pipeline_filepath, subtype_name=None):
    """
    Import a particular Sample subclass from a Python module.

    :param str pipeline_filepath: path to file to regard as Python module
    :param str subtype_name: name of the target class (which must derive from
        the base Sample class in order for it to be used), optional; if
        unspecified, if the module defines a single subtype, then that will
        be used; otherwise, the base Sample type will be used.
    :return type: the imported class, defaulting to base Sample in case of
        failure with the import or other logic
    """
    base_type = Sample

    _, ext = os.path.splitext(pipeline_filepath)
    if ext != ".py":
        return base_type

    try:
        _LOGGER.debug("Attempting to import module defined by {}".
                      format(pipeline_filepath))

        # TODO: consider more fine-grained control here. What if verbose
        # TODO: logging is only to file, not to stdout/err?

        # Redirect standard streams during the import to prevent noisy
        # error messaging in the shell that may distract or confuse a user.
        if _LOGGER.getEffectiveLevel() > logging.DEBUG:
            with open(os.devnull, 'w') as temp_standard_streams:
                with peputil.standard_stream_redirector(temp_standard_streams):
                    pipeline_module = \
                        peputil.import_from_source(pipeline_filepath)
        else:
            pipeline_module = peputil.import_from_source(pipeline_filepath)

    except SystemExit:
        # SystemExit would be caught as BaseException, but SystemExit is
        # particularly suggestive of an a script without a conditional
        # check on __main__, and as such warrant a tailored message.
        _LOGGER.warning("'%s' appears to attempt to run on import; "
                     "does it lack a conditional on '__main__'? "
                     "Using base type: %s",
                     pipeline_filepath, base_type.__name__)
        return base_type

    except (BaseException, Exception) as e:
        _LOGGER.debug("Can't import subtype from '%s', using base %s: %r",
                     pipeline_filepath, base_type.__name__,  e)
        return base_type

    else:
        _LOGGER.debug("Successfully imported pipeline module '%s', "
                      "naming it '%s'", pipeline_filepath,
                      pipeline_module.__name__)

    def class_names(cs):
        return ", ".join([c.__name__ for c in cs])

    # Find classes from pipeline module and determine which derive from Sample.
    classes = _fetch_classes(pipeline_module)
    _LOGGER.debug("Found %d classes: %s", len(classes), class_names(classes))

    # Base Sample could be imported; we want the true subtypes.
    proper_subtypes = _proper_subtypes(classes, base_type)
    _LOGGER.debug("%d proper %s subtype(s): %s", len(proper_subtypes),
                  base_type.__name__, class_names(proper_subtypes))

    # Determine course of action based on subtype request and number found.
    if not subtype_name:
        _LOGGER.debug("No specific subtype is requested from '%s'",
                      pipeline_filepath)
        if len(proper_subtypes) == 1:
            # No specific request and single subtype --> use single subtype.
            subtype = proper_subtypes[0]
            _LOGGER.debug("Single %s subtype found in '%s': '%s'",
                          base_type.__name__, pipeline_filepath,
                          subtype.__name__)
            return subtype
        else:
            # We can't arbitrarily select from among 0 or multiple subtypes.
            # Note that this text is used in the tests, as validation of which
            # branch of the code in this function is being hit in order to
            # return the base Sample type. If it changes, the corresponding
            # tests will also need to change.
            _LOGGER.debug("%s subtype cannot be selected from %d found in "
                          "'%s'; using base type", base_type.__name__,
                          len(proper_subtypes), pipeline_filepath)
            return base_type
    else:
        # Specific subtype request --> look for match.
        for st in proper_subtypes:
            if st.__name__ == subtype_name:
                _LOGGER.debug("Successfully imported %s from '%s'",
                              subtype_name, pipeline_filepath)
                return st
        raise ValueError(
                "'{}' matches none of the {} {} subtype(s) defined "
                "in '{}': {}".format(subtype_name, len(proper_subtypes),
                                     base_type.__name__, pipeline_filepath,
                                     class_names(proper_subtypes)))


def _fetch_classes(mod):
    """ Return the classes defined in a module. """
    try:
        _, classes = zip(*inspect.getmembers(
                mod, lambda o: inspect.isclass(o)))
    except ValueError:
        return []
    return list(classes)


def _proper_subtypes(types, supertype):
    """ Determine the proper subtypes of a supertype. """
    return list(filter(
            lambda t: issubclass(t, supertype) and t != supertype, types))
