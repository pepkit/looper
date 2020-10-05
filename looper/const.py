""" Shared project constants """

import os

__author__ = "Databio lab"
__email__ = "nathan@code.databio.org"

__all__ = [
    "BUTTON_APPEARANCE_BY_FLAG", "TABLE_APPEARANCE_BY_FLAG", "VAR_TEMPL_KEY",
    "ID_COLNAME", "NO_DATA_PLACEHOLDER", "OUTKEY", "ALL_SUBCMD_KEY",
    "OUTDIR_KEY", "LOOPER_KEY", "COMPUTE_KEY", "PIPELINE_INTERFACES_KEY",
    "SIZE_DEP_VARS_KEY", "FLAGS", "DYN_VARS_KEY", "SAMPLE_YAML_PATH_KEY",
    "RESOURCES_KEY", "NOT_SUB_MSG", "EXTRA_KEY", "DEFAULT_CFG_PATH",
    "PIFACE_SCHEMA_SRC", "RESULTS_SUBDIR_KEY", "SUBMISSION_SUBDIR_KEY",
    "TEMPLATES_DIRNAME", "FILE_SIZE_COLNAME", "COMPUTE_PACKAGE_KEY",
    "INPUT_SCHEMA_KEY", "OUTPUT_SCHEMA_KEY", "EXAMPLE_COMPUTE_SPEC_FMT",
    "SAMPLE_PL_KEY", "PROJECT_PL_KEY", "CFG_ENV_VARS", "LOGGING_LEVEL",
    "PIFACE_KEY_SELECTOR", "SUBMISSION_FAILURE_MESSAGE", "IMAGE_EXTS",
    "PROFILE_COLNAMES", "SAMPLE_TOGGLE_ATTR", "TOGGLE_KEY_SELECTOR",
    "LOOPER_DOTFILE_NAME", "POSITIONAL", "EXTRA_PROJECT_CMD_TEMPLATE",
    "EXTRA_SAMPLE_CMD_TEMPLATE", "SELECTED_COMPUTE_PKG", "CLI_PROJ_ATTRS",
    "DOTFILE_CFG_PTH_KEY", "DRY_RUN_KEY", "FILE_CHECKS_KEY", "CLI_KEY",
    "PRE_SUBMIT_HOOK_KEY", "PRE_SUBMIT_PY_FUN_KEY", "PRE_SUBMIT_CMD_KEY",
    "SUBMISSION_YAML_PATH_KEY", "SAMPLE_YAML_PRJ_PATH_KEY",
    "SAMPLE_CWL_YAML_PATH_KEY",
]

FLAGS = ["completed", "running", "failed", "waiting", "partial"]

APPEARANCE_BY_FLAG = {
    "completed": {
        "button_class": "{type}-success",
        "flag": "Completed"
    },
    "running": {
        "button_class": "{type}-primary",
        "flag": "Running"
    },
    "failed": {
        "button_class": "{type}-danger",
        "flag": "Failed"
    },
    "parital": {
        "button_class": "{type}-warning",
        "flag": "Partial"
    },
    "waiting": {
        "button_class": "{type}-info",
        "flag": "Waiting"
    }
}


def _get_apperance_dict(type, templ=APPEARANCE_BY_FLAG):
    """
    Based on the type of the HTML element provided construct the appearence
     mapping using the template

    :param dict templ: appearance template to populate
    :param str type: type of HTML element to populate template with
    :return dict: populated appearance template
    """
    from copy import deepcopy
    ret = deepcopy(templ)
    for flag, app_dict in ret.items():
        for key, app in app_dict.items():
            ret[flag][key] = ret[flag][key].format(type=type)
    return ret


PRE_SUBMIT_HOOK_KEY = "pre_submit"
PRE_SUBMIT_PY_FUN_KEY = "python_functions"
PRE_SUBMIT_CMD_KEY = "command_templates"

LOGGING_LEVEL = "INFO"
CFG_ENV_VARS = ["LOOPER"]
TABLE_APPEARANCE_BY_FLAG = _get_apperance_dict("table")
BUTTON_APPEARANCE_BY_FLAG = _get_apperance_dict("btn btn")
NO_DATA_PLACEHOLDER = "NA"
PIFACE_KEY_SELECTOR = "pipeline_interfaces_key"
PIPELINE_INTERFACES_KEY = "pipeline_interfaces"
RESOURCES_KEY = "resources"
SAMPLE_PL_KEY = "sample_pipeline"
PROJECT_PL_KEY = "project_pipeline"
PIFACE_SCHEMA_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "schemas", "pipeline_interface_schema_{}.yaml")
EXTRA_SAMPLE_CMD_TEMPLATE = "{%- if sample.command_extra is defined %} {sample.command_extra}   {% endif -%}"
EXTRA_PROJECT_CMD_TEMPLATE = "{%- if project.looper.command_extra is defined %} {project.looper.command_extra}{% endif -%}"
DOTFILE_CFG_PTH_KEY = "config_file_path"
INPUT_SCHEMA_KEY = "input_schema"
OUTPUT_SCHEMA_KEY = "output_schema"
SAMPLE_YAML_PATH_KEY = "sample_yaml_path"
SAMPLE_YAML_PRJ_PATH_KEY = "sample_yaml_prj_path"
SUBMISSION_YAML_PATH_KEY = "submission_yaml_path"
SAMPLE_CWL_YAML_PATH_KEY = "sample_cwl_yaml_path"
TOGGLE_KEY_SELECTOR = "toggle_key"
SAMPLE_TOGGLE_ATTR = "toggle"
OUTKEY = "outputs"
VAR_TEMPL_KEY = "var_templates"
COMPUTE_KEY = "compute"
COMPUTE_PACKAGE_KEY = "package"
SIZE_DEP_VARS_KEY = "size_dependent_variables"
DYN_VARS_KEY = "dynamic_variables_command_template"
TEMPLATES_DIRNAME = "jinja_templates"
NOT_SUB_MSG = "> Not submitted: {}"
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.svg', '.gif')
# this strongly depends on pypiper's profile.tsv format
PROFILE_COLNAMES = ['pid', 'hash', 'cid', 'runtime', 'mem', 'cmd', 'lock']

PIPE_ARGS_SECTION = "pipeline_args"
CLI_KEY = "cli"
LOOPER_KEY = "looper"
OUTDIR_KEY = "output_dir"
RESULTS_SUBDIR_KEY = "results_subdir"
SUBMISSION_SUBDIR_KEY = "submission_subdir"
DRY_RUN_KEY = "dry_run"
FILE_CHECKS_KEY = "skip_file_checks"
EXAMPLE_COMPUTE_SPEC_FMT = "k1=v1 k2=v2"
SUBMISSION_FAILURE_MESSAGE = "Cluster resource failure"
LOOPER_DOTFILE_NAME = "." + LOOPER_KEY + ".yaml"
POSITIONAL = ["config_file", "command"]
SELECTED_COMPUTE_PKG = "package"
EXTRA_KEY = "_cli_extra"
ALL_SUBCMD_KEY = "all"
DEFAULT_CFG_PATH = os.path.join(os.getcwd(), LOOPER_DOTFILE_NAME)
CLI_PROJ_ATTRS = [OUTDIR_KEY, TOGGLE_KEY_SELECTOR, SUBMISSION_SUBDIR_KEY, PIPELINE_INTERFACES_KEY,
                  RESULTS_SUBDIR_KEY, PIFACE_KEY_SELECTOR, COMPUTE_PACKAGE_KEY, DRY_RUN_KEY, FILE_CHECKS_KEY]

# resource package TSV-related consts
ID_COLNAME = "id"
FILE_SIZE_COLNAME = "max_file_size"
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.svg', '.gif')
# this strongly depends on pypiper's profile.tsv format
PROFILE_COLNAMES = ['pid', 'hash', 'cid', 'runtime', 'mem', 'cmd', 'lock']
