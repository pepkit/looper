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
from eido import inspect_project
from pephubclient import PEPHubClient
from pydantic2_argparse.argparse.parser import ArgumentParser

from divvy import select_divvy_config

from . import __version__
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
    is_pephub_registry_path,
    read_looper_config_file,
    read_looper_dotfile,
    initiate_looper_config,
    init_generic_pipeline,
    read_yaml_file,
    inspect_looper_config_file,
    is_PEP_file_type,
)

from typing import List, Tuple


run_arguments_dict = {
    "-d": "--dry-run",
    "-l": "--limit",
    "-k": "--skip",
    "-o": "--output-dir",
    "-S": "--sample-pipeline-interfaces",
    "-P": "--project-pipeline-interfaces",
    "-p": "--piface",
    "-i": "--ignore-flags",
    "-t": "--time-delay",
    "-x": "--command-extra",
    "-y": "--command-extra-override",
    "-f": "--skip-file-checks",
}


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

    if subcommand_name == "init_piface":
        sys.exit(int(not init_generic_pipeline()))

    _LOGGER.info("Looper version: {}\nCommand: {}".format(__version__, subcommand_name))

    if subcommand_args.config_file is None:
        looper_cfg_path = os.path.relpath(dotfile_path(), start=os.curdir)
        try:
            if subcommand_args.looper_config:
                looper_config_dict = read_looper_config_file(
                    subcommand_args.looper_config
                )
            else:
                looper_config_dict = read_looper_dotfile()
                _LOGGER.info(f"Using looper config ({looper_cfg_path}).")

            for looper_config_key, looper_config_item in looper_config_dict.items():
                setattr(subcommand_args, looper_config_key, looper_config_item)

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

    subcommand_args = enrich_args_via_cfg(
        subcommand_name, subcommand_args, parser, test_args=test_args
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
    if is_PEP_file_type(subcommand_args.config_file) and os.path.exists(
        subcommand_args.config_file
    ):
        try:
            p = Project(
                cfg=subcommand_args.config_file,
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
    elif is_pephub_registry_path(subcommand_args.config_file):
        if vars(subcommand_args)[SAMPLE_PL_ARG]:
            p = Project(
                amendments=subcommand_args.amend,
                divcfg_path=divcfg,
                runp=subcommand_name == "runp",
                project_dict=PEPHubClient()._load_raw_pep(
                    registry_path=subcommand_args.config_file
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
        if subcommand_name in ["run", "rerun"]:
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

        use_pipestat = (
            prj.pipestat_configured_project
            if getattr(subcommand_args, "project", None)
            else prj.pipestat_configured
        )

        if subcommand_name == "table":
            if use_pipestat:
                return Tabulator(prj)(subcommand_args)
            else:
                raise PipestatConfigurationException("table")

        if subcommand_name == "report":
            if use_pipestat:
                return Reporter(prj)(subcommand_args)
            else:
                raise PipestatConfigurationException("report")

        if subcommand_name == "link":
            if use_pipestat:
                Linker(prj)(subcommand_args)
            else:
                raise PipestatConfigurationException("link")

        if subcommand_name == "check":
            if use_pipestat:
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


def create_command_string(args, command):
    """
    This is a workaround for short form arguments not being supported by the pydantic argparse package
    """
    arguments_dict = {}

    # Must determine argument dict based on command since there is overlap in shortform keys...
    if command in ["run", "runp", "rerun"]:
        arguments_dict = run_arguments_dict

    modified_command_string = []
    for arg in args:
        replacement = arguments_dict.get(arg)
        modified_command_string.append(replacement if replacement else arg)

    if command not in modified_command_string:
        modified_command_string.insert(command)

    return modified_command_string


def main(test_args=None) -> None:
    parser = pydantic2_argparse.ArgumentParser(
        model=TopLevelParser,
        prog="looper",
        description="Looper Pydantic Argument Parser",
        add_help=True,
    )
    if test_args:
        command_string = create_command_string(args=test_args, command=test_args[0])
    else:
        sys_args = sys.argv[1:]
        command_string = create_command_string(args=sys_args, command=sys_args[0])

    args = parser.parse_typed_args(args=command_string)

    return run_looper(args, parser, test_args=test_args)


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


if __name__ == "__main__":
    main()
