""" Shared project constants """

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


__all__ = ["RESULTS_SUBDIR_KEY", "SUBMISSION_SUBDIR_KEY", "TEMPLATES_DIRNAME", "APPEARANCE_BY_FLAG",
           "NO_DATA_PLACEHOLDER"]


RESULTS_SUBDIR_KEY = "results_subdir"
SUBMISSION_SUBDIR_KEY = "submission_subdir"
TEMPLATES_DIRNAME = "jinja_templates"
NO_DATA_PLACEHOLDER = "NA"
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