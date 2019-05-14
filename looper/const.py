""" Shared project constants """

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


__all__ = ["APPEARANCE_BY_FLAG", "NO_DATA_PLACEHOLDER", "OUTKEY",
           "PIPELINE_INTERFACES_KEY", "RESULTS_SUBDIR_KEY",
           "SUBMISSION_SUBDIR_KEY", "TEMPLATES_DIRNAME"]

APPEARANCE_BY_FLAG = {
    "completed": {
        "button_class": "table-success",
        "flag": "Completed"
    },
    "running": {
        "button_class": "table-primary",
        "flag": "Running"
    },
    "failed": {
        "button_class": "table-danger",
        "flag": "Failed"
    },
    "parital": {
        "button_class": "table-warning",
        "flag": "Partial"
    },
    "waiting": {
        "button_class": "table-info",
        "flag": "Waiting"
    }
}
NO_DATA_PLACEHOLDER = "NA"
PIPELINE_INTERFACES_KEY = "pipeline_interfaces"
OUTKEY = "outputs"
RESULTS_SUBDIR_KEY = "results_subdir"
SUBMISSION_SUBDIR_KEY = "submission_subdir"
TEMPLATES_DIRNAME = "jinja_templates"
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.svg', '.gif')
PROFILE_COLNAMES = ['pid', 'hash', 'cid', 'runtime', 'mem', 'cmd', 'lock']  # this strongly depends on pypiper's profile.tsv format
