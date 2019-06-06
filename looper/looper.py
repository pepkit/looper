#!/usr/bin/env python
"""
Looper: a pipeline submission engine. https://github.com/pepkit/looper
"""

import abc
import csv
from collections import defaultdict
import glob
import logging
import os
import subprocess
import sys
if sys.version_info < (3, 3):
    from collections import Mapping
else:
    from collections.abc import Mapping
import yaml

# Need specific sequence of actions for colorama imports?
from colorama import init
init()
from colorama import Fore, Style
import pandas as _pd

from . import FLAGS, GENERIC_PROTOCOL_KEY, LOGGING_LEVEL, __version__, \
    build_parser, _LEVEL_BY_VERBOSITY
from .conductor import SubmissionConductor
from .const import *
from .exceptions import JobSubmissionException
from .html_reports import HTMLReportBuilder
from .pipeline_interface import RESOURCES_KEY
from .project import Project
from .utils import determine_config_path, fetch_flag_files, sample_folder

from divvy import DEFAULT_COMPUTE_RESOURCES_NAME, NEW_COMPUTE_KEY as COMPUTE_KEY
from logmuse import init_logger
from peppy import ProjectContext, METADATA_KEY, SAMPLE_EXECUTION_TOGGLE

from ubiquerg import query_yes_no

SUBMISSION_FAILURE_MESSAGE = "Cluster resource failure"


_FAIL_DISPLAY_PROPORTION_THRESHOLD = 0.5
_MAX_FAIL_SAMPLE_DISPLAY = 20
_PKGNAME = "looper"
_LOGGER = logging.getLogger(_PKGNAME)


class Executor(object):
    """ Base class that ensures the program's Sample counter starts.

    Looper is made up of a series of child classes that each extend the base
    Executor class. Each child class does a particular task (such as run the
    project, summarize the project, destroy the project, etc). The parent
    Executor class simply holds the code that is common to all child classes,
    such as counting samples as the class does its thing."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, prj):
        """
        The Project defines the instance; establish an iteration counter.

        :param Project prj: Project with which to work/operate on
        """
        super(Executor, self).__init__()
        self.prj = prj
        self.counter = LooperCounter(len(prj.samples))

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        """ Do the work of the subcommand/program. """
        pass


class Checker(Executor):

    def __call__(self, flags=None, all_folders=False, max_file_count=30):
        """
        Check Project status, based on flag files.

        :param Iterable[str] | str flags: Names of flags to check, optional;
            if unspecified, all known flags will be checked.
        :param bool all_folders: Whether to check flags in all folders, not
            just those for samples in the config file from which the Project
            was created.
        :param int max_file_count: Maximum number of filepaths to display for a
            given flag.
        """

        # Handle single or multiple flags, and alphabetize.
        flags = sorted([flags] if isinstance(flags, str)
                       else list(flags or FLAGS))
        flag_text = ", ".join(flags)

        # Collect the files by flag and sort by flag name.
        _LOGGER.debug("Checking project folders for flags: %s", flag_text)
        if all_folders:
            files_by_flag = fetch_flag_files(
                results_folder=self.prj.results_folder, flags=flags)
        else:
            files_by_flag = fetch_flag_files(prj=self.prj, flags=flags)

        # For each flag, output occurrence count.
        for flag in flags:
            _LOGGER.info("%s: %d", flag.upper(), len(files_by_flag[flag]))

        # For each flag, output filepath(s) if not overly verbose.
        for flag in flags:
            try:
                files = files_by_flag[flag]
            except:
                # No files for flag.
                continue
            # If checking on a specific flag, do not limit the number of
            # reported filepaths, but do not report empty file lists
            if len(flags) == 1 and len(files) > 0:
                _LOGGER.info("%s (%d):\n%s", flag.upper(),
                             len(files), "\n".join(files))
            # Regardless of whether 0-count flags are previously reported,
            # don't report an empty file list for a flag that's absent.
            # If the flag-to-files mapping is defaultdict, absent flag (key)
            # will fetch an empty collection, so check for length of 0.
            if 0 < len(files) <= max_file_count:
                _LOGGER.info("%s (%d):\n%s", flag.upper(),
                             len(files), "\n".join(files))


class Cleaner(Executor):
    """ Remove all intermediate files (defined by pypiper clean scripts). """

    def __call__(self, args, preview_flag=True):
        """
        Execute the file cleaning process.

        :param argparse.Namespace args: command-line options and arguments
        :param bool preview_flag: whether to halt before actually removing files
        """
        _LOGGER.info("Files to clean:")

        for sample in self.prj.samples:
            _LOGGER.info(self.counter.show(sample.sample_name, sample.protocol))
            sample_output_folder = sample_folder(self.prj, sample)
            cleanup_files = glob.glob(os.path.join(sample_output_folder,
                                                   "*_cleanup.sh"))
            if preview_flag:
                # Preview: Don't actually clean, just show what will be cleaned.
                _LOGGER.info("Files to clean: %s", ", ".join(cleanup_files))
            else:
                for f in cleanup_files:
                    _LOGGER.info(f)
                    subprocess.call(["sh", f])

        if not preview_flag:
            _LOGGER.info("Clean complete.")
            return 0

        if args.dry_run:
            _LOGGER.info("Dry run. No files cleaned.")
            return 0

        if not args.force_yes and not query_yes_no("Are you sure you want to permanently delete all "
                            "intermediate pipeline results for this project?"):
            _LOGGER.info("Clean action aborted by user.")
            return 1

        self.counter.reset()

        return self(args, preview_flag=False)


class Destroyer(Executor):
    """ Destroyer of files and folders associated with Project's Samples """

    def __call__(self, args, preview_flag=True):
        """
        Completely remove all output produced by any pipelines.

        :param argparse.Namespace args: command-line options and arguments
        :param bool preview_flag: whether to halt before actually removing files
        """

        _LOGGER.info("Results to destroy:")

        for sample in self.prj.samples:
            _LOGGER.info(
                self.counter.show(sample.sample_name, sample.protocol))
            sample_output_folder = sample_folder(self.prj, sample)
            if preview_flag:
                # Preview: Don't actually delete, just show files.
                _LOGGER.info(str(sample_output_folder))
            else:
                destroy_sample_results(sample_output_folder, args)

        if not preview_flag:
            _LOGGER.info("Destroy complete.")
            return 0

        if args.dry_run:
            _LOGGER.info("Dry run. No files destroyed.")
            return 0

        if not args.force_yes and not query_yes_no(
            "Are you sure you want to permanently delete all pipeline results "
            "for this project?"):
            _LOGGER.info("Destroy action aborted by user.")
            return 1

        self.counter.reset()

        # Finally, run the true destroy:
        return self(args, preview_flag=False)


def process_protocols(prj, protocols, resource_setting_kwargs=None, **kwargs):
    """
    Create submission conductors and collect by protocol the mapped pipelines.

    :param looper.Project prj: project definition
    :param Iterable[str] protocols: names of protocols mapped to pipelines
        for which conductors are to be created
    :param Mapping resource_setting_kwargs: key-value pairs collection storing
        specific compute resource settings
    :return Mapping[str, looper.conductor.SubmissionConductor], Mapping[str, list[str]]:
        mapping from pipeline key to submission conductor, and mapping from
        protocol name to collection of keys for pipelines for that protocol
    :raise TypeError: if the project's computing configuration instance isn't
        a mapping
    """
    # Job submissions are managed on a per-pipeline basis so that
    # individual commands (samples) may be lumped into a single job.
    submission_conductors = {}
    pipe_keys_by_protocol = defaultdict(list)

    if resource_setting_kwargs:
        if not isinstance(resource_setting_kwargs, Mapping):
            raise TypeError(
                "Resource settings argument must be mapping; got {} ({})".
                    format(resource_setting_kwargs, type(resource_setting_kwargs)))
    else:
        resource_setting_kwargs = {}

    try:
        comp_vars = prj.dcc[COMPUTE_KEY].to_map()
    except AttributeError:
        if not isinstance(prj.dcc[COMPUTE_KEY], Mapping):
            raise TypeError("Project's computing config isn't a mapping: {} ({})".
                            format(prj.dcc[COMPUTE_KEY], type(prj.dcc[COMPUTE_KEY])))
        from copy import deepcopy
        comp_vars = deepcopy(prj.dcc[COMPUTE_KEY])
    comp_vars.update(resource_setting_kwargs or {})

    _LOGGER.info("Known protocols: {}".format(
        ", ".join(prj.interfaces.protocols)))

    for proto in set(protocols) | {GENERIC_PROTOCOL_KEY}:
        _LOGGER.debug("Determining sample type, script, and flags for "
                      "pipeline(s) associated with protocol: %s", proto)
        submission_bundles = prj.build_submission_bundles(proto)
        if not submission_bundles:
            if proto != GENERIC_PROTOCOL_KEY:
                _LOGGER.warning("No mapping for protocol: '%s'", proto)
            continue
        for pl_iface, sample_subtype, pl_key, script_with_flags in \
                submission_bundles:
            _LOGGER.debug("%s: %s", pl_key, sample_subtype.__name__)
            conductor = SubmissionConductor(
                pl_key, pl_iface, script_with_flags, prj,
                sample_subtype=sample_subtype,
                compute_variables=comp_vars, **kwargs)
            submission_conductors[pl_key] = conductor
            pipe_keys_by_protocol[proto].append(pl_key)
    return submission_conductors, pipe_keys_by_protocol


class Runner(Executor):
    """ The true submitter of pipelines """

    def __call__(self, args, remaining_args, rerun=False, **compute_kwargs):
        """
        Do the Sample submission.

        :param argparse.Namespace args: parsed command-line options and
            arguments, recognized by looper
        :param list remaining_args: command-line options and arguments not
            recognized by looper, germane to samples/pipelines
        :param bool rerun: whether the given sample is being rerun rather than
            run for the first time
        """

        if not self.prj.interfaces:
            pipe_locs = getattr(self.prj[METADATA_KEY], PIPELINE_INTERFACES_KEY, [])
            # TODO: should these cases be handled as equally exceptional?
            # That is, should they either both raise errors, or both log errors?
            if len(pipe_locs) == 0:
                raise AttributeError(
                    "Looper requires at least one pointer to pipeline(s), set "
                    "with the pipeline_interfaces key in the metadata section "
                    "of a project config file")
            else:
                _LOGGER.error("No protocols found; does the PEP point to at "
                              "least one pipeline interface that exists? "
                              " Pipeline  interfaces: {}".
                              format(", ".format(pipe_locs)))
                return

        protocols = {s.protocol for s in self.prj.samples
                     if hasattr(s, "protocol")}
        failures = defaultdict(list)  # Collect problems by sample.
        processed_samples = set()  # Enforce one-time processing.

        _LOGGER.info("Finding pipelines for protocol(s): {}".
                     format(", ".join(self.prj.protocols)))

        submission_conductors, pipe_keys_by_protocol = process_protocols(
            self.prj, protocols, compute_kwargs, dry_run=args.dry_run,
            delay=args.time_delay, extra_args=remaining_args,
            ignore_flags=args.ignore_flags,
            max_cmds=args.lumpn, max_size=args.lump)
        mapped_protos = set(pipe_keys_by_protocol.keys())

        # Determine number of samples eligible for processing.
        num_samples = len(self.prj.samples)
        if args.limit is None:
            upper_sample_bound = num_samples
        elif args.limit < 0:
            raise ValueError(
                "Invalid number of samples to run: {}".format(args.limit))
        else:
            upper_sample_bound = min(args.limit, num_samples)
        _LOGGER.debug("Limiting to %d of %d samples",
                      upper_sample_bound, num_samples)

        num_commands_possible = 0
        failed_submission_scripts = []

        for sample in self.prj.samples[:upper_sample_bound]:
            # First, step through the samples and determine whether any
            # should be skipped entirely, based on sample attributes alone
            # and independent of anything about any of its pipelines.

            # Start by displaying the sample index and a fresh collection
            # of sample-skipping reasons.
            _LOGGER.info(self.counter.show(
                    sample.sample_name, sample.protocol))
            skip_reasons = []

            # Don't submit samples with duplicate names unless suppressed.
            if sample.sample_name in processed_samples:
                if args.allow_duplicate_names:
                    _LOGGER.warning("Duplicate name detected, but submitting anyway")
                else:
                    skip_reasons.append("Duplicate sample name")

            # Check if sample should be run.
            if sample.is_dormant():
                skip_reasons.append(
                        "Inactive status (via '{}' column/attribute)".
                        format(SAMPLE_EXECUTION_TOGGLE))

            # Get the base protocol-to-pipeline mappings.
            try:
                protocol = sample.protocol
            except AttributeError:
                skip_reasons.append("Sample has no protocol")
            else:
                if protocol not in mapped_protos and \
                        GENERIC_PROTOCOL_KEY not in mapped_protos:
                    skip_reasons.append("No pipeline for protocol")

            if skip_reasons:
                _LOGGER.warning(
                    "> Not submitted: {}".format(", ".join(skip_reasons)))
                failures[sample.name] = skip_reasons
                continue

            # Processing preconditions have been met.
            # Add this sample to the processed collection.
            processed_samples.add(sample.sample_name)

            # At this point, we have a generic Sample; write that to disk
            # for reuse in case of many jobs (pipelines) using base Sample.
            # Do a single overwrite here, then any subsequent Sample can be sure
            # that the file is fresh, with respect to this run of looper.
            sample.to_yaml(subs_folder_path=self.prj.submission_folder)

            pipe_keys = pipe_keys_by_protocol.get(sample.protocol) \
                or pipe_keys_by_protocol.get(GENERIC_PROTOCOL_KEY)
            _LOGGER.debug("Considering {} pipeline(s): {}".
                          format(len(pipe_keys), ", ".join(pipe_keys)))

            pl_fails = []
            for pl_key in pipe_keys:
                num_commands_possible += 1
                # TODO: of interest to track failures by pipeline?
                conductor = submission_conductors[pl_key]
                # TODO: check return value from add() to determine whether
                # TODO (cont.) to grow the failures list.
                try:
                    curr_pl_fails = conductor.add_sample(sample, rerun=rerun)
                except JobSubmissionException as e:
                    failed_submission_scripts.append(e.script)
                else:
                    pl_fails.extend(curr_pl_fails)
            if pl_fails:
                failures[sample.name].extend(pl_fails)

        job_sub_total = 0
        cmd_sub_total = 0
        for conductor in submission_conductors.values():
            conductor.submit(force=True)
            job_sub_total += conductor.num_job_submissions
            cmd_sub_total += conductor.num_cmd_submissions
            skipped_sample_scripts = conductor.write_skipped_sample_scripts()
            if skipped_sample_scripts:
                _LOGGER.info(
                    "{} script(s) for skipped samples:\n{}".
                    format(len(skipped_sample_scripts),
                           "\n".join(skipped_sample_scripts)))

        # Report what went down.
        max_samples = min(len(self.prj.samples), args.limit or float("inf"))
        _LOGGER.info("\nLooper finished")
        _LOGGER.info("Samples valid for job generation: %d of %d",
                     len(processed_samples), max_samples)
        _LOGGER.info("Successful samples: %d of %d",
                     max_samples - len(failures), max_samples)
        _LOGGER.info("Commands submitted: %d of %d",
                     cmd_sub_total, num_commands_possible)
        _LOGGER.info("Jobs submitted: %d", job_sub_total)
        if args.dry_run:
            _LOGGER.info("Dry run. No jobs were actually submitted.")

        # Restructure sample/failure data for display.
        samples_by_reason = defaultdict(set)
        # Collect names of failed sample(s) by failure reason.
        for sample, failures in failures.items():
            for f in failures:
                samples_by_reason[f].add(sample)
        # Collect samples by pipeline with submission failure.
        failed_samples_by_pipeline = defaultdict(set)
        for pl_key, conductor in submission_conductors.items():
            # Don't add failure key if there are no samples that failed for
            # that reason.
            if conductor.failed_samples:
                fails = set(conductor.failed_samples)
                samples_by_reason[SUBMISSION_FAILURE_MESSAGE] |= fails
                failed_samples_by_pipeline[pl_key] |= fails

        failed_sub_samples = samples_by_reason.get(SUBMISSION_FAILURE_MESSAGE)
        if failed_sub_samples:
            _LOGGER.info("\n{} samples with at least one failed job submission: {}".
                         format(len(failed_sub_samples),
                                ", ".join(failed_sub_samples)))

        # If failure keys are only added when there's at least one sample that
        # failed for that reason, we can display information conditionally,
        # depending on whether there's actually failure(s).
        if samples_by_reason:
            _LOGGER.info("\n{} unique reasons for submission failure: {}".format(
                len(samples_by_reason), ", ".join(samples_by_reason.keys())))
            full_fail_msgs = [create_failure_message(reason, samples)
                              for reason, samples in samples_by_reason.items()]
            _LOGGER.info("\nSummary of failures:\n{}".
                         format("\n".join(full_fail_msgs)))


class Summarizer(Executor):
    """ Project/Sample output summarizer """
    def __init__(self, prj):
        # call the inherited initialization
        super(Summarizer, self).__init__(prj)
        # pull together all the fits and stats from each sample into project-combined spreadsheets.
        self.stats, self.columns = _create_stats_summary(self.prj, self.counter)
        self.objs = _create_obj_summary(self.prj, self.counter)

    def __call__(self):
        """ Do the summarization. """
        run_custom_summarizers(self.prj)
        # initialize the report builder
        report_builder = HTMLReportBuilder(self.prj)
        # run the report builder. a set of HTML pages is produced
        report_path = report_builder(self.objs, self.stats, uniqify(self.columns))
        _LOGGER.info("HTML Report (n=" + str(len(self.stats)) + "): " + report_path)


def run_custom_summarizers(project):
    """
    Run custom summarizers if any are defined

    :param looper.Project project: the project to be summarized
    """
    # Next, looper can run custom summarizers, if they exist.
    all_protocols = [sample.protocol for sample in project.samples]

    for protocol in set(all_protocols):
        try:
            ifaces = project.get_interfaces(protocol)
        except KeyError:
            _LOGGER.warning("No interface for protocol '{}', skipping summary".format(protocol))
            continue
        for iface in ifaces:
            _LOGGER.debug(iface)
            pl = iface.fetch_pipelines(protocol)
            summarizers = iface.get_attribute(pl, "summarizers")
            if summarizers is not None:
                for summarizer in set(summarizers):
                    summarizer_abspath = os.path.join(os.path.dirname(iface.pipe_iface_file), summarizer)
                    try:
                        subprocess.call([summarizer_abspath, project.config_file])
                    except OSError:
                        _LOGGER.warning("Summarizer was unable to run: " + str(summarizer))


def _create_stats_summary(project, counter):
    """
    Create stats spreadsheet and columns to be considered in the report, save the spreadsheet to file

    :param looper.Project project: the project to be summarized
    :param looper.LooperCounter counter: a counter object
    """
    # Create stats_summary file
    columns = []
    stats = []
    project_samples = project.samples
    missing_files = 0
    _LOGGER.info("Creating stats summary...")
    for sample in project_samples:
        _LOGGER.info(counter.show(sample.sample_name, sample.protocol))
        sample_output_folder = sample_folder(project, sample)
        # Grab the basic info from the annotation sheet for this sample.
        # This will correspond to a row in the output.
        sample_stats = sample.get_sheet_dict()
        columns.extend(sample_stats.keys())
        # Version 0.3 standardized all stats into a single file
        stats_file = os.path.join(sample_output_folder, "stats.tsv")
        if not os.path.isfile(stats_file):
            missing_files += 1
            continue
        t = _pd.read_csv(stats_file, sep="\t", header=None, names=['key', 'value', 'pl'])
        t.drop_duplicates(subset=['key', 'pl'], keep='last', inplace=True)
        t.loc[:, 'plkey'] = t['pl'] + ":" + t['key']
        dupes = t.duplicated(subset=['key'], keep=False)
        t.loc[dupes, 'key'] = t.loc[dupes, 'plkey']
        sample_stats.update(t.set_index('key')['value'].to_dict())
        stats.append(sample_stats)
        columns.extend(t.key.tolist())
    tsv_outfile_path = get_file_for_project(project, 'stats_summary.tsv')
    if missing_files > 0:
        _LOGGER.warning("Stats files missing for {} samples".format(missing_files))
    tsv_outfile = open(tsv_outfile_path, 'w')
    tsv_writer = csv.DictWriter(tsv_outfile, fieldnames=uniqify(columns), delimiter='\t', extrasaction='ignore')
    tsv_writer.writeheader()
    for row in stats:
        tsv_writer.writerow(row)
    tsv_outfile.close()
    _LOGGER.info("Summary (n=" + str(len(stats)) + "): " + tsv_outfile_path)
    counter.reset()
    return stats, uniqify(columns)


def _create_obj_summary(project, counter):
    """
    Read sample specific objects files and save to a data frame

    :param looper.Project project: the project to be summarized
    :param looper.LooperCounter counter: a counter object
    :return pandas.DataFrame: objects spreadsheet
    """
    _LOGGER.info("Creating objects summary...")
    objs = _pd.DataFrame()
    # Create objects summary file
    missing_files = 0
    for sample in project.samples:
        # Process any reported objects
        _LOGGER.info(counter.show(sample.sample_name, sample.protocol))
        sample_output_folder = sample_folder(project, sample)
        objs_file = os.path.join(sample_output_folder, "objects.tsv")
        if not os.path.isfile(objs_file):
            missing_files += 1
            continue
        t = _pd.read_csv(objs_file, sep="\t", header=None,
                         names=['key', 'filename', 'anchor_text', 'anchor_image', 'annotation'])
        t['sample_name'] = sample.name
        objs = objs.append(t, ignore_index=True)
    if missing_files > 0:
        _LOGGER.warning("Object files missing for {} samples".format(missing_files))
    # create the path to save the objects file in
    objs.to_csv(get_file_for_project(project, 'objs_summary.tsv'), sep="\t")
    return objs


def get_file_for_project(prj, appendix):
    """
    Create a path to the file for the current project. Takes the possibility of subproject being activated at the time
    :param looper.Project prj: project object
    :param str appendix: the appendix of the file to create the path for, like 'objs_summary.tsv' for objects summary file
    :return str: path to the file
    """
    fp = os.path.join(prj.metadata.output_dir, prj.name)
    if hasattr(prj, "subproject") and prj.subproject:
        fp += '_' + prj.subproject
    fp += '_' + appendix
    return fp


def aggregate_exec_skip_reasons(skip_reasons_sample_pairs):
    """
    Collect the reasons for skipping submission/execution of each sample

    :param Iterable[(Iterable[str], str)] skip_reasons_sample_pairs: pairs of
        collection of reasons for which a sample was skipped for submission,
        and the name of the sample itself
    :return Mapping[str, Iterable[str]]: mapping from explanation to
        collection of names of samples to which it pertains
    """
    samples_by_skip_reason = defaultdict(list)
    for skip_reasons, sample in skip_reasons_sample_pairs:
        for reason in set(skip_reasons):
            samples_by_skip_reason[reason].append(sample)
    return samples_by_skip_reason


def create_failure_message(reason, samples):
    """ Explain lack of submission for a single reason, 1 or more samples. """
    color = Fore.LIGHTRED_EX
    reason_text = color + reason + Style.RESET_ALL
    samples_text = ", ".join(samples)
    return "{}: {}".format(reason_text, samples_text)


def destroy_sample_results(result_outfolder, args):
    """
    This function will delete all results for this sample
    """
    import shutil

    if os.path.exists(result_outfolder):
        if args.dry_run:
            _LOGGER.info("DRY RUN. I would have removed: " + result_outfolder)
        else:
            _LOGGER.info("Removing: " + result_outfolder)
            shutil.rmtree(result_outfolder)
    else:
        _LOGGER.info(result_outfolder + " does not exist.")


def uniqify(seq):
    """
    Fast way to uniqify while preserving input order.
    """
    # http://stackoverflow.com/questions/480214/
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


class LooperCounter(object):
    """
    Count samples as you loop through them, and create text for the
    subcommand logging status messages.

    :param int total: number of jobs to process
    """

    def __init__(self, total):
        self.count = 0
        self.total = total

    def show(self, name, protocol):
        """
        Display sample counts status for a particular protocol type.

        The counts are running vs. total for the protocol within the Project,
        and as a side-effect of the call, the running count is incremented.

        :param str name: name of the sample
        :param str protocol: name of the protocol
        :return str: message suitable for logging a status update
        """
        self.count += 1
        return _submission_status_text(
            curr=self.count, total=self.total, sample_name=name,
            sample_protocol=protocol, color=Fore.CYAN)

    def reset(self):
        self.count = 0

    def __str__(self):
        return "LooperCounter of size {}".format(self.total)


def _submission_status_text(curr, total, sample_name, sample_protocol, color):
    return color + \
           "## [{n} of {N}] {sample} ({protocol})".format(
               n=curr, N=total, sample=sample_name, protocol=sample_protocol) + \
           Style.RESET_ALL


def _proc_resources_spec(spec):
    """
    Process CLI-specified itemized compute resource setting specification.

    :param str | NoneType spec: itemized resource specification from CLI
    :return Mapping[str, str]: binding between resource setting name and value
    :raise ValueError: if interpretation of the given specification as encoding
        of key-value pairs fails
    """
    if not spec:
        return {}
    kvs = spec.strip().split(",")
    pairs = [(kv, kv.split("=")) for kv in kvs]
    bads, data = [], {}
    for orig, pair in pairs:
        try:
            k, v = pair
        except ValueError:
            bads.append(orig)
        else:
            data[k] = v
    if bads:
        raise ValueError("Could not completely parse itemized resource "
                         "specification; these failed as key-value pairs; "
                         "please check usage: {}".format(", ".join(bads)))
    return data


def main():
    """ Primary workflow """

    parser = build_parser()
    args, remaining_args = parser.parse_known_args()

    try:
        conf_file = args.config_file
    except AttributeError:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Set the logging level.
    if args.dbg:
        # Debug mode takes precedence and will listen for all messages.
        level = args.logging_level or logging.DEBUG
    elif args.verbosity is not None:
        # Verbosity-framed specification trumps logging_level.
        level = _LEVEL_BY_VERBOSITY[args.verbosity]
    else:
        # Normally, we're not in debug mode, and there's not verbosity.
        level = LOGGING_LEVEL

    # Establish the project-root logger and attach one for this module.
    logger_kwargs = {"level": level, "logfile": args.logfile, "devmode": args.dbg}
    init_logger(name="peppy", **logger_kwargs)
    global _LOGGER
    _LOGGER = init_logger(name=_PKGNAME, **logger_kwargs)

    if len(remaining_args) > 0:
        _LOGGER.debug("Remaining arguments passed to pipelines: {}".
                      format(" ".join([str(x) for x in remaining_args])))

    _LOGGER.info("Command: {} (Looper version: {})".
                 format(args.command, __version__))
    # Initialize project

    # Although the value of args.env might be None, the actual env variable used will be DIVCFG or PEPENV
    # (checked in this very order), which is implemented in divvy, the underlying package for
    # computing environment configuration
    if getattr(args, 'env', None) is None:
        _LOGGER.debug("compute_env_file: DIVCFG or PEPENV")
    else:
        _LOGGER.debug("compute_env_file: " + str(getattr(args, 'env', None)))
    _LOGGER.debug("Building Project")
    try:
        prj = Project(
            determine_config_path(conf_file), subproject=args.subproject,
            file_checks=args.file_checks, compute_env_file=getattr(args, 'env', None))
    except yaml.parser.ParserError as e:
        _LOGGER.error("Project config parse failed -- {}".format(e))
        sys.exit(1)

    compute_cli_spec = getattr(args, COMPUTE_KEY, None)
    if compute_cli_spec and compute_cli_spec != DEFAULT_COMPUTE_RESOURCES_NAME:
        prj.dcc.activate_package(compute_cli_spec)

    _LOGGER.debug("Results subdir: " + prj.results_folder)

    with ProjectContext(prj,
            selector_attribute=args.selector_attribute,
            selector_include=args.selector_include,
            selector_exclude=args.selector_exclude) as prj:

        if args.command in ["run", "rerun"]:
            run = Runner(prj)
            try:
                compute_kwargs = _proc_resources_spec(
                    getattr(args, RESOURCES_KEY, ""))
                run(args, remaining_args,
                    rerun=(args.command == "rerun"), **compute_kwargs)
            except IOError:
                _LOGGER.error("{} pipeline_interfaces: '{}'".format(
                        prj.__class__.__name__, prj.metadata.pipeline_interfaces))
                raise

        if args.command == "destroy":
            return Destroyer(prj)(args)

        if args.command == "summarize":
            Summarizer(prj)()

        if args.command == "check":
            # TODO: hook in fixed samples once protocol differentiation is
            # TODO (continued) figured out (related to #175).
            Checker(prj)(flags=args.flags)

        if args.command == "clean":
            return Cleaner(prj)(args)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        _LOGGER.error("Program canceled by user!")
        sys.exit(1)
