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

import os
import sys
from argparse import Namespace

import pydantic_argparse
import yaml
from pephubclient import PEPHubClient
from pydantic_argparse.argparse.parser import ArgumentParser

from divvy import select_divvy_config

from . import __version__
from .cli_looper import _proc_resources_spec
from .command_models.commands import TopLevelParser
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
    read_looper_dotfile,
)


def run_looper(
    args: Namespace | TopLevelParser, parser: ArgumentParser, http_api=False
):
    # here comes adapted `cli_looper.py` code
    looper_cfg_path = os.path.relpath(dotfile_path(), start=os.curdir)
    try:
        looper_config_dict = read_looper_dotfile()

        for looper_config_key, looper_config_item in looper_config_dict.items():
            print(looper_config_key, looper_config_item)
            setattr(args, looper_config_key, looper_config_item)

    except OSError:
        if not http_api:
            parser.print_help(sys.stderr)
        raise ValueError(
            f"Looper config file does not exist. Use looper init to create one at {looper_cfg_path}."
        )

    args = enrich_args_via_cfg(args, parser, False, http_api)
    divcfg = (
        select_divvy_config(filepath=args.run.divvy)
        if hasattr(args.run, "divvy")
        else None
    )
    # Ignore flags if user is selecting or excluding on flags:
    if args.sel_flag or args.exc_flag:
        args.ignore_flags = True

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
                runp=False,
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
        selector_attribute="toggle",
        selector_include=None,
        selector_exclude=None,
        selector_flag=None,
        exclusion_flag=None,
    ) as prj:
        command = "run"
        if command == "run":
            run = Runner(prj)
            try:
                compute_kwargs = _proc_resources_spec(args)
                return run(args, rerun=False, **compute_kwargs)
            except SampleFailedException:
                sys.exit(1)
            except IOError:
                _LOGGER.error(
                    "{} pipeline_interfaces: '{}'".format(
                        prj.__class__.__name__, prj.pipeline_interface_sources
                    )
                )
                raise


def main() -> None:
    parser = pydantic_argparse.ArgumentParser(
        model=TopLevelParser,
        prog="looper",
        description="pydantic-argparse demo",
        add_help=True,
    )
    args = parser.parse_typed_args()
    print(args)
    print("#########################################")
    run_looper(args, parser)


if __name__ == "__main__":
    main()
