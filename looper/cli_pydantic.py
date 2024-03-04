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

import os
import sys

import logmuse
import pydantic2_argparse
import yaml
from pephubclient import PEPHubClient
from pydantic2_argparse.argparse.parser import ArgumentParser

from divvy import select_divvy_config

from . import __version__
from .cli_looper import _proc_resources_spec
from .command_models.commands import SUPPORTED_COMMANDS, TopLevelParser
from .const import *
from .divvy import DEFAULT_COMPUTE_RESOURCES_NAME, select_divvy_config
from .exceptions import *
from .looper import *
from .parser_types import *
from .project import Project, ProjectContext
from .utils import (
    dotfile_path,
    enrich_args_via_cfg,
    is_registry_path,
    read_looper_config_file,
    read_looper_dotfile,
    initiate_looper_config,
    init_generic_pipeline,
)


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

    if subcommand_name in ["init"]:
        return int(
            not initiate_looper_config(
                dotfile_path(),
                args.pep_config,
                args.init.output_dir,
                args.sample_pipeline_interfaces,
                args.project_pipeline_interfaces,
                args.init.force_yes,
            )
        )

    if subcommand_name in ["init_piface"]:
        sys.exit(int(not init_generic_pipeline()))

    _LOGGER.info("Looper version: {}\nCommand: {}".format(__version__, subcommand_name))

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

    args = enrich_args_via_cfg(args, parser, test_args=test_args)

    # If project pipeline interface defined in the cli, change name to: "pipeline_interface"
    if vars(args)[PROJECT_PL_ARG]:
        args.pipeline_interfaces = vars(args)[PROJECT_PL_ARG]

    divcfg = (
        select_divvy_config(filepath=subcommand_args.divvy)
        if hasattr(subcommand_args, "divvy")
        else None
    )
    # Ignore flags if user is selecting or excluding on flags:
    if subcommand_args.sel_flag or subcommand_args.exc_flag:
        subcommand_args.ignore_flags = True

    # Initialize project
    if is_registry_path(args.config_file):
        if vars(args)[SAMPLE_PL_ARG]:
            p = Project(
                amendments=args.amend,
                divcfg_path=divcfg,
                runp=subcommand_name == "runp",
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
                runp=subcommand_name == "runp",
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
        selector_flag=subcommand_args.sel_flag,
        exclusion_flag=subcommand_args.exc_flag,
    ) as prj:
        if subcommand_name in ["run", "rerun"]:
            run = Runner(prj)
            try:
                # compute_kwargs = _proc_resources_spec(args)
                compute_kwargs = _proc_resources_spec(subcommand_args)

                # TODO Shouldn't top level args and subcommand args be accessible on the same object?
                return run(
                    subcommand_args, top_level_args=args, rerun=False, **compute_kwargs
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

        if subcommand_name in ["runp"]:
            compute_kwargs = _proc_resources_spec(subcommand_args)
            collate = Collator(prj)
            collate(args, **compute_kwargs)
            return collate.debug

        if subcommand_name in ["destroy"]:
            return Destroyer(prj)(args)

        use_pipestat = (
            prj.pipestat_configured_project
            if getattr(args, "project", None)
            else prj.pipestat_configured
        )

        if subcommand_name in ["table"]:
            if use_pipestat:
                return Tabulator(prj)(args)
            else:
                raise PipestatConfigurationException("table")

        if subcommand_name in ["report"]:
            if use_pipestat:
                return Reporter(prj)(args)
            else:
                raise PipestatConfigurationException("report")

        if subcommand_name in ["link"]:
            if use_pipestat:
                Linker(prj)(args)
            else:
                raise PipestatConfigurationException("link")

        if subcommand_name in ["check"]:
            if use_pipestat:
                return Checker(prj)(args)
            else:
                raise PipestatConfigurationException("check")

        if subcommand_name in ["clean"]:
            return Cleaner(prj)(args)

        if subcommand_name in ["inspect"]:
            from warnings import warn

            warn(
                "The inspect feature has moved to eido."
                "Use `eido inspect` from now on.",
            )


def main(test_args=None) -> None:
    parser = pydantic2_argparse.ArgumentParser(
        model=TopLevelParser,
        prog="looper",
        description="Looper Pydantic Argument Parser",
        add_help=True,
    )
    if test_args:
        args = parser.parse_typed_args(args=test_args)
    else:
        args = parser.parse_typed_args()
    return run_looper(args, parser, test_args=test_args)


if __name__ == "__main__":
    main()
