""" Model the connection between a pipeline and a project or executor. """

import inspect
import logging
import os
import sys
if sys.version_info < (3, 3):
    from collections import Mapping
else:
    from collections.abc import Mapping
import warnings

import yaml
from yaml import SafeLoader

from .exceptions import InvalidResourceSpecificationException, \
    MissingPipelineConfigurationException, PipelineInterfaceConfigError
from .sample import Sample
from .utils import get_logger
from attmap import PathExAttMap
from divvy import DEFAULT_COMPUTE_RESOURCES_NAME, NEW_COMPUTE_KEY as COMPUTE_KEY
from divvy.const import OLD_COMPUTE_KEY
from peppy import utils as peputil
from ubiquerg import expandpath


_LOGGER = get_logger(__name__)


PL_KEY = "pipelines"
PROTOMAP_KEY = "protocol_mapping"
RESOURCES_KEY = "resources"
SUBTYPE_MAPPING_SECTION = "sample_subtypes"


@peputil.copy
class PipelineInterface(PathExAttMap):
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
            try:
                with open(config, 'r') as f:
                    config = yaml.load(f, SafeLoader)
            except yaml.parser.ParserError:
                with open(config, 'r') as f:
                    _LOGGER.error(
                        "Failed to parse YAML from {}:\n{}".
                        format(config, "".join(f.readlines())))
                raise
            self.source = config

        # Check presence of 2 main sections (protocol mapping and pipelines).
        missing = [s for s in self.REQUIRED_SECTIONS if s not in config]
        if missing:
            raise PipelineInterfaceConfigError(missing)

        # Format and add the protocol mappings and individual interfaces.
        config = expand_pl_paths(config)
        config = standardize_protocols(config)
        self.add_entries(config)

    def __repr__(self):
        """ String representation """
        source = self.pipe_iface_file or "Mapping"
        num_pipelines = len(self.pipelines)
        # TODO: could use 'name' here
        pipelines = ", ".join(self.pipelines.keys())
        return "{} from {}, with {} pipeline(s): {}".format(
                self.__class__.__name__, source, num_pipelines, pipelines)

    def choose_resource_package(self, pipeline_name, file_size):
        """
        Select resource bundle for given input file size to given pipeline.

        :param str pipeline_name: Name of pipeline.
        :param float file_size: Size of input data (in gigabytes).
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

        def notify(msg):
            msg += " for pipeline {}".format(pipeline_name)
            if self.pipe_iface_file is not None:
                msg += " in interface {}".format(self.pipe_iface_file)
            _LOGGER.debug(msg)

        pl = self.select_pipeline(pipeline_name)

        try:
            universal_compute = pl[COMPUTE_KEY]
        except KeyError:
            notify("No compute settings (by {})".format(COMPUTE_KEY))
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                try:
                    universal_compute = pl[OLD_COMPUTE_KEY]
                except KeyError:
                    universal_compute = PathExAttMap()
                else:
                    warnings.warn(
                        "To declare pipeline compute section, use {} rather "
                        "than {}".format(COMPUTE_KEY, OLD_COMPUTE_KEY),
                        DeprecationWarning)
        _LOGGER.debug("Universal compute (for {}): {}".
                      format(pipeline_name, universal_compute))

        try:
            resources = universal_compute[RESOURCES_KEY]
        except KeyError:
            try:
                resources = pl[RESOURCES_KEY]
            except KeyError:
                notify("No resources")
                return {}
        else:
            if RESOURCES_KEY in pl:
                _LOGGER.warning(
                    "{rk} section found in both {c} section and top-level "
                    "pipelines section of pipeline interface; {c} section "
                    "version will be used".format(rk=RESOURCES_KEY, c=COMPUTE_KEY))

        # Require default resource package specification.
        try:
            default_resource_package = \
                    resources[DEFAULT_COMPUTE_RESOURCES_NAME]
        except KeyError:
            raise InvalidResourceSpecificationException(
                "Pipeline resources specification lacks '{}' section".
                    format(DEFAULT_COMPUTE_RESOURCES_NAME))

        # Parse min file size to trigger use of a resource package.
        def file_size_ante(name, data):
            # Retrieve this package's minimum file size.
            # Retain backwards compatibility while enforcing key presence.
            try:
                fsize = data["min_file_size"]
            except KeyError:
                fsize = data["file_size"]
            fsize = float(fsize)
            # Negative file size is illogical and problematic for comparison.
            if fsize < 0:
                raise ValueError(
                        "Negative file size threshold for resource package "
                        "'{}': {}".format(name, fsize))
            return fsize

        # Enforce default package minimum of 0.
        if "file_size" in default_resource_package:
            del default_resource_package["file_size"]
        resources[DEFAULT_COMPUTE_RESOURCES_NAME]["min_file_size"] = 0

        try:
            # Sort packages by descending file size minimum to return first
            # package for which given file size satisfies the minimum.
            resource_packages = sorted(
                resources.items(),
                key=lambda name_and_data: file_size_ante(*name_and_data),
                reverse=True)
        except ValueError:
            _LOGGER.error("Unable to use file size to prioritize "
                          "resource packages: {}".format(resources))
            raise

        # "Descend" packages by min file size, choosing minimally-sufficient.
        for rp_name, rp_data in resource_packages:
            size_ante = file_size_ante(rp_name, rp_data)
            if file_size >= size_ante:
                _LOGGER.debug(
                    "Selected '{}' package with min file size {} Gb for file "
                    "of size {} Gb.".format(rp_name, size_ante, file_size))
                rp_data.update(universal_compute)
                return rp_data

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
                peputil.is_command_callable(script_path_only):
            _LOGGER.whisper("Expanding non-absolute script path: '%s'",
                            script_path_only)
            script_path_only = os.path.join(
                    self.pipelines_path, script_path_only)
            _LOGGER.whisper("Absolute script path: '%s'", script_path_only)
            script_path_with_flags = os.path.join(
                    self.pipelines_path, script_path_with_flags)
            _LOGGER.whisper("Absolute script path with flags: '%s'",
                            script_path_with_flags)

        return strict_pipeline_key, script_path_only, script_path_with_flags

    def get_arg_string(self, pipeline_name, sample,
                       submission_folder_path="", **null_replacements):
        """
        For a given pipeline and sample, return the argument string.

        :param str pipeline_name: Name of pipeline.
        :param Sample sample: current sample for which job is being built
        :param str submission_folder_path: path to folder in which files
            related to submission of this sample will be placed.
        :param dict null_replacements: mapping from name of Sample attribute
            name to value to use in arg string if Sample attribute's value
            is null
        :return str: command-line argument string for pipeline
        """

        def update_argtext(argtext, option, argument):
            if argument is None or "" == argument:
                _LOGGER.debug("Skipping null/empty argument for option "
                              "'{}': {}".format(option, type(argument)))
                return argtext
            _LOGGER.debug("Adding argument for pipeline option '{}': {}".
                          format(option, argument))
            return "{} {} {}".format(argtext, option, argument)

        default_filepath = os.path.join(
                submission_folder_path, sample.generate_filename())
        _LOGGER.debug("Default sample filepath: '%s'", default_filepath)
        proxies = {"yaml_file": default_filepath}
        proxies.update(null_replacements)

        _LOGGER.debug("Building arguments string")
        config = self.select_pipeline(pipeline_name)
        argstring = ""

        if "arguments" not in config:
            _LOGGER.info("No arguments found for '%s' in '%s'",
                              pipeline_name, self.pipe_iface_file)
            return argstring

        args = config["arguments"]
        for pipe_opt, sample_attr in args.iteritems():
            if sample_attr is None:
                _LOGGER.debug("Option '%s' is not mapped to a sample "
                              "attribute, so it will be added to the pipeline "
                              "argument string as a flag-like option.",
                              str(pipe_opt))
                argstring += " {}".format(pipe_opt)
                continue

            try:
               arg = getattr(sample, sample_attr)
            except AttributeError:
                _LOGGER.error(
                        "Error (missing attribute): '%s' requires sample "
                        "attribute '%s' for option '%s'",
                        pipeline_name, sample_attr, pipe_opt)
                raise

            # It's undesirable to put a null value in the argument string.
            if arg is None:
                _LOGGER.debug("Null value for sample attribute: '%s'",
                              sample_attr)
                try:
                    arg = proxies[sample_attr]
                except KeyError:
                    reason = "No default for null sample attribute: '{}'".\
                            format(sample_attr)
                    raise ValueError(reason)
                _LOGGER.debug("Found default for '{}': '{}'".
                              format(sample_attr, arg))

            argstring = update_argtext(
                    argstring, option=pipe_opt, argument=arg)

        # Add optional arguments
        if "optional_arguments" in config:
            _LOGGER.debug("Processing options")
            args = config["optional_arguments"]
            for pipe_opt, sample_attr in args.iteritems():
                _LOGGER.debug("Option '%s' maps to sample attribute '%s'",
                              pipe_opt, sample_attr)
                if sample_attr is None or sample_attr == "":
                    _LOGGER.debug("Null/empty sample attribute name for "
                                  "pipeline option '{}'".format(pipe_opt))
                    continue
                try:
                    arg = getattr(sample, sample_attr)
                except AttributeError:
                    _LOGGER.warning(
                        "> Note (missing optional attribute): '%s' requests "
                        "sample attribute '%s' for option '%s'",
                        pipeline_name, sample_attr, pipe_opt)
                    continue
                argstring = update_argtext(
                        argstring, option=pipe_opt, argument=arg)

        _LOGGER.debug("Script args: '%s'", argstring)

        return argstring

    def fetch_pipelines(self, protocol):
        """
        Fetch the mapping for a particular protocol, null if unmapped.

        :param str protocol: name/key for the protocol for which to fetch the
            pipeline(s)
        :return str | Iterable[str] | NoneType: pipeline(s) to which the given
            protocol is mapped, otherwise null
        """
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

    def get_pipeline_name(self, pipeline):
        """
        Translate a pipeline name (e.g., stripping file extension).

        :param str pipeline: Pipeline name or script (top-level key in
            pipeline interface mapping).
        :return str: translated pipeline name, as specified in config or by
            stripping the pipeline's file extension
        """
        config = self.select_pipeline(pipeline)
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

    def select_pipeline(self, pipeline_name):
        """
        Check to make sure that pipeline has an entry and if so, return it.

        :param str pipeline_name: Name of pipeline.
        :return Mapping: configuration data for pipeline indicated
        :raises MissingPipelineConfigurationException: if there's no
            configuration data for the indicated pipeline
        """
        try:
            # For unmapped pipeline, Return empty interface instead of None.
            return self[PL_KEY][pipeline_name] or dict()
        except KeyError:
            names = ["'{}'".format(p) for p in self.pipelines.keys()]
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
            _LOGGER.whisper("Expanding path: '%s'", pipe_path)
            pipe_path = expandpath(pipe_path)
            _LOGGER.whisper("Expanded: '%s'", pipe_path)
            pipe_data["path"] = pipe_path
    return piface


def standardize_protocols(piface):
    """
    Handle casing and punctuation of protocol keys in pipeline interface.

    :param MutableMapping piface: Pipeline interface data to standardize.
    :return MutableMapping: Same as the input, but with protocol keys case and
        punctuation handled in a more uniform way for matching later.
    """
    from copy import copy as cp
    assert PROTOMAP_KEY in piface, "For protocol mapping standardization, " \
        "pipeline interface data must contain key '{}'".format(PROTOMAP_KEY)
    piface[PROTOMAP_KEY] = cp(piface[PROTOMAP_KEY])
    return piface


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
                    pipeline_module = peputil.import_from_source(pipeline_filepath)
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
