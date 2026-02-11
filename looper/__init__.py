"""Project configuration, particularly for logging.

Project-scope constants may reside here, but more importantly, some setup here
will provide a logging infrastructure for all of the project's modules.
Individual modules and classes may provide separate configuration on a more
local level, but this will at least provide a foundation.

"""

import logmuse

logmuse.init_logger("looper")

from importlib.metadata import version

from .divvy import (
    DEFAULT_COMPUTE_RESOURCES_NAME,
    ComputingConfiguration,
    select_divvy_config,
)
from .divvy import NEW_COMPUTE_KEY as COMPUTE_KEY

__version__ = version("looper")
from .conductor import (
    SubmissionConductor,
    write_submission_yaml,
)
from .pipeline_interface import PipelineInterface
from .plugins import (
    write_custom_template,
    write_sample_yaml,
    write_sample_yaml_cwl,
    write_sample_yaml_prj,
)
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
