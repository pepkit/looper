#!/usr/bin/env python
"""
Looper: a pipeline submission engine. https://github.com/pepkit/looper
"""

import abc
import argparse
from collections import defaultdict
import glob
import logging
import os
import subprocess
import sys

# Need specific sequence of actions for colorama imports?
from colorama import init
init()
from colorama import Fore, Style
import pandas as _pd

from . import \
    setup_looper_logger, FLAGS, GENERIC_PROTOCOL_KEY, \
    LOGGING_LEVEL, __version__
from .exceptions import JobSubmissionException
from .project import Project
from .submission_manager import SubmissionConductor
from .utils import fetch_flag_files, sample_folder
#from .html_funcs import *
from .html_vars import *

from peppy import \
    ProjectContext, COMPUTE_SETTINGS_VARNAME, SAMPLE_EXECUTION_TOGGLE
from peppy.utils import alpha_cased



SUBMISSION_FAILURE_MESSAGE = "Cluster resource failure"

# Descending by severity for correspondence with logic inversion.
# That is, greater verbosity setting corresponds to lower logging level.
_LEVEL_BY_VERBOSITY = [logging.ERROR, logging.CRITICAL, logging.WARN,
                       logging.INFO, logging.DEBUG]
_FAIL_DISPLAY_PROPORTION_THRESHOLD = 0.5
_MAX_FAIL_SAMPLE_DISPLAY = 20
_LOGGER = logging.getLogger()



def parse_arguments():
    """
    Argument Parsing.

    :return argparse.Namespace, list[str]: namespace parsed according to
        arguments defined here, and additional options arguments undefined
        here and to be handled downstream
    """

    # Main looper program help text messages
    banner = "%(prog)s - Loop through samples and submit pipelines."
    additional_description = "For subcommand-specific options, type: " \
            "'%(prog)s <subcommand> -h'"
    additional_description += "\nhttps://github.com/pepkit/looper"

    parser = _VersionInHelpParser(
            description=banner,
            epilog=additional_description,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            "-V", "--version",
            action="version",
            version="%(prog)s {v}".format(v=__version__))

    # Logging control
    parser.add_argument(
            "--logfile", dest="logfile",
            help="Optional output file for looper logs")
    parser.add_argument(
            "--verbosity", dest="verbosity",
            type=int, choices=range(len(_LEVEL_BY_VERBOSITY)),
            help="Choose level of verbosity")
    parser.add_argument(
            "--logging-level", dest="logging_level",
            help=argparse.SUPPRESS)
    parser.add_argument(
            "--dbg", dest="dbg", action="store_true",
            help="Turn on debug mode")

    # Individual subcommands
    msg_by_cmd = {
            "run": "Main Looper function: Submit jobs for samples.",
            "summarize": "Summarize statistics of project samples.",
            "destroy": "Remove all files of the project.", 
            "check": "Checks flag status of current runs.", 
            "clean": "Runs clean scripts to remove intermediate "
                     "files of already processed jobs."}
    subparsers = parser.add_subparsers(dest="command")
    def add_subparser(cmd):
        message = msg_by_cmd[cmd]
        return subparsers.add_parser(cmd, description=message, help=message)

    # Run command
    run_subparser = add_subparser("run")
    run_subparser.add_argument(
            "-t", "--time-delay", dest="time_delay",
            type=int, default=0,
            help="Time delay in seconds between job submissions.")
    run_subparser.add_argument(
            "--ignore-flags", dest="ignore_flags",
            action="store_true",
            help="Ignore run status flags? Default: False. "
                 "By default, pipelines will not be submitted if a pypiper "
                 "flag file exists marking the run (e.g. as "
                 "'running' or 'failed'). Set this option to ignore flags "
                 "and submit the runs anyway.")
    run_subparser.add_argument(
            "--ignore-duplicate-names",
            action="store_true",
            help="Ignore duplicate names? Default: False. "
                 "By default, pipelines will not be submitted if a sample name "
                 "is duplicated, since samples names should be unique.  "
                 " Set this option to override this setting and "
                 "and submit the runs anyway.")
    run_subparser.add_argument(
            "--compute", dest="compute",
            help="YAML file with looper environment compute settings.")
    run_subparser.add_argument(
            "--env", dest="env",
            default=os.getenv("{}".format(COMPUTE_SETTINGS_VARNAME), ""),
            help="Employ looper environment compute settings.")
    run_subparser.add_argument(
            "--limit", dest="limit", default=None,
            type=int,
            help="Limit to n samples.")
    # Note that defaults for otherwise numeric lump parameters are set to
    # null by default so that the logic that parses their values may
    # distinguish between explicit 0 and lack of specification.
    run_subparser.add_argument(
            "--lump", type=float, default=None,
            help="Maximum total input file size for a lump/batch of commands "
                 "in a single job (in GB)")
    run_subparser.add_argument(
            "--lumpn", type=int, default=None,
            help="Number of individual scripts grouped into single submission")

    # Other commands
    summarize_subparser = add_subparser("summarize")
    destroy_subparser = add_subparser("destroy")
    check_subparser = add_subparser("check")
    clean_subparser = add_subparser("clean")

    check_subparser.add_argument(
            "-A", "--all-folders", action="store_true",
            help="Check status for all project's output folders, not just "
                 "those for samples specified in the config file used")
    check_subparser.add_argument(
            "-F", "--flags", nargs='*', default=FLAGS,
            help="Check on only these flags/status values.")

    # Common arguments
    for subparser in [run_subparser, summarize_subparser,
                destroy_subparser, check_subparser, clean_subparser]:
        subparser.add_argument(
                "config_file",
                help="Project configuration file (YAML).")
        subparser.add_argument(
                "--file-checks", dest="file_checks",
                action="store_false",
                help="Perform input file checks. Default=True.")
        subparser.add_argument(
                "-d", "--dry-run", dest="dry_run",
                action="store_true",
                help="Don't actually submit the project/subproject.")
        protocols = subparser.add_mutually_exclusive_group()
        protocols.add_argument(
                "--exclude-protocols", nargs='*', dest="exclude_protocols",
                help="Operate only on samples that either lack a protocol or "
                     "for which protocol is not in this collection.")
        protocols.add_argument(
                "--include-protocols", nargs='*', dest="include_protocols",
                help="Operate only on samples associated with these protocols; "
                     "if not provided, all samples are used.")
        subparser.add_argument(
                "--sp", dest="subproject",
                help="Name of subproject to use, as designated in the "
                     "project's configuration file")

    # To enable the loop to pass args directly on to the pipelines...
    args, remaining_args = parser.parse_known_args()

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
    setup_looper_logger(level=level,
                        additional_locations=(args.logfile, ),
                        devmode=args.dbg)
    global _LOGGER
    _LOGGER = logging.getLogger(__name__)

    if len(remaining_args) > 0:
        _LOGGER.debug("Remaining arguments passed to pipelines: {}".
                      format(" ".join([str(x) for x in remaining_args])))

    return args, remaining_args



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
        if all_folders:
            _LOGGER.info("Checking project folders for flags: %s", flag_text)
            files_by_flag = fetch_flag_files(
                results_folder=self.prj.metadata.results_subdir, flags=flags)
        else:
            _LOGGER.info("Checking project samples for flags: %s", flag_text)
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

        if not query_yes_no("Are you sure you want to permanently delete all "
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
    
        if not query_yes_no("Are you sure you want to permanently delete "
                            "all pipeline results for this project?"):
            _LOGGER.info("Destroy action aborted by user.")
            return 1

        self.counter.reset()

        # Finally, run the true destroy:
        return self(args, preview_flag=False)



class Runner(Executor):
    """ The true submitter of pipelines """

    def __call__(self, args, remaining_args):
        """
        Do the Sample submission.
        
        :param argparse.Namespace args: parsed command-line options and 
            arguments, recognized by looper 
        :param list remaining_args: command-line options and arguments not 
            recognized by looper, germane to samples/pipelines
        """

        protocols = {s.protocol for s in self.prj.samples
                     if hasattr(s, "protocol")}
        failures = defaultdict(list)  # Collect problems by sample.
        processed_samples = set()  # Enforce one-time processing.

        _LOGGER.info("Finding pipelines for protocol(s): {}".
                     format(", ".join(self.prj.protocols)))

        # Job submissions are managed on a per-pipeline basis so that
        # individual commands (samples) may be lumped into a single job.
        submission_conductors = {}
        pipe_keys_by_protocol = defaultdict(list)
        mapped_protos = set()
        for proto in protocols | {GENERIC_PROTOCOL_KEY}:
            proto_key = alpha_cased(proto)
            _LOGGER.debug("Determining sample type, script, and flags for "
                          "pipeline(s) associated with protocol: %s", proto)
            submission_bundles = self.prj.build_submission_bundles(proto_key)
            if not submission_bundles:
                if proto_key != GENERIC_PROTOCOL_KEY:
                    _LOGGER.warn("No mapping for protocol: '%s'", proto)
                continue
            mapped_protos.add(proto)
            for pl_iface, sample_subtype, pl_key, script_with_flags in \
                    submission_bundles:
                _LOGGER.debug("%s: %s", pl_key, sample_subtype.__name__)
                conductor = SubmissionConductor(
                        pl_key, pl_iface, script_with_flags, self.prj,
                        args.dry_run, args.time_delay, sample_subtype,
                        remaining_args, args.ignore_flags,
                        self.prj.compute.partition,
                        max_cmds=args.lumpn, max_size=args.lump)
                submission_conductors[pl_key] = conductor
                pipe_keys_by_protocol[proto_key].append(pl_key)

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
                if args.ignore_duplicate_names:
                    _LOGGER.warn("Duplicate name detected, but submitting anyway")
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
                _LOGGER.warn(
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
            sample.to_yaml(subs_folder_path=self.prj.metadata.submission_subdir)

            pipe_keys = pipe_keys_by_protocol.get(alpha_cased(sample.protocol)) \
                        or pipe_keys_by_protocol.get(GENERIC_PROTOCOL_KEY)
            _LOGGER.debug("Considering %d pipeline(s)", len(pipe_keys))

            pl_fails = []
            for pl_key in pipe_keys:
                num_commands_possible += 1
                # TODO: of interest to track failures by pipeline?
                conductor = submission_conductors[pl_key]
                # TODO: check return value from add() to determine whether
                # TODO (cont.) to grow the failures list.
                try:
                    curr_pl_fails = conductor.add_sample(sample)
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

        # Report what went down.
        max_samples = min(len(self.prj.samples), args.limit or float("inf"))
        _LOGGER.info("\nLooper finished")
        _LOGGER.info("Samples qualified for job generation: %d of %d",
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
            _LOGGER.info("\nSamples by failure:\n{}".
                         format("\n".join(full_fail_msgs)))

        """
        if failed_submission_scripts:
            _LOGGER.info(
                    Fore.LIGHTRED_EX +
                    "\n{} scripts with failed submission: ".
                    format(len(failed_submission_scripts)) + Style.RESET_ALL +
                    ", ".join(failed_submission_scripts))
        """



class Summarizer(Executor):
    """ Project/Sample output summarizer """
    
    def __call__(self):
        """ Do the summarization. """
        import csv

        columns = []
        stats = []
        #figs = _pd.DataFrame()
        objs = _pd.DataFrame()
        
        # def create_figures_html(figs):
            # # QUESTION: Is not being used? ...Original usage was?
            # # figs_tsv_path = "{root}_figs_summary.tsv".format(
                # # root=os.path.join(self.prj.metadata.output_dir, self.prj.name))
            # # DEPRECATED

            # figs_html_path = "{root}_figs_summary.html".format(
                # root=os.path.join(self.prj.metadata.output_dir, self.prj.name))

            # figs_html_file = open(figs_html_path, 'w')
            # html_header = "<html><h1>Summary of sample figures for project {}</h1>\n".format(self.prj.name)
            # figs_html_file.write(html_header)
            # sample_img_header = "<h3>{sample_name}</h3>\n"
            # sample_img_code = "<p><a href='{path}'><img src='{path}'>{key}</a></p>\n"

            # figs.drop_duplicates(keep='last', inplace=True)
            # for sample_name in figs['sample_name'].drop_duplicates().sort_values():
                # f = figs[figs['sample_name'] == sample_name]
                # figs_html_file.write(
                    # sample_img_header.format(sample_name=sample_name))

                # for i, row in f.iterrows():
                    # figs_html_file.write(sample_img_code.format(
                        # key=str(row['key']),
                        # path=str(self.prj.metadata.results_subdir + '/' +
                                 # sample_name + '/' + row['value'])))

            # html_footer = "</html>"
            # figs_html_file.write(html_footer)

            # figs_html_file.close()
            # _LOGGER.info(
                # "Summary (n=" + str(len(stats)) + "): " + tsv_outfile_path)
        def create_object_parent_html(objs):
            reports_dir = os.path.join(self.prj.metadata.output_dir,
                                       "reports")
            object_parent_path = os.path.join(reports_dir, "objects.html")
            if not os.path.exists(os.path.dirname(object_parent_path)):
                os.makedirs(os.path.dirname(object_parent_path))
            with open(object_parent_path, 'w') as html_file:
                html_file.write(HTML_HEAD_OPEN)
                html_file.write(create_navbar(objs, reports_dir))
                html_file.write(HTML_HEAD_CLOSE)
                html_file.write("\t<h4>Click link to view all samples for each object</h4>\n")
                html_file.write("\t\t<ul style='list-style-type:circle'>\n")
                for key in objs['key'].drop_duplicates().sort_values():
                    page_name = key + ".html"
                    page_path = os.path.join(reports_dir,
                                    page_name).replace(' ', '_').lower()
                    page_relpath = os.path.relpath(page_path, reports_dir)
                    html_file.write(GENERIC_LIST_ENTRY.format(
                                            page=page_relpath,
                                            label=key))
                html_file.write(HTML_FOOTER)
                html_file.close()
                
        def create_sample_parent_html(objs):        
            reports_dir = os.path.join(self.prj.metadata.output_dir,
                                       "reports")
            sample_parent_path = os.path.join(reports_dir, "samples.html")
            if not os.path.exists(os.path.dirname(sample_parent_path)):
                os.makedirs(os.path.dirname(sample_parent_path))
            with open(sample_parent_path, 'w') as html_file:
                html_file.write(HTML_HEAD_OPEN)
                html_file.write(create_navbar(objs,reports_dir))
                html_file.write(HTML_HEAD_CLOSE)
                html_file.write("\t<h4>Click link to view all objects for each sample</h4>\n")
                html_file.write("\t\t<ul style='list-style-type:circle'>\n")
                for sample in self.prj.samples:
                    sample_name = str(sample.sample_name)
                    page_name = sample_name + ".html"
                    page_path = os.path.join(reports_dir,
                                    page_name).replace(' ', '_').lower()
                    page_relpath = os.path.relpath(page_path, reports_dir)
                    html_file.write(GENERIC_LIST_ENTRY.format(
                                            page=page_relpath,
                                            label=sample_name))
                # old method follows
                # for sample_name in objs['sample_name'].drop_duplicates().sort_values():
                    # page_name = sample_name + ".html"
                    # page_path = os.path.join(reports_dir,
                                    # page_name).replace(' ', '_').lower()
                    # page_relpath = os.path.relpath(page_path, reports_dir)
                    # html_file.write(GENERIC_LIST_ENTRY.format(
                                            # page=page_relpath,
                                            # label=sample_name))
                html_file.write(HTML_FOOTER)
                html_file.close()

        def create_object_html(objs, nb, type, filename, index_html):
            # TODO: Build a page for an individual object type with all of its 
            #       plots from each sample
            reports_dir = os.path.join(self.prj.metadata.output_dir,
                                       "reports")
            object_path = os.path.join(reports_dir,
                                       filename).replace(' ', '_').lower()
            if not os.path.exists(os.path.dirname(object_path)):
                os.makedirs(os.path.dirname(object_path))
            with open(object_path, 'w') as html_file:
                html_file.write(HTML_HEAD_OPEN)
                html_file.write(create_navbar(nb, reports_dir))
                for i, row in objs.iterrows():
                    page_path = os.path.join(
                                 self.prj.metadata.results_subdir,
                                 row['sample_name'], row['filename'])
                    image_path = os.path.join(
                                  self.prj.metadata.results_subdir,
                                  row['sample_name'], row['anchor_image'])
                    page_relpath = os.path.relpath(page_path, reports_dir)
                    image_relpath = os.path.relpath(image_path, reports_dir)
                    html_file.write(OBJECTS_PLOTS.format(
                                        label=str(row['sample_name']),
                                        path=page_relpath,
                                        image=image_relpath))
                    # html_file.write(OBJECTS_PLOTS.format(
                        # label=str(row['sample_name']),
                        # path=str(os.path.join(
                                 # self.prj.metadata.results_subdir,
                                 # row['sample_name'], row['filename'])),
                        # image=str(os.path.join(
                                  # self.prj.metadata.results_subdir,
                                  # row['sample_name'], row['anchor_image']))))
            
                html_file.write(HTML_FOOTER)
                html_file.close()
        
        def create_status_html(all_samples):
            # Need all the sample names for sample folders
            # The flags for each of those
            reports_dir = os.path.join(self.prj.metadata.output_dir,
                                       "reports")
            status_html_path = os.path.join(reports_dir, "status.html")
            if not os.path.exists(os.path.dirname(status_html_path)):
                os.makedirs(os.path.dirname(status_html_path))
            with open(status_html_path, 'w') as html_file:
                html_file.write(HTML_HEAD_OPEN)
                html_file.write(create_navbar(all_samples, reports_dir))
                html_file.write("\t\t<body>\n")
                html_file.write(STATUS_HEADER)
                html_file.write(STATUS_TABLE_HEAD)
                #for sample_name in all_samples['sample_name'].drop_duplicates().sort_values():
                for sample in self.prj.samples:
                    sample_name = str(sample.sample_name)
                    # Grab the status flag for the current sample
                    flag = glob.glob(os.path.join(self.prj.metadata.results_subdir,
                                                  sample_name, '*.flag'))
                    if "completed" in str(flag):
                        button_class = "table-success"
                        flag = "Completed"
                    elif "running" in str(flag):
                        button_class = "table-warning"
                        flag = "Running"
                    elif "failed" in str(flag):
                        button_class = "table-danger"
                        flag = "Failed"
                    else:
                        button_class = "table-secondary"
                        flag = "Unknown"
                    
                    # Create table entry for each sample
                    html_file.write(STATUS_ROW_HEADER)
                    # First Col: Sample_Name
                    html_file.write(STATUS_ROW_VALUE.format(
                                        row_class="",
                                        value=sample_name))
                    # Second Col: Status
                    html_file.write(STATUS_ROW_VALUE.format(
                                        row_class=button_class,
                                        value=flag))
                    # Third Col: Log File
                    #for annotation in all_samples
                    single_sample = all_samples[all_samples['sample_name'] == sample_name]
                    if single_sample.empty:
                        #print (sample_name + " is empty")  # DEBUGGING
                        # When there is no objects.tsv file, search for the
                        # presence of log, profile, and command files
                        log_name = os.path.basename(str(glob.glob(os.path.join(
                                    self.prj.metadata.results_subdir,
                                    sample_name, '*log.md'))[0]))
                        # Currently unused. Future?
                        # profile_name = os.path.basename(str(glob.glob(os.path.join(
                                            # self.prj.metadata.results_subdir,
                                            # sample_name, '*profile.tsv'))[0]))
                        # command_name = os.path.basename(str(glob.glob(os.path.join(
                                            # self.prj.metadata.results_subdir,
                                            # sample_name, '*commands.sh'))[0]))
                    else:
                        log_name = str(single_sample.iloc[0]['annotation']) + "_log.md"
                        # Currently unused. Future?
                        #profile_name = str(single_sample.iloc[0]['annotation']) + "_profile.tsv"
                        #command_name = str(single_sample.iloc[0]['annotation']) + "_commands.sh"
                    #log_name = str(single_sample.iloc[0]['annotation']) + "_log.md"
                    log_file = os.path.join(self.prj.metadata.results_subdir,
                                            sample_name, log_name)
                    log_relpath = os.path.relpath(log_file, reports_dir)
                    html_file.write(STATUS_ROW_LINK.format(
                                        row_class="",
                                        file_link=log_relpath,
                                        link_name=log_name))
                    # Fourth Col: Current runtime
                    # If Completed, use stats.tsv
                    stats_file = os.path.join(
                                    self.prj.metadata.results_subdir,
                                    sample_name, "stats.tsv")
                    if os.path.isfile(stats_file):
                        t = _pd.read_table(stats_file, header=None,
                                           names=['key', 'value', 'pl'])
                        t.drop_duplicates(subset=['key', 'pl'],
                                          keep='last', inplace=True)
                        time = str(t[t['key'] == 'Time'].iloc[0]['value'])
                        html_file.write(STATUS_ROW_VALUE.format(
                                            row_class="",
                                            value=str(time)))
                    else:
                        # TODO: If still running, use _profile.tsv
                        html_file.write(STATUS_ROW_VALUE.format(
                                            row_class=button_class,
                                            value="Unknown"))
                    html_file.write(STATUS_ROW_FOOTER)
                    # Create a button for the sample's STATUS and its LOGFILE
                    # html_file.write(STATUS_BUTTON.format(
                                        # button_class=button_class,
                                        # sample=sample_name,
                                        # flag=flag))
                html_file.write(STATUS_FOOTER)
                html_file.write(HTML_FOOTER)
                html_file.close()
        
        def create_sample_html(single_sample, all_samples, sample_name,
                               sample_stats, filename, index_html):
            # Produce an HTML page containing all of a sample's objects
            reports_dir = os.path.join(self.prj.metadata.output_dir,
                                       "reports")
            sample_html_path = os.path.join(reports_dir,
                                            filename).replace(' ', '_').lower()
            if not os.path.exists(os.path.dirname(sample_html_path)):
                os.makedirs(os.path.dirname(sample_html_path))
            with open(sample_html_path, 'w') as html_file:
                html_file.write(HTML_HEAD_OPEN)
                html_file.write(TABLE_STYLE_ROTATED_HEADER)
                html_file.write(create_navbar(all_samples, reports_dir))
                html_file.write("\t\t<body>\n")
                if single_sample.empty:
                    #print (sample_name + " is empty")  # DEBUGGING
                    # When there is no objects.tsv file, search for the
                    # presence of log, profile, and command files
                    log_name = os.path.basename(str(glob.glob(os.path.join(
                                    self.prj.metadata.results_subdir,
                                    sample_name, '*log.md'))[0]))
                    profile_name = os.path.basename(str(glob.glob(os.path.join(
                                        self.prj.metadata.results_subdir,
                                        sample_name, '*profile.tsv'))[0]))
                    command_name = os.path.basename(str(glob.glob(os.path.join(
                                        self.prj.metadata.results_subdir,
                                        sample_name, '*commands.sh'))[0]))
                else:
                    log_name = str(single_sample.iloc[0]['annotation']) + "_log.md"
                    profile_name = str(single_sample.iloc[0]['annotation']) + "_profile.tsv"
                    command_name = str(single_sample.iloc[0]['annotation']) + "_commands.sh"
                # Get relative path to the log file
                log_file = os.path.join(self.prj.metadata.results_subdir,
                                        sample_name, log_name)              
                log_relpath = os.path.relpath(log_file, reports_dir)
                # Grab the status flag for the current sample
                flag = glob.glob(os.path.join(self.prj.metadata.results_subdir,
                                              sample_name, '*.flag'))[0]
                if "completed" in str(flag):
                    button_class = "btn btn-success"
                    flag = "Completed"
                elif "running" in str(flag):
                    button_class = "btn btn-warning"
                    flag = "Running"
                elif "failed" in str(flag):
                    button_class = "btn btn-danger"
                    flag = "Failed"
                else:
                    button_class = "btn btn-secondary"
                    flag = "Unknown"
                # Create a button for the sample's STATUS, LOGFILE, and STATS
                # add button linking to profile.tsv and commands.sh
                stats_relpath = os.path.relpath(os.path.join(
                                    self.prj.metadata.results_subdir,
                                    sample_name, "stats.tsv"), reports_dir)
                profile_relpath = os.path.relpath(os.path.join(
                                    self.prj.metadata.results_subdir,
                                    sample_name, profile_name), reports_dir)              
                command_relpath = os.path.relpath(os.path.join(
                                    self.prj.metadata.results_subdir,
                                    sample_name, command_name), reports_dir)
                html_file.write(SAMPLE_BUTTONS.format(
                                    button_class=button_class,
                                    flag=flag,
                                    log_file=log_relpath,
                                    profile_file=profile_relpath,
                                    commands_file=command_relpath,
                                    stats_file=stats_relpath))
                
                # Add the sample's statistics as a table
                html_file.write("\t\t<div class='container-fluid'>\n")
                html_file.write(TABLE_HEADER)   
                for key, value in sample_stats.items():
                    html_file.write(TABLE_COLS.format(col_val=str(key)))
                html_file.write(TABLE_COLS_FOOTER)

                # Produce table rows      
                html_file.write(TABLE_ROW_HEADER)                    
                for key, value in sample_stats.items():
                    # Treat sample_name as a link to sample page
                    if key=='sample_name':                       
                        html_filename = str(value) + ".html"
                        html_page = os.path.join(reports_dir,
                                                 html_filename).lower()
                        page_relpath = os.path.relpath(html_page, reports_dir)
                        html_file.write(TABLE_ROWS_LINK.format(
                                            html_page=page_relpath,
                                            page_name=html_filename,
                                            link_name=str(value)))
                    # Otherwise add as a static cell value
                    else:
                        html_file.write(TABLE_ROWS.format(
                            row_val=str(value)))
                html_file.write(TABLE_ROW_FOOTER)                                   
                html_file.write(TABLE_FOOTER)               
                html_file.write("\t\t</div>\n")
                html_file.write("\t\t<hr>\n")

                # Add all the objects for the current sample
                html_file.write("\t\t<div class='container-fluid'>\n")
                html_file.write("\t\t<h4>{sample} figures</h4>\n".format(sample=sample_name))
                for sample_name in single_sample['sample_name'].drop_duplicates().sort_values():
                    o = single_sample[single_sample['sample_name'] == sample_name]
                    for i, row in o.iterrows():
                        image_path = os.path.join(
                                        self.prj.metadata.results_subdir,
                                        sample_name, row['anchor_image'])
                        image_relpath = os.path.relpath(image_path, reports_dir)
                        page_path = os.path.join(
                                        self.prj.metadata.results_subdir,
                                        sample_name, row['filename'])
                        page_relpath = os.path.relpath(page_path, reports_dir)
                        # If the object has a png image, use it!
                        if os.path.isfile(image_path):
                            html_file.write(SAMPLE_PLOTS.format(
                                label=str(row['key']),
                                path=page_relpath,
                                image=image_relpath))
                        # Otherwise it's just a link
                        else:
                            html_file.write(SAMPLE_PLOTS.format(
                                label=str(row['key']),
                                path=page_relpath,
                                image=""))
                html_file.write("\t\t</div>\n")
                html_file.write(HTML_FOOTER)
                html_file.close()

        def create_navbar(objs, wd):
            # Need all the pages
            # Need all the links
            # Return a string containing the navbar prebuilt html           
            objs_html_path = "{root}_objs_summary.html".format(
                root=os.path.join(self.prj.metadata.output_dir, self.prj.name))
            reports_dir = os.path.join(self.prj.metadata.output_dir,
                                       "reports")
            index_page_relpath = os.path.relpath(objs_html_path, wd)
            navbar_header = NAVBAR_HEADER.format(index_html=index_page_relpath)
            # Add link to STATUS page
            status_page = os.path.join(self.prj.metadata.output_dir,
                                       "reports", "status.html")
            # Use relative linking structure
            relpath = os.path.relpath(status_page, wd)
            #print (relpath)  #  DEBUGGING
            status_link = NAVBAR_MENU_LINK.format(html_page=relpath,
                                                  page_name="Status")
            # Absolute paths formatted like this; TESTING purposes only
            # status_link = NAVBAR_MENU_LINK.format(html_page=os.path.join(
                                        # self.prj.metadata.output_dir,
                                        # "reports", "status.html"),
                                        # page_name="Status")
                               
            # Create list of object page links
            obj_links = []
            # If the number of objects is 20 or less, use a drop-down menu
            if len(objs['key'].drop_duplicates()) <= 20:
                # Create drop-down menu item for all the objects
                obj_links.append(NAVBAR_DROPDOWN_HEADER.format(menu_name="Objects"))
                objects_page = os.path.join(self.prj.metadata.output_dir,
                                            "reports", "objects.html")
                relpath = os.path.relpath(objects_page, wd)
                obj_links.append(NAVBAR_DROPDOWN_LINK.format(
                                    html_page=relpath,
                                    page_name="All objects"))
                obj_links.append(NAVBAR_DROPDOWN_DIVIDER)             
                for key in objs['key'].drop_duplicates().sort_values():
                    page_name = key + ".html"
                    # Absolute path for testing purposes
                    #page_path = os.path.join(wd, page_name).replace(' ', '_').lower()
                    page_path = os.path.join(reports_dir, page_name).replace(' ', '_').lower()
                    relpath = os.path.relpath(page_path, wd)
                    obj_links.append(NAVBAR_DROPDOWN_LINK.format(
                                        html_page=relpath,
                                        page_name=key))
                obj_links.append(NAVBAR_DROPDOWN_FOOTER)
            else:
                # Create a menu link to the objects parent page
                objects_page = os.path.join(self.prj.metadata.output_dir,
                                            "reports", "objects.html")
                relpath = os.path.relpath(objects_page, wd)
                obj_links.append(NAVBAR_MENU_LINK.format(
                                    html_page=relpath,
                                    page_name="Objects"))

            # Create list of sample page links
            sample_links = []
            # If the number of samples is 20 or less, use a drop-down menu
            if len(objs['sample_name'].drop_duplicates()) <= 20:
                # Create drop-down menu item for all the samples
                sample_links.append(NAVBAR_DROPDOWN_HEADER.format(menu_name="Samples"))
                samples_page = os.path.join(self.prj.metadata.output_dir,
                                            "reports", "samples.html")
                relpath = os.path.relpath(samples_page, wd)
                sample_links.append(NAVBAR_DROPDOWN_LINK.format(
                                        html_page=relpath,
                                        page_name="All samples"))
                sample_links.append(NAVBAR_DROPDOWN_DIVIDER)   
                for sample_name in objs['sample_name'].drop_duplicates().sort_values():
                    page_name = sample_name + ".html"
                    # Absolute path for testing purposes
                    #page_path = os.path.join(wd, page_name).replace(' ', '_').lower()
                    page_path = os.path.join(reports_dir, page_name).replace(' ', '_').lower()
                    relpath = os.path.relpath(page_path, wd)
                    sample_links.append(NAVBAR_DROPDOWN_LINK.format(
                                            html_page=relpath,
                                            page_name=sample_name))
                sample_links.append(NAVBAR_DROPDOWN_FOOTER)
            else:
                # Create a menu link to the samples parent page
                samples_page = os.path.join(self.prj.metadata.output_dir,
                                            "reports", "samples.html")
                relpath = os.path.relpath(samples_page, wd)
                sample_links.append(NAVBAR_MENU_LINK.format(
                                        html_page=relpath,
                                        page_name="Samples"))

            return ("\n".join([navbar_header, status_link,
                               "\n".join(obj_links),
                               "\n".join(sample_links),
                               NAVBAR_FOOTER]))
                
        def create_index_html(objs, stats):
            # TODO: Need to add a file check for stats to make sure it's present
            #       or I guess to make sure stats here is not empty
            objs.drop_duplicates(keep='last', inplace=True)
            reports_dir = os.path.join(self.prj.metadata.output_dir,
                                       "reports")
            # Generate parent index.html page
            objs_html_path = "{root}_objs_summary.html".format(
                root=os.path.join(self.prj.metadata.output_dir, self.prj.name))
            # Generate parent objects.html page
            object_parent_path = os.path.join(reports_dir, "objects.html")
            # Generate parent samples.html page
            sample_parent_path = os.path.join(reports_dir, "samples.html")
            
            objs_html_file = open(objs_html_path, 'w')
            objs_html_file.write(HTML_HEAD_OPEN)
            objs_html_file.write(TABLE_STYLE_ROTATED_HEADER)
            objs_html_file.write(HTML_TITLE.format(project_name=self.prj.name))
            navbar = create_navbar(objs, self.prj.metadata.output_dir)
            # navbar = create_navbar(objs, os.path.join(
                                    # self.prj.metadata.output_dir,
                                    # "reports"))
            objs_html_file.write(navbar)
            objs_html_file.write(HTML_HEAD_CLOSE)

            # Add stats_summary.tsv button link
            stats_relpath = os.path.relpath(tsv_outfile_path,
                                            self.prj.metadata.output_dir)
            objs_html_file.write(HTML_BUTTON.format(
                file_path=stats_relpath, label="Stats Summary File"))

            # Add stats summary table to index page
            #print ("objs['sample_name']: " + objs['sample_name'].drop_duplicates())
            #print ("num samples: " + str(len(objs['sample_name'].drop_duplicates())))
            if os.path.isfile(stats_file):
                objs_html_file.write(TABLE_HEADER)
                # Produce table columns                
                for key, value in stats[0].items():
                    objs_html_file.write(TABLE_COLS.format(col_val=str(key)))
                objs_html_file.write(TABLE_COLS_FOOTER)
                # Produce table rows
                sample_pos = 0
                #print ("num samples: " + str(len(stats)))
                # TODO: Need to get sample names from the stats summary file
                #       Otherwise if the objects file is missing it won't add it
                               
                while sample_pos < len(stats):
                    #print ("sample_pos: " + str(sample_pos))
                    sample_name = str(stats[sample_pos]['sample_name'])
                    #print ("sample_name: " + sample_name)
                    #print ("")
                #for sample_name in objs['sample_name'].drop_duplicates().sort_values():
                    single_sample = objs[objs['sample_name'] == sample_name]
                    #if not single_sample.empty:                 
                    #print ("single_sample: " + single_sample)
                    #print ("")
                    objs_html_file.write(TABLE_ROW_HEADER)                   
                    #print ("stats[sample_pos]: " + str(stats[sample_pos].items()))
                    #print ("")
                    for key, value in stats[sample_pos].items():
                        # Treat sample_name as a link to sample page
                        if key=='sample_name':
                            html_filename = str(value) + ".html"
                            html_page = os.path.join(reports_dir,
                                                     html_filename).lower()
                            page_relpath = os.path.relpath(html_page,
                                            self.prj.metadata.output_dir)
                            create_sample_html(single_sample, objs, value,
                                               stats[sample_pos],
                                               html_filename,
                                               objs_html_path)
                            objs_html_file.write(TABLE_ROWS_LINK.format(
                                html_page=page_relpath,
                                page_name=page_relpath,
                                link_name=str(value)))
                        # Otherwise add as a static cell value
                        else:
                            objs_html_file.write(TABLE_ROWS.format(
                                row_val=str(value)))
                    objs_html_file.write(TABLE_ROW_FOOTER)
                    sample_pos += 1
                objs_html_file.write(TABLE_FOOTER)
            else:
                _LOGGER.warn("No stats file '%s'", stats_file)
            # Create parent samples page with links to each sample
            create_sample_parent_html(objs)

            # Create objects pages
            for key in objs['key'].drop_duplicates().sort_values():
                objects = objs[objs['key'] == key]
                object_filename = str(key) + ".html"
                create_object_html(
                    objects, objs, key, object_filename, objs_html_path)

            # Create parent objects page with links to each object type
            create_object_parent_html(objs)

            # Create status page with each sample's status listed
            create_status_html(objs)

            # Complete and close HTML file
            objs_html_file.write(HTML_FOOTER)

            objs_html_file.close()
            _LOGGER.info(
                "Summary (n=" + str(len(stats)) + "): " + tsv_outfile_path)

        # Create stats_summary file
        for sample in self.prj.samples:
            _LOGGER.info(self.counter.show(sample.sample_name,
                                           sample.protocol))
            sample_output_folder = sample_folder(self.prj, sample)

            # Grab the basic info from the annotation sheet for this sample.
            # This will correspond to a row in the output.
            sample_stats = sample.get_sheet_dict()
            columns.extend(sample_stats.keys())
            # Version 0.3 standardized all stats into a single file
            stats_file = os.path.join(sample_output_folder, "stats.tsv")
            if os.path.isfile(stats_file):
                _LOGGER.info("Found stats file: '%s'", stats_file)
            else:
                _LOGGER.warn("No stats file '%s'", stats_file)
                continue

            t = _pd.read_table(
                stats_file, header=None, names=['key', 'value', 'pl'])

            t.drop_duplicates(subset=['key', 'pl'], keep='last', inplace=True)
            # t.duplicated(subset= ['key'], keep = False)
            t.loc[:, 'plkey'] = t['pl'] + ":" + t['key']
            dupes = t.duplicated(subset=['key'], keep=False)
            t.loc[dupes, 'key'] = t.loc[dupes, 'plkey']

            sample_stats.update(t.set_index('key')['value'].to_dict())
            stats.append(sample_stats)
            columns.extend(t.key.tolist())

        self.counter.reset()

        # Create objects summary file
        for sample in self.prj.samples:
            _LOGGER.info(self.counter.show(sample.sample_name, sample.protocol))
            sample_output_folder = sample_folder(self.prj, sample)
            # Now process any reported figures <DEPRECATED>            
            # figs_file = os.path.join(sample_output_folder, "figures.tsv")
            # if os.path.isfile(figs_file):
                # _LOGGER.info("Found figures file: '%s'", figs_file)
            # else:
                # _LOGGER.warn("No figures file '%s'", figs_file)
                # continue
            # t = _pd.read_table(
                # figs_file, header=None, names=['key', 'value', 'pl'])
            # t['sample_name'] = sample.name
            # figs = figs.append(t, ignore_index=True)
            
            # Now process any reported objects
            # TODO: only use the objects tsv once confirmed working
            objs_file = os.path.join(sample_output_folder, "objects.tsv")
            if os.path.isfile(objs_file):
                _LOGGER.info("Found objects file: '%s'", objs_file)
            else:
                _LOGGER.warn("No objects file '%s'", objs_file)
                continue
            t = _pd.read_table(objs_file, header=None,
                               names=['key', 'filename', 'anchor_text',
                                      'anchor_image', 'annotation'])
            t['sample_name'] = sample.name
            objs = objs.append(t, ignore_index=True)

        tsv_outfile_path = os.path.join(self.prj.metadata.output_dir, self.prj.name)
        if hasattr(self.prj, "subproject") and self.prj.subproject:
            tsv_outfile_path += '_' + self.prj.subproject
        tsv_outfile_path += '_stats_summary.tsv'

        tsv_outfile = open(tsv_outfile_path, 'w')

        tsv_writer = csv.DictWriter(tsv_outfile, fieldnames=uniqify(columns),
                                    delimiter='\t', extrasaction='ignore')
        tsv_writer.writeheader()

        for row in stats:
            tsv_writer.writerow(row)

        tsv_outfile.close()            
        
        # all samples are parsed. 
        # Produce figures html file. <DEPRECATED>
        #create_figures_html(figs)
        # Produce objects html file.
        create_index_html(objs, stats)
        

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



def query_yes_no(question, default="no"):
    """
    Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {
        "yes": True, "y": True, "ye": True,
        "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write(
                "Please respond with 'yes' or 'no' "
                "(or 'y' or 'n').\n")



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

    :param total: number of jobs to process
    :type total: int

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



class _VersionInHelpParser(argparse.ArgumentParser):
    def format_help(self):
        """ Add version information to help text. """
        return "version: {}\n".format(__version__) + \
               super(_VersionInHelpParser, self).format_help()



def main():
    # Parse command-line arguments and establish logger.
    args, remaining_args = parse_arguments()

    _LOGGER.info("Command: {} (Looper version: {})".
                 format(args.command, __version__))
    # Initialize project
    _LOGGER.debug("compute_env_file: " + str(getattr(args, 'env', None)))
    _LOGGER.info("Building Project")
    if args.subproject is not None:
        _LOGGER.info("Using subproject: %s", args.subproject)
    prj = Project(
        args.config_file, subproject=args.subproject,
        file_checks=args.file_checks,
        compute_env_file=getattr(args, 'env', None))

    _LOGGER.info("Results subdir: " + prj.metadata.results_subdir)

    with ProjectContext(prj,
            include_protocols=args.include_protocols,
            exclude_protocols=args.exclude_protocols) as prj:

        if args.command == "run":
            if args.compute:
                prj.set_compute(args.compute)

            # TODO split here, spawning separate run process for each
            # pipelines directory in project metadata pipelines directory.

            if not hasattr(prj.metadata, "pipelines_dir") or \
                            len(prj.metadata.pipelines_dir) == 0:
                raise AttributeError(
                        "Looper requires at least one pipeline(s) location.")

            if not prj.interfaces_by_protocol:
                _LOGGER.error(
                        "The Project knows no protocols. Does it point "
                        "to at least one pipelines location that exists?")
                return

            run = Runner(prj)
            try:
                run(args, remaining_args)
            except IOError:
                _LOGGER.error("{} pipelines_dir: '{}'".format(
                        prj.__class__.__name__, prj.metadata.pipelines_dir))
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
