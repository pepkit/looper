""" Shared project constants """

import os

__author__ = "Databio lab"
__email__ = "nathan@code.databio.org"

__all__ = [
    "BUTTON_APPEARANCE_BY_FLAG", "TABLE_APPEARANCE_BY_FLAG",
    "ID_COLNAME", "NO_DATA_PLACEHOLDER", "OUTKEY", "RESULTS_FOLDER_KEY",
    "OUTDIR_KEY", "LOOPER_KEY", "COMPUTE_KEY", "PIPELINE_INTERFACES_KEY",
    "SIZE_DEP_VARS_KEY", "FLAGS", "DYN_VARS_KEY", "SAMPLE_YAML_PATH_KEY",
    "RESOURCES_KEY", "SUBMISSION_FOLDER_KEY", "NOT_SUB_MSG",
    "PIFACE_SCHEMA_SRC", "RESULTS_SUBDIR_KEY", "SUBMISSION_SUBDIR_KEY",
    "TEMPLATES_DIRNAME", "REQUIRED_INPUTS_ATTR_NAME", "FILE_SIZE_COLNAME",
    "COMPUTE_PACKAGE_KEY", "INPUT_SCHEMA_KEY", "OUTPUT_SCHEMA_KEY",
    "EXAMPLE_COMPUTE_SPEC_FMT", "ALL_INPUTS_ATTR_NAME", "SAMPLE_PL_KEY",
    "PROJECT_PL_KEY", "CFG_ENV_VARS", "LOGGING_LEVEL", "PIFACE_KEY_SELECTOR",
    "SUBMISSION_FAILURE_MESSAGE", "IMAGE_EXTS", "PROFILE_COLNAMES"
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
                                 "schemas", "pipeline_interface_schema.yaml")
INPUT_SCHEMA_KEY = "input_schema"
OUTPUT_SCHEMA_KEY = "output_schema"
SAMPLE_YAML_PATH_KEY = "sample_yaml_path"
OUTKEY = "outputs"
RESULTS_SUBDIR_KEY = "results_subdir"
SUBMISSION_SUBDIR_KEY = "submission_subdir"
COMPUTE_KEY = "compute"
COMPUTE_PACKAGE_KEY = "compute_package"
SIZE_DEP_VARS_KEY = "size_dependent_variables"
DYN_VARS_KEY = "dynamic_variables_command_template"
TEMPLATES_DIRNAME = "jinja_templates"
NOT_SUB_MSG = "> Not submitted: {}"
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.svg', '.gif')
PROFILE_COLNAMES = ['pid', 'hash', 'cid', 'runtime', 'mem', 'cmd', 'lock']  # this strongly depends on pypiper's profile.tsv format

REQUIRED_INPUTS_ATTR_NAME = "required_inputs_attr"
ALL_INPUTS_ATTR_NAME = "all_inputs_attr"
PIPE_ARGS_SECTION = "pipeline_args"
RESULTS_FOLDER_KEY = "results_subdir"
LOOPER_KEY = "looper"
SUBMISSION_FOLDER_KEY = "submission_subdir"
OUTDIR_KEY = "output_dir"
EXAMPLE_COMPUTE_SPEC_FMT = "--compute k1=v1,k2=v2"
SUBMISSION_FAILURE_MESSAGE = "Cluster resource failure"

# resource package TSV-related consts
ID_COLNAME = "id"
FILE_SIZE_COLNAME = "max_file_size"
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.svg', '.gif')
PROFILE_COLNAMES = ['pid', 'hash', 'cid', 'runtime', 'mem', 'cmd', 'lock']  # this strongly depends on pypiper's profile.tsv format
