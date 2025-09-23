"""
CLI script using `pydantic-argparse` for parsing of arguments

Arguments / commands are defined in `command_models/` and are given, eventually, as
`pydantic` models, allowing for type-checking and validation of arguments.

Note: this is only a test script so far, and coexists next to the current CLI
(`cli_looper.py`), which uses `argparse` directly. The goal is to eventually
replace the current CLI with a CLI based on above-mentioned `pydantic` models,
but whether this will happen with `pydantic-argparse` or another, possibly self-
written library is not yet clear.
It is well possible that this script will be removed again.
"""

# Note: The following import is used for forward annotations (Python 3.8)
# to prevent potential 'TypeError' related to the use of the '|' operator
# with types.
from __future__ import annotations

import sys

import logmuse
import pydantic_argparse
import yaml
from eido import inspect_project
from pephubclient import PEPHubClient
from pydantic_argparse.argparse.parser import ArgumentParser

from . import __version__

from .command_models.arguments import ArgumentEnum

from .command_models.commands import (
    SUPPORTED_COMMANDS,
    TopLevelParser,
    add_short_arguments,
)
from .const import *
from .divvy import DEFAULT_COMPUTE_RESOURCES_NAME, select_divvy_config
from .exceptions import *
from .looper import *
from .parser_types import *
from .project import Project, ProjectContext
from .utils import (
    dotfile_path,
    enrich_args_via_cfg,
    is_pephub_registry_path,
    read_looper_config_file,
    read_looper_dotfile,
    initiate_looper_config,
    init_generic_pipeline,
    read_yaml_file,
    inspect_looper_config_file,
    is_PEP_file_type,
    looper_config_tutorial,
)

from typing import List, Tuple
from rich.console import Console


def opt_attr_pair(name: str) -> Tuple[str, str]:
    """Takes argument as attribute and returns as tuple of top-level or subcommand used."""
    return f"--{name}", name.replace("-", "_")


def validate_post_parse(args: argparse.Namespace) -> List[str]:
    """Checks if user is attempting to use mutually exclusive options."""
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
        # Depending on the subcommand used, the above options might either be in
        # the top-level namespace or in the subcommand namespace (the latter due
        # to a `modify_args_namespace()`)
        if getattr(
            args, attr, None
        )  # or (getattr(args.run, attr, None) if hasattr(args, "run") else False)
    ]
    if len(used_exclusives) > 1:
        problems.append(
            f"Used multiple mutually exclusive options: {', '.join(used_exclusives)}"
        )
    return problems


# TODO rename to run_looper_via_cli for running lloper as a python library:
#  https://github.com/pepkit/looper/pull/472#discussion_r1521970763
def run_looper(args: TopLevelParser, parser: ArgumentParser, test_args=None):
    # here comes adapted `cli_looper.py` code
    global _LOGGER

    _LOGGER = logmuse.logger_via_cli(args, make_root=True)

    # Find out which subcommand was used
    supported_command_names = [cmd.name for cmd in SUPPORTED_COMMANDS]
    subcommand_valued_args = [
        (arg, value)
        for arg, value in vars(args).items()
        if arg and arg in supported_command_names and value is not None
    ]
    # Only one subcommand argument will be not `None`, else we found a bug in `pydantic-argparse`
    [(subcommand_name, subcommand_args)] = subcommand_valued_args

    cli_use_errors = validate_post_parse(subcommand_args)
    if cli_use_errors:
        parser.print_help(sys.stderr)
        parser.error(
            f"{len(cli_use_errors)} CLI use problem(s): {', '.join(cli_use_errors)}"
        )

    if subcommand_name is None:
        parser.print_help(sys.stderr)
        sys.exit(1)

    if subcommand_name == "init":

        console = Console()
        console.clear()
        console.rule(f"\n[magenta]Looper initialization[/magenta]")
        selection = subcommand_args.generic
        if selection is True:
            console.clear()
            return int(
                not initiate_looper_config(
                    dotfile_path(),
                    subcommand_args.pep_config,
                    subcommand_args.output_dir,
                    subcommand_args.sample_pipeline_interfaces,
                    subcommand_args.project_pipeline_interfaces,
                    subcommand_args.force_yes,
                )
            )
        else:
            console.clear()
            return int(looper_config_tutorial())

    if subcommand_name == "init_piface":
        sys.exit(int(not init_generic_pipeline()))

    _LOGGER.info("Looper version: {}\nCommand: {}".format(__version__, subcommand_name))

    looper_cfg_path = os.path.relpath(dotfile_path(), start=os.curdir)
    try:
        if subcommand_args.config:
            looper_config_dict = read_looper_config_file(subcommand_args.config)
        else:
            looper_config_dict = read_looper_dotfile()
            _LOGGER.info(f"Using looper config ({looper_cfg_path}).")

        cli_modifiers_dict = None
        for looper_config_key, looper_config_item in looper_config_dict.items():
            if looper_config_key == CLI_KEY:
                cli_modifiers_dict = looper_config_item
            else:
                setattr(subcommand_args, looper_config_key, looper_config_item)

    except OSError as e:
        if subcommand_args.config:
            _LOGGER.warning(
                f"\nLooper config file does not exist at given path {subcommand_args.config}. Use looper init to create one at {looper_cfg_path}."
            )
        else:
            _LOGGER.warning(e)

        sys.exit(1)

    subcommand_args = enrich_args_via_cfg(
        subcommand_name,
        subcommand_args,
        parser,
        test_args=test_args,
        cli_modifiers=cli_modifiers_dict,
    )

    # If project pipeline interface defined in the cli, change name to: "pipeline_interface"
    if vars(subcommand_args)[PROJECT_PL_ARG]:
        subcommand_args.pipeline_interfaces = vars(subcommand_args)[PROJECT_PL_ARG]

    divcfg = (
        select_divvy_config(filepath=subcommand_args.divvy)
        if hasattr(subcommand_args, "divvy")
        else None
    )
    # Ignore flags if user is selecting or excluding on flags:
    if subcommand_args.sel_flag or subcommand_args.exc_flag:
        subcommand_args.ignore_flags = True

    # Initialize project
    if is_PEP_file_type(subcommand_args.pep_config) and os.path.exists(
        subcommand_args.pep_config
    ):
        try:
            p = Project(
                cfg=subcommand_args.pep_config,
                amendments=subcommand_args.amend,
                divcfg_path=divcfg,
                runp=subcommand_name == "runp",
                **{
                    attr: getattr(subcommand_args, attr)
                    for attr in CLI_PROJ_ATTRS
                    if attr in subcommand_args
                },
            )
        except yaml.parser.ParserError as e:
            _LOGGER.error(f"Project config parse failed -- {e}")
            sys.exit(1)
    elif is_pephub_registry_path(subcommand_args.pep_config):
        if vars(subcommand_args)[SAMPLE_PL_ARG]:
            p = Project(
                amendments=subcommand_args.amend,
                divcfg_path=divcfg,
                runp=subcommand_name == "runp",
                project_dict=PEPHubClient().load_raw_pep(
                    registry_path=subcommand_args.pep_config
                ),
                **{
                    attr: getattr(subcommand_args, attr)
                    for attr in CLI_PROJ_ATTRS
                    if attr in subcommand_args
                },
            )
        else:
            raise MisconfigurationException(
                f"`sample_pipeline_interface` is missing. Provide it in the parameters."
            )
    else:
        raise MisconfigurationException(
            f"Cannot load PEP. Check file path or registry path to pep."
        )

    selected_compute_pkg = p.selected_compute_package or DEFAULT_COMPUTE_RESOURCES_NAME
    if p.dcc is not None and not p.dcc.activate_package(selected_compute_pkg):
        _LOGGER.info(
            "Failed to activate '{}' computing package. "
            "Using the default one".format(selected_compute_pkg)
        )

    with ProjectContext(
        prj=p,
        selector_attribute=subcommand_args.sel_attr,
        selector_include=subcommand_args.sel_incl,
        selector_exclude=subcommand_args.sel_excl,
        selector_flag=subcommand_args.sel_flag,
        exclusion_flag=subcommand_args.exc_flag,
    ) as prj:

        # Check at the beginning if user wants to use pipestat and pipestat is configurable
        is_pipestat_configured = (
            prj._check_if_pipestat_configured(pipeline_type=PipelineLevel.PROJECT.value)
            if getattr(subcommand_args, "project", None) or subcommand_name == "runp"
            else prj._check_if_pipestat_configured()
        )

        if subcommand_name in ["run", "rerun"]:
            if getattr(subcommand_args, "project", None):
                _LOGGER.warning(
                    "Project flag set but 'run' command was used. Please use 'runp' to run at project-level."
                )
            rerun = subcommand_name == "rerun"
            run = Runner(prj)
            try:
                # compute_kwargs = _proc_resources_spec(args)
                compute_kwargs = _proc_resources_spec(subcommand_args)

                # TODO Shouldn't top level args and subcommand args be accessible on the same object?
                return run(
                    subcommand_args, top_level_args=args, rerun=rerun, **compute_kwargs
                )
            except SampleFailedException:
                sys.exit(1)
            except IOError:
                _LOGGER.error(
                    "{} pipeline_interfaces: '{}'".format(
                        prj.__class__.__name__, prj.pipeline_interface_sources
                    )
                )
                raise

        if subcommand_name == "runp":
            compute_kwargs = _proc_resources_spec(subcommand_args)
            collate = Collator(prj)
            collate(subcommand_args, **compute_kwargs)
            return collate.debug

        if subcommand_name == "destroy":
            return Destroyer(prj)(subcommand_args)

        if subcommand_name == "table":
            if is_pipestat_configured:
                return Tabulator(prj)(subcommand_args)
            else:
                raise PipestatConfigurationException("table")

        if subcommand_name == "report":
            if is_pipestat_configured:
                return Reporter(prj)(subcommand_args)
            else:
                raise PipestatConfigurationException("report")

        if subcommand_name == "link":
            if is_pipestat_configured:
                Linker(prj)(subcommand_args)
            else:
                raise PipestatConfigurationException("link")

        if subcommand_name == "check":
            if is_pipestat_configured:
                return Checker(prj)(subcommand_args)
            else:
                raise PipestatConfigurationException("check")

        if subcommand_name == "clean":
            return Cleaner(prj)(subcommand_args)

        if subcommand_name == "inspect":
            # Inspect PEP from Eido
            sample_names = []
            for sample in p.samples:
                sample_names.append(sample["sample_name"])
            inspect_project(p, sample_names)
            # Inspect looper config file
            if looper_config_dict:
                inspect_looper_config_file(looper_config_dict)
            else:
                _LOGGER.warning("No looper configuration was supplied.")


def main(test_args=None) -> dict:
    parser = pydantic_argparse.ArgumentParser(
        model=TopLevelParser,
        prog="looper",
        description="Looper: A job submitter for Portable Encapsulated Projects",
        add_help=True,
        version="2.0.3",
    )

    parser = add_short_arguments(parser, ArgumentEnum)

    if test_args:
        args = parser.parse_typed_args(args=test_args)
    else:
        args = parser.parse_typed_args()

    return run_looper(args, parser, test_args=test_args)


def main_cli() -> None:
    main()


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
    settings = args.settings
    try:
        settings_data = read_yaml_file(settings) or {}
    except yaml.YAMLError:
        _LOGGER.warning(
            "Settings file ({}) does not follow YAML format,"
            " disregarding".format(settings)
        )
        settings_data = {}
    if not spec:
        return settings_data
    if isinstance(
        spec, str
    ):  # compute: "partition=standard time='01-00:00:00' cores='32' mem='32000'"
        spec = spec.split(sep=" ")
    if isinstance(spec, list):
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
    elif isinstance(spec, dict):
        for key, value in spec.items():
            settings_data[key] = value

    return settings_data


if __name__ == "__main__":
    main()
