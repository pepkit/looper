""" Helpers without an obvious logical home. """

import argparse
from collections import defaultdict, namedtuple
import glob
import itertools
from logging import getLogger
import os
import sys
from typing import *
import re

import jinja2
import yaml
from peppy import Project as peppyProject
from peppy.const import *
from ubiquerg import convert_value, expandpath, parse_registry_path
from pephubclient.constants import RegistryPath
from pydantic import ValidationError

from .const import *
from .command_models.commands import SUPPORTED_COMMANDS
from .exceptions import MisconfigurationException, RegistryPathException

_LOGGER = getLogger(__name__)


def fetch_flag_files(prj=None, results_folder="", flags=FLAGS):
    """
    Find all flag file paths for the given project.

    :param Project | AttributeDict prj: full Project or AttributeDict with
        similar metadata and access/usage pattern
    :param str results_folder: path to results folder, corresponding to the
        1:1 sample:folder notion that a looper Project has. That is, this
        function uses the assumption that if results_folder rather than project
        is provided, the structure of the file tree rooted at results_folder is
        such that any flag files to be found are not directly within rootdir but
        are directly within on of its first layer of subfolders.
    :param Iterable[str] | str flags: Collection of flag names or single flag
        name for which to fetch files
    :return Mapping[str, list[str]]: collection of filepaths associated with
        particular flag for samples within the given project
    :raise TypeError: if neither or both of project and rootdir are given
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


def fetch_sample_flags(prj, sample, pl_name, flag_dir=None):
    """
    Find any flag files present for a sample associated with a project

    :param looper.Project prj: project of interest
    :param peppy.Sample sample: sample object of interest
    :param str pl_name: name of the pipeline for which flag(s) should be found
    :return Iterable[str]: collection of flag file path(s) associated with the
        given sample for the given project
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


def get_sample_status(sample, flags):
    """
    get a sample status

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


def grab_project_data(prj):
    """
    From the given Project, grab Sample-independent data.

    There are some aspects of a Project of which it's beneficial for a Sample
    to be aware, particularly for post-hoc analysis. Since Sample objects
    within a Project are mutually independent, though, each doesn't need to
    know about any of the others. A Project manages its, Sample instances,
    so for each Sample knowledge of Project data is limited. This method
    facilitates adoption of that conceptual model.

    :param Project prj: Project from which to grab data
    :return Mapping: Sample-independent data sections from given Project
    """
    if not prj:
        return {}

    try:
        return prj[CONFIG_KEY]
    except KeyError:
        _LOGGER.debug("Project lacks section '%s', skipping", CONFIG_KEY)


def sample_folder(prj, sample):
    """
    Get the path to this Project's root folder for the given Sample.

    :param AttributeDict | Project prj: project with which sample is associated
    :param Mapping sample: Sample or sample data for which to get root output
        folder path.
    :return str: this Project's root folder for the given Sample
    """
    return os.path.join(prj.results_folder, sample[prj.sample_table_index])


def get_file_for_project(prj, pipeline_name, appendix=None, directory=None):
    """
    Create a path to the file for the current project.
    Takes the possibility of amendment being activated at the time

    Format of the output path:
    {output_dir}/{directory}/{p.name}_{pipeline_name}_{active_amendments}_{appendix}

    :param looper.Project prj: project object
    :param str pipeline_name: name of the pipeline to get the file for
    :param str appendix: the appendix of the file to create the path for,
        like 'objs_summary.tsv' for objects summary file
    :return str: path to the file
    """
    fp = os.path.join(
        prj.output_dir, directory or "", f"{prj[NAME_KEY]}_{pipeline_name}"
    )
    if hasattr(prj, "amendments") and getattr(prj, "amendments"):
        fp += f"_{'_'.join(prj.amendments)}"
    fp += f"_{appendix}"
    return fp


def get_file_for_project_old(prj, appendix):
    """
    Create a path to the file for the current project.
    Takes the possibility of amendment being activated at the time

    :param looper.Project prj: project object
    :param str appendix: the appendix of the file to create the path for,
        like 'objs_summary.tsv' for objects summary file
    :return str: path to the file
    """
    fp = os.path.join(prj.output_dir, prj[NAME_KEY])
    if hasattr(prj, AMENDMENTS_KEY) and getattr(prj, AMENDMENTS_KEY):
        fp += "_" + "_".join(getattr(prj, AMENDMENTS_KEY))
    fp += "_" + appendix
    return fp


def jinja_render_template_strictly(template, namespaces):
    """
    Render a command string in the provided namespaces context.

    Strictly, which means that all the requested attributes must be
    available in the namespaces

    :param str template: command template do be filled in with the
        variables in the provided namespaces. For example:
        "prog.py --name {project.name} --len {sample.len}"
    :param Mapping[Mapping[str] namespaces: context for command rendering.
        Possible namespaces are: looper, project, sample, pipeline
    :return str: rendered command
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


def read_yaml_file(filepath):
    """
    Read a YAML file

    :param str filepath: path to the file to read
    :return dict: read data
    """
    data = None
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
    return data


def enrich_args_via_cfg(subcommand_name, parser_args, aux_parser, test_args=None):
    """
    Read in a looper dotfile and set arguments.

    Priority order: CLI > dotfile/config > parser default

    :param subcommand name: the name of the command used
    :param argparse.Namespace parser_args: parsed args by the original parser
    :param argparse.Namespace aux_parser: parsed args by the a parser
        with defaults suppressed
    :return argparse.Namespace: selected argument values
    """
    cfg_args_all = (
        _get_subcommand_args(subcommand_name, parser_args)
        if os.path.exists(parser_args.config_file)
        else dict()
    )
    result = argparse.Namespace()
    if test_args:
        cli_args, _ = aux_parser.parse_known_args(args=test_args)

    else:
        cli_args, _ = aux_parser.parse_known_args()

    def set_single_arg(argname, default_source_namespace, result_namespace):
        if argname not in POSITIONAL or not hasattr(result, argname):
            if argname in cli_args:
                cli_provided_value = getattr(cli_args, argname)
                r = (
                    convert_value(cli_provided_value)
                    if isinstance(cli_provided_value, str)
                    else cli_provided_value
                )
            elif cfg_args_all is not None and argname in cfg_args_all:
                if isinstance(cfg_args_all[argname], list):
                    r = [convert_value(i) for i in cfg_args_all[argname]]
                else:
                    r = convert_value(cfg_args_all[argname])
            else:
                r = getattr(default_source_namespace, argname)
            setattr(result_namespace, argname, r)

    for top_level_argname in vars(parser_args):
        if top_level_argname not in [cmd.name for cmd in SUPPORTED_COMMANDS]:
            # this argument is a top-level argument
            set_single_arg(top_level_argname, parser_args, result)
        else:
            # this argument actually is a subcommand
            enriched_command_namespace = argparse.Namespace()
            command_namespace = getattr(parser_args, top_level_argname)
            if command_namespace:
                for argname in vars(command_namespace):
                    set_single_arg(
                        argname, command_namespace, enriched_command_namespace
                    )
            setattr(result, top_level_argname, enriched_command_namespace)
    return result


def _get_subcommand_args(subcommand_name, parser_args):
    """
    Get the union of values for the subcommand arguments from
    Project.looper, Project.looper.cli.<subcommand> and Project.looper.cli.all.
    If any are duplicated, the above is the selection priority order.

    Additionally, convert the options strings to destinations (replace '-'
    with '_'), which strongly relies on argument parser using default
    destinations.

    :param argparser.Namespace parser_args: argument namespace
    :return dict: mapping of argument destinations to their values
    """
    args = dict()
    cfg = peppyProject(
        parser_args.config_file,
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


def init_generic_pipeline():
    """
    Create generic pipeline interface
    """
    try:
        os.makedirs("pipeline")
    except FileExistsError:
        pass

    # Destination one level down from CWD in pipeline folder
    dest_file = os.path.join(os.getcwd(), "pipeline", LOOPER_GENERIC_PIPELINE)

    # Create Generic Pipeline Interface
    generic_pipeline_dict = {
        "pipeline_name": "default_pipeline_name",
        "pipeline_type": "sample",
        "output_schema": "output_schema.yaml",
        "var_templates": {"pipeline": "{looper.piface_dir}/pipeline.sh"},
        "command_template": "{pipeline.var_templates.pipeline} {sample.file} "
        "--output-parent {looper.sample_output_folder}",
    }

    # Write file
    if not os.path.exists(dest_file):
        with open(dest_file, "w") as file:
            yaml.dump(generic_pipeline_dict, file)
        print(f"Pipeline interface successfully created at: {dest_file}")
    else:
        print(
            f"Pipeline interface file already exists `{dest_file}`. Skipping creation.."
        )

    # Create Generic Output Schema
    dest_file = os.path.join(os.getcwd(), "pipeline", LOOPER_GENERIC_OUTPUT_SCHEMA)
    generic_output_schema_dict = {
        "pipeline_name": "default_pipeline_name",
        "samples": {
            "number_of_lines": {
                "type": "integer",
                "description": "Number of lines in the input file.",
            }
        },
    }
    # Write file
    if not os.path.exists(dest_file):
        with open(dest_file, "w") as file:
            yaml.dump(generic_output_schema_dict, file)
        print(f"Output schema successfully created at: {dest_file}")
    else:
        print(f"Output schema file already exists `{dest_file}`. Skipping creation..")

    # Create Generic countlines.sh
    dest_file = os.path.join(os.getcwd(), "pipeline", LOOPER_GENERIC_COUNT_LINES)
    shell_code = """#!/bin/bash
linecount=`wc -l $1 | sed -E 's/^[[:space:]]+//' | cut -f1 -d' '`
pipestat report -r $2 -i 'number_of_lines' -v $linecount -c $3
echo "Number of lines: $linecount"
    """
    if not os.path.exists(dest_file):
        with open(dest_file, "w") as file:
            file.write(shell_code)
        print(f"count_lines.sh successfully created at: {dest_file}")
    else:
        print(f"count_lines.sh file already exists `{dest_file}`. Skipping creation..")

    return True


def read_looper_dotfile():
    """
    Read looper config file
    :return str: path to the config file read from the dotfile
    :raise MisconfigurationException: if the dotfile does not consist of the
        required key pointing to the PEP
    """
    dot_file_path = dotfile_path(must_exist=True)
    return read_looper_config_file(looper_config_path=dot_file_path)


def initiate_looper_config(
    looper_config_path: str,
    pep_path: str = None,
    output_dir: str = None,
    sample_pipeline_interfaces: Union[List[str], str] = None,
    project_pipeline_interfaces: Union[List[str], str] = None,
    force=False,
):
    """
    Initialize looper config file

    :param str looper_config_path: absolute path to the file to initialize
    :param str pep_path: path to the PEP to be used in pipeline
    :param str output_dir: path to the output directory
    :param str|list sample_pipeline_interfaces: path or list of paths to sample pipeline interfaces
    :param str|list project_pipeline_interfaces: path or list of paths to project pipeline interfaces
    :param bool force: whether the existing file should be overwritten
    :return bool: whether the file was initialized
    """
    if os.path.exists(looper_config_path) and not force:
        print(f"Can't initialize, file exists: {looper_config_path}")
        return False

    if pep_path:
        if is_registry_path(pep_path):
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

    looper_config_dict = {
        "pep_config": os.path.relpath(pep_path),
        "output_dir": output_dir,
        "pipeline_interfaces": {
            "sample": sample_pipeline_interfaces,
            "project": project_pipeline_interfaces,
        },
    }

    with open(looper_config_path, "w") as dotfile:
        yaml.dump(looper_config_dict, dotfile)
    print(f"Initialized looper config file: {looper_config_path}")
    return True


def read_looper_config_file(looper_config_path: str) -> dict:
    """
    Read Looper config file which includes:
    - PEP config (local path or pephub registry path)
    - looper output dir
    - looper pipeline interfaces

    :param str looper_config_path: path to looper config path
    :return dict: looper config file content
    :raise MisconfigurationException: incorrect configuration.
    """
    return_dict = {}
    with open(looper_config_path, "r") as dotfile:
        dp_data = yaml.safe_load(dotfile)

    if PEP_CONFIG_KEY in dp_data:
        # Looper expects the config path to live at looper.config_file
        # However, user may wish to access the pep at looper.pep_config
        return_dict[PEP_CONFIG_FILE_KEY] = dp_data[PEP_CONFIG_KEY]
        return_dict[PEP_CONFIG_KEY] = dp_data[PEP_CONFIG_KEY]

    # TODO: delete it in looper 2.0
    elif DOTFILE_CFG_PTH_KEY in dp_data:
        return_dict[PEP_CONFIG_FILE_KEY] = dp_data[DOTFILE_CFG_PTH_KEY]

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

    if PIPELINE_INTERFACES_KEY in dp_data:
        dp_data.setdefault(PIPELINE_INTERFACES_KEY, {})
        return_dict[SAMPLE_PL_ARG] = dp_data.get(PIPELINE_INTERFACES_KEY).get("sample")
        return_dict[PROJECT_PL_ARG] = dp_data.get(PIPELINE_INTERFACES_KEY).get(
            "project"
        )

    else:
        _LOGGER.warning(
            f"{PIPELINE_INTERFACES_KEY} is not defined in looper config file ({looper_config_path})"
        )
        dp_data.setdefault(PIPELINE_INTERFACES_KEY, {})

    config_dir_path = os.path.dirname(os.path.abspath(looper_config_path))

    # Expand paths in case ENV variables are used
    for k, v in return_dict.items():
        if isinstance(v, str):
            v = expandpath(v)
            if not os.path.isabs(v) and not is_registry_path(v):
                return_dict[k] = os.path.join(config_dir_path, v)
            else:
                return_dict[k] = v

    return return_dict


def dotfile_path(directory=os.getcwd(), must_exist=False):
    """
    Get the path to the looper dotfile

    If file existence is forced this function will look for it in
    the directory parents

    :param str directory: directory path to start the search in
    :param bool must_exist: whether the file must exist
    :return str: path to the dotfile
    :raise OSError: if the file does not exist
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
                "Looper dotfile ({}) not found in '{}' and all "
                "its parents".format(LOOPER_DOTFILE_NAME, directory)
            )
        cur_dir = parent_dir


def is_PEP_file_type(input_string: str) -> bool:
    """
    Determines if the provided path is actually a file type that Looper can use for loading PEP
    """

    PEP_FILE_TYPES = ["yaml", "csv"]

    parsed_path = parse_registry_path(input_string)

    if parsed_path["subitem"] in PEP_FILE_TYPES:
        return True
    else:
        return False


def is_registry_path(input_string: str) -> bool:
    """
    Check if input is a registry path to pephub
    :param str input_string: path to the PEP (or registry path)
    :return bool: True if input is a registry path
    """
    try:
        if input_string.endswith(".yaml") or input_string.endswith(".csv"):
            return False
    except AttributeError:
        raise RegistryPathException(
            msg=f"Malformed registry path. Unable to parse {input_string} as a registry path."
        )
    try:
        registry_path = RegistryPath(**parse_registry_path(input_string))
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
        return type(other) == type(self) and self.to_tuple() == other.to_tuple()

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.to_tuple()}"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.to_tuple()}"

    def to_tuple(self) -> Tuple[int, int]:
        return self.lo, self.hi

    @property
    def lo(self) -> int:
        return self._lo

    @property
    def hi(self) -> int:
        return self._hi

    def _invalidations(self) -> Iterable[str]:
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
    def from_string(cls, s: str, upper_bound: int) -> "IntRange":
        """
        Create an instance from a string, e.g. command-line argument.

        :param str s: The string to parse as an interval
        :param int upper_bound: the default upper bound
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
    """
    Create a contiguous interval of natural numbers. Used for _positive_ selection of samples.

    Interpret given arg as upper bound (1-based) if it's a single value, but take the
    minimum of that and the given number of samples. If arg is parseable as a range,
    use that.

    :param str arg: CLI specification of a range of samples to use, or as the greatest
        1-based index of a sample to include
    :param int num_samples: what to use as the upper bound on the 1-based index interval
        if the given arg isn't a range but rather a single value.
    :return: an iterable of 1-based indices into samples to select
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
    """
    Create a contiguous interval of natural numbers. Used for _negative_ selection of samples.

    :param str arg: CLI specification of a range of samples to use, or as the lowest
        1-based index of a sample to skip
    :param int num_samples: highest 1-based index of samples to include
    :return: an iterable of 1-based indices into samples to select
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


def write_submit_script(fp, content, data):
    """
    Write a submission script for divvy by populating a template with data.
    :param str fp: Path to the file to which to create/write submissions script.
    :param str content: Template for submission script, defining keys that
        will be filled by given data
    :param Mapping data: a "pool" from which values are available to replace
        keys in the template
    :return str: Path to the submission script
    """

    for k, v in data.items():
        placeholder = "{" + str(k).upper() + "}"
        content = content.replace(placeholder, str(v))

    keys_left = re.findall(r"!$\{(.+?)\}", content)
    if len(keys_left) > 0:
        _LOGGER.warning(
            "> Warning: %d submission template variables are not " "populated: '%s'",
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
    """
    Inspects looper config by printing it to terminal.
    param dict looper_config_dict: dict representing looper_config

    """
    # Simply print this to terminal
    print("LOOPER INSPECT")
    for key, value in looper_config_dict.items():
        print(f"{key} {value}")
