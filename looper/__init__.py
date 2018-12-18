"""Project configuration, particularly for logging.

Project-scope constants may reside here, but more importantly, some setup here
will provide a logging infrastructure for all of the project's modules.
Individual modules and classes may provide separate configuration on a more
local level, but this will at least provide a foundation.

"""

import logging
import os
from sys import stdout

from .pipeline_interface import PipelineInterface
from ._version import __version__

# Not used here, but make this the main import interface between peppy and
# looper, so that other modules within this package need not worry about
# the locations of some of the peppy declarations. Effectively, concentrate
# the connection between peppy and looper here, to the extent possible.
from peppy import \
    COMPUTE_SETTINGS_VARNAME, FLAGS, IMPLICATIONS_DECLARATION, \
    SAMPLE_INDEPENDENT_PROJECT_SECTIONS, SAMPLE_NAME_COLNAME


__classes__ = ["PipelineInterface"]


GENERIC_PROTOCOL_KEY = "*"
LOGGING_LEVEL = "INFO"
LOGGING_LOCATIONS = (stdout, )

# Default user logging format is simple
DEFAULT_LOGGING_FMT = "%(message)s"
# Developer logger format is more information-rich
DEV_LOGGING_FMT = "%(module)s:%(lineno)d (%(funcName)s) [%(levelname)s] > %(message)s "



def setup_looper_logger(level, additional_locations=None, devmode=False):
    """
    Establish a logger for a looper CLI program.

    This configures a logger to provide information about a looper program's
    execution. Verbosity, destination(s) for messages, and message text
    format are controlled by the arguments' values. This is also used by
    looper's test suite.

    :param int | str level: logging level
    :param tuple(str | FileIO[str]) additional_locations: supplementary
        destination(s) to which to ship logs
    :param bool devmode: whether to use developer logging config
    :return logging.Logger: project-root logger
    """

    logging.addLevelName(5, "VERY_FINE")

    fmt = DEV_LOGGING_FMT if devmode else DEFAULT_LOGGING_FMT

    # Establish the logger.
    LOOPER_LOGGER = logging.getLogger()
    # First remove any previously-added handlers
    LOOPER_LOGGER.handlers = []
    LOOPER_LOGGER.propagate = False

    # Handle int- or text-specific logging level.
    try:
        level = int(level)
    except ValueError:
        level = level.upper()

    try:
        LOOPER_LOGGER.setLevel(level)
    except Exception:
        logging.error("Can't set logging level to %s; instead using: '%s'",
                      str(level), str(LOGGING_LEVEL))
        level = LOGGING_LEVEL
        LOOPER_LOGGER.setLevel(level)

    # Process any additional locations.
    locations_exception = None
    where = LOGGING_LOCATIONS
    if additional_locations:
        if isinstance(additional_locations, str):
            additional_locations = (additional_locations, )
        try:
            where = LOGGING_LOCATIONS + tuple(additional_locations)
        except TypeError as e:
            locations_exception = e
    if locations_exception:
        logging.warn("Could not interpret {} as supplementary root logger "
                     "target destinations; using {} as root logger location(s)".
                     format(additional_locations, LOGGING_LOCATIONS))

    # Add the handlers.
    formatter = logging.Formatter(fmt=(fmt or DEFAULT_LOGGING_FMT))

    for loc in where:
        if not loc:
            continue
        if isinstance(loc, str):
            # File destination
            dirpath = os.path.abspath(os.path.dirname(loc))
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            handler_type = logging.FileHandler
        elif hasattr(loc, "write"):
            # Stream destination
            handler_type = logging.StreamHandler
        else:
            # Strange supplementary destination
            logging.info("{} as logs destination appears to be neither "
                         "a filepath nor a stream.".format(loc))
            continue

        if handler_type is logging.FileHandler:
            handler = handler_type(loc, mode='w')
        else:
            handler = handler_type(loc)

        handler.setLevel(level)
        handler.setFormatter(formatter)
        LOOPER_LOGGER.addHandler(handler)

    return LOOPER_LOGGER
