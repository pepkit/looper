import argparse
import logmuse
import os
import sys
import yaml

from eido import inspect_project
from pephubclient import PEPHubClient
from typing import Tuple, List
from ubiquerg import VersionInHelpParser

from . import __version__
from .const import *
from .divvy import DEFAULT_COMPUTE_RESOURCES_NAME, select_divvy_config
from .exceptions import *
from .looper import *
from .parser_types import *
from .project import Project, ProjectContext
from .utils import (
    dotfile_path,
    enrich_args_via_cfg,
    init_dotfile,
    is_registry_path,
    read_looper_dotfile,
    read_looper_config_file,
    read_yaml_file,
)


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
        init_piface = add_subparser("init-piface")

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
            "config_file", help="Project configuration file (YAML)"
        )

        init_subparser.add_argument(
            "-f", "--force", help="Force overwrite", action="store_true", default=False
        )

        init_subparser.add_argument(
            "-o",
            "--output-dir",
            dest="output_dir",
            metavar="DIR",
            default=None,
            type=str,
        )

        init_subparser.add_argument(
            "-S",
            "--sample-pipeline-interfaces",
            dest=SAMPLE_PL_ARG,
            metavar="YAML",
            default=None,
            nargs="+",
            type=str,
            help="Path to looper sample config file",
        )
        init_subparser.add_argument(
            "-P",
            "--project-pipeline-interfaces",
            dest=PROJECT_PL_ARG,
            metavar="YAML",
            default=None,
            nargs="+",
            type=str,
            help="Path to looper project config file",
        )

        # TODO: add  ouput dir, sample, project pifaces

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
                help="Project configuration file (YAML) or pephub registry path.",
            )
            subparser.add_argument(
                "--looper-config",
                required=False,
                default=None,
                type=str,
                help="Looper configuration file (YAML)",
            )
            # help="Path to the looper config file"
            subparser.add_argument(
                "-S",
                "--sample-pipeline-interfaces",
                dest=SAMPLE_PL_ARG,
                metavar="YAML",
                default=None,
                nargs="+",
                type=str,
                help="Path to looper sample config file",
            )
            subparser.add_argument(
                "-P",
                "--project-pipeline-interfaces",
                dest=PROJECT_PL_ARG,
                metavar="YAML",
                default=None,
                nargs="+",
                type=str,
                help="Path to looper project config file",
            )
            # help="Path to the output directory"
            subparser.add_argument(
                "-o",
                "--output-dir",
                dest="output_dir",
                metavar="DIR",
                default=None,
                type=str,
                help=argparse.SUPPRESS,
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
        # if hasattr(args, "project"):
        #     use_pipestat = (
        #         prj.pipestat_configured_project
        #         if args.project
        #         else prj.pipestat_configured
        #     )
        use_pipestat = (
            prj.pipestat_configured_project if args.project else prj.pipestat_configured
        )
        if args.command == "table":
            if use_pipestat:
                Tabulator(prj)(args)
            else:
                raise PipestatConfigurationException("table")

        if args.command == "report":
            if use_pipestat:
                Reporter(prj)(args)
            else:
                raise PipestatConfigurationException("report")

        if args.command == "check":
            if use_pipestat:
                Checker(prj)(args)
            else:
                raise PipestatConfigurationException("check")

        if args.command == "clean":
            return Cleaner(prj)(args)

        if args.command == "inspect":
            inspect_project(p, args.sample_names, args.attr_limit)
            from warnings import warn

            warn(
                "The inspect feature has moved to eido and will be removed in the future release of looper. "
                "Use `eido inspect` from now on.",
            )
