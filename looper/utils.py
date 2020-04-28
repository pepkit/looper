""" Helpers without an obvious logical home. """

from collections import defaultdict, Iterable
from logging import getLogger
import glob
import os
from .const import *
from peppy.const import *
import jinja2
import yaml
import argparse


DEFAULT_METADATA_FOLDER = "metadata"
DEFAULT_CONFIG_SUFFIX = "_config.yaml"


_LOGGER = getLogger(__name__)


def determine_config_path(
        root, folders=(DEFAULT_METADATA_FOLDER, ),
        patterns=("*" + DEFAULT_CONFIG_SUFFIX, )):
    """
    Determine path to Project config file, allowing folder-based specification.

    :param str root: path to file or main (e.g., project, folder)
    :param Iterable[str] folders: collection of names of subfolders to consider
    :param Iterable[str] patterns: collection of filename patterns to consider
    :return str: unique path to extant Project config file
    :raise ValueError: if the given root path doesn't exist, or if multiple
        matching files are found
    """

    # Base cases
    if not os.path.exists(root):
        raise ValueError("Path doesn't exist: {}".format(root))
    if os.path.isfile(root):
        return root

    # Deal with single-string argument.
    if isinstance(folders, str):
        folders = (folders, )
    if isinstance(patterns, str):
        patterns = (patterns, )

    # Search particular folder for any pattern
    def search(path):
        return [m for p in patterns for m in glob.glob(os.path.join(path, p))]

    # Search results
    top_res = search(root)
    sub_res = [m for sub in folders for m in search(os.path.join(root, sub))]
    all_res = top_res + sub_res

    # Deal with the 3 match count cases.
    if len(all_res) > 1:
        raise ValueError("Multiple ({}) config paths: {}".format(
            len(all_res), ", ".join(map(str, all_res))))
    try:
        return all_res[0]
    except IndexError:
        return None


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


def fetch_sample_flags(prj, sample, pl_name):
    """
    Find any flag files present for a sample associated with a project

    :param looper.Project prj: project of interest
    :param peppy.Sample sample: sample object of interest
    :param str pl_name: name of the pipeline for which flag(s) should be found
    :return Iterable[str]: collection of flag file path(s) associated with the
        given sample for the given project
    """
    sfolder = sample_folder(prj=prj, sample=sample)
    if not os.path.isdir(sfolder):
        _LOGGER.debug("Results folder ({}) doesn't exist for sample {}".
                      format(sfolder, str(sample)))
        return []
    folder_contents = [os.path.join(sfolder, f) for f in os.listdir(sfolder)]
    return [x for x in folder_contents if os.path.splitext(x)[1] == ".flag"
            and os.path.basename(x).startswith(pl_name)]


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
        data = prj[CONFIG_KEY]
    except KeyError:
        _LOGGER.debug("Project lacks section '%s', skipping", CONFIG_KEY)
    return data


def partition(items, test):
    """
    Partition items into a pair of disjoint multisets,
    based on the evaluation of each item as input to boolean test function.
    There are a couple of evaluation options here. One builds a mapping
    (assuming each item is hashable) from item to boolean test result, then
    uses that mapping to partition the elements on a second pass.
    The other simply is single-pass, evaluating the function on each item.
    A time-costly function suggests the two-pass, mapping-based approach while
    a large input suggests a single-pass approach to conserve memory. We'll
    assume that the argument is not terribly large and that the function is
    cheap to compute and use a simpler single-pass approach.

    :param Sized[object] items: items to partition
    :param function(object) -> bool test: test to apply to each item to
        perform the partitioning procedure
    :return: list[object], list[object]: partitioned items sequences
    """
    passes, fails = [], []
    _LOGGER.debug("Testing {} items: {}".format(len(items), items))
    for item in items:
        _LOGGER.debug("Testing item {}".format(item))
        group = passes if test(item) else fails
        group.append(item)
    return passes, fails


def sample_folder(prj, sample):
    """
    Get the path to this Project's root folder for the given Sample.

    :param AttributeDict | Project prj: project with which sample is associated
    :param Mapping sample: Sample or sample data for which to get root output
        folder path.
    :return str: this Project's root folder for the given Sample
    """
    return os.path.join(prj.results_folder,
                        sample[SAMPLE_NAME_ATTR])


def get_file_for_project(prj, appendix):
    """
    Create a path to the file for the current project.
    Takes the possibility of amendment being activated at the time

    :param looper.Project prj: project object
    :param str appendix: the appendix of the file to create the path for,
        like 'objs_summary.tsv' for objects summary file
    :return str: path to the file
    """
    fp = os.path.join(prj[CONFIG_KEY][LOOPER_KEY][OUTDIR_KEY], prj[NAME_KEY])
    if hasattr(prj, AMENDMENTS_KEY) and getattr(prj, AMENDMENTS_KEY):
        fp += '_' + '_'.join(getattr(prj, AMENDMENTS_KEY))
    fp += '_' + appendix
    return fp


def jinja_render_cmd_strictly(cmd_template, namespaces):
    """
    Render a command string in the provided namespaces context.

    Strictly, which means that all the requested attributes must be
    available in the namespaces

    :param str cmd_template: command template do be filled in with the
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

    env = jinja2.Environment(undefined=jinja2.StrictUndefined,
                             variable_start_string="{",
                             variable_end_string="}",
                             finalize=_finfun)
    template = env.from_string(cmd_template)
    try:
        rendered = template.render(**namespaces)
    except jinja2.exceptions.UndefinedError:
        _LOGGER.error("Missing sample, project or pipeline attributes"
                      " required by command template: '{}'"
                      .format(cmd_template))
        raise
    _LOGGER.debug("rendered arg str: {}".format(rendered))
    return rendered


def enrich_args_via_dotfile(parser_args, dotfile_path):
    """
    Read in a looper dotfile and set arguments.

    Priority order: CLI > dotfile > parser default

    :param argparse.Namespace parser_args: parsed args by the original parser
    :param str dotfile_path: path to a dotfile to use
    :return argparse.Namespace: selected argument values
    """
    def _read_yaml_file(filepath):
        """
        Read a YAML file

        :param str filepath: path to the file to read
        :return dict: read data
        """
        data = None
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
        return data

    dotfile_args = _read_yaml_file(dotfile_path)
    aux_parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    result = argparse.Namespace()
    for arg in vars(parser_args):
        aux_parser.add_argument('--' + arg)
    cli_args, _ = aux_parser.parse_known_args()
    for dest in vars(parser_args):
        if dest in cli_args:
            r = getattr(cli_args, dest)
        elif dotfile_args is not None and dest in dotfile_args:
            r = dotfile_args[dest]
        else:
            r = getattr(parser_args, dest)
        setattr(result, dest, r)
    return result
