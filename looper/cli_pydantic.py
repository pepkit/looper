"""
CLI script using pydantic-settings for CLI parsing.

Arguments / commands are defined in `command_models/` as pydantic models,
allowing for type-checking and validation of arguments.
"""

import os
import sys
from argparse import Namespace

from pydantic_settings import get_subcommand

from .command_models.commands import SUPPORTED_COMMANDS, TopLevelParser


def flatten_args(args: TopLevelParser) -> Namespace:
    """Convert pydantic-settings args to argparse.Namespace for compatibility.

    pydantic-settings produces a nested structure where subcommand args are
    accessed via args.run.dry_run, args.check.flags, etc. The rest of looper
    expects flat access (args.dry_run, args.flags). This function flattens
    the active subcommand's arguments into a standard Namespace.

    Only one subcommand is ever active at a time, so there are no conflicts
    between arguments with the same name on different subcommands.
    """
    subcmd_args = get_subcommand(args, is_required=True)

    # Determine command name from the subcommand model
    command = None
    for cmd in SUPPORTED_COMMANDS:
        if getattr(args, cmd.name, None) is subcmd_args:
            command = cmd.name
            break

    ns = Namespace(
        command=command,
        silent=args.silent,
        verbosity=args.verbosity,
        logdev=args.logdev,
    )
    if subcmd_args is not None:
        for k, v in subcmd_args.model_dump().items():
            setattr(ns, k, v)
    return ns


def opt_attr_pair(name: str) -> tuple[str, str]:
    """Takes argument as attribute and returns as tuple of top-level or subcommand used."""
    return f"--{name}", name.replace("-", "_")


def validate_post_parse(
    args, sample_exclusion_optname: str, sample_inclusion_optname: str
) -> list[str]:
    """Checks if user is attempting to use mutually exclusive options."""
    problems = []
    used_exclusives = [
        opt
        for opt, attr in map(
            opt_attr_pair,
            [
                "skip",
                "limit",
                sample_exclusion_optname,
                sample_inclusion_optname,
            ],
        )
        if getattr(args, attr, None)
    ]
    if len(used_exclusives) > 1:
        problems.append(
            f"Used multiple mutually exclusive options: {', '.join(used_exclusives)}"
        )
    return problems


def run_looper(args: Namespace, test_args=None):
    """Run looper with parsed arguments.

    Args:
        args: Flattened arguments from pydantic-settings
        test_args: Optional test arguments for testing purposes
    """
    # Lazy imports - only load when actually running commands
    import logmuse
    import yaml
    from eido import inspect_project
    from pephubclient import PEPHubClient
    from rich.console import Console

    from . import __version__
    from .const import (
        CLI_KEY,
        CLI_PROJ_ATTRS,
        EXAMPLE_COMPUTE_SPEC_FMT,
        PROJECT_PL_ARG,
        SAMPLE_EXCLUSION_OPTNAME,
        SAMPLE_INCLUSION_OPTNAME,
        SAMPLE_PL_ARG,
        PipelineLevel,
    )
    from .divvy import DEFAULT_COMPUTE_RESOURCES_NAME, select_divvy_config
    from .exceptions import (
        MisconfigurationException,
        PipestatConfigurationException,
        SampleFailedException,
    )
    from .looper import (
        Checker,
        Cleaner,
        Collator,
        Destroyer,
        Linker,
        Reporter,
        Runner,
        Tabulator,
    )
    from .project import Project, ProjectContext
    from .utils import (
        dotfile_path,
        enrich_args_via_cfg,
        init_generic_pipeline,
        initiate_looper_config,
        inspect_looper_config_file,
        is_PEP_file_type,
        is_pephub_registry_path,
        looper_config_tutorial,
        read_looper_config_file,
        read_looper_dotfile,
        read_yaml_file,
    )

    global _LOGGER

    _LOGGER = logmuse.logger_via_cli(args, make_root=True)

    subcommand_name = args.command

    if subcommand_name is None:
        print("No command specified. Use --help for usage.", file=sys.stderr)
        sys.exit(1)

    cli_use_errors = validate_post_parse(
        args, SAMPLE_EXCLUSION_OPTNAME, SAMPLE_INCLUSION_OPTNAME
    )
    if cli_use_errors:
        print(f"Error: {', '.join(cli_use_errors)}", file=sys.stderr)
        print("Run 'looper <command> --help' for usage information.", file=sys.stderr)
        sys.exit(1)

    if subcommand_name == "init":
        console = Console()
        console.clear()
        console.rule("\n[magenta]Looper initialization[/magenta]")
        selection = args.generic
        if selection is True:
            console.clear()
            return int(
                not initiate_looper_config(
                    dotfile_path(),
                    args.pep_config,
                    args.output_dir,
                    args.sample_pipeline_interfaces,
                    args.project_pipeline_interfaces,
                    args.force_yes,
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
        if args.config:
            looper_config_dict = read_looper_config_file(args.config)
        else:
            looper_config_dict = read_looper_dotfile()
            _LOGGER.info(f"Using looper config ({looper_cfg_path}).")

        cli_modifiers_dict = None
        for looper_config_key, looper_config_item in looper_config_dict.items():
            if looper_config_key == CLI_KEY:
                cli_modifiers_dict = looper_config_item
            else:
                setattr(args, looper_config_key, looper_config_item)

    except OSError as e:
        if args.config:
            _LOGGER.warning(
                f"\nLooper config file does not exist at given path {args.config}. Use looper init to create one at {looper_cfg_path}."
            )
        else:
            _LOGGER.warning(e)

        sys.exit(1)

    args = enrich_args_via_cfg(
        subcommand_name,
        args,
        test_args=test_args,
        cli_modifiers=cli_modifiers_dict,
    )

    # If project pipeline interface defined in the cli, change name to: "pipeline_interface"
    if getattr(args, PROJECT_PL_ARG, None):
        args.pipeline_interfaces = getattr(args, PROJECT_PL_ARG)

    divcfg = (
        select_divvy_config(filepath=args.divvy) if hasattr(args, "divvy") else None
    )
    # Ignore flags if user is selecting or excluding on flags:
    if args.sel_flag or args.exc_flag:
        args.ignore_flags = True

    # Initialize project
    if is_PEP_file_type(args.pep_config) and os.path.exists(args.pep_config):
        try:
            p = Project(
                cfg=args.pep_config,
                amendments=args.amend,
                divcfg_path=divcfg,
                runp=subcommand_name == "runp",
                **{
                    attr: getattr(args, attr)
                    for attr in CLI_PROJ_ATTRS
                    if hasattr(args, attr)
                },
            )
        except yaml.parser.ParserError as e:
            _LOGGER.error(f"Project config parse failed -- {e}")
            sys.exit(1)
    elif is_pephub_registry_path(args.pep_config):
        if getattr(args, SAMPLE_PL_ARG, None):
            p = Project(
                amendments=args.amend,
                divcfg_path=divcfg,
                runp=subcommand_name == "runp",
                project_dict=PEPHubClient().load_raw_pep(registry_path=args.pep_config),
                **{
                    attr: getattr(args, attr)
                    for attr in CLI_PROJ_ATTRS
                    if hasattr(args, attr)
                },
            )
        else:
            raise MisconfigurationException(
                "`sample_pipeline_interface` is missing. Provide it in the parameters."
            )
    else:
        raise MisconfigurationException(
            "Cannot load PEP. Check file path or registry path to pep."
        )

    selected_compute_pkg = p.selected_compute_package or DEFAULT_COMPUTE_RESOURCES_NAME
    if p.dcc is not None and not p.dcc.activate_package(selected_compute_pkg):
        _LOGGER.info(
            "Failed to activate '{}' computing package. Using the default one".format(
                selected_compute_pkg
            )
        )

    with ProjectContext(
        prj=p,
        selector_attribute=args.sel_attr,
        selector_include=args.sel_incl,
        selector_exclude=args.sel_excl,
        selector_flag=args.sel_flag,
        exclusion_flag=args.exc_flag,
    ) as prj:
        # Check at the beginning if user wants to use pipestat and pipestat is configurable
        is_pipestat_configured = (
            prj._check_if_pipestat_configured(pipeline_type=PipelineLevel.PROJECT.value)
            if getattr(args, "project", None) or subcommand_name == "runp"
            else prj._check_if_pipestat_configured()
        )

        if subcommand_name in ["run", "rerun"]:
            if getattr(args, "project", None):
                _LOGGER.warning(
                    "Project flag set but 'run' command was used. Please use 'runp' to run at project-level."
                )
            rerun = subcommand_name == "rerun"
            run = Runner(prj)
            try:
                compute_kwargs = _proc_resources_spec(
                    args, read_yaml_file, EXAMPLE_COMPUTE_SPEC_FMT, _LOGGER
                )

                return run(args, rerun=rerun, **compute_kwargs)
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
            compute_kwargs = _proc_resources_spec(
                args, read_yaml_file, EXAMPLE_COMPUTE_SPEC_FMT, _LOGGER
            )
            collate = Collator(prj)
            collate(args, **compute_kwargs)
            return collate.debug

        if subcommand_name == "destroy":
            return Destroyer(prj)(args)

        if subcommand_name == "table":
            if is_pipestat_configured:
                return Tabulator(prj)(args)
            else:
                raise PipestatConfigurationException("table")

        if subcommand_name == "report":
            if is_pipestat_configured:
                return Reporter(prj)(args)
            else:
                raise PipestatConfigurationException("report")

        if subcommand_name == "link":
            if is_pipestat_configured:
                Linker(prj)(args)
            else:
                raise PipestatConfigurationException("link")

        if subcommand_name == "check":
            if is_pipestat_configured:
                return Checker(prj)(args)
            else:
                raise PipestatConfigurationException("check")

        if subcommand_name == "clean":
            return Cleaner(prj)(args)

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
    """Main entry point for looper CLI.

    Uses pydantic-settings for CLI parsing.

    Args:
        test_args: Optional list of arguments for testing

    Returns:
        Result from run_looper
    """
    if test_args:
        args = TopLevelParser(_cli_parse_args=test_args)
    else:
        args = TopLevelParser()

    flat_args = flatten_args(args)
    return run_looper(flat_args, test_args=test_args)


def main_cli() -> None:
    main()


def _proc_resources_spec(
    args, read_yaml_file, example_compute_spec_fmt, logger
) -> dict[str, str]:
    """Process CLI-sources compute setting specification.

    There are two sources of compute settings in the CLI alone:
        * YAML file (--settings argument)
        * itemized compute settings (--compute argument)

    The itemized compute specification is given priority.

    Args:
        args (argparse.Namespace): Arguments namespace.
        read_yaml_file: Function to read YAML files.
        example_compute_spec_fmt: Example format string for error messages.
        logger: Logger instance.

    Returns:
        Mapping[str, str]: Binding between resource setting name and value.

    Raises:
        ValueError: If interpretation of the given specification as encoding
            of key-value pairs fails.
    """
    import yaml

    spec = getattr(args, "compute", None)
    settings = args.settings
    try:
        settings_data = read_yaml_file(settings) or {}
    except yaml.YAMLError:
        logger.warning(
            "Settings file ({}) does not follow YAML format, disregarding".format(
                settings
            )
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
                "Correct format: " + example_compute_spec_fmt
            )
    elif isinstance(spec, dict):
        for key, value in spec.items():
            settings_data[key] = value

    return settings_data


if __name__ == "__main__":
    main()
