#!/usr/bin/env python
"""
Looper: a pipeline submission engine. https://github.com/pepkit/looper
"""

import abc
import csv
import logging
import subprocess
import sys

if sys.version_info < (3, 3):
    from collections import Mapping
else:
    from collections.abc import Mapping

import logmuse
import pandas as _pd

# Need specific sequence of actions for colorama imports?
from colorama import init

init()
from shutil import rmtree

from colorama import Fore, Style
from eido import inspect_project, validate_config, validate_sample
from eido.exceptions import EidoValidationError
from jsonschema import ValidationError
from pephubclient import PEPHubClient
from peppy.const import *
from peppy.exceptions import RemoteYAMLError
from rich.color import Color
from rich.console import Console
from rich.table import Table
from ubiquerg.cli_tools import query_yes_no
from ubiquerg.collection import uniqify

from . import __version__, build_parser, validate_post_parse
from .conductor import SubmissionConductor
from .const import *
from .divvy import DEFAULT_COMPUTE_RESOURCES_NAME, select_divvy_config
from .exceptions import (
    JobSubmissionException,
    MisconfigurationException,
    SampleFailedException,
)
from .html_reports import HTMLReportBuilderOld
from .html_reports_pipestat import HTMLReportBuilder, fetch_pipeline_results
from .html_reports_project_pipestat import HTMLReportBuilderProject
from .pipeline_interface import PipelineInterface
from .project import Project, ProjectContext
from .utils import *

_PKGNAME = "looper"
_LOGGER = logging.getLogger(_PKGNAME)


class Executor(object):
    """Base class that ensures the program's Sample counter starts.

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
        """Do the work of the subcommand/program."""
        pass


class Checker(Executor):
    def __call__(self, args):
        """
        Check Project status, using pipestat.

        :param argparse.Namespace: arguments provided to the command
        """

        # aggregate pipeline status data
        status = {}
        if args.project:
            psms = self.prj.get_pipestat_managers(project_level=True)
            for pipeline_name, psm in psms.items():
                s = psm.get_status() or "unknown"
                status.setdefault(pipeline_name, {})
                status[pipeline_name][self.prj.name] = s
                _LOGGER.debug(f"{self.prj.name} ({pipeline_name}): {s}")
        else:
            for sample in self.prj.samples:
                psms = self.prj.get_pipestat_managers(sample_name=sample.sample_name)
                for pipeline_name, psm in psms.items():
                    s = psm.get_status(sample_name=sample.sample_name)
                    status.setdefault(pipeline_name, {})
                    status[pipeline_name][sample.sample_name] = s
                    _LOGGER.debug(f"{sample.sample_name} ({pipeline_name}): {s}")

        console = Console()

        for pipeline_name, pipeline_status in status.items():
            table_title = f"'{pipeline_name}' pipeline status summary"
            table = Table(
                show_header=True,
                header_style="bold magenta",
                title=table_title,
                width=len(table_title) + 10,
            )
            table.add_column(f"Status", justify="center")
            table.add_column("Jobs count/total jobs", justify="center")
            for status_id in psm.status_schema.keys():
                status_list = list(pipeline_status.values())
                if status_id in status_list:
                    status_count = status_list.count(status_id)
                    table.add_row(status_id, f"{status_count}/{len(status_list)}")
            console.print(table)

        if args.itemized:
            for pipeline_name, pipeline_status in status.items():
                table_title = f"Pipeline: '{pipeline_name}'"
                table = Table(
                    show_header=True,
                    header_style="bold magenta",
                    title=table_title,
                    min_width=len(table_title) + 10,
                )
                table.add_column(
                    f"{'Project' if args.project else 'Sample'} name",
                    justify="right",
                    no_wrap=True,
                )
                table.add_column("Status", justify="center")
                for name, status_id in pipeline_status.items():
                    try:
                        color = Color.from_rgb(
                            *psm.status_schema[status_id]["color"]
                        ).name
                    except KeyError:
                        color = "#bcbcbc"
                        status_id = "unknown"
                    table.add_row(name, f"[{color}]{status_id}[/{color}]")
                console.print(table)

        if args.describe_codes:
            table = Table(
                show_header=True,
                header_style="bold magenta",
                title=f"Status codes description",
                width=len(psm.status_schema_source) + 20,
                caption=f"Descriptions source: {psm.status_schema_source}",
            )
            table.add_column("Status code", justify="center")
            table.add_column("Description", justify="left")
            for status, status_obj in psm.status_schema.items():
                if "description" in status_obj:
                    desc = status_obj["description"]
                else:
                    desc = ""
                table.add_row(status, desc)
            console.print(table)


class CheckerOld(Executor):
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
        flags = sorted([flags] if isinstance(flags, str) else list(flags or FLAGS))
        flag_text = ", ".join(flags)

        # Collect the files by flag and sort by flag name.
        _LOGGER.debug("Checking project folders for flags: %s", flag_text)
        if all_folders:
            files_by_flag = fetch_flag_files(
                results_folder=self.prj.results_folder, flags=flags
            )
        else:
            files_by_flag = fetch_flag_files(prj=self.prj, flags=flags)

        # For each flag, output occurrence count.
        for flag in flags:
            _LOGGER.info("%s: %d", flag.upper(), len(files_by_flag[flag]))

        # For each flag, output filepath(s) if not overly verbose.
        for flag in flags:
            try:
                files = files_by_flag[flag]
            except Exception as e:
                _LOGGER.debug(
                    "No files for {} flag. Caught exception: {}".format(
                        flags, getattr(e, "message", repr(e))
                    )
                )
                continue
            # If checking on a specific flag, do not limit the number of
            # reported filepaths, but do not report empty file lists
            if len(flags) == 1 and len(files) > 0:
                _LOGGER.info("%s (%d):\n%s", flag.upper(), len(files), "\n".join(files))
            # Regardless of whether 0-count flags are previously reported,
            # don't report an empty file list for a flag that's absent.
            # If the flag-to-files mapping is defaultdict, absent flag (key)
            # will fetch an empty collection, so check for length of 0.
            if 0 < len(files) <= max_file_count:
                _LOGGER.info("%s (%d):\n%s", flag.upper(), len(files), "\n".join(files))


class Cleaner(Executor):
    """Remove all intermediate files (defined by pypiper clean scripts)."""

    def __call__(self, args, preview_flag=True):
        """
        Execute the file cleaning process.

        :param argparse.Namespace args: command-line options and arguments
        :param bool preview_flag: whether to halt before actually removing files
        """
        self.counter.show(name=self.prj.name, type="project")
        for sample in self.prj.samples:
            _LOGGER.info(self.counter.show(sample.sample_name))
            sample_output_folder = sample_folder(self.prj, sample)
            cleanup_files = glob.glob(
                os.path.join(sample_output_folder, "*_cleanup.sh")
            )
            if not cleanup_files:
                _LOGGER.info("Nothing to clean.")
                continue
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
        if not args.force_yes and not query_yes_no(
            "Are you sure you want to permanently delete all "
            "intermediate pipeline results for this project?"
        ):
            _LOGGER.info("Clean action aborted by user.")
            return 1
        self.counter.reset()
        return self(args, preview_flag=False)


def select_samples(prj: Project, args: argparse.Namespace) -> Iterable[Any]:
    """Use CLI limit/skip arguments to select subset of project's samples."""
    # TODO: get proper element type for signature.
    num_samples = len(prj.samples)
    if args.limit is None and args.skip is None:
        index = range(1, num_samples + 1)
    elif args.skip is not None:
        index = desired_samples_range_skipped(args.skip, num_samples)
    elif args.limit is not None:
        index = desired_samples_range_limited(args.limit, num_samples)
    else:
        raise argparse.ArgumentError(
            "Both --limit and --skip are in use, but they should be mutually exclusive."
        )
    return (prj.samples[i - 1] for i in index)


class Destroyer(Executor):
    """Destroyer of files and folders associated with Project's Samples"""

    def __call__(self, args, preview_flag=True):
        """
        Completely remove all output produced by any pipelines.

        :param argparse.Namespace args: command-line options and arguments
        :param bool preview_flag: whether to halt before actually removing files
        """

        _LOGGER.info("Removing results:")

        for sample in select_samples(prj=self.prj, args=args):
            _LOGGER.info(self.counter.show(sample.sample_name))
            sample_output_folder = sample_folder(self.prj, sample)
            if preview_flag:
                # Preview: Don't actually delete, just show files.
                _LOGGER.info(str(sample_output_folder))
            else:
                _remove_or_dry_run(sample_output_folder, args.dry_run)

        _LOGGER.info("Removing summary:")
        destroy_summary(self.prj, args.dry_run)

        if not preview_flag:
            _LOGGER.info("Destroy complete.")
            return 0

        if args.dry_run:
            _LOGGER.info("Dry run. No files destroyed.")
            return 0

        if not args.force_yes and not query_yes_no(
            "Are you sure you want to permanently delete all pipeline "
            "results for this project?"
        ):
            _LOGGER.info("Destroy action aborted by user.")
            return 1

        self.counter.reset()

        # Finally, run the true destroy:
        return self(args, preview_flag=False)


class Collator(Executor):
    """Submitter for project-level pipelines"""

    def __init__(self, prj):
        """
        Initializes an instance

        :param Project prj: Project with which to work/operate on
        """
        super(Executor, self).__init__()
        self.prj = prj

    def __call__(self, args, **compute_kwargs):
        """
        Matches collators by protocols, creates submission scripts
        and submits them

        :param argparse.Namespace args: parsed command-line options and
            arguments, recognized by looper
        """
        jobs = 0
        self.debug = {}
        project_pifaces = self.prj.project_pipeline_interface_sources
        if not project_pifaces:
            raise MisconfigurationException(
                "Looper requires a pointer to at least one project pipeline. "
                "Please refer to the documentation on linking project to a "
                "pipeline: "
                "http://looper.databio.org/en/latest/defining-a-project"
            )
        self.counter = LooperCounter(len(project_pifaces))
        for project_piface in project_pifaces:
            try:
                project_piface_object = PipelineInterface(
                    project_piface, pipeline_type="project"
                )
            except (IOError, ValidationError) as e:
                _LOGGER.warning(
                    "Ignoring invalid pipeline interface source: {}. "
                    "Caught exception: {}".format(
                        project_piface, getattr(e, "message", repr(e))
                    )
                )
                continue
            _LOGGER.info(
                self.counter.show(
                    name=self.prj.name,
                    type="project",
                    pipeline_name=project_piface_object.pipeline_name,
                )
            )
            conductor = SubmissionConductor(
                pipeline_interface=project_piface_object,
                prj=self.prj,
                compute_variables=compute_kwargs,
                delay=args.time_delay,
                extra_args=args.command_extra,
                extra_args_override=args.command_extra_override,
                ignore_flags=args.ignore_flags,
                collate=True,
            )
            if conductor.is_project_submittable(force=args.ignore_flags):
                conductor._pool = [None]
                conductor.submit()
                jobs += conductor.num_job_submissions
        _LOGGER.info("\nLooper finished")
        _LOGGER.info("Jobs submitted: {}".format(jobs))
        self.debug["Jobs submitted"] = jobs
        return self.debug


class Runner(Executor):
    """The true submitter of pipelines"""

    def __call__(self, args, rerun=False, **compute_kwargs):
        """
        Do the Sample submission.

        :param argparse.Namespace args: parsed command-line options and
            arguments, recognized by looper
        :param list remaining_args: command-line options and arguments not
            recognized by looper, germane to samples/pipelines
        :param bool rerun: whether the given sample is being rerun rather than
            run for the first time
        """
        self.debug = {}  # initialize empty dict for return values
        max_cmds = sum(list(map(len, self.prj._samples_by_interface.values())))
        self.counter.total = max_cmds
        failures = defaultdict(list)  # Collect problems by sample.
        processed_samples = set()  # Enforce one-time processing.
        comp_vars = compute_kwargs or {}

        # Determine number of samples eligible for processing.
        num_samples = len(self.prj.samples)

        num_commands_possible = 0
        failed_submission_scripts = []

        # config validation (samples excluded) against all schemas defined
        # for every pipeline matched for this project
        for schema_file in self.prj.get_schemas(self.prj.pipeline_interfaces):
            try:
                validate_config(self.prj, schema_file)
            except RemoteYAMLError:
                _LOGGER.warning(
                    "Could not read remote schema, skipping config validation."
                )

        submission_conductors = {}
        for piface in self.prj.pipeline_interfaces:
            conductor = SubmissionConductor(
                pipeline_interface=piface,
                prj=self.prj,
                compute_variables=comp_vars,
                delay=args.time_delay,
                extra_args=args.command_extra,
                extra_args_override=args.command_extra_override,
                ignore_flags=args.ignore_flags,
                max_cmds=args.lumpn,
                max_size=args.lump,
            )
            submission_conductors[piface.pipe_iface_file] = conductor

        _LOGGER.info(f"Pipestat compatible: {self.prj.pipestat_configured_project}")

        for sample in select_samples(prj=self.prj, args=args):
            pl_fails = []
            skip_reasons = []
            sample_pifaces = self.prj.get_sample_piface(
                sample[self.prj.sample_table_index]
            )
            if not sample_pifaces:
                skip_reasons.append("No pipeline interfaces defined")

            if skip_reasons:
                _LOGGER.warning(NOT_SUB_MSG.format(", ".join(skip_reasons)))
                failures[sample.sample_name] = skip_reasons
                continue

            # single sample validation against a single schema
            # (from sample's piface)
            for schema_file in self.prj.get_schemas(sample_pifaces):
                try:
                    validate_sample(self.prj, sample.sample_name, schema_file)
                except EidoValidationError as e:
                    _LOGGER.error(f"Short-circuiting due to validation error: {e}")
                    self.debug[
                        "EidoValidationError"
                    ] = f"Short-circuiting due to validation error: {e}"
                    return False
                except RemoteYAMLError:
                    _LOGGER.warn(
                        f"Could not read remote schema, skipping '{sample.sample_name}' "
                        f"sample validation against {schema_file}"
                    )

            processed_samples.add(sample[self.prj.sample_table_index])

            for sample_piface in sample_pifaces:
                _LOGGER.info(
                    self.counter.show(
                        name=sample.sample_name,
                        pipeline_name=sample_piface.pipeline_name,
                    )
                )
                num_commands_possible += 1
                cndtr = submission_conductors[sample_piface.pipe_iface_file]
                try:
                    curr_pl_fails = cndtr.add_sample(sample, rerun=rerun)
                except JobSubmissionException as e:
                    failed_submission_scripts.append(e.script)
                else:
                    pl_fails.extend(curr_pl_fails)
            if pl_fails:
                failures[sample.sample_name].extend(pl_fails)

        job_sub_total = 0
        cmd_sub_total = 0

        for piface, conductor in submission_conductors.items():
            conductor.submit(force=True)
            job_sub_total += conductor.num_job_submissions
            cmd_sub_total += conductor.num_cmd_submissions

        # Report what went down.
        _LOGGER.info("\nLooper finished")
        _LOGGER.info(
            "Samples valid for job generation: {} of {}".format(
                len(processed_samples), num_samples
            )
        )
        _LOGGER.info("Commands submitted: {} of {}".format(cmd_sub_total, max_cmds))
        self.debug["Commands submitted"] = "Commands submitted: {} of {}".format(
            cmd_sub_total, max_cmds
        )
        if args.dry_run:
            job_sub_total_if_real = job_sub_total
            job_sub_total = 0
            _LOGGER.info(
                f"Dry run. No jobs were actually submitted, but {job_sub_total_if_real} would have been."
            )
        _LOGGER.info("Jobs submitted: {}".format(job_sub_total))
        self.debug["Jobs submitted"] = job_sub_total

        # Restructure sample/failure data for display.
        samples_by_reason = defaultdict(set)
        # Collect names of failed sample(s) by failure reason.
        for sample, failures in failures.items():
            for f in failures:
                samples_by_reason[f].add(sample)
                self.debug[f] = sample
        # Collect samples by pipeline with submission failure.
        for piface, conductor in submission_conductors.items():
            # Don't add failure key if there are no samples that failed for
            # that reason.
            if conductor.failed_samples:
                fails = set(conductor.failed_samples)
                samples_by_reason[SUBMISSION_FAILURE_MESSAGE] |= fails

        failed_sub_samples = samples_by_reason.get(SUBMISSION_FAILURE_MESSAGE)
        if failed_sub_samples:
            _LOGGER.info(
                "\n{} samples with at least one failed job submission:"
                " {}".format(len(failed_sub_samples), ", ".join(failed_sub_samples))
            )

        # If failure keys are only added when there's at least one sample that
        # failed for that reason, we can display information conditionally,
        # depending on whether there's actually failure(s).
        if samples_by_reason:
            _LOGGER.info(
                "\n{} unique reasons for submission failure: {}".format(
                    len(samples_by_reason), ", ".join(samples_by_reason.keys())
                )
            )
            full_fail_msgs = [
                _create_failure_message(reason, samples)
                for reason, samples in samples_by_reason.items()
            ]
            _LOGGER.info("\nSummary of failures:\n{}".format("\n".join(full_fail_msgs)))

        if failed_sub_samples:
            _LOGGER.debug("Raising SampleFailedException")
            raise SampleFailedException

        return self.debug


class Reporter(Executor):
    """Combine project outputs into a browsable HTML report"""

    def __call__(self, args):
        # initialize the report builder
        p = self.prj
        project_level = args.project

        if project_level:
            psms = self.prj.get_pipestat_managers(project_level=True)
            print(psms)
            for name, psm in psms.items():
                # Summarize will generate the static HTML Report Function
                psm.summarize()
        else:
            for sample in p.prj.samples:
                psms = self.prj.get_pipestat_managers(sample_name=sample.sample_name)
                print(psms)
                for name, psm in psms.items():
                    # Summarize will generate the static HTML Report Function
                    psm.summarize()


class Tabulator(Executor):
    """Project/Sample statistics and table output generator"""

    def __call__(self, args):
        project_level = args.project
        if project_level:
            self.counter = LooperCounter(len(self.prj.project_pipeline_interfaces))
            for piface in self.prj.project_pipeline_interfaces:
                # Do the stats and object summarization.
                pipeline_name = piface.pipeline_name
                # pull together all the fits and stats from each sample into
                # project-combined spreadsheets.
                self.stats = _create_stats_summary(
                    self.prj, pipeline_name, project_level, self.counter
                )
                self.objs = _create_obj_summary(
                    self.prj, pipeline_name, project_level, self.counter
                )
        else:
            for piface_source in self.prj._samples_by_piface(
                self.prj.piface_key
            ).keys():
                # Do the stats and object summarization.
                pipeline_name = PipelineInterface(config=piface_source).pipeline_name
                # pull together all the fits and stats from each sample into
                # project-combined spreadsheets.
                self.stats = _create_stats_summary(
                    self.prj, pipeline_name, project_level, self.counter
                )
                self.objs = _create_obj_summary(
                    self.prj, pipeline_name, project_level, self.counter
                )
        return self


def _create_stats_summary(project, pipeline_name, project_level, counter):
    """
    Create stats spreadsheet and columns to be considered in the report, save
    the spreadsheet to file

    :param looper.Project project: the project to be summarized
    :param str pipeline_name: name of the pipeline to tabulate results for
    :param bool project_level: whether the project-level pipeline resutlts
        should be tabulated
    :param looper.LooperCounter counter: a counter object
    """
    # Create stats_summary file
    columns = set()
    stats = []
    _LOGGER.info("Creating stats summary")
    if project_level:
        _LOGGER.info(
            counter.show(name=project.name, type="project", pipeline_name=pipeline_name)
        )
        reported_stats = {"project_name": project.name}
        results = fetch_pipeline_results(
            project=project,
            pipeline_name=pipeline_name,
            inclusion_fun=lambda x: x not in OBJECT_TYPES,
        )
        reported_stats.update(results)
        stats.append(reported_stats)
        columns |= set(reported_stats.keys())

    else:
        for sample in project.samples:
            sn = sample.sample_name
            _LOGGER.info(counter.show(sn, pipeline_name))
            reported_stats = {project.sample_table_index: sn}
            results = fetch_pipeline_results(
                project=project,
                pipeline_name=pipeline_name,
                sample_name=sn,
                inclusion_fun=lambda x: x not in OBJECT_TYPES,
            )
            reported_stats.update(results)
            stats.append(reported_stats)
            columns |= set(reported_stats.keys())

    tsv_outfile_path = get_file_for_project(project, pipeline_name, "stats_summary.tsv")
    tsv_outfile = open(tsv_outfile_path, "w")
    tsv_writer = csv.DictWriter(
        tsv_outfile, fieldnames=list(columns), delimiter="\t", extrasaction="ignore"
    )
    tsv_writer.writeheader()
    for row in stats:
        tsv_writer.writerow(row)
    tsv_outfile.close()
    _LOGGER.info(
        f"'{pipeline_name}' pipeline stats summary (n={len(stats)}):"
        f" {tsv_outfile_path}"
    )
    counter.reset()
    return stats


def _create_obj_summary(project, pipeline_name, project_level, counter):
    """
    Read sample specific objects files and save to a data frame

    :param looper.Project project: the project to be summarized
    :param str pipeline_name: name of the pipeline to tabulate results for
    :param looper.LooperCounter counter: a counter object
    :param bool project_level: whether the project-level pipeline resutlts
        should be tabulated
    """
    _LOGGER.info("Creating objects summary")
    reported_objects = {}
    if project_level:
        _LOGGER.info(
            counter.show(name=project.name, type="project", pipeline_name=pipeline_name)
        )
        res = fetch_pipeline_results(
            project=project,
            pipeline_name=pipeline_name,
            inclusion_fun=lambda x: x in OBJECT_TYPES,
        )
        # need to cast to a dict, since other mapping-like objects might
        # cause issues when writing to the collective yaml file below
        project_reported_objects = {k: dict(v) for k, v in res.items()}
        reported_objects[project.name] = project_reported_objects
    else:
        for sample in project.samples:
            sn = sample.sample_name
            _LOGGER.info(counter.show(sn, pipeline_name))
            res = fetch_pipeline_results(
                project=project,
                pipeline_name=pipeline_name,
                sample_name=sn,
                inclusion_fun=lambda x: x in OBJECT_TYPES,
            )
            # need to cast to a dict, since other mapping-like objects might
            # cause issues when writing to the collective yaml file below
            sample_reported_objects = {k: dict(v) for k, v in res.items()}
            reported_objects[sn] = sample_reported_objects
    objs_yaml_path = get_file_for_project(project, pipeline_name, "objs_summary.yaml")
    with open(objs_yaml_path, "w") as outfile:
        yaml.dump(reported_objects, outfile)
    _LOGGER.info(
        f"'{pipeline_name}' pipeline objects summary "
        f"(n={len(reported_objects.keys())}): {objs_yaml_path}"
    )
    counter.reset()
    return reported_objects


class ReportOld(Executor):
    """Combine project outputs into a browsable HTML report"""

    def __init__(self, prj):
        # call the inherited initialization
        super(ReportOld, self).__init__(prj)
        self.prj = prj

    def __call__(self, args):
        # initialize the report builder
        report_builder = HTMLReportBuilderOld(self.prj)

        # Do the stats and object summarization.
        table = TableOld(self.prj)()
        # run the report builder. a set of HTML pages is produced
        report_path = report_builder(table.objs, table.stats, uniqify(table.columns))

        _LOGGER.info("HTML Report (n=" + str(len(table.stats)) + "): " + report_path)


class TableOld(Executor):
    """Project/Sample statistics and table output generator"""

    def __init__(self, prj):
        # call the inherited initialization
        super(TableOld, self).__init__(prj)
        self.prj = prj

    def __call__(self):
        def _create_stats_summary_old(project, counter):
            """
            Create stats spreadsheet and columns to be considered in the report, save
            the spreadsheet to file
            :param looper.Project project: the project to be summarized
            :param looper.LooperCounter counter: a counter object
            """
            # Create stats_summary file
            columns = []
            stats = []
            project_samples = project.samples
            missing_files = []
            _LOGGER.info("Creating stats summary...")
            for sample in project_samples:
                # _LOGGER.info(counter.show(sample.sample_name, sample.protocol))
                sample_output_folder = sample_folder(project, sample)
                # Grab the basic info from the annotation sheet for this sample.
                # This will correspond to a row in the output.
                sample_stats = sample.get_sheet_dict()
                columns.extend(sample_stats.keys())
                # Version 0.3 standardized all stats into a single file
                stats_file = os.path.join(sample_output_folder, "stats.tsv")
                if not os.path.isfile(stats_file):
                    missing_files.append(stats_file)
                    continue
                t = _pd.read_csv(
                    stats_file, sep="\t", header=None, names=["key", "value", "pl"]
                )
                t.drop_duplicates(subset=["key", "pl"], keep="last", inplace=True)
                t.loc[:, "plkey"] = t["pl"] + ":" + t["key"]
                dupes = t.duplicated(subset=["key"], keep=False)
                t.loc[dupes, "key"] = t.loc[dupes, "plkey"]
                sample_stats.update(t.set_index("key")["value"].to_dict())
                stats.append(sample_stats)
                columns.extend(t.key.tolist())
            if missing_files:
                _LOGGER.warning(
                    "Stats files missing for {} samples: {}".format(
                        len(missing_files), missing_files
                    )
                )
            tsv_outfile_path = get_file_for_project_old(project, "stats_summary.tsv")
            tsv_outfile = open(tsv_outfile_path, "w")
            tsv_writer = csv.DictWriter(
                tsv_outfile,
                fieldnames=uniqify(columns),
                delimiter="\t",
                extrasaction="ignore",
            )
            tsv_writer.writeheader()
            for row in stats:
                tsv_writer.writerow(row)
            tsv_outfile.close()
            _LOGGER.info(
                "Statistics summary (n=" + str(len(stats)) + "): " + tsv_outfile_path
            )
            counter.reset()
            return stats, uniqify(columns)

        def _create_obj_summary_old(project, counter):
            """
            Read sample specific objects files and save to a data frame
            :param looper.Project project: the project to be summarized
            :param looper.LooperCounter counter: a counter object
            :return pandas.DataFrame: objects spreadsheet
            """
            _LOGGER.info("Creating objects summary...")
            objs = _pd.DataFrame()
            # Create objects summary file
            missing_files = []
            for sample in project.samples:
                # Process any reported objects
                # _LOGGER.info(counter.show(sample.sample_name, sample.protocol))
                sample_output_folder = sample_folder(project, sample)
                objs_file = os.path.join(sample_output_folder, "objects.tsv")
                if not os.path.isfile(objs_file):
                    missing_files.append(objs_file)
                    continue
                t = _pd.read_csv(
                    objs_file,
                    sep="\t",
                    header=None,
                    names=[
                        "key",
                        "filename",
                        "anchor_text",
                        "anchor_image",
                        "annotation",
                    ],
                )
                t["sample_name"] = sample.sample_name
                objs = objs.append(t, ignore_index=True)
            if missing_files:
                _LOGGER.warning(
                    "Object files missing for {} samples: {}".format(
                        len(missing_files), missing_files
                    )
                )
            # create the path to save the objects file in
            objs_file = get_file_for_project_old(project, "objs_summary.tsv")
            objs.to_csv(objs_file, sep="\t")
            _LOGGER.info(
                "Objects summary (n="
                + str(len(project.samples) - len(missing_files))
                + "): "
                + objs_file
            )
            return objs

        # pull together all the fits and stats from each sample into
        # project-combined spreadsheets.
        self.stats, self.columns = _create_stats_summary_old(self.prj, self.counter)
        self.objs = _create_obj_summary_old(self.prj, self.counter)
        return self


def _create_failure_message(reason, samples):
    """Explain lack of submission for a single reason, 1 or more samples."""
    return f"{Fore.LIGHTRED_EX + reason + Style.RESET_ALL}: {', '.join(samples)}"


def _remove_or_dry_run(paths, dry_run=False):
    """
    Remove file or directory or just inform what would be removed in
    case of dry run

    :param list|str paths: list of paths to files/dirs to be removed
    :param bool dry_run: logical indicating whether the files should remain
        untouched and massage printed
    """
    paths = paths if isinstance(paths, list) else [paths]
    for path in paths:
        if os.path.exists(path):
            if dry_run:
                _LOGGER.info("DRY RUN. I would have removed: " + path)
            else:
                _LOGGER.info("Removing: " + path)
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    rmtree(path, ignore_errors=True)
        else:
            _LOGGER.info(path + " does not exist.")


def destroy_summary(prj, dry_run=False):
    """
    Delete the summary files if not in dry run mode
    """
    # TODO: update after get_file_for_project signature change
    _remove_or_dry_run(
        [
            get_file_for_project(prj, "summary.html"),
            get_file_for_project(prj, "stats_summary.tsv"),
            get_file_for_project(prj, "objs_summary.tsv"),
            get_file_for_project(prj, "reports"),
        ],
        dry_run,
    )


class LooperCounter(object):
    """
    Count samples as you loop through them, and create text for the
    subcommand logging status messages.

    :param int total: number of jobs to process
    """

    def __init__(self, total):
        self.count = 0
        self.total = total

    def show(self, name, type="sample", pipeline_name=None):
        """
        Display sample counts status for a particular protocol type.

        The counts are running vs. total for the protocol within the Project,
        and as a side-effect of the call, the running count is incremented.

        :param str name: name of the sample
        :param str type: the name of the level of entity being displayed,
            either project or sample
        :param str pipeline_name: name of the pipeline
        :return str: message suitable for logging a status update
        """
        self.count += 1
        return _submission_status_text(
            type=type,
            curr=self.count,
            total=self.total,
            name=name,
            pipeline_name=pipeline_name,
            color=Fore.CYAN,
        )

    def reset(self):
        self.count = 0

    def __str__(self):
        return "LooperCounter of size {}".format(self.total)


def _submission_status_text(
    curr, total, name, pipeline_name=None, type="sample", color=Fore.CYAN
):
    """Generate submission sample text for run or collate"""
    txt = color + f"## [{curr} of {total}] {type}: {name}"
    if pipeline_name:
        txt += f"; pipeline: {pipeline_name}"
    return txt + Style.RESET_ALL


def _proc_resources_spec(args):
    """
    Process CLI-sources compute setting specification. There are two sources
    of compute settings in the CLI alone:
        * YAML file (--settings argument)
        * itemized compute settings (--compute argument)

    The itemized compute specification is given priority

    :param argparse.Namespace: arguments namespace
    :return Mapping[str, str]: binding between resource setting name and value
    :raise ValueError: if interpretation of the given specification as encoding
        of key-value pairs fails
    """
    spec = getattr(args, "compute", None)
    try:
        settings_data = read_yaml_file(args.settings) or {}
    except yaml.YAMLError:
        _LOGGER.warning(
            "Settings file ({}) does not follow YAML format,"
            " disregarding".format(args.settings)
        )
        settings_data = {}
    if not spec:
        return settings_data
    pairs = [(kv, kv.split("=")) for kv in spec]
    bads = []
    for orig, pair in pairs:
        try:
            k, v = pair
        except ValueError:
            bads.append(orig)
        else:
            settings_data[k] = v
    if bads:
        raise ValueError(
            "Could not correctly parse itemized compute specification. "
            "Correct format: " + EXAMPLE_COMPUTE_SPEC_FMT
        )
    return settings_data


def main(test_args=None):
    """Primary workflow"""
    global _LOGGER

    parser, aux_parser = build_parser()
    aux_parser.suppress_defaults()

    if test_args:
        args, remaining_args = parser.parse_known_args(args=test_args)
    else:
        args, remaining_args = parser.parse_known_args()

    cli_use_errors = validate_post_parse(args)
    if cli_use_errors:
        parser.print_help(sys.stderr)
        parser.error(
            f"{len(cli_use_errors)} CLI use problem(s): {', '.join(cli_use_errors)}"
        )
    if args.command is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if args.command == "init":
        return int(
            not init_dotfile(
                dotfile_path(),
                args.config_file,
                args.output_dir,
                args.sample_pipeline_interfaces,
                args.project_pipeline_interfaces,
                args.force,
            )
        )

    if args.command == "init-piface":
        sys.exit(int(not init_generic_pipeline()))

    _LOGGER = logmuse.logger_via_cli(args, make_root=True)
    _LOGGER.info("Looper version: {}\nCommand: {}".format(__version__, args.command))

    if "config_file" in vars(args):
        if args.config_file is None:
            looper_cfg_path = os.path.relpath(dotfile_path(), start=os.curdir)
            try:
                if args.looper_config:
                    looper_config_dict = read_looper_config_file(args.looper_config)
                else:
                    looper_config_dict = read_looper_dotfile()
                    _LOGGER.info(f"Using looper config ({looper_cfg_path}).")

                for looper_config_key, looper_config_item in looper_config_dict.items():
                    setattr(args, looper_config_key, looper_config_item)

            except OSError:
                parser.print_help(sys.stderr)
                _LOGGER.warning(
                    f"Looper config file does not exist. Use looper init to create one at {looper_cfg_path}."
                )
                sys.exit(1)
        else:
            _LOGGER.warning(
                "This PEP configures looper through the project config. This approach is deprecated and will "
                "be removed in future versions. Please use a looper config file. For more information see "
                "looper.databio.org/en/latest/looper-config"
            )

    args = enrich_args_via_cfg(args, aux_parser, test_args)

    # If project pipeline interface defined in the cli, change name to: "pipeline_interface"
    if vars(args)[PROJECT_PL_ARG]:
        args.pipeline_interfaces = vars(args)[PROJECT_PL_ARG]

    if len(remaining_args) > 0:
        _LOGGER.warning(
            "Unrecognized arguments: {}".format(
                " ".join([str(x) for x in remaining_args])
            )
        )

    divcfg = (
        select_divvy_config(filepath=args.divvy) if hasattr(args, "divvy") else None
    )

    # Initialize project
    if is_registry_path(args.config_file):
        if vars(args)[SAMPLE_PL_ARG]:
            p = Project(
                amendments=args.amend,
                divcfg_path=divcfg,
                runp=args.command == "runp",
                project_dict=PEPHubClient()._load_raw_pep(
                    registry_path=args.config_file
                ),
                **{
                    attr: getattr(args, attr) for attr in CLI_PROJ_ATTRS if attr in args
                },
            )
        else:
            raise MisconfigurationException(
                f"`sample_pipeline_interface` is missing. Provide it in the parameters."
            )
    else:
        try:
            p = Project(
                cfg=args.config_file,
                amendments=args.amend,
                divcfg_path=divcfg,
                runp=args.command == "runp",
                **{
                    attr: getattr(args, attr) for attr in CLI_PROJ_ATTRS if attr in args
                },
            )
        except yaml.parser.ParserError as e:
            _LOGGER.error(f"Project config parse failed -- {e}")
            sys.exit(1)

    selected_compute_pkg = p.selected_compute_package or DEFAULT_COMPUTE_RESOURCES_NAME
    if p.dcc is not None and not p.dcc.activate_package(selected_compute_pkg):
        _LOGGER.info(
            "Failed to activate '{}' computing package. "
            "Using the default one".format(selected_compute_pkg)
        )

    with ProjectContext(
        prj=p,
        selector_attribute=args.sel_attr,
        selector_include=args.sel_incl,
        selector_exclude=args.sel_excl,
    ) as prj:
        if args.command in ["run", "rerun"]:
            run = Runner(prj)
            try:
                compute_kwargs = _proc_resources_spec(args)
                return run(args, rerun=(args.command == "rerun"), **compute_kwargs)
            except SampleFailedException:
                sys.exit(1)
            except IOError:
                _LOGGER.error(
                    "{} pipeline_interfaces: '{}'".format(
                        prj.__class__.__name__, prj.pipeline_interface_sources
                    )
                )
                raise

        if args.command == "runp":
            compute_kwargs = _proc_resources_spec(args)
            collate = Collator(prj)
            collate(args, **compute_kwargs)
            return collate.debug

        if args.command == "destroy":
            return Destroyer(prj)(args)

        # pipestat support introduces breaking changes and pipelines run
        # with no pipestat reporting would not be compatible with
        # commands: table, report and check. Therefore we plan maintain
        # the old implementations for a couple of releases.
        if hasattr(args, "project"):
            use_pipestat = (
                prj.pipestat_configured_project
                if args.project
                else prj.pipestat_configured
            )
        if args.command == "table":
            if use_pipestat:
                Tabulator(prj)(args)
            else:
                TableOld(prj)()

        if args.command == "report":
            if use_pipestat:
                Reporter(prj)(args)
            else:
                ReportOld(prj)(args)

        if args.command == "check":
            if use_pipestat:
                Checker(prj)(args)
            else:
                CheckerOld(prj)(flags=args.flags)

        if args.command == "clean":
            return Cleaner(prj)(args)

        if args.command == "inspect":
            inspect_project(p, args.sample_names, args.attr_limit)
            from warnings import warn

            warn(
                "The inspect feature has moved to eido and will be removed in the future release of looper. "
                "Use `eido inspect` from now on.",
            )
