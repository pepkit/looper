""" Looper version of NGS project model. """

from collections import defaultdict, namedtuple
from functools import partial
import itertools
import os

import peppy
from peppy.utils import is_command_callable
from .const import *
from .pipeline_interface import PipelineInterface
from .utils import get_logger, partition


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


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
        self.interfaces_by_protocol = \
            process_pipeline_interfaces(self.metadata.pipeline_interfaces)

    @property
    def project_folders(self):
        """ Keys for paths to folders to ensure exist. """
        return ["output_dir", RESULTS_SUBDIR_KEY, SUBMISSION_SUBDIR_KEY]

    @property
    def required_metadata(self):
        """ Which metadata attributes are required. """
        return ["output_dir"]

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
            pipeline_interfaces = \
                self.interfaces_by_protocol[protocol]
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
    interface_by_protocol = defaultdict(list)
    for pipe_iface_location in pipeline_interface_locations:
        if not os.path.exists(pipe_iface_location):
            _LOGGER.warning("Ignoring nonexistent pipeline interface "
                         "location: '%s'", pipe_iface_location)
            continue
        pipe_iface = PipelineInterface(pipe_iface_location)
        for proto_name in pipe_iface.protocol_mapping:
            _LOGGER.whisper("Adding protocol name: '%s'", proto_name)
            interface_by_protocol[proto_name].append(pipe_iface)
    return interface_by_protocol


# Collect PipelineInterface, Sample type, pipeline path, and script with flags.
SubmissionBundle = namedtuple(
    "SubmissionBundle",
    field_names=["interface", "subtype", "pipeline", "pipeline_with_flags"])
SUBMISSION_BUNDLE_PIPELINE_KEY_INDEX = 2


def _is_member(item, items):
    """ Determine whether an iterm is a member of a collection. """
    return item in items
