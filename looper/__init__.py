"""Project configuration, particularly for logging.

Project-scope constants may reside here, but more importantly, some setup here
will provide a logging infrastructure for all of the project's modules.
Individual modules and classes may provide separate configuration on a more
local level, but this will at least provide a foundation.

"""

import argparse
import logging
from .conductor import SubmissionConductor
from .pipeline_interface import PipelineInterface
from .project import Project
from ._version import __version__
from .parser_types import *
from .const import *

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

    # Logging control
    parser.add_argument(
            "--logfile", dest="logfile",
            help="Optional output file for looper logs (default: %(default)s)")
    parser.add_argument(
            "--verbosity", dest="verbosity",
            type=int, choices=range(len(_LEVEL_BY_VERBOSITY)),
            help="Choose level of verbosity (default: %(default)s)")
    parser.add_argument(
            "--logging-level", dest="logging_level",
            help=argparse.SUPPRESS)
    parser.add_argument(
            "--dbg", dest="dbg", action="store_true",
            help="Turn on debug mode (default: %(default)s)")
    parser.add_argument(
            "--env", dest="env",
            default=None,
            help="Environment variable that points to the DIVCFG file. "
                 "(default: DIVCFG)")

    # Individual subcommands
    # TODO: "table" & "report" (which calls table by default)
    msg_by_cmd = {
            "run": "Run or submit sample jobs.",
            "rerun": "Resubmit sample jobs with failed flags.",
            "runp": "Run or submit a project job.",
            "table": "Write summary stats table for project samples.",
            "report": "Create browsable HTML report of project results.",
            "destroy": "Remove output files of the project.",
            "check": "Check flag status of current runs.",
            "clean": "Run clean scripts of already processed jobs.",
            "inspect": "Print information about a project.",
            "init": "Initialize looper dotfile.",
            "mod": "Modify looper dotfile."
    }

    subparsers = parser.add_subparsers(dest="command")

    def add_subparser(cmd):
        message = msg_by_cmd[cmd]
        return subparsers.add_parser(cmd, description=message, help=message, formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=28, width=100))

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
    mod_subparser = add_subparser("mod")
    for subparser in [run_subparser, rerun_subparser, collate_subparser,
                      init_subparser, mod_subparser]:
        subparser.add_argument(
                "--ignore-flags", dest="ignore_flags", default=False,
                action=_StoreBoolActionType, type=html_checkbox(checked=False),
                help="Ignore run status flags? Default: False. "
                     "By default, pipelines will not be submitted if a pypiper "
                     "flag file exists marking the run (e.g. as "
                     "'running' or 'failed'). Set this option to ignore flags "
                     "and submit the runs anyway. Default=False")
        subparser.add_argument(
                "-t", "--time-del", dest="time_delay", metavar="S",
                type=html_range(min_val=0, max_val=30, value=0), default=0,
                help="Time delay in seconds between job submissions.")
        subparser.add_argument(
                "-p", "--package", metavar="P",
                help="Divvy: Name of computing resource package to use")
        subparser.add_argument(
                "-s", "--settings", dest="settings", default="", metavar="S",
                help="Divvy: Path to a YAML settings file with compute settings")
        subparser.add_argument(
                "-m", "--compute", metavar="C",
                help="Divvy: Comma-separated list of computing resource "
                     "key-value pairs, e.g., " + EXAMPLE_COMPUTE_SPEC_FMT)
        subparser.add_argument(
                "-l", "--limit", dest="limit", default=None, metavar="N",
                type=html_range(min_val=1, max_val="num_samples",
                                value="num_samples"),
                help="Limit to n samples.")
        subparser.add_argument(
                "-x", "--command-extra", dest="command_extra", default="",
                metavar="S", help="String to append to every command")
        subparser.add_argument(
                "-y", "--command-extra-override", dest="command_extra_override",
                metavar="S", default="",
                help="String to append to every command, "
                     "overriding values in PEP.")
        
    for subparser in [run_subparser, rerun_subparser, init_subparser, mod_subparser]:
        # Note that defaults for otherwise numeric lump parameters are set to
        # null by default so that the logic that parses their values may
        # distinguish between explicit 0 and lack of specification.
        subparser.add_argument(
                "-u", "--lump", default=None, metavar="SIZE",
                type=html_range(min_val=0, max_val=100, step=0.1, value=0),
                help="Total input file size in GB to batch into a single job")
        subparser.add_argument(
                "-n", "--lumpn", default=None, metavar="N",
                type=html_range(min_val=1, max_val="num_samples", value=1),
                help="Number of individual commands to batch into a single job")

    inspect_subparser.add_argument("-n", "--sample-name", required=False,
                                   nargs="+",
                                   help="Name of the samples to inspect.")

    check_subparser.add_argument(
            "-A", "--all-folders", action=_StoreBoolActionType,
            default=False, type=html_checkbox(checked=False),
            help="Check status for all project's output folders, not just "
                 "those for samples specified in the config file used. "
                 "Default=False")
    check_subparser.add_argument(
            "-F", "--flags", nargs='*', default=FLAGS,
            type=html_select(choices=FLAGS),
            help="Check on only these flags/status values.")

    for subparser in [destroy_subparser, clean_subparser, init_subparser, mod_subparser]:
        subparser.add_argument(
                "--force-yes", action=_StoreBoolActionType, default=False,
                type=html_checkbox(checked=False),
                help="Provide upfront confirmation of destruction intent, "
                     "to skip console query.  Default=False")

    # Common arguments
    for subparser in [run_subparser, rerun_subparser, table_subparser,
                      report_subparser, destroy_subparser, check_subparser,
                      clean_subparser, collate_subparser, inspect_subparser,
                      init_subparser, mod_subparser]:
        subparser.add_argument("config_file", nargs="?",
                               help="Project configuration file (YAML).")
        subparser.add_argument(
                "--pipeline-interfaces", dest="pifaces", metavar="P",
                nargs="+", action='append',
                help="Path to a pipeline interface file")
        subparser.add_argument(
                "--file-checks", dest="file_checks",
                action=_StoreBoolActionType, default=True,
                type=html_checkbox(checked=True),
                help="Perform input file checks. Default=True.")
        subparser.add_argument(
                "-d", "--dry-run", dest="dry_run",
                action=_StoreBoolActionType, default=False,
                type=html_checkbox(checked=False),
                help="Don't actually submit the jobs.  Default=False")

        fetch_samples_group = \
            subparser.add_argument_group(
                "select samples",
                "This group of arguments lets you specify samples to use by "
                "exclusion OR inclusion of the samples attribute values.")
        fetch_samples_group.add_argument(
            "--selector-attribute", dest="selector_attribute", default="toggle",
            help="Specify the attribute for samples exclusion OR inclusion")
        protocols = fetch_samples_group.add_mutually_exclusive_group()
        protocols.add_argument(
                "--selector-exclude", nargs='*', dest="selector_exclude",
                help="Operate only on samples that either lack this attribute "
                     "value or for which this value is not in this collection.")
        protocols.add_argument(
                "--selector-include", nargs='*', dest="selector_include",
                help="Operate only on samples associated with these attribute "
                     "values; if not provided, all samples are used.")
        subparser.add_argument(
                "-a", "--amendments", dest="amendments", nargs="+",
                help="List of of amendments to activate")

    return parser
