#!/usr/bin/env python
"""
Looper: a pipeline submission engine. https://github.com/pepkit/looper
"""

import abc
import argparse
import csv
import glob
import logging
import subprocess
import yaml
import os
import pandas as _pd

# Need specific sequence of actions for colorama imports?
from colorama import init

from .const import PipelineLevel

init()
from shutil import rmtree

# from collections.abc import Mapping
from collections import defaultdict
from colorama import Fore, Style
from eido import validate_config, validate_sample
from eido.exceptions import EidoValidationError
from jsonschema import ValidationError
from peppy.const import *
from peppy.exceptions import RemoteYAMLError
from rich.color import Color
from rich.console import Console
from rich.table import Table
from ubiquerg.cli_tools import query_yes_no


from .conductor import SubmissionConductor

from .exceptions import *
from .const import *
from .project import Project
from .utils import (
    desired_samples_range_skipped,
    desired_samples_range_limited,
    sample_folder,
)
from pipestat.reports import get_file_for_table
from pipestat.exceptions import PipestatSummarizeError

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

        psms = {}
        if getattr(args, "project", None):

            for piface in self.prj.project_pipeline_interfaces:
                if piface.psm.pipeline_type == PipelineLevel.PROJECT.value:
                    if piface.psm.pipeline_name not in psms:
                        psms[piface.psm.pipeline_name] = piface.psm
            for pl_name, psm in psms.items():
                all_project_level_records = psm.select_records()
                for record in all_project_level_records["records"]:
                    s = piface.psm.get_status(
                        record_identifier=record["record_identifier"]
                    )
                    status.setdefault(piface.psm.pipeline_name, {})
                    status[piface.psm.pipeline_name][record["record_identifier"]] = s
                    _LOGGER.debug(
                        f"{self.prj.name} ({record['record_identifier']}): {s}"
                    )

        else:
            for sample in self.prj.samples:
                for piface in sample.project.pipeline_interfaces:
                    if piface.psm.pipeline_type == PipelineLevel.SAMPLE.value:
                        psms[piface.psm.pipeline_name] = piface.psm
                        s = piface.psm.get_status(record_identifier=sample.sample_name)
                        status.setdefault(piface.psm.pipeline_name, {})
                        status[piface.psm.pipeline_name][sample.sample_name] = s
                        _LOGGER.debug(
                            f"{sample.sample_name} ({piface.psm.pipeline_name}): {s}"
                        )

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
            for status_id in psms[pipeline_name].status_schema.keys():
                status_list = list(pipeline_status.values())
                if status_id in status_list:
                    status_count = status_list.count(status_id)
                    table.add_row(status_id, f"{status_count}/{len(status_list)}")
            console.print(table)

        if getattr(args, "itemized", None):
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
                            *psms[pipeline_name].status_schema[status_id]["color"]
                        ).name
                    except KeyError:
                        color = "#bcbcbc"
                        status_id = "unknown"
                    table.add_row(name, f"[{color}]{status_id}[/{color}]")
                console.print(table)

        if args.describe_codes:
            # TODO this needs to be redone because it only takes the last psm in the list and gets status code and descriptions
            table = Table(
                show_header=True,
                header_style="bold magenta",
                title=f"Status codes description",
                width=len(psms[pipeline_name].status_schema_source) + 20,
                caption=f"Descriptions source: {psms[pipeline_name].status_schema_source}",
            )
            table.add_column("Status code", justify="center")
            table.add_column("Description", justify="left")
            for status, status_obj in psms[pipeline_name].status_schema.items():
                if "description" in status_obj:
                    desc = status_obj["description"]
                else:
                    desc = ""
                table.add_row(status, desc)
            console.print(table)
        return status


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
        if getattr(args, "dry_run", None):
            _LOGGER.info("Dry run. No files cleaned.")
            return 0
        if not getattr(args, "force_yes", None) and not query_yes_no(
            "Are you sure you want to permanently delete all "
            "intermediate pipeline results for this project?"
        ):
            _LOGGER.info("Clean action aborted by user.")
            return 1
        self.counter.reset()
        return self(args, preview_flag=False)


# NOTE: Adding type hint -> Iterable[Any] gives me  TypeError: 'ABCMeta' object is not subscriptable
def select_samples(prj: Project, args: argparse.Namespace):
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

        use_pipestat = (
            self.prj.pipestat_configured_project
            if getattr(args, "project", None)
            else self.prj.pipestat_configured
        )

        if use_pipestat:
            _LOGGER.info("Removing summary:")
            destroy_summary(
                self.prj,
                dry_run=preview_flag,
                project_level=getattr(args, "project", None),
            )

        _LOGGER.info("Removing results:")
        psms = {}
        for sample in select_samples(prj=self.prj, args=args):
            _LOGGER.info(self.counter.show(sample.sample_name))
            sample_output_folder = sample_folder(self.prj, sample)
            if preview_flag:
                # Preview: Don't actually delete, just show files.
                _LOGGER.info(str(sample_output_folder))
            else:
                if use_pipestat:
                    for piface in sample.project.pipeline_interfaces:
                        if piface.psm.pipeline_type == PipelineLevel.SAMPLE.value:
                            psms[piface.psm.pipeline_name] = piface.psm
                    for pipeline_name, psm in psms.items():
                        psm.backend.remove_record(
                            record_identifier=sample.sample_name, rm_record=True
                        )
                else:
                    _remove_or_dry_run(sample_output_folder, args.dry_run)

        if not preview_flag:
            _LOGGER.info("Destroy complete.")
            return 0

        if getattr(args, "dry_run", None):
            _LOGGER.info("Dry run. No files destroyed.")
            return 0

        if not getattr(args, "force_yes", None) and not query_yes_no(
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
        project_pifaces = self.prj.project_pipeline_interfaces
        if not project_pifaces:
            raise MisconfigurationException(
                "Looper requires a pointer to at least one project pipeline. "
                "Please refer to the documentation on linking project to a "
                "pipeline: "
                "http://looper.databio.org/en/latest/defining-a-project"
            )
        self.counter = LooperCounter(len(project_pifaces))
        for project_piface in project_pifaces:
            _LOGGER.info(
                self.counter.show(
                    name=self.prj.name,
                    type="project",
                    pipeline_name=project_piface.pipeline_name,
                )
            )
            conductor = SubmissionConductor(
                pipeline_interface=project_piface,
                prj=self.prj,
                compute_variables=compute_kwargs,
                delay=getattr(args, "time_delay", None),
                extra_args=getattr(args, "command_extra", None),
                extra_args_override=getattr(args, "command_extra_override", None),
                ignore_flags=getattr(args, "ignore_flags", None),
                collate=True,
            )
            if conductor.is_project_submittable(
                force=getattr(args, "ignore_flags", None)
            ):
                conductor._pool = [None]
                conductor.submit()
                jobs += conductor.num_job_submissions
        _LOGGER.info("\nLooper finished")
        _LOGGER.info("Jobs submitted: {}".format(jobs))
        self.debug[DEBUG_JOBS] = jobs
        return self.debug


class Runner(Executor):
    """The true submitter of pipelines"""

    def __call__(self, args, top_level_args=None, rerun=False, **compute_kwargs):
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
                delay=getattr(args, "time_delay", None),
                extra_args=getattr(args, "command_extra", None),
                extra_args_override=getattr(args, "command_extra_override", None),
                ignore_flags=getattr(args, "ignore_flags", None),
                max_cmds=getattr(args, "lump_n", None),
                max_size=getattr(args, "lump", None),
                max_jobs=getattr(args, "lump_j", None),
            )
            submission_conductors[piface.pipe_iface_file] = conductor

        _LOGGER.debug(f"Pipestat compatible: {self.prj.pipestat_configured}")
        self.debug["Pipestat compatible"] = self.prj.pipestat_configured

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
                    _LOGGER.error(
                        f"Short-circuiting due to validation error!\nSchema file: "
                        f"{schema_file}\nError: {e}\n{list(e.errors_by_type.keys())}"
                    )
                    self.debug[DEBUG_EIDO_VALIDATION] = (
                        f"Short-circuiting due to validation error!\nSchema file: "
                        f"{schema_file}\nError: {e}\n{list(e.errors_by_type.keys())}"
                    )
                    return False
                except RemoteYAMLError:
                    _LOGGER.warning(
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
        _LOGGER.debug("Commands submitted: {} of {}".format(cmd_sub_total, max_cmds))
        self.debug[DEBUG_COMMANDS] = "{} of {}".format(cmd_sub_total, max_cmds)
        if getattr(args, "dry_run", None):
            job_sub_total_if_real = job_sub_total
            job_sub_total = 0
            _LOGGER.info(
                f"Dry run. No jobs were actually submitted, but {job_sub_total_if_real} would have been."
            )
        _LOGGER.debug("Jobs submitted: {}".format(job_sub_total))
        self.debug[DEBUG_JOBS] = job_sub_total

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
        self.debug = {}
        p = self.prj
        project_level = getattr(args, "project", None)

        portable = args.portable

        report_dir = getattr(args, "report_dir", None)

        psms = {}

        if project_level:

            for piface in self.prj.project_pipeline_interfaces:
                if piface.psm.pipeline_type == PipelineLevel.PROJECT.value:
                    if piface.psm.pipeline_name not in psms:
                        psms[piface.psm.pipeline_name] = piface.psm
            for pl_name, psm in psms.items():
                try:
                    report_directory = psm.summarize(
                        looper_samples=self.prj.samples,
                        portable=portable,
                        output_dir=report_dir,
                    )
                except PipestatSummarizeError as e:
                    raise LooperReportError(
                        f"Looper report error due to the following exception: {e}"
                    )
                print(f"Report directory: {report_directory}")
                self.debug["report_directory"] = report_directory
            return self.debug
        else:
            for piface in self.prj.pipeline_interfaces:
                if piface.psm.pipeline_type == PipelineLevel.SAMPLE.value:
                    if piface.psm.pipeline_name not in psms:
                        psms[piface.psm.pipeline_name] = piface.psm
            for pl_name, psm in psms.items():
                try:
                    report_directory = psm.summarize(
                        looper_samples=self.prj.samples,
                        portable=portable,
                        output_dir=report_dir,
                    )
                except PipestatSummarizeError as e:
                    raise LooperReportError(
                        f"Looper report error due to the following exception: {e}"
                    )
                print(f"Report directory: {report_directory}")
                self.debug["report_directory"] = report_directory
            return self.debug


class Linker(Executor):
    """Create symlinks for reported results. Requires pipestat to be configured."""

    def __call__(self, args):
        # initialize the report builder
        p = self.prj
        project_level = getattr(args, "project", None)
        link_dir = getattr(args, "output_dir", None)

        psms = {}

        if project_level:
            for piface in self.prj.project_pipeline_interfaces:
                if piface.psm.pipeline_type == PipelineLevel.PROJECT.value:
                    psms[piface.psm.pipeline_name] = piface.psm
                    linked_results_path = piface.psm.link(link_dir=link_dir)
                    print(f"Linked directory: {linked_results_path}")
        else:
            for piface in self.prj.pipeline_interfaces:
                if piface.psm.pipeline_type == PipelineLevel.SAMPLE.value:
                    psms[piface.psm.pipeline_name] = piface.psm
                    linked_results_path = piface.psm.link(link_dir=link_dir)
                    print(f"Linked directory: {linked_results_path}")


class Tabulator(Executor):
    """Project/Sample statistics and table output generator

    :return list[str|any] results: list containing output file paths of stats and objects
    """

    def __call__(self, args):
        # p = self.prj
        project_level = getattr(args, "project", None)
        report_dir = getattr(args, "report_dir", None)
        results = []
        psms = {}
        if project_level:
            for piface in self.prj.project_pipeline_interfaces:
                if piface.psm.pipeline_type == PipelineLevel.PROJECT.value:
                    if piface.psm.pipeline_name not in psms:
                        psms[piface.psm.pipeline_name] = piface.psm
            for pl_name, psm in psms.items():
                results = psm.table(output_dir=report_dir)
        else:
            for piface in self.prj.pipeline_interfaces:
                if piface.psm.pipeline_type == PipelineLevel.SAMPLE.value:
                    if piface.psm.pipeline_name not in psms:
                        psms[piface.psm.pipeline_name] = piface.psm
            for pl_name, psm in psms.items():
                results = psm.table(output_dir=report_dir)
        # Results contains paths to stats and object summaries.
        return results


def _create_failure_message(reason, samples):
    """Explain lack of submission for a single reason, 1 or more samples."""
    return f"{Fore.LIGHTRED_EX + reason + Style.RESET_ALL}: {', '.join(samples)}"


def _remove_or_dry_run(paths, dry_run=False):
    """
    Remove file or directory or just inform what would be removed in
    case of dry run

    :param list|str paths: list of paths to files/dirs to be removed
    :param bool dry_run: logical indicating whether the files should remain
        untouched and message printed
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


def destroy_summary(prj, dry_run=False, project_level=False):
    """
    Delete the summary files if not in dry run mode
    This function is for use with pipestat configured projects.
    """

    psms = {}
    if project_level:
        for piface in prj.pipeline_interfaces:
            if piface.psm.pipeline_type == PipelineLevel.PROJECT.value:
                psms[piface.psm.pipeline_name] = piface.psm

        for name, psm in psms.items():
            _remove_or_dry_run(
                [
                    get_file_for_table(
                        psm, pipeline_name=psm.pipeline_name, directory="reports"
                    ),
                    get_file_for_table(
                        psm,
                        pipeline_name=psm.pipeline_name,
                        appendix="stats_summary.tsv",
                    ),
                    get_file_for_table(
                        psm,
                        pipeline_name=psm.pipeline_name,
                        appendix="objs_summary.yaml",
                    ),
                    os.path.join(
                        os.path.dirname(psm.config_path), "aggregate_results.yaml"
                    ),
                ],
                dry_run,
            )
    else:
        for piface in prj.pipeline_interfaces:
            if piface.psm.pipeline_type == PipelineLevel.SAMPLE.value:
                psms[piface.psm.pipeline_name] = piface.psm
        for name, psm in psms.items():
            _remove_or_dry_run(
                [
                    get_file_for_table(
                        psm, pipeline_name=psm.pipeline_name, directory="reports"
                    ),
                    get_file_for_table(
                        psm,
                        pipeline_name=psm.pipeline_name,
                        appendix="stats_summary.tsv",
                    ),
                    get_file_for_table(
                        psm,
                        pipeline_name=psm.pipeline_name,
                        appendix="objs_summary.yaml",
                    ),
                    os.path.join(
                        os.path.dirname(psm.config_path), "aggregate_results.yaml"
                    ),
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
