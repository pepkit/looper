""" Shared project constants """

__author__ = "Databio lab"
__email__ = "nathan@code.databio.org"


__all__ = [
    "BUTTON_APPEARANCE_BY_FLAG", "TABLE_APPEARANCE_BY_FLAG", "ID_COLNAME",
    "NO_DATA_PLACEHOLDER", "OUTKEY", "RESULTS_FOLDER_KEY", "OUTDIR_KEY",
    "LOOPER_KEY", "COMPUTE_KEY", "PIPELINE_INTERFACES_KEY", "SIZE_DEP_VARS_KEY",
    "PIPELINE_REQUIREMENTS_KEY", "FLAGS", "PIPE_ARGS_SECTION", "FLUID_ATTRS_KEY",
    "SUBMISSION_FOLDER_KEY", "GENERIC_PROTOCOL_KEY", "NOT_SUB_MSG",
    "RESULTS_SUBDIR_KEY", "SUBMISSION_SUBDIR_KEY", "TEMPLATES_DIRNAME",
    "SAMPLE_YAML_FILE_KEY", "SAMPLE_YAML_EXT", "SAMPLE_EXECUTION_TOGGLE",
    "VALID_READ_TYPES", "REQUIRED_INPUTS_ATTR_NAME", "ALL_INPUTS_ATTR_NAME",
    "FILE_SIZE_COLNAME", "COMPUTE_PACKAGE_KEY", "COLLATORS_KEY"
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


TABLE_APPEARANCE_BY_FLAG = _get_apperance_dict("table")
BUTTON_APPEARANCE_BY_FLAG = _get_apperance_dict("btn btn")
NO_DATA_PLACEHOLDER = "NA"
PIPELINE_INTERFACES_KEY = "pipeline_interfaces"
COLLATORS_KEY = "collators"
PIPELINE_REQUIREMENTS_KEY = "required_executables"
OUTKEY = "outputs"
RESULTS_SUBDIR_KEY = "results_subdir"
SUBMISSION_SUBDIR_KEY = "submission_subdir"
COMPUTE_KEY = "compute"
COMPUTE_PACKAGE_KEY = "compute_package"
SIZE_DEP_VARS_KEY = "size_dependent_variables"
FLUID_ATTRS_KEY = "fluid_attributes"
TEMPLATES_DIRNAME = "jinja_templates"
NOT_SUB_MSG = "> Not submitted: {}"
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.svg', '.gif')
PROFILE_COLNAMES = ['pid', 'hash', 'cid', 'runtime', 'mem', 'cmd', 'lock']  # this strongly depends on pypiper's profile.tsv format

SAMPLE_YAML_FILE_KEY = "yaml_file"
SAMPLE_YAML_EXT = ".yaml"
SAMPLE_EXECUTION_TOGGLE = "toggle"
VALID_READ_TYPES = ["single", "paired"]
REQUIRED_INPUTS_ATTR_NAME = "required_inputs_attr"
ALL_INPUTS_ATTR_NAME = "all_inputs_attr"
PIPE_ARGS_SECTION = "pipeline_args"
RESULTS_FOLDER_KEY = "results_subdir"
LOOPER_KEY = "looper"
SUBMISSION_FOLDER_KEY = "submission_subdir"
OUTDIR_KEY = "output_dir"
GENERIC_PROTOCOL_KEY = "*"

# resource package TSV-related consts
ID_COLNAME = "id"
FILE_SIZE_COLNAME = "max_file_size"
