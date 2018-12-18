""" Command-line interface """

import abc
import argparse
import copy
import logging
import os

from . import __version__, COMPUTE_SETTINGS_VARNAME, FLAGS


# Descending by severity for correspondence with logic inversion.
# That is, greater verbosity setting corresponds to lower logging level.
_LEVEL_BY_VERBOSITY = [
    logging.ERROR, logging.CRITICAL, logging.WARN, logging.INFO, logging.DEBUG]


class CliOpt(object):
    """ Base class for a CLI option """

    __metaclass__ = abc.ABCMeta

    def __init__(self, name, help, suppress=False, **kwargs):
        """
        Create option with name and help message, and possible other settings.

        :param str name: name for this option; determines Namespace attribute;
            for an non-required option, this also determines the long form.
        :param str help: help text for this option
        :param bool suppress: whether to suppress help message
        :param kwargs: variable keyword arguments, passed to a the add_argument
            method on a target object
        """
        if "help" in kwargs:
            raise ValueError("Found help as a variable keyword argument; "
                             "it must be provided as a positional")
        self._name = name
        self._help = help
        self._suppress = suppress
        self._kwargs = kwargs

    @property
    def as_argparse(self):
        """
        :return tuple, dict: positional and keyword arguments to add_argument.
        """
        return self._positionals, self._keywords

    @property
    def _keywords(self):
        """
        :return dict: keyword arguments for add_argument call
        """
        kwargs = copy.deepcopy(self._kwargs)
        kwargs["help"] = argparse.SUPPRESS if self._suppress else self._help
        return kwargs

    @abc.abstractproperty
    def _positionals(self):
        """
        :return tuple: positional arguments for add_argument call
        """
        pass

    def __str__(self):
        return "{}: ({}, {})".format(
            self.__class__.__name__, self._positionals, self._kwargs)


class ReqCliOpt(CliOpt):
    @property
    def _positionals(self):
        return (self._name, )


class OptCliOpt(CliOpt):
    """ Optional CLI option """

    def __init__(self, name, help, short=None, **kwargs):
        """ Optional CLI option adds hook for one-letter opt name use. """
        super(OptCliOpt, self).__init__(name, help, **kwargs)
        if short and len(short) > 1:
            raise ValueError("Multi-character short name: {}".format(short))
        self._short = short

    @property
    def _positionals(self):
        long_name = "--" + self._name
        return ("-" + self._short, long_name) if self._short else (long_name,)


class ToggleCliOpt(OptCliOpt):
    """ Flag-like CLI option; sets a flag to true """

    @property
    def _keywords(self):
        kwargs = super(ToggleCliOpt, self)._keywords
        kwargs["action"] = "store_true"
        return kwargs


class ExclOptGroup(object):
    """ Mutually exclusive option group """

    def __init__(self, opts, required=False):
        """
        Create a group by specifying its members, and whether one is required.

        :param Iterable[CliOpt] opts: collection of the group's member options
        :param bool required: whether specification of one of the group's
            members is required
        """
        if len(opts) < 2:
            raise ValueError("Too few opts for group: {}".format(len(opts)))
        non_opts = [o for o in opts if not isinstance(o, CliOpt)]
        if len(non_opts) > 0:
            raise TypeError("{} non-option objects: {}".format(
                    len(non_opts), ", ".join(non_opts)))
        self._opts = list(opts)
        self.required = required

    @property
    def options(self):
        """ Each option in the group """
        return copy.deepcopy(self._opts)

    def __str__(self):
        return "{}:\n{}".format(
            self.__class__.__name__, "\n".join(map(str, self.options)))


class Subparser(object):
    """ Specification of subparser for a particular program/subcommand """

    def __init__(self, name, message, opts=None):
        """

        :param str name: name for a particular prgogram/subcommand
        :param str message: description and help message
        :param Iterable[CliOpt | ExclCliGroup] opts: collection of options
            and option groups specific to a program/subcommand
        """
        self.name = name
        self._message = message
        self._opts = opts

    @property
    def description(self):
        """ Subcommand description """
        return self._message

    @property
    def help(self):
        """ Subcommand help message """
        return self._message

    @property
    def options(self):
        """ The collection of options/groups specific for this program """
        return copy.deepcopy(self._opts) if self._opts else []


class _LooperCliParser(argparse.ArgumentParser):

    def format_help(self):
        """ Add version information to help text. """
        return "version: {}\n".format(__version__) + \
               super(_LooperCliParser, self).format_help()

    def add_opt(self, opt):
        """
        Add an option to this parser.

        :param CliOpt opt: specification of a CLI option
        :return _LooperCliParser: updated instance
        """
        try:
            args, kwargs = opt.as_argparse
        except AttributeError:
            raise TypeError(
                "Not a valid CLI option type: {} ({})".format(opt, type(opt)))
        else:
            self.add_argument(*args, **kwargs)
            return self


# looper check options
_CHECK_OPTS = [
    ToggleCliOpt("all-folders",
                 "Check status for all project's output folders, not just those "
                 "for samples specified in the config file used", short="A"),
    OptCliOpt("flags", "Check on only these flags/status values.", short="F")
]

# looper destroy options
_DESTROY_OPTS = [
    ToggleCliOpt("force-yes", "Provide upfront confirmation of destruction "
                              "intent, to skip console query")]

# looper run options
_RUN_OPTS = [
    OptCliOpt("time-delay", "Time delay in seconds between job submissions.",
              short="t", type=int, default=0),
    ToggleCliOpt("ignore-flags", "Ignore run status flags? Default: False. "
                 "By default, pipelines will not be submitted if a pypiper "
                 "flag file exists marking the run (e.g. as "
                 "'running' or 'failed'). Set this option to ignore flags "
                 "and submit the runs anyway."),
    OptCliOpt("compute", "YAML file with looper environment compute settings."),
    OptCliOpt("env", "Employ looper environment compute settings.",
              default=os.getenv("{}".format(COMPUTE_SETTINGS_VARNAME), "")),
    OptCliOpt("limit", "Limit to n samples", default=None, type=int),
    OptCliOpt("lump", "Maximum total input file size for a lump/batch of "
                      "commands in a single job (in GB)",
              type=float, default=None),
    OptCliOpt("lumpn",
              "Number of individual scripts grouped into single submission",
              type=int, default=None)
]

# options to add for each program/subcommand
_ALL_COMMAND_OPTS = [
    ReqCliOpt("config_file", "Project configuration file (YAML)."),
    ToggleCliOpt("file-checks", "Perform input file checks."),
    ToggleCliOpt("dry-run", "Don't actually submit the project/subproject.",
                 short="d"),
    OptCliOpt("sp", "Name of subproject to use, as designated in the project's "
                    "configuration file", dest="subproject"),
    ExclOptGroup([
        OptCliOpt("include-protocols",
                  "Operate only on samples associated with these protocols; "
                  "if not provided, all samples are used.", nargs='*'),
        OptCliOpt("exclude-protocols",
                  "Operate only on samples that either lack a protocol or for "
                  "which protocol is not in this collection.", nargs='*')
    ])
]

# Specification of parser for each program/subcommand
PROGRAM_CLI_PARSERS = [
    Subparser("check", "Checks flag status of current runs.", _CHECK_OPTS),
    Subparser("clean", "Runs clean scripts to remove intermediate files of "
                       "already processed jobs."),
    Subparser("destroy", "Remove all files of the project.", _DESTROY_OPTS),
    Subparser("run", "Main Looper function: Submit jobs for samples.", _RUN_OPTS),
    Subparser("summarize", "Summarize statistics of project samples.")
]


def build_parser():
    """
    Building argument parser.

    :return looper.cli._LooperCliParser
    """

    # Main looper program help text messages
    banner = "%(prog)s - Loop through samples and submit pipelines."
    additional_description = "For subcommand-specific options, type: " \
                             "'%(prog)s <subcommand> -h'"
    additional_description += "\nhttps://github.com/pepkit/looper"

    # Logging control
    log_opts = [
        OptCliOpt("logfile", "Optional output file for looper logs"),
        OptCliOpt("verbosity", "Choose level of verbosity",
                  type=int, choices=list(range(len(_LEVEL_BY_VERBOSITY)))),
        OptCliOpt("logging-level", "Logging module level", suppress=True),
        ToggleCliOpt("dbg", "Turn on debug mode")
    ]

    parser = _LooperCliParser(
            description=banner,
            epilog=additional_description,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
            "-V", "--version",
            action="version",
            version="%(prog)s {v}".format(v=__version__))

    # Add the logging options.
    for a, kw in map(lambda o: o.as_argparse, log_opts):
        parser.add_argument(*a, **kw)

    subparsers = parser.add_subparsers(dest="command")

    # Update a parser/subparser with a CLI option.
    def update(obj, opt):
        try:
            if isinstance(opt, CliOpt):
                a, kw = opt.as_argparse
                obj.add_argument(*a, **kw)
            elif isinstance(opt, ExclOptGroup):
                g = obj.add_mutually_exclusive_group(required=opt.required)
                for a, kw in map(lambda o: o.as_argparse, opt.options):
                    g.add_argument(*a, **kw)
            else:
                raise TypeError("Neither an option group nor singleton: {} ({})".format(opt, type(opt)))
        except AttributeError:
            raise TypeError("Could not add a {} as an argument to a {}"
                            .format(type(opt), type(obj)))

    # Add each program
    for prog_spec in PROGRAM_CLI_PARSERS:
        sub = subparsers.add_parser(prog_spec.name,
            description=prog_spec.description, help=prog_spec.help)
        for opt in prog_spec.options:
            # Program-dependent options
            update(sub, opt)
        for opt in _ALL_COMMAND_OPTS:
            # Program-independent options
            update(sub, opt)

    return parser
