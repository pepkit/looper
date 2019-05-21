""" Looper version of NGS project model. """

from collections import namedtuple
import copy
from functools import partial
import itertools
import os

import peppy
from peppy import METADATA_KEY, OUTDIR_KEY
from peppy.utils import is_command_callable
from .const import *
from .exceptions import DuplicatePipelineKeyException
from .pipeline_interface import PROTOMAP_KEY
from .project_piface_group import ProjectPifaceGroup
from .utils import get_logger, partition


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"

__all__ = ["Project", "process_pipeline_interfaces"]


_LOGGER = get_logger(__name__)


class Project(peppy.Project):
    """
    Looper-specific NGS Project.

    :param str config_file: path to configuration file with data from
        which Project is to be built
    :param str subproject: name indicating subproject to use, optional
    """
    def __init__(self, config_file, subproject=None, **kwargs):
        super(Project, self).__init__(
                config_file, subproject=subproject, 
                no_environment_exception=RuntimeError,
                no_compute_exception=RuntimeError, **kwargs)
        self.interfaces = process_pipeline_interfaces(
            self[METADATA_KEY][PIPELINE_INTERFACES_KEY])

    @property
    def project_folders(self):
        """ Critical project folder keys """
        return {OUTDIR_KEY: OUTDIR_KEY, RESULTS_SUBDIR_KEY: "results_pipeline",
                SUBMISSION_SUBDIR_KEY: "submission"}

    @property
    def required_metadata(self):
        """ Which metadata attributes are required. """
        return [OUTDIR_KEY]

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
            # "Break"-like mechanism for short-circuiting if we care only
            # about the highest-priority match for pipeline submission.
            # That is, if the intent is to submit pipeline(s) from a single
            # location for each sample of the given protocol, we can stop
            # searching the pool of pipeline interface information once we've
            # found a match for the protocol.
            if priority and len(job_submission_bundles) > 0:
                return job_submission_bundles[0]

            this_protocol_pipelines = pipe_iface.fetch_pipelines(protocol)
            if not this_protocol_pipelines:
                _LOGGER.debug("No pipelines; available: {}".format(
                        ", ".join(pipe_iface.protocol_mapping.keys())))
                continue

            # TODO: update once dependency-encoding logic is in place.
            # The proposed dependency-encoding format uses a semicolon
            # between pipelines for which the dependency relationship is
            # serial. For now, simply treat those as multiple independent
            # pipelines by replacing the semicolon with a comma, which is the
            # way in which multiple independent pipelines for a single protocol
            # are represented in the mapping declaration.
            pipeline_keys = \
                this_protocol_pipelines.replace(";", ",") \
                    .strip(" ()\n") \
                    .split(",")
            # These cleaned pipeline keys are what's used to resolve the path
            # to the pipeline to run.
            pipeline_keys = [pk.strip() for pk in pipeline_keys]

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
                    pipe_iface.finalize_pipeline_key_and_paths(
                        pipeline_key)

                # Skip and warn about nonexistent alleged pipeline path.
                if not (os.path.exists(full_pipe_path) or
                            is_command_callable(full_pipe_path)):
                    _LOGGER.warning(
                        "Missing pipeline script: '%s'", full_pipe_path)
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
                             "'{}'\n{}".format(
                        strict_pipe_key, maybe_new_bundle, old_bundle)
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
            snames = [s.name for s in self.samples if s.protocol in prots]
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


def process_pipeline_interfaces(pipeline_interface_locations):
    """
    Create a PipelineInterface for each pipeline location given.

    :param Iterable[str] pipeline_interface_locations: locations, each of
        which should be either a directory path or a filepath, that specifies
        pipeline interface and protocol mappings information. Each such file
        should have a pipelines section and a protocol mappings section.
    :return Mapping[str, Iterable[PipelineInterface]]: mapping from protocol
        name to interface(s) for which that protocol is mapped
    """
    iface_group = ProjectPifaceGroup()
    for loc in pipeline_interface_locations:
        if not os.path.exists(loc):
            _LOGGER.warning("Ignoring nonexistent pipeline interface location: "
                            "{}".format(loc))
            continue
        fs = [loc] if os.path.isfile(loc) else \
            [os.path.join(loc, f) for f in os.listdir(loc)
             if os.path.splitext(f)[1] in [".yaml", ".yml"]]
        for f in fs:
            _LOGGER.debug("Processing interface definition: {}".format(f))
            iface_group.update(f)
    return iface_group


OutputGroup = namedtuple("OutputGroup", field_names=["path", "samples"])


# Collect PipelineInterface, Sample type, pipeline path, and script with flags.
SubmissionBundle = namedtuple(
    "SubmissionBundle",
    field_names=["interface", "subtype", "pipeline", "pipeline_with_flags"])
SUBMISSION_BUNDLE_PIPELINE_KEY_INDEX = 2


def _is_member(item, items):
    """ Determine whether an item is a member of a collection. """
    return item in items
