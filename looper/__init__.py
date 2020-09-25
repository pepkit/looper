"""Project configuration, particularly for logging.

Project-scope constants may reside here, but more importantly, some setup here
will provide a logging infrastructure for all of the project's modules.
Individual modules and classes may provide separate configuration on a more
local level, but this will at least provide a foundation.

"""

import argparse
import os
import logging
from .conductor import SubmissionConductor
from .pipeline_interface import PipelineInterface
from .project import Project
from ._version import __version__
from .parser_types import *
from .const import *

from .conductor import write_sample_yaml_cwl, write_sample_yaml, \
    write_sample_yaml_prj, write_submission_yaml

from ubiquerg import VersionInHelpParser
from divvy import DEFAULT_COMPUTE_RESOURCES_NAME, NEW_COMPUTE_KEY as COMPUTE_KEY
# Not used here, but make this the main import interface between peppy and
# looper, so that other modules within this package need not worry about
# the locations of some of the peppy declarations. Effectively, concentrate
# the connection between peppy and looper here, to the extent possible.

__all__ = ["Project", "PipelineInterface", "SubmissionConductor"]

# Descending by severity for correspondence with logic inversion.
# That is, greater verbosity setting corresponds to lower logging level.
_LEVEL_BY_VERBOSITY = [logging.ERROR, logging.CRITICAL, logging.WARN,
                       logging.INFO, logging.DEBUG]


class _StoreBoolActionType(argparse.Action):
    """
    Enables the storage of a boolean const and custom type definition needed
    for systematic html interface generation. To get the _StoreTrueAction
    output use default=False in the add_argument function
    and default=True to get _StoreFalseAction output.
    """
    def __init__(self, option_strings, dest, type, default,
                 required=False, help=None):
        super(_StoreBoolActionType, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            const=not default,
            default=default,
            type=type,
            required=required,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, self.const)

        
def build_parser():
    """
    Building argument parser.

    :return argparse.ArgumentParser
    """
    # Main looper program help text messages
    banner = "%(prog)s - A project job submission engine and project manager."
    additional_description = "For subcommand-specific options, " \
                             "type: '%(prog)s <subcommand> -h'"
    additional_description += "\nhttps://github.com/pepkit/looper"

    parser = VersionInHelpParser(
        prog="looper", description=banner, epilog=additional_description,
        version=__version__)

    aux_parser = VersionInHelpParser(
        prog="looper", description=banner, epilog=additional_description,
        version=__version__)
    result = []
    for parser in [parser, aux_parser]:
        # Logging control
        parser.add_argument(
                "--logfile", help="Optional output file for looper logs "
                                  "(default: %(default)s)")
        parser.add_argument(
                "--verbosity", type=int, choices=range(len(_LEVEL_BY_VERBOSITY)),
                help="Choose level of verbosity (default: %(default)s)")
        parser.add_argument(
                "--logging-level", help=argparse.SUPPRESS)
        parser.add_argument(
                "--dbg", action="store_true",
                help="Turn on debug mode (default: %(default)s)")
        # Individual subcommands
        msg_by_cmd = {
                "run": "Run or submit sample jobs.",
                "rerun": "Resubmit sample jobs with failed flags.",
                "runp": "Run or submit project jobs.",
                "table": "Write summary stats table for project samples.",
                "report": "Create browsable HTML report of project results.",
                "destroy": "Remove output files of the project.",
                "check": "Check flag status of current runs.",
                "clean": "Run clean scripts of already processed jobs.",
                "inspect": "Print information about a project.",
                "init": "Initialize looper dotfile."
        }

        subparsers = parser.add_subparsers(dest="command")

        def add_subparser(cmd):
            message = msg_by_cmd[cmd]
            return subparsers.add_parser(cmd, description=message, help=message,
                formatter_class=lambda prog: argparse.HelpFormatter(
                    prog, max_help_position=37, width=90))

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
                    "-i", "--ignore-flags", default=False,
                    action=_StoreBoolActionType, type=html_checkbox(checked=False),
                    help="Ignore run status flags? Default=False")

        for subparser in [run_subparser, rerun_subparser, destroy_subparser,
                          clean_subparser, collate_subparser]:
            subparser.add_argument(
                    "-d", "--dry-run",
                    action=_StoreBoolActionType, default=False,
                    type=html_checkbox(checked=False),
                    help="Don't actually submit the jobs.  Default=False")

        # Parameter arguments
        ####################################################################
        for subparser in [run_subparser, rerun_subparser, collate_subparser]:
            subparser.add_argument(
                    "-t", "--time-delay", metavar="S",
                    type=html_range(min_val=0, max_val=30, value=0), default=0,
                    help="Time delay in seconds between job submissions")
            subparser.add_argument(
                    "-l", "--limit", default=None, metavar="N",
                    type=html_range(min_val=1, max_val="num_samples",
                                    value="num_samples"),
                    help="Limit to n samples")
            subparser.add_argument(
                    "-x", "--command-extra", default="",
                    metavar="S", help="String to append to every command")
            subparser.add_argument(
                    "-y", "--command-extra-override", metavar="S", default="",
                    help="Same as command-extra, but overrides values in PEP")
            subparser.add_argument(
                    "-f", "--skip-file-checks",
                    action=_StoreBoolActionType, default=False,
                    type=html_checkbox(checked=False),
                    help="Do not perform input file checks")

            divvy_group = \
                subparser.add_argument_group(
                    "divvy arguments",
                    "Configure divvy to change computing settings")
            divvy_group.add_argument(
                "--divvy", default=None, metavar="DIVCFG",
                help="Path to divvy configuration file. Default=$DIVCFG env "
                     "variable. Currently: {}".format(os.getenv('DIVCFG', None)
                                                      or "not set"))
            divvy_group.add_argument(
                    "-p", "--package", metavar="P",
                    help="Name of computing resource package to use")
            divvy_group.add_argument(
                    "-s", "--settings", default="", metavar="S",
                    help="Path to a YAML settings file with compute settings")
            divvy_group.add_argument(
                    "-c", "--compute", metavar="K", nargs="+",
                    help="List of key-value pairs (k1=v1)")

        for subparser in [run_subparser, rerun_subparser]:
            subparser.add_argument(
                    "-u", "--lump", default=None, metavar="X",
                    type=html_range(min_val=0, max_val=100, step=0.1, value=0),
                    help="Total input file size (GB) to batch into one job")
            subparser.add_argument(
                    "-n", "--lumpn", default=None, metavar="N",
                    type=html_range(min_val=1, max_val="num_samples", value=1),
                    help="Number of commands to batch into one job")

        inspect_subparser.add_argument(
            "-n", "--snames", required=False, nargs="+", metavar="S",
            help="Name of the samples to inspect")
        inspect_subparser.add_argument(
            "-l", "--attr-limit", required=False, type=int, default=10,
            metavar="L", help="Number of sample attributes to display")

        check_subparser.add_argument(
                "-A", "--all-folders", action=_StoreBoolActionType,
                default=False, type=html_checkbox(checked=False),
                help="Check status for all  output folders, not just for "
                     "samples specified in the config. Default=False")
        check_subparser.add_argument(
                "-f", "--flags", nargs='*', default=FLAGS,
                type=html_select(choices=FLAGS), metavar="F",
                help="Check on only these flags/status values")

        for subparser in [destroy_subparser, clean_subparser]:
            subparser.add_argument(
                    "--force-yes", action=_StoreBoolActionType, default=False,
                    type=html_checkbox(checked=False),
                    help="Provide upfront confirmation of destruction intent, "
                         "to skip console query.  Default=False")

        init_subparser.add_argument("config_file", help="Project configuration "
                                                        "file (YAML)")

        init_subparser.add_argument("-f", "--force", help="Force overwrite",
            action="store_true", default=False)

        # Common arguments
        for subparser in [run_subparser, rerun_subparser, table_subparser,
                          report_subparser, destroy_subparser, check_subparser,
                          clean_subparser, collate_subparser, inspect_subparser]:
            subparser.add_argument("config_file", nargs="?", default=None,
                                   help="Project configuration file (YAML)")
            # help="Path to the output directory"
            subparser.add_argument("-o", "--output-dir", metavar="DIR",
                                   help=argparse.SUPPRESS)
            # "Submission subdirectory name"
            subparser.add_argument("--submission-subdir", metavar="DIR",
                                   help=argparse.SUPPRESS)
            # "Results subdirectory name"
            subparser.add_argument("--results-subdir", metavar="DIR",
                                   help=argparse.SUPPRESS)
            # "Sample attribute for pipeline interface sources"
            subparser.add_argument("--pipeline-interfaces-key", metavar="K",
                                   help=argparse.SUPPRESS)
            # "Paths to pipeline interface files"
            subparser.add_argument("--pipeline-interfaces", metavar="P",
                                   nargs="+", action="append",
                                   help=argparse.SUPPRESS)

        for subparser in [run_subparser, rerun_subparser, table_subparser,
                          report_subparser, destroy_subparser, check_subparser,
                          clean_subparser, collate_subparser, inspect_subparser]:
            fetch_samples_group = \
                subparser.add_argument_group(
                    "sample selection arguments",
                    "Specify samples to include or exclude based on sample attribute values")
            fetch_samples_group.add_argument(
                "-g", "--toggle-key", metavar="K",
                help="Sample attribute specifying toggle. Default: toggle")
            fetch_samples_group.add_argument(
                "--sel-attr", default="toggle", metavar="ATTR",
                help="Attribute for sample exclusion OR inclusion")
            protocols = fetch_samples_group.add_mutually_exclusive_group()
            protocols.add_argument(
                    "--sel-excl", nargs='*', metavar="E",
                    help="Exclude samples with these values")
            protocols.add_argument(
                    "--sel-incl", nargs='*', metavar="I",
                    help="Include only samples with these values")
            subparser.add_argument(
                    "-a", "--amend", nargs="+", metavar="A",
                    help="List of amendments to activate")
        result.append(parser)
    return result
