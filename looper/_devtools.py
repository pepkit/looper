""" Utility functions for internal, developmental use """

import copy
from logmuse import init_logger

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"

__all__ = ["est_log"]


def est_log(**kwargs):
    """
    Establish logging, e.g. for an interactive session.

    :param dict kwargs: keyword arguments for logger setup.
    :return logging.Logger: looper logger
    """
    kwds = copy.copy(kwargs)
    if "name" in kwds:
        print("Ignoring {} and setting fixed values for logging names".
              format(kwds["name"]))
        del kwds["name"]
    init_logger(name="peppy", **kwds)
    return init_logger(name="looper", **kwds)
