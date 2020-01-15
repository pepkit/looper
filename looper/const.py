""" Shared project constants """

__author__ = "Databio lab"
__email__ = "nathan@code.databio.org"


__all__ = ["BUTTON_APPEARANCE_BY_FLAG", "TABLE_APPEARANCE_BY_FLAG", "NO_DATA_PLACEHOLDER", "OUTKEY",
           "PIPELINE_INTERFACES_KEY", "PIPELINE_REQUIREMENTS_KEY",
           "RESULTS_SUBDIR_KEY", "SUBMISSION_SUBDIR_KEY", "TEMPLATES_DIRNAME"]

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
    Based on the type of the HTML element provided construct the appearence mapping using the template

    :param dict templ: appearance templete to populate
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
PIPELINE_REQUIREMENTS_KEY = "required_executables"
OUTKEY = "outputs"
RESULTS_SUBDIR_KEY = "results_subdir"
SUBMISSION_SUBDIR_KEY = "submission_subdir"
TEMPLATES_DIRNAME = "jinja_templates"
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.svg', '.gif')
PROFILE_COLNAMES = ['pid', 'hash', 'cid', 'runtime', 'mem', 'cmd', 'lock']  # this strongly depends on pypiper's profile.tsv format
