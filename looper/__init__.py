"""Project configuration, particularly for logging.

Project-scope constants may reside here, but more importantly, some setup here
will provide a logging infrastructure for all of the project's modules.
Individual modules and classes may provide separate configuration on a more
local level, but this will at least provide a foundation.

"""

import argparse
import logging
import os
from sys import stdout

from .pipeline_interface import PipelineInterface
from ._version import __version__
from .parser_types import *
from functools import partial

# Not used here, but make this the main import interface between peppy and
# looper, so that other modules within this package need not worry about
# the locations of some of the peppy declarations. Effectively, concentrate
# the connection between peppy and looper here, to the extent possible.
from peppy import \
    FLAGS, IMPLICATIONS_DECLARATION, SAMPLE_INDEPENDENT_PROJECT_SECTIONS, \
    SAMPLE_NAME_COLNAME, COMPUTE_SETTINGS_VARNAME

__classes__ = ["PipelineInterface"]


GENERIC_PROTOCOL_KEY = "*"
LOGGING_LEVEL = "INFO"
LOGGING_LOCATIONS = (stdout, )

# Default user logging format is simple
DEFAULT_LOGGING_FMT = "%(message)s"
# Developer logger format is more information-rich
DEV_LOGGING_FMT = "%(module)s:%(lineno)d (%(funcName)s) [%(levelname)s] > %(message)s "

# Descending by severity for correspondence with logic inversion.
# That is, greater verbosity setting corresponds to lower logging level.
_LEVEL_BY_VERBOSITY = [logging.ERROR, logging.CRITICAL, logging.WARN,
                       logging.INFO, logging.DEBUG]


def setup_looper_logger(level, additional_locations=None, devmode=False,
                        formatter_template=None):
    """
    Establish a logger for a looper CLI program.

    This configures a logger to provide information about a looper program's
    execution. Verbosity, destination(s) for messages, and message text
    format are controlled by the arguments' values. This is also used by
    looper's test suite.

    :param int | str level: logging level
    :param tuple(str | FileIO[str]) additional_locations: supplementary
        destination(s) to which to ship logs
    :param bool devmode: whether to use developer logging config
    :param str formatter_template: message template for the logging formatter
    :return logging.Logger: project-root logger
    """

    logging.addLevelName(5, "VERY_FINE")

    fmt = formatter_template or \
        (DEV_LOGGING_FMT if devmode else DEFAULT_LOGGING_FMT)

    # Establish the logger.
    LOOPER_LOGGER = logging.getLogger()
    # First remove any previously-added handlers
    LOOPER_LOGGER.handlers = []
    LOOPER_LOGGER.propagate = False

    # Handle int- or text-specific logging level.
    try:
        level = int(level)
    except ValueError:
        level = level.upper()

    try:
        LOOPER_LOGGER.setLevel(level)
    except Exception:
        logging.error("Can't set logging level to %s; instead using: '%s'",
                      str(level), str(LOGGING_LEVEL))
        level = LOGGING_LEVEL
        LOOPER_LOGGER.setLevel(level)

    # Process any additional locations.
    locations_exception = None
    where = LOGGING_LOCATIONS
    if additional_locations:
        if isinstance(additional_locations, str):
            additional_locations = (additional_locations, )
        try:
            where = LOGGING_LOCATIONS + tuple(additional_locations)
        except TypeError as e:
            locations_exception = e
    if locations_exception:
        logging.warn("Could not interpret {} as supplementary root logger "
                     "target destinations; using {} as root logger location(s)".
                     format(additional_locations, LOGGING_LOCATIONS))

    formatter = logging.Formatter(fmt=fmt)

    # Add the handlers.
    for loc in where:
        if not loc:
            continue
        if isinstance(loc, str):
            # File destination
            dirpath = os.path.abspath(os.path.dirname(loc))
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            handler_type = logging.FileHandler
        elif hasattr(loc, "write"):
            # Stream destination
            handler_type = logging.StreamHandler
        else:
            # Strange supplementary destination
            logging.info("{} as logs destination appears to be neither "
                         "a filepath nor a stream.".format(loc))
            continue

        if handler_type is logging.FileHandler:
            handler = handler_type(loc, mode='w')
        else:
            handler = handler_type(loc)

        handler.setLevel(level)
        handler.setFormatter(formatter)
        LOOPER_LOGGER.addHandler(handler)

    return LOOPER_LOGGER



class _VersionInHelpParser(argparse.ArgumentParser):
    def format_help(self):
        """ Add version information to help text. """
        return "version: {}\n".format(__version__) + \
               super(_VersionInHelpParser, self).format_help()


class _StoreBoolActionType(argparse.Action):
    """
    Enables the storage of a boolean const and custom type definition needed for systematic html interface generation.
    To get the _StoreTrueAction output use default=False in the add_argument function
    and default=True to get _StoreFalseAction output.
    """
    def __init__(self, option_strings, dest, type, default, required=False, help=None):
        super(_StoreBoolActionType, self).__init__(
            option_strings=option_strings,
            dest=dest,
            nargs=0,
            const=not(default),
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
    parser.add_argument(
            "--env", dest="env",
            default=os.getenv(COMPUTE_SETTINGS_VARNAME, ""),
            help="Employ looper environment compute settings.")

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
            type=partial(range, min=0, max=30, value=0), default=0,
            help="Time delay in seconds between job submissions.")
    run_subparser.add_argument(
            "--ignore-flags", dest="ignore_flags", default=False,
            action=_StoreBoolActionType, type=partial(checkbox, checked=False),
            help="Ignore run status flags? Default: False. "
                 "By default, pipelines will not be submitted if a pypiper "
                 "flag file exists marking the run (e.g. as "
                 "'running' or 'failed'). Set this option to ignore flags "
                 "and submit the runs anyway. Default=False")
    run_subparser.add_argument(
            "--allow-duplicate-names", default=False,
            action=_StoreBoolActionType, type=partial(checkbox, checked=False),
            help="Allow duplicate names? Default: False. "
                 "By default, pipelines will not be submitted if a sample name"
                 " is duplicated, since samples names should be unique.  "
                 " Set this option to override this setting. Default=False")
    run_subparser.add_argument(
            "--compute", dest="compute",
            help="YAML file with looper environment compute settings.")
    run_subparser.add_argument(
            "--limit", dest="limit", default=None,
            type=partial(range, min=0, max=10),
            help="Limit to n samples.")
    # Note that defaults for otherwise numeric lump parameters are set to
    # null by default so that the logic that parses their values may
    # distinguish between explicit 0 and lack of specification.
    run_subparser.add_argument(
            "--lump", type=partial(range, min=0, max=100, step=0.1, value=100), default=None,
            help="Maximum total input file size for a lump/batch of commands "
                 "in a single job (in GB)")
    run_subparser.add_argument(
            "--lumpn", type=partial(range, min=0, max=10), default=None,
            help="Number of individual scripts grouped into single submission")

    # Other commands
    summarize_subparser = add_subparser("summarize")
    destroy_subparser = add_subparser("destroy")
    check_subparser = add_subparser("check")
    clean_subparser = add_subparser("clean")

    check_subparser.add_argument(
            "-A", "--all-folders", action=_StoreBoolActionType, default=False, type=partial(checkbox, checked=False),
            help="Check status for all project's output folders, not just "
                 "those for samples specified in the config file used. Default=False")
    check_subparser.add_argument(
            "-F", "--flags", nargs='*', default=FLAGS, type=partial(select, options=FLAGS),
            help="Check on only these flags/status values.")

    destroy_subparser.add_argument(
            "--force-yes", action=_StoreBoolActionType, default=False, type=partial(checkbox, checked=False),
            help="Provide upfront confirmation of destruction intent, "
                 "to skip console query.  Default=False")

    # Common arguments
    for subparser in [run_subparser, summarize_subparser,
                      destroy_subparser, check_subparser, clean_subparser]:
        subparser.add_argument(
                "config_file",
                help="Project configuration file (YAML).")
        subparser.add_argument(
                "--file-checks", dest="file_checks",
                action=_StoreBoolActionType, default=True, type=partial(checkbox, checked=True),
                help="Perform input file checks. Default=True.")
        subparser.add_argument(
                "-d", "--dry-run", dest="dry_run",
                action=_StoreBoolActionType, default=False, type=partial(checkbox, checked=False),
                help="Don't actually submit the project/subproject.  Default=False")
        fetch_samples_group = \
            subparser.add_argument_group("select samples",
                                         "This group of arguments lets you specify samples to use by "
                                         "exclusion OR inclusion of the samples attribute values.")
        fetch_samples_group.add_argument("--selector-attribute", nargs=1, dest="selector_attribute",
                                         help="Specify the attribute for samples exclusion OR inclusion",
                                         default="protocol")
        protocols = fetch_samples_group.add_mutually_exclusive_group()
        protocols.add_argument(
                "--selector-exclude", nargs='*', dest="selector_exclude",
                help="Operate only on samples that either lack this attribute value or "
                     "for which this value is not in this collection.")
        protocols.add_argument(
                "--selector-include", nargs='*', dest="selector_include",
                help="Operate only on samples associated with these attribute values;"
                     " if not provided, all samples are used.")
        subparser.add_argument(
                "--sp", dest="subproject",
                help="Name of subproject to use, as designated in the "
                     "project's configuration file")

    return parser
