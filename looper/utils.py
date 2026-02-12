"""Helpers without an obvious logical home."""

import argparse
import glob
import itertools
import os
import re
from collections import defaultdict
from collections.abc import Iterable
from logging import getLogger

import jinja2
import yaml
from pephubclient.constants import RegistryPath
from peppy import Project as peppyProject
from peppy.const import CONFIG_KEY, NAME_KEY, SAMPLE_MODS_KEY
from pydantic import ValidationError
from rich.console import Console
from rich.pretty import pprint
from ubiquerg import convert_value, deep_update, expandpath, parse_registry_path
from yacman import load_yaml
from yaml.parser import ParserError

from .const import (
    ALL_SUBCMD_KEY,
    CLI_KEY,
    FLAGS,
    LOOPER_DOTFILE_NAME,
    LOOPER_GENERIC_COUNT_LINES,
    LOOPER_GENERIC_OUTPUT_SCHEMA,
    LOOPER_GENERIC_PIPELINE,
    LOOPER_KEY,
    OUTDIR_KEY,
    PEP_CONFIG_KEY,
    PIPELINE_INTERFACES_KEY,
    PIPESTAT_KEY,
    PROJECT_PL_ARG,
    SAMPLE_PL_ARG,
    PipelineLevel,
)
from .exceptions import MisconfigurationException, PipelineInterfaceConfigError

_LOGGER = getLogger(__name__)


def fetch_flag_files(
    prj=None, results_folder: str = "", flags: Iterable[str] | str = FLAGS
) -> dict[str, list[str]]:
    """Find all flag file paths for the given project.

    Args:
        prj (Project | AttributeDict): Full Project or AttributeDict with
            similar metadata and access/usage pattern.
        results_folder (str): Path to results folder, corresponding to the
            1:1 sample:folder notion that a looper Project has. That is, this
            function uses the assumption that if results_folder rather than project
            is provided, the structure of the file tree rooted at results_folder is
            such that any flag files to be found are not directly within rootdir but
            are directly within one of its first layer of subfolders.
        flags (Iterable[str] | str): Collection of flag names or single flag
            name for which to fetch files.

    Returns:
        Mapping[str, list[str]]: Collection of filepaths associated with
            particular flag for samples within the given project.

    Raises:
        TypeError: If neither or both of project and rootdir are given.
    """

    if not (prj or results_folder) or (prj and results_folder):
        raise TypeError("Need EITHER project OR rootdir")

    # Just create the filenames once, and pair once with flag name.
    flags = [flags] if isinstance(flags, str) else list(flags)
    flagfile_suffices = ["*{}.flag".format(f) for f in flags]
    flag_suffix_pairs = list(zip(flags, flagfile_suffices))

    # Collect the flag file paths by flag name.
    files_by_flag = defaultdict(list)

    if prj is None:
        for flag, suffix in flag_suffix_pairs:
            flag_expr = os.path.join(results_folder, "*", suffix)
            flags_present = glob.glob(flag_expr)
            files_by_flag[flag] = flags_present
    else:
        # Iterate over samples to collect flag files.
        for s in prj.samples:
            folder = sample_folder(prj, s)
            # Check each candidate flag for existence, collecting if present.
            for flag, suffix in flag_suffix_pairs:
                flag_expr = os.path.join(folder, suffix)
                flags_present = glob.glob(flag_expr)
                files_by_flag[flag].extend(flags_present)

    return files_by_flag


def fetch_sample_flags(
    prj, sample, pl_name: str, flag_dir: str | None = None
) -> list[str]:
    """Find any flag files present for a sample associated with a project.

    Args:
        prj (looper.Project): Project of interest.
        sample (peppy.Sample): Sample object of interest.
        pl_name (str): Name of the pipeline for which flag(s) should be found.
        flag_dir: Flag directory path.

    Returns:
        Iterable[str]: Collection of flag file path(s) associated with the
            given sample for the given project.
    """
    sfolder = flag_dir or sample_folder(prj=prj, sample=sample)
    if not os.path.isdir(sfolder):
        _LOGGER.debug(
            "Results folder ({}) doesn't exist for sample {}".format(
                sfolder, str(sample)
            )
        )
        return []
    folder_contents = [os.path.join(sfolder, f) for f in os.listdir(sfolder)]
    return [
        x
        for x in folder_contents
        if os.path.splitext(x)[1] == ".flag"
        and os.path.basename(x).startswith(pl_name)
        and sample.sample_name in x
    ]


def get_sample_status(sample: str, flags: list[str]) -> str | None:
    """Get a sample status.

    Args:
        sample: Sample identifier.
        flags: Collection of flag file paths.

    Returns:
        str or None: Status string if found, None otherwise.
    """

    statuses = []

    for f in flags:
        basename = os.path.basename(f)
        status = os.path.splitext(basename)[0].split("_")[-1]
        if sample in basename:
            statuses.append(status.upper())

    if len(statuses) > 1:
        _LOGGER.warning(f"Multiple status flags found for {sample}")

    if statuses == []:
        return None

    return statuses[0]


def grab_project_data(prj) -> dict:
    """From the given Project, grab Sample-independent data.

    There are some aspects of a Project of which it's beneficial for a Sample
    to be aware, particularly for post-hoc analysis. Since Sample objects
    within a Project are mutually independent, though, each doesn't need to
    know about any of the others. A Project manages its, Sample instances,
    so for each Sample knowledge of Project data is limited. This method
    facilitates adoption of that conceptual model.

    Args:
        prj (Project): Project from which to grab data.

    Returns:
        Mapping: Sample-independent data sections from given Project.
    """
    if not prj:
        return {}

    try:
        return prj[CONFIG_KEY]
    except KeyError:
        _LOGGER.debug("Project lacks section '%s', skipping", CONFIG_KEY)


def sample_folder(prj, sample) -> str:
    """Get the path to this Project's root folder for the given Sample.

    Args:
        prj (AttributeDict | Project): Project with which sample is associated.
        sample (Mapping): Sample or sample data for which to get root output
            folder path.

    Returns:
        str: This Project's root folder for the given Sample.
    """
    return os.path.join(prj.results_folder, sample[prj.sample_table_index])


def get_file_for_project(
    prj, pipeline_name: str, appendix: str | None = None, directory: str | None = None
) -> str:
    """Create a path to the file for the current project.

    Takes the possibility of amendment being activated at the time.

    Format of the output path:
    {output_dir}/{directory}/{p.name}_{pipeline_name}_{active_amendments}_{appendix}

    Args:
        prj (looper.Project): Project object.
        pipeline_name (str): Name of the pipeline to get the file for.
        appendix (str): The appendix of the file to create the path for,
            like 'objs_summary.tsv' for objects summary file.
        directory (str): Directory path component.

    Returns:
        str: Path to the file.
    """
    fp = os.path.join(
        prj.output_dir, directory or "", f"{prj[NAME_KEY]}_{pipeline_name}"
    )
    if hasattr(prj, "amendments") and getattr(prj, "amendments"):
        fp += f"_{'_'.join(prj.amendments)}"
    fp += f"_{appendix}"
    return fp


def jinja_render_template_strictly(template: str, namespaces: dict) -> str:
    """Render a command string in the provided namespaces context.

    Strictly, which means that all the requested attributes must be
    available in the namespaces.

    Args:
        template (str): Command template to be filled in with the
            variables in the provided namespaces. For example:
            "prog.py --name {project.name} --len {sample.len}".
        namespaces (Mapping[Mapping[str]]): Context for command rendering.
            Possible namespaces are: looper, project, sample, pipeline.

    Returns:
        str: Rendered command.
    """

    def _finfun(x):
        """
        A callable that can be used to process the result of a variable
        expression before it is output. Joins list elements
        """
        return " ".join(x) if isinstance(x, list) else x

    env = jinja2.Environment(
        undefined=jinja2.StrictUndefined,
        variable_start_string="{",
        variable_end_string="}",
        finalize=_finfun,
    )
    templ_obj = env.from_string(template)
    try:
        rendered = templ_obj.render(**namespaces)
    except jinja2.exceptions.UndefinedError as e:
        _LOGGER.error("Error populating command template: " + str(e))
        _LOGGER.debug(f"({', '.join(list(namespaces.keys()))}) missing for ")
        _LOGGER.debug(f"Template: '{template}'")
        raise e
    _LOGGER.debug("rendered arg str: {}".format(rendered))
    return rendered


def read_yaml_file(filepath: str) -> dict | None:
    """Read a YAML file.

    Args:
        filepath (str): Path to the file to read.

    Returns:
        dict: Read data.
    """
    data = None
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
    return data


def enrich_args_via_cfg(
    subcommand_name: str,
    parser_args,
    test_args: dict | None = None,
    cli_modifiers: dict | None = None,
) -> argparse.Namespace:
    """Read in a looper dotfile, pep config and set arguments.

    Priority order: CLI > dotfile/config > pep_config > parser default

    Args:
        subcommand_name: The name of the command used.
        parser_args (argparse.Namespace): Parsed args by the original parser.
        test_args (dict): Dict of args used for pytesting.
        cli_modifiers (dict): Dict of args existing if user supplied cli args
            in looper config file.

    Returns:
        argparse.Namespace: Selected argument values.
    """

    # Did the user provide arguments in the PEP config?
    cfg_args_all = (
        _get_subcommand_args(subcommand_name, parser_args)
        if os.path.exists(parser_args.pep_config)
        else dict()
    )
    if not cfg_args_all:
        cfg_args_all = {}

    # Did the user provide arguments/modifiers in the looper config file?
    looper_config_cli_modifiers = None
    if cli_modifiers:
        if str(subcommand_name) in cli_modifiers:
            looper_config_cli_modifiers = cli_modifiers[subcommand_name]
            looper_config_cli_modifiers = (
                {k.replace("-", "_"): v for k, v in looper_config_cli_modifiers.items()}
                if looper_config_cli_modifiers
                else None
            )

    if looper_config_cli_modifiers:
        _LOGGER.warning(
            "CLI modifiers were provided in Looper Config and in PEP Project Config. Merging..."
        )
        deep_update(cfg_args_all, looper_config_cli_modifiers)
        _LOGGER.debug(msg=f"Merged CLI modifiers: {cfg_args_all}")

    result = argparse.Namespace()
    cli_args = parser_args  # Use parser_args directly, already parsed

    def set_single_arg(argname, default_source_namespace, result_namespace):
        # Priority: CLI > cfg_args_all (PEP config) > parser default
        cli_value = getattr(cli_args, argname, None)
        cfg_value = cfg_args_all.get(argname) if cfg_args_all else None
        default_value = getattr(default_source_namespace, argname, None)

        if cli_value is not None and cli_value != default_value:
            # CLI provided a non-default value - use it
            r = convert_value(cli_value) if isinstance(cli_value, str) else cli_value
        elif cfg_value is not None:
            # PEP config provided a value
            if isinstance(cfg_value, list):
                r = [convert_value(i) for i in cfg_value]
            elif isinstance(cfg_value, dict):
                r = cfg_value
            else:
                r = convert_value(cfg_value)
        else:
            # Use default
            r = default_value
        setattr(result_namespace, argname, r)

    # Copy all arguments from parser_args to result
    for argname in vars(parser_args):
        set_single_arg(argname, parser_args, result)

    # Also add any cfg_args that weren't in parser_args
    if cfg_args_all:
        for argname in cfg_args_all:
            if not hasattr(result, argname):
                cfg_value = cfg_args_all[argname]
                if isinstance(cfg_value, list):
                    r = [convert_value(i) for i in cfg_value]
                elif isinstance(cfg_value, dict):
                    r = cfg_value
                else:
                    r = convert_value(cfg_value)
                setattr(result, argname, r)

    return result


def _get_subcommand_args(subcommand_name: str, parser_args) -> dict | None:
    """Get the union of values for the subcommand arguments.

    Get the union of values for the subcommand arguments from
    Project.looper, Project.looper.cli.<subcommand> and Project.looper.cli.all.
    If any are duplicated, the above is the selection priority order.

    Additionally, convert the options strings to destinations (replace '-'
    with '_'), which strongly relies on argument parser using default
    destinations.

    Args:
        parser_args (argparser.Namespace): Argument namespace.

    Returns:
        dict: Mapping of argument destinations to their values.
    """
    args = dict()
    cfg = peppyProject(
        parser_args.pep_config,
        defer_samples_creation=True,
        amendments=parser_args.amend,
    )
    if (
        CONFIG_KEY in cfg
        and LOOPER_KEY in cfg[CONFIG_KEY]
        and CLI_KEY in cfg[CONFIG_KEY][LOOPER_KEY]
    ):
        try:
            cfg_args = cfg[CONFIG_KEY][LOOPER_KEY][CLI_KEY] or dict()
            args = (
                cfg_args[ALL_SUBCMD_KEY] or dict()
                if ALL_SUBCMD_KEY in cfg_args
                else dict()
            )
            args.update(
                cfg_args[subcommand_name] or dict()
                if subcommand_name in cfg_args
                else dict()
            )
        except (TypeError, KeyError, AttributeError, ValueError) as e:
            raise MisconfigurationException(
                "Invalid '{}.{}' section in the config. Caught exception: {}".format(
                    LOOPER_KEY, CLI_KEY, getattr(e, "message", repr(e))
                )
            )
    if CONFIG_KEY in cfg and LOOPER_KEY in cfg[CONFIG_KEY]:
        try:
            if CLI_KEY in cfg[CONFIG_KEY][LOOPER_KEY]:
                del cfg[CONFIG_KEY][LOOPER_KEY][CLI_KEY]
            args.update(cfg[CONFIG_KEY][LOOPER_KEY])
        except (TypeError, KeyError, AttributeError, ValueError) as e:
            raise MisconfigurationException(
                "Invalid '{}' section in the config. Caught exception: {}".format(
                    LOOPER_KEY, getattr(e, "message", repr(e))
                )
            )
    args = {k.replace("-", "_"): v for k, v in args.items()} if args else None
    return args


def init_generic_pipeline(pipelinepath: str | None = None):
    """Create generic pipeline interface.

    Args:
        pipelinepath (str, optional): Path to pipeline directory.

    Returns:
        bool: True if successful.
    """
    console = Console()

    # Destination one level down from CWD in pipeline folder
    if not pipelinepath:
        try:
            os.makedirs("pipeline")
        except FileExistsError:
            pass

        dest_file = os.path.join(os.getcwd(), "pipeline", LOOPER_GENERIC_PIPELINE)
    else:
        if os.path.isabs(pipelinepath):
            dest_file = pipelinepath
        else:
            dest_file = os.path.join(os.getcwd(), os.path.relpath(pipelinepath))
        try:
            os.makedirs(os.path.dirname(dest_file))
        except FileExistsError:
            pass

    # Create Generic Pipeline Interface
    generic_pipeline_dict = {
        "pipeline_name": "default_pipeline_name",
        "output_schema": "output_schema.yaml",
        "sample_interface": {
            "command_template": "{looper.piface_dir}/count_lines.sh {sample.file} "
            "--output-parent {looper.sample_output_folder}"
        },
    }

    console.rule("\n[magenta]Pipeline Interface[/magenta]")
    # Write file
    if not os.path.exists(dest_file):
        pprint(generic_pipeline_dict, expand_all=True)

        with open(dest_file, "w") as file:
            yaml.dump(generic_pipeline_dict, file)

        console.print(
            f"Pipeline interface successfully created at: [yellow]{dest_file}[/yellow]"
        )

    else:
        console.print(
            f"Pipeline interface file already exists [yellow]`{dest_file}`[/yellow]. Skipping creation.."
        )

    # Create Generic Output Schema
    if not pipelinepath:
        dest_file = os.path.join(os.getcwd(), "pipeline", LOOPER_GENERIC_OUTPUT_SCHEMA)
    else:
        dest_file = os.path.join(
            os.path.dirname(dest_file), LOOPER_GENERIC_OUTPUT_SCHEMA
        )

    generic_output_schema_dict = {
        "pipeline_name": "default_pipeline_name",
        "samples": {
            "number_of_lines": {
                "type": "integer",
                "description": "Number of lines in the input file.",
            }
        },
    }

    console.rule("\n[magenta]Output Schema[/magenta]")
    # Write file
    if not os.path.exists(dest_file):
        pprint(generic_output_schema_dict, expand_all=True)
        with open(dest_file, "w") as file:
            yaml.dump(generic_output_schema_dict, file)
        console.print(
            f"Output schema successfully created at: [yellow]{dest_file}[/yellow]"
        )
    else:
        console.print(
            f"Output schema file already exists [yellow]`{dest_file}`[/yellow]. Skipping creation.."
        )

    console.rule("\n[magenta]Example Pipeline Shell Script[/magenta]")
    # Create Generic countlines.sh

    if not pipelinepath:
        dest_file = os.path.join(os.getcwd(), "pipeline", LOOPER_GENERIC_COUNT_LINES)
    else:
        dest_file = os.path.join(os.path.dirname(dest_file), LOOPER_GENERIC_COUNT_LINES)

    shell_code = """#!/bin/bash
linecount=`wc -l $1 | sed -E 's/^[[:space:]]+//' | cut -f1 -d' '`
pipestat report -r $2 -i 'number_of_lines' -v $linecount -c $3
echo "Number of lines: $linecount"
    """
    if not os.path.exists(dest_file):
        console.print(shell_code)
        with open(dest_file, "w") as file:
            file.write(shell_code)
        console.print(
            f"count_lines.sh successfully created at: [yellow]{dest_file}[/yellow]"
        )
    else:
        console.print(
            f"count_lines.sh file already exists [yellow]`{dest_file}`[/yellow]. Skipping creation.."
        )

    return True


def read_looper_dotfile() -> dict:
    """Read looper config file.

    Returns:
        str: Path to the config file read from the dotfile.

    Raises:
        MisconfigurationException: If the dotfile does not consist of the
            required key pointing to the PEP.
    """
    dot_file_path = dotfile_path(must_exist=True)
    return read_looper_config_file(looper_config_path=dot_file_path)


def initiate_looper_config(
    looper_config_path: str,
    pep_path: str = None,
    output_dir: str = None,
    sample_pipeline_interfaces: list[str] | str = None,
    project_pipeline_interfaces: list[str] | str = None,
    force: bool = False,
) -> bool:
    """Initialize looper config file.

    Args:
        looper_config_path (str): Absolute path to the file to initialize.
        pep_path (str): Path to the PEP to be used in pipeline.
        output_dir (str): Path to the output directory.
        sample_pipeline_interfaces (str | list): Path or list of paths to
            sample pipeline interfaces.
        project_pipeline_interfaces (str | list): Path or list of paths to
            project pipeline interfaces.
        force (bool): Whether the existing file should be overwritten.

    Returns:
        bool: Whether the file was initialized.
    """
    console = Console()
    console.clear()
    console.rule("\n[magenta]Looper initialization[/magenta]")

    if os.path.exists(looper_config_path) and not force:
        console.print(
            f"[red]Can't initialize, file exists:[/red] [yellow]{looper_config_path}[/yellow]"
        )
        return False

    if pep_path:
        if is_pephub_registry_path(pep_path):
            pass
        else:
            pep_path = expandpath(pep_path)
            if not os.path.isabs(pep_path):
                pep_path = os.path.join(os.path.dirname(looper_config_path), pep_path)
            assert os.path.exists(pep_path), OSError(
                "Provided config path is invalid. You must provide path "
                f"that is either absolute or relative to: {os.path.dirname(looper_config_path)}"
            )
    else:
        pep_path = "example/pep/path"

    if not output_dir:
        output_dir = "."

    if sample_pipeline_interfaces is None or sample_pipeline_interfaces == []:
        sample_pipeline_interfaces = "pipeline_interface1.yaml"

    if project_pipeline_interfaces is None or project_pipeline_interfaces == []:
        project_pipeline_interfaces = "pipeline_interface2.yaml"

    looper_config_dict = {
        "pep_config": os.path.relpath(pep_path),
        "output_dir": output_dir,
        "pipeline_interfaces": [
            sample_pipeline_interfaces,
            project_pipeline_interfaces,
        ],
    }

    pprint(looper_config_dict, expand_all=True)

    with open(looper_config_path, "w") as dotfile:
        yaml.dump(looper_config_dict, dotfile)
    console.print(
        f"Initialized looper config file: [yellow]{looper_config_path}[/yellow]"
    )

    return True


def looper_config_tutorial() -> bool:
    """Prompt a user through configuring a .looper.yaml file for a new project.

    Returns:
        bool: Whether the file was initialized.
    """

    console = Console()
    console.clear()
    console.rule("\n[magenta]Looper initialization[/magenta]")

    looper_cfg_path = ".looper.yaml"  # not changeable

    if os.path.exists(looper_cfg_path):
        console.print(
            f"[bold red]File exists at '{looper_cfg_path}'. Delete it to re-initialize. \n[/bold red]"
        )
        raise SystemExit

    cfg = {}

    console.print(
        "This utility will walk you through creating a [yellow].looper.yaml[/yellow] file."
    )
    console.print("See [yellow]`looper init --help`[/yellow] for details.")
    console.print("Use [yellow]`looper run`[/yellow] afterwards to run the pipeline.")
    console.print("Press [yellow]^C[/yellow] at any time to quit.\n")

    DEFAULTS = {  # What you get if you just press enter
        "pep_config": "databio/example",
        "output_dir": "results",
        "piface_path": "pipeline/pipeline_interface.yaml",
        "project_name": os.path.basename(os.getcwd()),
    }

    cfg["project_name"] = (
        console.input(f"Project name: [yellow]({DEFAULTS['project_name']})[/yellow] >")
        or DEFAULTS["project_name"]
    )

    cfg["pep_config"] = (
        console.input(
            f"Registry path or file path to PEP: [yellow]({DEFAULTS['pep_config']})[/yellow] >"
        )
        or DEFAULTS["pep_config"]
    )

    if not os.path.exists(cfg["pep_config"]) and not is_pephub_registry_path(
        cfg["pep_config"]
    ):
        console.print(
            f"Warning: PEP file does not exist at [yellow]'{cfg['pep_config']}[/yellow]'"
        )

    cfg["output_dir"] = (
        console.input(
            f"Path to output directory: [yellow]({DEFAULTS['output_dir']})[/yellow] >"
        )
        or DEFAULTS["output_dir"]
    )

    add_more_pifaces = True
    piface_paths = []
    while add_more_pifaces:
        piface_path = (
            console.input(
                "Add each path to a pipeline interface: [yellow](pipeline_interface.yaml)[/yellow] >"
            )
            or None
        )
        if piface_path is None:
            if piface_paths == []:
                piface_paths.append(DEFAULTS["piface_path"])
            add_more_pifaces = False
        else:
            piface_paths.append(piface_path)

    console.print("\n")

    console.print(f"""\
[yellow]pep_config:[/yellow] {cfg["pep_config"]}
[yellow]output_dir:[/yellow] {cfg["output_dir"]}
[yellow]pipeline_interfaces:[/yellow]
  - {piface_paths}
""")

    for piface_path in piface_paths:
        if not os.path.exists(piface_path):
            console.print(
                f"[bold red]Warning:[/bold red] File does not exist at [yellow]{piface_path}[/yellow]"
            )
            console.print(
                "Do you wish to initialize a generic pipeline interface? [bold green]Y[/bold green]/[red]n[/red]..."
            )
            selection = None
            while selection not in ["y", "n"]:
                selection = console.input("\nSelection: ").lower().strip()
            if selection == "n":
                console.print(
                    "Use command [yellow]`looper init_piface`[/yellow] to create a generic pipeline interface."
                )
            if selection == "y":
                init_generic_pipeline(pipelinepath=piface_path)

    console.print(f"Writing config file to [yellow]{looper_cfg_path}[/yellow]")

    looper_config_dict = {}
    looper_config_dict["pep_config"] = cfg["pep_config"]
    looper_config_dict["output_dir"] = cfg["output_dir"]
    looper_config_dict["pipeline_interfaces"] = piface_paths

    with open(looper_cfg_path, "w") as fp:
        yaml.dump(looper_config_dict, fp)

    return True


def determine_pipeline_type(
    piface_path: str, looper_config_path: str
) -> tuple[list[str] | None, str | None]:
    """Read pipeline interface and determine its type.

    Read pipeline interface from disk and determine if it contains
    "sample_interface", "project_interface" or both.

    Args:
        piface_path (str): Path to pipeline_interface.
        looper_config_path (str): Path to looper config file.

    Returns:
        Tuple[Union[str, None], Union[str, None]]: (pipeline type, resolved path)
            or (None, None).
    """

    if piface_path is None:
        return None, None
    try:
        piface_path = expandpath(piface_path)
    except TypeError as e:
        _LOGGER.warning(
            f"Pipeline interface not found at given path: {piface_path}. Type Error: "
            + str(e)
        )
        return None, None

    if not os.path.isabs(piface_path):
        piface_path = os.path.realpath(
            os.path.join(os.path.dirname(looper_config_path), piface_path)
        )
    try:
        piface_dict = load_yaml(piface_path)
    except FileNotFoundError:
        _LOGGER.warning(f"Pipeline interface not found at given path: {piface_path}")
        return None, None

    pipeline_types = []
    if piface_dict.get("sample_interface", None):
        pipeline_types.append(PipelineLevel.SAMPLE.value)
    if piface_dict.get("project_interface", None):
        pipeline_types.append(PipelineLevel.PROJECT.value)

    if pipeline_types == []:
        raise PipelineInterfaceConfigError(
            "sample_interface and/or project_interface must be defined in each pipeline interface."
        )

    return pipeline_types, piface_path


def read_looper_config_file(looper_config_path: str) -> dict:
    """Read Looper config file.

    Read Looper config file which includes:
    - PEP config (local path or pephub registry path)
    - looper output dir
    - looper pipeline interfaces

    Args:
        looper_config_path (str): Path to looper config path.

    Returns:
        dict: Looper config file content.

    Raises:
        MisconfigurationException: Incorrect configuration.
    """
    return_dict = {}

    try:
        with open(looper_config_path, "r") as dotfile:
            dp_data = yaml.safe_load(dotfile)
    except ParserError as e:
        _LOGGER.warning(
            "Could not load looper config file due to the following exception"
        )
        raise ParserError(context=str(e))

    if PEP_CONFIG_KEY in dp_data:
        return_dict[PEP_CONFIG_KEY] = dp_data[PEP_CONFIG_KEY]
    else:
        raise MisconfigurationException(
            f"Looper dotfile ({looper_config_path}) is missing '{PEP_CONFIG_KEY}' key"
        )

    if OUTDIR_KEY in dp_data:
        return_dict[OUTDIR_KEY] = dp_data[OUTDIR_KEY]
    else:
        _LOGGER.warning(
            f"{OUTDIR_KEY} is not defined in looper config file ({looper_config_path})"
        )

    if PIPESTAT_KEY in dp_data:
        return_dict[PIPESTAT_KEY] = dp_data[PIPESTAT_KEY]

    if SAMPLE_MODS_KEY in dp_data:
        return_dict[SAMPLE_MODS_KEY] = dp_data[SAMPLE_MODS_KEY]

    if CLI_KEY in dp_data:
        return_dict[CLI_KEY] = dp_data[CLI_KEY]

    if PIPELINE_INTERFACES_KEY in dp_data:
        dp_data.setdefault(PIPELINE_INTERFACES_KEY, {})

        all_pipeline_interfaces = dp_data.get(PIPELINE_INTERFACES_KEY)

        sample_pifaces = []
        project_pifaces = []
        if isinstance(all_pipeline_interfaces, str):
            all_pipeline_interfaces = [all_pipeline_interfaces]
        for piface in all_pipeline_interfaces:
            pipeline_types, piface_path = determine_pipeline_type(
                piface, looper_config_path
            )
            if pipeline_types is not None:
                if PipelineLevel.SAMPLE.value in pipeline_types:
                    sample_pifaces.append(piface_path)
                if PipelineLevel.PROJECT.value in pipeline_types:
                    project_pifaces.append(piface_path)
        if len(sample_pifaces) > 0:
            return_dict[SAMPLE_PL_ARG] = sample_pifaces
        if len(project_pifaces) > 0:
            return_dict[PROJECT_PL_ARG] = project_pifaces

    else:
        _LOGGER.warning(
            f"{PIPELINE_INTERFACES_KEY} is not defined in looper config file ({looper_config_path})"
        )
        dp_data.setdefault(PIPELINE_INTERFACES_KEY, {})

    config_dir_path = os.path.dirname(os.path.abspath(looper_config_path))

    # Expand paths in case ENV variables are used
    for k, v in return_dict.items():
        if k == SAMPLE_PL_ARG or k == PROJECT_PL_ARG:
            # Pipeline interfaces are resolved at a later point. Do it there only to maintain consistency. #474

            pass
        if isinstance(v, str):
            v = expandpath(v)
            # TODO this is messy because is_pephub_registry needs to fail on anything NOT a pephub registry path
            # https://github.com/pepkit/ubiquerg/issues/43
            if is_PEP_file_type(v):
                if not os.path.isabs(v):
                    return_dict[k] = os.path.join(config_dir_path, v)
                else:
                    return_dict[k] = v
            elif is_pephub_registry_path(v):
                return_dict[k] = v
            else:
                if not os.path.isabs(v):
                    return_dict[k] = os.path.join(config_dir_path, v)
                else:
                    return_dict[k] = v

    return return_dict


def dotfile_path(directory: str = os.getcwd(), must_exist: bool = False) -> str:
    """Get the path to the looper dotfile.

    If file existence is forced this function will look for it in
    the directory parents.

    Args:
        directory (str): Directory path to start the search in.
        must_exist (bool): Whether the file must exist.

    Returns:
        str: Path to the dotfile.

    Raises:
        OSError: If the file does not exist.
    """
    cur_dir = directory
    if not must_exist:
        return os.path.join(cur_dir, LOOPER_DOTFILE_NAME)
    while True:
        parent_dir = os.path.dirname(cur_dir)
        if LOOPER_DOTFILE_NAME in os.listdir(cur_dir):
            return os.path.join(cur_dir, LOOPER_DOTFILE_NAME)
        if cur_dir == parent_dir:
            # root, file does not exist
            raise OSError(
                "Looper dotfile ({}) not found in '{}' and all its parents".format(
                    LOOPER_DOTFILE_NAME, directory
                )
            )
        cur_dir = parent_dir


def is_PEP_file_type(input_string: str) -> bool:
    """Determines if the provided path is a file type that Looper can use for loading PEP.

    Args:
        input_string (str): Path to check.

    Returns:
        bool: True if the path is a valid PEP file type.
    """

    PEP_FILE_TYPES = ["yaml", "csv"]

    res = list(filter(input_string.endswith, PEP_FILE_TYPES)) != []
    return res


def is_pephub_registry_path(input_string: str) -> bool:
    """Check if input is a registry path to pephub.

    Args:
        input_string (str): Path to the PEP (or registry path).

    Returns:
        bool: True if input is a registry path.
    """
    try:
        RegistryPath(**parse_registry_path(input_string))
    except (ValidationError, TypeError):
        return False
    return True


class NatIntervalException(Exception):
    """Subtype for errors specifically related to natural number interval"""

    pass


class NatIntervalInclusive(object):
    def __init__(self, lo: int, hi: int):
        super().__init__()
        self._lo = lo
        self._hi = hi
        problems = self._invalidations()
        if problems:
            raise NatIntervalException(
                f"{len(problems)} issues with interval on natural numbers: {', '.join(problems)}"
            )

    def __eq__(self, other) -> bool:
        return type(other) is type(self) and self.to_tuple() == other.to_tuple()

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.to_tuple()}"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.to_tuple()}"

    def to_tuple(self) -> tuple[int, int]:
        return self.lo, self.hi

    @property
    def lo(self) -> int:
        return self._lo

    @property
    def hi(self) -> int:
        return self._hi

    def _invalidations(self) -> list[str]:
        problems = []
        if self.lo < 1:
            problems.append(f"Interval must be on natural numbers: {self.lo}")
        if self.hi < self.lo:
            problems.append(
                f"Upper bound must not be less than lower bound: {self.hi} < {self.lo}"
            )
        return problems

    def to_range(self) -> Iterable[int]:
        return range(self.lo, self.hi + 1)

    @classmethod
    def from_string(cls, s: str, upper_bound: int) -> "NatIntervalInclusive":
        """Create an instance from a string, e.g. command-line argument.

        Args:
            s (str): The string to parse as an interval.
            upper_bound (int): The default upper bound.

        Returns:
            IntRange: New instance created from the string.
        """
        if upper_bound < 1:
            raise NatIntervalException(f"Upper bound must be positive: {upper_bound}")

        # Determine delimiter, invalidating presence of multiple occurrences.
        delim_histo = defaultdict(int)
        candidates = [":", "-"]
        for c in s:
            if c in candidates:
                delim_histo[c] += 1
        seps = [sep for sep, num_occ in delim_histo.items() if num_occ == 1]
        if len(seps) != 1:
            raise NatIntervalException(
                f"Did not find exactly one candidate delimiter with occurrence count of 1: {delim_histo}"
            )
        sep = seps[0]

        # Use the determined delimiter.
        lo, hi = s.split(sep)
        if lo == "" and hi == "":
            # We could do an interval like [1, upper_bound], but this is nonsensical as input.
            raise NatIntervalException(
                f"Parsed both lower and upper limit as empty from given arg: {s}"
            )
        try:
            lo = 1 if lo == "" else int(lo)
            hi = upper_bound if hi == "" else min(int(hi), upper_bound)
        except ValueError as e:
            raise NatIntervalException(str(e))
        return cls(lo, hi)


def desired_samples_range_limited(arg: str, num_samples: int) -> Iterable[int]:
    """Create a contiguous interval of natural numbers for positive selection of samples.

    Interpret given arg as upper bound (1-based) if it's a single value, but take the
    minimum of that and the given number of samples. If arg is parseable as a range,
    use that.

    Args:
        arg (str): CLI specification of a range of samples to use, or as the greatest
            1-based index of a sample to include.
        num_samples (int): What to use as the upper bound on the 1-based index interval
            if the given arg isn't a range but rather a single value.

    Returns:
        Iterable[int]: An iterable of 1-based indices into samples to select.
    """
    try:
        upper_bound = min(int(arg), num_samples)
    except ValueError:
        intv = NatIntervalInclusive.from_string(arg, upper_bound=num_samples)
    else:
        _LOGGER.debug("Limiting to {} of {} samples".format(upper_bound, num_samples))
        intv = NatIntervalInclusive(1, upper_bound)
    return intv.to_range()


def desired_samples_range_skipped(arg: str, num_samples: int) -> Iterable[int]:
    """Create a contiguous interval of natural numbers for negative selection of samples.

    Args:
        arg (str): CLI specification of a range of samples to use, or as the lowest
            1-based index of a sample to skip.
        num_samples (int): Highest 1-based index of samples to include.

    Returns:
        Iterable[int]: An iterable of 1-based indices into samples to select.
    """
    try:
        lower_bound = int(arg)
    except ValueError:
        intv = NatIntervalInclusive.from_string(arg, upper_bound=num_samples)
        lower = range(1, intv.lo)
        upper = range(intv.hi + 1, num_samples + 1)
        return itertools.chain(lower, upper)
    else:
        if num_samples <= lower_bound:
            return []
        intv = NatIntervalInclusive(lower_bound + 1, num_samples)
        return intv.to_range()


def write_submit_script(fp: str, content: str, data: dict) -> str:
    """Write a submission script for divvy by populating a template with data.

    Args:
        fp (str): Path to the file to which to create/write submissions script.
        content (str): Template for submission script, defining keys that
            will be filled by given data.
        data (Mapping): A "pool" from which values are available to replace
            keys in the template.

    Returns:
        str: Path to the submission script.
    """

    for k, v in data.items():
        placeholder = "{" + str(k).upper() + "}"
        content = content.replace(placeholder, str(v))

    keys_left = re.findall(r"!$\{(.+?)\}", content)
    if len(keys_left) > 0:
        _LOGGER.warning(
            "> Warning: %d submission template variables are not populated: '%s'",
            len(keys_left),
            str(keys_left),
        )

    if not fp:
        print(content)
        return content
    else:
        outdir = os.path.dirname(fp)
        if outdir and not os.path.isdir(outdir):
            os.makedirs(outdir)
        with open(fp, "w") as f:
            f.write(content)
        return fp


def inspect_looper_config_file(looper_config_dict) -> None:
    """Inspects looper config by printing it to terminal.

    Args:
        looper_config_dict (dict): Dict representing looper_config.
    """
    # Simply print this to terminal
    print("LOOPER INSPECT")
    for key, value in looper_config_dict.items():
        print(f"{key} {value}")


def expand_nested_var_templates(var_templates_dict: dict, namespaces: dict) -> dict:
    "Takes all var_templates as a dict and recursively expands any paths."

    result = {}

    for k, v in var_templates_dict.items():
        if isinstance(v, dict):
            result[k] = expand_nested_var_templates(v, namespaces)
        else:
            result[k] = expandpath(v)

    return result


def render_nested_var_templates(var_templates_dict: dict, namespaces: dict) -> dict:
    "Takes all var_templates as a dict and recursively renders the jinja templates."

    result = {}

    for k, v in var_templates_dict.items():
        if isinstance(v, dict):
            result[k] = expand_nested_var_templates(v, namespaces)
        else:
            result[k] = jinja_render_template_strictly(v, namespaces)

    return result
