"""Project configuration, particularly for logging.

Project-scope constants may reside here, but more importantly, some setup here
will provide a logging infrastructure for all of the project's modules.
Individual modules and classes may provide separate configuration on a more
local level, but this will at least provide a foundation.

"""

import logmuse

logmuse.init_logger("looper")

from .divvy import ComputingConfiguration, select_divvy_config
from .divvy import DEFAULT_COMPUTE_RESOURCES_NAME
from .divvy import NEW_COMPUTE_KEY as COMPUTE_KEY

from ._version import __version__
from .conductor import (
    SubmissionConductor,
    write_submission_yaml,
)
from .plugins import (
    write_sample_yaml,
    write_sample_yaml_cwl,
    write_sample_yaml_prj,
    write_custom_template,
)
from .const import *
from .pipeline_interface import PipelineInterface
from .project import Project

# Not used here, but make this the main import interface between peppy and
# looper, so that other modules within this package need not worry about
# the locations of some of the peppy declarations. Effectively, concentrate
# the connection between peppy and looper here, to the extent possible.

__all__ = [
    "Project",
    "PipelineInterface",
    "SubmissionConductor",
    "ComputingConfiguration",
    "select_divvy_config",
]
