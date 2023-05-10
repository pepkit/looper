"""Project configuration, particularly for logging.

Project-scope constants may reside here, but more importantly, some setup here
will provide a logging infrastructure for all of the project's modules.
Individual modules and classes may provide separate configuration on a more
local level, but this will at least provide a foundation.

"""

import logmuse

logmuse.init_logger("looper")

import argparse
import logging
import os
from typing import *
from .divvy import ComputingConfiguration, select_divvy_config
from .divvy import DEFAULT_COMPUTE_RESOURCES_NAME
from .divvy import NEW_COMPUTE_KEY as COMPUTE_KEY
from ubiquerg import VersionInHelpParser

from ._version import __version__
from .conductor import (
    SubmissionConductor,
    write_sample_yaml,
    write_sample_yaml_cwl,
    write_sample_yaml_prj,
    write_submission_yaml,
    write_custom_template,
)
from .const import *
from .parser_types import *
from .pipeline_interface import PipelineInterface
from .project import Project

# Not used here, but make this the main import interface between peppy and
# looper, so that other modules within this package need not worry about
# the locations of some of the peppy declarations. Effectively, concentrate
# the connection between peppy and looper here, to the extent possible.

__all__ = [
    "Project",
    "PipelineInterface",
    "SubmissionConductor",
    "ComputingConfiguration",
    "select_divvy_config",
]


SAMPLE_SELECTION_ATTRIBUTE_OPTNAME = "sel-attr"
SAMPLE_EXCLUSION_OPTNAME = "sel-excl"
SAMPLE_INCLUSION_OPTNAME = "sel-incl"


class _StoreBoolActionType(argparse.Action):
    """
    Enables the storage of a boolean const and custom type definition needed
    for systematic html interface generation. To get the _StoreTrueAction
    output use default=False in the add_argument function
    and default=True to get _StoreFalseAction output.
    """

    def __init__(self, option_strings, dest, type, default, required=False, help=None):
        super(_StoreBoolActionType, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            const=not default,
            default=default,
            type=type,
            required=required,
            help=help,
        )

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, self.const)


MESSAGE_BY_SUBCOMMAND = {
    "run": "Run or submit sample jobs.",
    "rerun": "Resubmit sample jobs with failed flags.",
    "runp": "Run or submit project jobs.",
    "table": "Write summary stats table for project samples.",
    "report": "Create browsable HTML report of project results.",
    "destroy": "Remove output files of the project.",
    "check": "Check flag status of current runs.",
    "clean": "Run clean scripts of already processed jobs.",
    "inspect": "Print information about a project.",
    "init": "Initialize looper dotfile.",
}


def build_parser():
    """
    Building argument parser.

    :return argparse.ArgumentParser
    """
    # Main looper program help text messages
    banner = "%(prog)s - A project job submission engine and project manager."
    additional_description = (
        "For subcommand-specific options, " "type: '%(prog)s <subcommand> -h'"
    )
    additional_description += "\nhttps://github.com/pepkit/looper"

    parser = VersionInHelpParser(
        prog="looper",
        description=banner,
        epilog=additional_description,
        version=__version__,
    )

    aux_parser = VersionInHelpParser(
        prog="looper",
        description=banner,
        epilog=additional_description,
        version=__version__,
    )
    result = []
    for parser in [parser, aux_parser]:
        # Logging control
        parser.add_argument(
            "--logfile",
            help="Optional output file for looper logs " "(default: %(default)s)",
        )
        parser.add_argument("--logging-level", help=argparse.SUPPRESS)
        parser.add_argument(
            "--dbg",
            action="store_true",
            help="Turn on debug mode (default: %(default)s)",
        )

        parser = logmuse.add_logging_options(parser)
        subparsers = parser.add_subparsers(dest="command")

        def add_subparser(cmd):
            message = MESSAGE_BY_SUBCOMMAND[cmd]
            return subparsers.add_parser(
                cmd,
                description=message,
                help=message,
                formatter_class=lambda prog: argparse.HelpFormatter(
                    prog, max_help_position=37, width=90
                ),
            )

        # Run and rerun command
        run_subparser = add_subparser("run")
        rerun_subparser = add_subparser("rerun")
        collate_subparser = add_subparser("runp")
        table_subparser = add_subparser("table")
        report_subparser = add_subparser("report")
        destroy_subparser = add_subparser("destroy")
        check_subparser = add_subparser("check")
        clean_subparser = add_subparser("clean")
        inspect_subparser = add_subparser("inspect")
        init_subparser = add_subparser("init")

        # Flag arguments
        ####################################################################
        for subparser in [run_subparser, rerun_subparser, collate_subparser]:
            subparser.add_argument(
                "-i",
                "--ignore-flags",
                default=False,
                action=_StoreBoolActionType,
                type=html_checkbox(checked=False),
                help="Ignore run status flags? Default=False",
            )

        for subparser in [
            run_subparser,
            rerun_subparser,
            destroy_subparser,
            clean_subparser,
            collate_subparser,
        ]:
            subparser.add_argument(
                "-d",
                "--dry-run",
                action=_StoreBoolActionType,
                default=False,
                type=html_checkbox(checked=False),
                help="Don't actually submit the jobs.  Default=False",
            )

        # Parameter arguments
        ####################################################################
        for subparser in [run_subparser, rerun_subparser, collate_subparser]:
            subparser.add_argument(
                "-t",
                "--time-delay",
                metavar="S",
                type=html_range(min_val=0, max_val=30, value=0),
                default=0,
                help="Time delay in seconds between job submissions",
            )

            subparser.add_argument(
                "-x",
                "--command-extra",
                default="",
                metavar="S",
                help="String to append to every command",
            )
            subparser.add_argument(
                "-y",
                "--command-extra-override",
                metavar="S",
                default="",
                help="Same as command-extra, but overrides values in PEP",
            )
            subparser.add_argument(
                "-f",
                "--skip-file-checks",
                action=_StoreBoolActionType,
                default=False,
                type=html_checkbox(checked=False),
                help="Do not perform input file checks",
            )

            divvy_group = subparser.add_argument_group(
                "divvy arguments", "Configure divvy to change computing settings"
            )
            divvy_group.add_argument(
                "--divvy",
                default=None,
                metavar="DIVCFG",
                help="Path to divvy configuration file. Default=$DIVCFG env "
                "variable. Currently: {}".format(
                    os.getenv("DIVCFG", None) or "not set"
                ),
            )
            divvy_group.add_argument(
                "-p",
                "--package",
                metavar="P",
                help="Name of computing resource package to use",
            )
            divvy_group.add_argument(
                "-s",
                "--settings",
                default="",
                metavar="S",
                help="Path to a YAML settings file with compute settings",
            )
            divvy_group.add_argument(
                "-c",
                "--compute",
                metavar="K",
                nargs="+",
                help="List of key-value pairs (k1=v1)",
            )

        for subparser in [run_subparser, rerun_subparser]:
            subparser.add_argument(
                "-u",
                "--lump",
                default=None,
                metavar="X",
                type=html_range(min_val=0, max_val=100, step=0.1, value=0),
                help="Total input file size (GB) to batch into one job",
            )
            subparser.add_argument(
                "-n",
                "--lumpn",
                default=None,
                metavar="N",
                type=html_range(min_val=1, max_val="num_samples", value=1),
                help="Number of commands to batch into one job",
            )

        check_subparser.add_argument(
            "--describe-codes",
            help="Show status codes description",
            action="store_true",
            default=False,
        )

        check_subparser.add_argument(
            "--itemized",
            help="Show a detailed, by sample statuses",
            action="store_true",
            default=False,
        )

        check_subparser.add_argument(
            "-f",
            "--flags",
            nargs="*",
            default=FLAGS,
            type=html_select(choices=FLAGS),
            metavar="F",
            help="Check on only these flags/status values",
        )

        for subparser in [destroy_subparser, clean_subparser]:
            subparser.add_argument(
                "--force-yes",
                action=_StoreBoolActionType,
                default=False,
                type=html_checkbox(checked=False),
                help="Provide upfront confirmation of destruction intent, "
                "to skip console query.  Default=False",
            )

        init_subparser.add_argument(
            "config_file", help="Project configuration " "file (YAML)"
        )

        init_subparser.add_argument(
            "-f", "--force", help="Force overwrite", action="store_true", default=False
        )

        init_subparser.add_argument(
            "-p",
            "--piface",
            help="Generates generic pipeline interface",
            action="store_true",
            default=False,
        )

        # Common arguments
        for subparser in [
            run_subparser,
            rerun_subparser,
            table_subparser,
            report_subparser,
            destroy_subparser,
            check_subparser,
            clean_subparser,
            collate_subparser,
            inspect_subparser,
        ]:
            subparser.add_argument(
                "config_file",
                nargs="?",
                default=None,
                help="Project configuration file (YAML)",
            )
            # help="Path to the output directory"
            subparser.add_argument(
                "-o", "--output-dir", metavar="DIR", help=argparse.SUPPRESS
            )
            # "Submission subdirectory name"
            subparser.add_argument(
                "--submission-subdir", metavar="DIR", help=argparse.SUPPRESS
            )
            # "Results subdirectory name"
            subparser.add_argument(
                "--results-subdir", metavar="DIR", help=argparse.SUPPRESS
            )
            # "Sample attribute for pipeline interface sources"
            subparser.add_argument(
                "--pipeline-interfaces-key", metavar="K", help=argparse.SUPPRESS
            )
            # "Paths to pipeline interface files"
            subparser.add_argument(
                "--pipeline-interfaces",
                metavar="P",
                nargs="+",
                action="append",
                help=argparse.SUPPRESS,
            )

        for subparser in [
            run_subparser,
            rerun_subparser,
            table_subparser,
            report_subparser,
            destroy_subparser,
            check_subparser,
            clean_subparser,
            collate_subparser,
            inspect_subparser,
        ]:
            fetch_samples_group = subparser.add_argument_group(
                "sample selection arguments",
                "Specify samples to include or exclude based on sample attribute values",
            )
            fetch_samples_group.add_argument(
                "-l",
                "--limit",
                default=None,
                metavar="N",
                type=html_range(min_val=1, max_val="num_samples", value="num_samples"),
                help="Limit to n samples",
            )
            fetch_samples_group.add_argument(
                "-k",
                "--skip",
                default=None,
                metavar="N",
                type=html_range(min_val=1, max_val="num_samples", value="num_samples"),
                help="Skip samples by numerical index",
            )

            fetch_samples_group.add_argument(
                f"--{SAMPLE_SELECTION_ATTRIBUTE_OPTNAME}",
                default="toggle",
                metavar="ATTR",
                help="Attribute for sample exclusion OR inclusion",
            )
            protocols = fetch_samples_group.add_mutually_exclusive_group()
            protocols.add_argument(
                f"--{SAMPLE_EXCLUSION_OPTNAME}",
                nargs="*",
                metavar="E",
                help="Exclude samples with these values",
            )
            protocols.add_argument(
                f"--{SAMPLE_INCLUSION_OPTNAME}",
                nargs="*",
                metavar="I",
                help="Include only samples with these values",
            )
            subparser.add_argument(
                "-a",
                "--amend",
                nargs="+",
                metavar="A",
                help="List of amendments to activate",
            )
        for subparser in [report_subparser, table_subparser, check_subparser]:
            subparser.add_argument(
                "--project",
                help="Process project-level pipelines",
                action="store_true",
                default=False,
            )
        inspect_subparser.add_argument(
            "--sample-names",
            help="Names of the samples to inspect",
            nargs="*",
            default=None,
        )

        inspect_subparser.add_argument(
            "--attr-limit",
            help="Number of attributes to display",
            type=int,
        )
        result.append(parser)
    return result


def opt_attr_pair(name: str) -> Tuple[str, str]:
    return f"--{name}", name.replace("-", "_")


def validate_post_parse(args: argparse.Namespace) -> List[str]:
    problems = []
    used_exclusives = [
        opt
        for opt, attr in map(
            opt_attr_pair,
            [
                "skip",
                "limit",
                SAMPLE_EXCLUSION_OPTNAME,
                SAMPLE_INCLUSION_OPTNAME,
            ],
        )
        if getattr(args, attr, None)
    ]
    if len(used_exclusives) > 1:
        problems.append(
            f"Used multiple mutually exclusive options: {', '.join(used_exclusives)}"
        )
    return problems
