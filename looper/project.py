""" Looper version of NGS project model. """

from collections import namedtuple
from functools import partial
from logging import getLogger
import itertools
import os

import peppy
from peppy import OUTDIR_KEY, CONFIG_KEY
from divvy import DEFAULT_COMPUTE_RESOURCES_NAME, ComputingConfiguration
from ubiquerg import is_command_callable, is_url
from .const import *
from .exceptions import DuplicatePipelineKeyException, \
    PipelineInterfaceRequirementsError, MisconfigurationException
from .pipeline_interface import PROTOMAP_KEY
from .project_piface_group import ProjectPifaceGroup
from .utils import partition


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"

__all__ = ["Project", "process_pipeline_interfaces"]


_LOGGER = getLogger(__name__)


class ProjectContext(object):
    """ Wrap a Project to provide protocol-specific Sample selection. """

    def __init__(self, prj, selector_attribute="protocol",
                 selector_include=None, selector_exclude=None):
        """ Project and what to include/exclude defines the context. """
        if not isinstance(selector_attribute, str):
            raise TypeError(
                "Name of attribute for sample selection isn't a string: {} "
                "({})".format(selector_attribute, type(selector_attribute)))
        self.prj = prj
        self.include = selector_include
        self.exclude = selector_exclude
        self.attribute = selector_attribute

    def __getattr__(self, item):
        """ Samples are context-specific; other requests are handled
        locally or dispatched to Project. """
        if item == "samples":
            return fetch_samples(prj=self.prj,
                                 selector_attribute=self.attribute,
                                 selector_include=self.include,
                                 selector_exclude=self.exclude)
        if item in ["prj", "include", "exclude"]:
            # Attributes requests that this context/wrapper handles
            return self.__dict__[item]
        else:
            # Dispatch attribute request to Project.
            return getattr(self.prj, item)

    def __getitem__(self, item):
        """ Provide the Mapping-like item access to the instance's Project. """
        return self.prj[item]

    def __enter__(self):
        """ References pass through this instance as needed, so the context
         provided is the instance itself. """
        return self

    def __exit__(self, *args):
        """ Context teardown. """
        pass


class Project(peppy.Project):
    """
    Looper-specific NGS Project.

    :param str config_file: path to configuration file with data from
        which Project is to be built
    :param Iterable[str] amendments: name indicating amendment to use, optional
    :param str compute_env_file: Environment configuration YAML file specifying
        compute settings.
    :param Iterable[str] pifaces: list of path to pipeline interfaces.
        Overrides the config-defined ones.
    :param bool dry: If dry mode is activated, no directories
        will be created upon project instantiation.
    :param bool permissive: Whether a error should be thrown if
        a sample input file(s) do not exist or cannot be open.
    :param bool file_checks: Whether sample input files should be checked
        for their  attributes (read type, read length)
        if this is not set in sample metadata.
    :param str compute_env_file: Environment configuration YAML file specifying
        compute settings.
    :param type no_environment_exception: type of exception to raise if environment
        settings can't be established, optional; if null (the default),
        a warning message will be logged, and no exception will be raised.
    :param type no_compute_exception: type of exception to raise if compute
        settings can't be established, optional; if null (the default),
        a warning message will be logged, and no exception will be raised.
    """
    def __init__(self, config_file, amendments=None, pifaces=None, dry=False,
                 compute_env_file=None, no_environment_exception=RuntimeError,
                no_compute_exception=RuntimeError, file_checks=False,
                 permissive=True, **kwargs):
        super(Project, self).__init__(config_file, amendments=amendments,
                                      **kwargs)
        if LOOPER_KEY not in self[CONFIG_KEY]:
            raise MisconfigurationException("'{}' key not found in config".
                                            format(LOOPER_KEY))
        pifaces_paths = pifaces or \
                        self[CONFIG_KEY][LOOPER_KEY][PIPELINE_INTERFACES_KEY]
        self.interfaces = process_pipeline_interfaces(pifaces_paths)
        self.file_checks = file_checks
        self.permissive = permissive
        self.dcc = ComputingConfiguration(
            config_file=compute_env_file, no_env_error=no_environment_exception,
            no_compute_exception=no_compute_exception
        )
        # Set project's directory structure
        if not dry:
            _LOGGER.debug("Ensuring project directories exist")
            self.make_project_dirs()

    @property
    def project_folders(self):
        """ Critical project folder keys """
        return {OUTDIR_KEY: OUTDIR_KEY,
                RESULTS_SUBDIR_KEY: "results_pipeline",
                SUBMISSION_SUBDIR_KEY: "submission"}

    @property
    def results_folder(self):
        return self._relpath(RESULTS_FOLDER_KEY)

    @property
    def submission_folder(self):
        return self._relpath(SUBMISSION_FOLDER_KEY)

    @property
    def output_dir(self):
        """
        Directory in which to place results and submissions folders.
        By default, assume that the project's configuration file specifies
        an output directory, and that this is therefore available within
        the project metadata. If that assumption does not hold, though,
        consider the folder in which the project configuration file lives
        to be the project's output directory.
        :return str: path to the project's output directory, either as
            specified in the configuration file or the folder that contains
            the project's configuration file.
        :raise Exception: if this property is requested on a project that
            was not created from a config file and lacks output folder
            declaration in its metadata section
        """
        try:
            return self[CONFIG_KEY][LOOPER_KEY][OUTDIR_KEY]
        except KeyError:
            if not self.config_file:
                raise Exception("Project lacks both a config file and an "
                                "output folder in metadata; using ")
            return os.path.dirname(self.config_file)

    def _relpath(self, key):
        return os.path.join(
            self[CONFIG_KEY][LOOPER_KEY][OUTDIR_KEY],
            self[CONFIG_KEY][LOOPER_KEY].get(key, self.project_folders[key]))

    def make_project_dirs(self):
        """
        Creates project directory structure if it doesn't exist.
        """
        for folder_key, folder_val in self.project_folders.items():
            try:
                folder_path = self[CONFIG_KEY][LOOPER_KEY][folder_key]
            except KeyError:
                if OUTDIR_KEY in self[CONFIG_KEY][LOOPER_KEY]:
                    folder_path = \
                        os.path.join(self[CONFIG_KEY][LOOPER_KEY][OUTDIR_KEY],
                                     folder_val)
                    _LOGGER.debug("Ensuring project dir exists: '{}'".
                                  format(folder_path))
                else:
                    raise MisconfigurationException("'{}' not found in config"
                                                    .format(OUTDIR_KEY))
            if not os.path.exists(folder_path):
                _LOGGER.debug("Attempting to create project folder: '{}'".
                              format(folder_path))
                try:
                    os.makedirs(folder_path)
                except OSError as e:
                    _LOGGER.warning("Could not create project folder: '{}'".
                                    format(str(e)))

    @property
    def protocols(self):
        """
        Determine this Project's unique protocol names.
        :return Set[str]: collection of this Project's unique protocol names
        """
        protos = set()
        for s in self.samples:
            try:
                protos.add(s.protocol)
            except AttributeError:
                _LOGGER.debug("Sample '{}' lacks protocol".
                              format(s.sample_name))
        return protos

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
                "so only the first interface with a protocol match is used.)")

        # Pull out the collection of interfaces (potentially one from each of
        # the locations indicated in the project configuration file) as a
        # sort of pool of information about possible ways in which to submit
        # pipeline(s) for sample(s) of the indicated protocol.
        try:
            pipeline_interfaces = self.get_interfaces(protocol)
        except KeyError:
            # Messaging can be done by the caller.
            _LOGGER.debug("No interface for protocol: %s", protocol)
            return []

        job_submission_bundles = []
        pipeline_keys_used = set()
        _LOGGER.debug("Building pipelines for {} interface(s)...".
                      format(len(pipeline_interfaces)))

        bundle_by_strict_pipe_key = {}

        for pipe_iface in pipeline_interfaces:
            pipeline_keys = pipe_iface.parse_mapped_pipelines(protocol)
            if pipeline_keys is None:
                continue

            # Skip over pipelines already mapped by another location.
            already_mapped, new_scripts = \
                partition(pipeline_keys,
                          partial(_is_member, items=pipeline_keys_used))
            pipeline_keys_used |= set(pipeline_keys)

            # Attempt to validate that partition yielded disjoint subsets.
            try:
                disjoint_partition_violation = \
                    set(already_mapped) & set(new_scripts)
            except TypeError:
                _LOGGER.debug("Unable to hash partitions for validation")
            else:
                assert not disjoint_partition_violation, \
                    "Partitioning {} with membership in {} as " \
                    "predicate produced intersection: {}".format(
                        pipeline_keys, pipeline_keys_used,
                        disjoint_partition_violation)

            if len(already_mapped) > 0:
                _LOGGER.debug("Skipping {} already-mapped script name(s): {}".
                              format(len(already_mapped), already_mapped))
            _LOGGER.debug("{} new scripts for protocol {} from "
                          "pipeline(s) location '{}': {}".
                          format(len(new_scripts), protocol,
                                 pipe_iface.source, new_scripts))

            # For each pipeline script to which this protocol will pertain,
            # create the new jobs/submission bundles.
            new_jobs = []
            for pipeline_key in new_scripts:
                # Determine how to reference the pipeline and where it is.
                strict_pipe_key, full_pipe_path, full_pipe_path_with_flags = \
                    pipe_iface.finalize_pipeline_key_and_paths(pipeline_key)
                # Skip and warn about nonexistent alleged pipeline path.
                if not (os.path.exists(full_pipe_path) or
                        is_command_callable(full_pipe_path)):
                    _LOGGER.warning(
                        "Missing pipeline script: '%s'", full_pipe_path)
                    continue

                if not pipe_iface.validate(pipeline_key):
                    unmet = pipe_iface.missing_requirements(pipeline_key)
                    _LOGGER.warning(
                        "{n} requirements unsatisfied for pipeline '{p}' "
                        "(interface from {s}): {data}".format(
                            n=len(unmet), p=pipeline_key, s=pipe_iface.source,
                            data=unmet))
                    continue

                # Determine which interface and Sample subtype to use.
                sample_subtype = \
                    pipe_iface.fetch_sample_subtype(
                            protocol, strict_pipe_key, full_pipe_path)

                # Package the pipeline's interface, subtype, command, and key.
                submission_bundle = SubmissionBundle(
                    pipe_iface, sample_subtype, strict_pipe_key,
                    full_pipe_path_with_flags)

                # Enforce bundle uniqueness for each strict pipeline key.
                maybe_new_bundle = (full_pipe_path_with_flags,
                                    sample_subtype, pipe_iface)
                old_bundle = bundle_by_strict_pipe_key.setdefault(
                    strict_pipe_key, maybe_new_bundle)
                if old_bundle != maybe_new_bundle:
                    errmsg = "Strict pipeline key '{}' maps to more than " \
                             "one combination of pipeline script + flags, " \
                             "sample subtype, and pipeline interface. " \
                             "'{}'\n{}".format(strict_pipe_key,
                                               maybe_new_bundle, old_bundle)
                    raise ValueError(errmsg)

                # Add this bundle to the collection of ones relevant for the
                # current PipelineInterface.
                new_jobs.append(submission_bundle)

            job_submission_bundles.append(new_jobs)

        # Repeat logic check of short-circuit conditional to account for
        # edge case in which it's satisfied during the final iteration.
        if priority and len(job_submission_bundles) > 1:
            return job_submission_bundles[0]
        else:
            return list(itertools.chain(*job_submission_bundles))

    def get_interfaces(self, protocol):
        """
        Get the pipeline interfaces associated with the given protocol.

        :param str protocol: name of the protocol for which to get interfaces
        :return Iterable[looper.PipelineInterface]: collection of pipeline
            interfaces associated with the given protocol
        :raise KeyError: if the given protocol is not (perhaps yet) mapped
            to any pipeline interface
        """
        return self.interfaces[protocol]

    def get_schemas(self, protocols):
        """
        Get the list of unique schema paths for a list of protocols

        :param str | Iterable[str] protocols: protocols to
            search pipeline schemas for
        :return Iterable[str]: unique list of schema file paths
        """
        if isinstance(protocols, str):
            protocols = [protocols]
        schema_set = set()
        for protocol in protocols:
            for piface in self.get_interfaces(protocol):
                pipelines = piface.parse_mapped_pipelines(protocol)
                if not isinstance(pipelines, list):
                    pipelines = [pipelines]
                for pipeline in pipelines:
                    schema_file = piface.get_pipeline_schema(pipeline)
                    if schema_file:
                        schema_set.update([schema_file])
        return list(schema_set)

    def get_outputs(self, skip_sample_less=True):
        """
        Map pipeline identifier to collection of output specifications.

        This method leverages knowledge of two collections of different kinds
        of entities that meet in the manifestation of a Project. The first
        is a collection of samples, which is known even in peppy.Project. The
        second is a mapping from protocol/assay/library strategy to a collection
        of pipeline interfaces, in which kinds of output may be declared.

        Knowledge of these two items is here harnessed to map the identifier
        for each pipeline about which this Project is aware to a collection of
        pairs of identifier for a kind of output and the collection of
        this Project's samples for which it's applicable (i.e., those samples
        with protocol that maps to the corresponding pipeline).

        :param bool skip_sample_less: whether to omit pipelines that are for
            protocols of which the Project has no Sample instances
        :return Mapping[str, Mapping[str, namedtuple]]: collection of bindings
            between identifier for pipeline and collection of bindings between
            name for a kind of output and pair in which first component is a
            path template and the second component is a collection of
            sample names
        :raise TypeError: if argument to sample-less pipeline skipping parameter
            is not a Boolean
        """
        if not isinstance(skip_sample_less, bool):
            raise TypeError(
                "Non-Boolean argument to sample-less skip flag: {} ({})".
                format(skip_sample_less, type(skip_sample_less)))
        prots_data_pairs = _gather_ifaces(self.interfaces)
        m = {}
        for name, (prots, data) in prots_data_pairs.items():
            try:
                outs = data[OUTKEY]
            except KeyError:
                _LOGGER.debug("No {} declared for pipeline: {}".
                              format(OUTKEY, name))
                continue
            snames = \
                [s.sample_name for s in self.samples if s.protocol in prots]
            if not snames and skip_sample_less:
                _LOGGER.debug("No samples matching protocol(s): {}".
                              format(", ".join(prots)))
                continue
            m[name] = {path_key: (path_val, snames)
                       for path_key, path_val in outs.items()}
        return m

    def _omit_from_repr(self, k, cls):
        """
        Exclude the interfaces from representation.

        :param str k: key of item to consider for omission
        :param type cls: placeholder to comply with superclass signature
        """
        return super(Project, self)._omit_from_repr(k, cls) or k == "interfaces"


def _gather_ifaces(ifaces):
    """
    For each pipeline map identifier to protocols and interface data.

    :param Iterable[looper.PipelineInterface] ifaces: collection of pipeline
        interface objects
    :return Mapping[str, (set[str], attmap.AttMap)]: collection of bindings
        between pipeline identifier and pair in which first component is
        collection of associated protocol names, and second component is a
        collection of interface data for pipeline identified by the key
    :raise looper.DuplicatePipelineKeyException: if the same identifier (key or
        name) points to collections of pipeline interface data (for a
        particular pipeline) that are not equivalent
    """
    specs = {}
    for pi in ifaces:
        protos_by_name = {}
        for p, names in pi[PROTOMAP_KEY].items():
            if isinstance(names, str):
                names = [names]
            for n in names:
                protos_by_name.setdefault(n, set()).add(p)
        for k, dat in pi.iterpipes():
            name = dat.get("name") or k
            try:
                old_prots, old_dat = specs[name]
            except KeyError:
                old_prots = set()
            else:
                if dat != old_dat:
                    raise DuplicatePipelineKeyException(name)
            new_prots = protos_by_name.get(name, set()) | \
                        protos_by_name.get(k, set())
            specs[name] = (old_prots | new_prots, dat)
    return specs


def process_pipeline_interfaces(piface_paths):
    """
    Create a PipelineInterface for each pipeline location given.

    :param Iterable[str] | str piface_paths: locations, each of
        which should be either a directory path or a filepath, that specifies
        pipeline interface and protocol mappings information. Each such file
        should have a pipelines section and a protocol mappings section.
    :return Mapping[str, Iterable[PipelineInterface]]: mapping from protocol
        name to interface(s) for which that protocol is mapped
    """
    iface_group = ProjectPifaceGroup()
    piface_paths = piface_paths \
        if isinstance(piface_paths, list) else [piface_paths]
    for loc in piface_paths:
        if not os.path.exists(loc):
            if not is_url(loc):
                _LOGGER.warning("Ignoring nonexistent pipeline interface "
                                "location: {}".format(loc))
                continue
            _LOGGER.debug("Got remote pipeline interface: {}".format(loc))
        if os.path.isdir(loc):
            # loc is a directory, get all the yamls
            fs = [os.path.join(loc, f) for f in os.listdir(loc)
                  if os.path.splitext(f)[1] in [".yaml", ".yml"]]
        else:
            # existing file or URL
            fs = [loc]
        for f in fs:
            _LOGGER.debug("Processing interface definition: {}".format(f))
            try:
                iface_group.update(f)
            except PipelineInterfaceRequirementsError as e:
                _LOGGER.warning("Cannot build pipeline interface from {} ({})".
                                format(f, str(e)))
    return iface_group


def fetch_samples(prj, selector_attribute=None, selector_include=None,
                  selector_exclude=None):
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
    if selector_attribute is None or \
            (not selector_include and not selector_exclude):
        # Simple; keep all samples.  In this case, this function simply
        # offers a list rather than an iterator.
        return list(prj.samples)

    if not isinstance(selector_attribute, str):
        raise TypeError(
            "Name for attribute on which to base selection isn't string: "
            "{} "
            "({})".format(selector_attribute, type(selector_attribute)))

    # At least one of the samples has to have the specified attribute
    if prj.samples and not any(
            [hasattr(s, selector_attribute) for s in prj.samples]):
        raise AttributeError(
            "The Project samples do not have the attribute '{attr}'".
                format(attr=selector_attribute))

    # Intersection between selector_include and selector_exclude is
    # nonsense user error.
    if selector_include and selector_exclude:
        raise TypeError(
            "Specify only selector_include or selector_exclude parameter, "
            "not both.")

    # Ensure that we're working with sets.
    def make_set(items):
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
            return not hasattr(s, selector_attribute) \
                   or getattr(s, selector_attribute) \
                   not in make_set(selector_exclude)
    else:
        # Strict; keep only samples in the selector_include.
        def keep(s):
            return hasattr(s, selector_attribute) \
                   and getattr(s, selector_attribute) \
                   in make_set(selector_include)

    return list(filter(keep, prj.samples))


OutputGroup = namedtuple("OutputGroup", field_names=["path", "samples"])


# Collect PipelineInterface, Sample type, pipeline path, and script with flags.
SubmissionBundle = namedtuple(
    "SubmissionBundle",
    field_names=["interface", "subtype", "pipeline", "pipeline_with_flags"])
SUBMISSION_BUNDLE_PIPELINE_KEY_INDEX = 2


def _is_member(item, items):
    """ Determine whether an item is a member of a collection. """
    return item in items
