""" Looper configuration file manager """
import os
from yacman import YacAttMap, select_config
from logging import getLogger
from ubiquerg import expandpath, is_url

from .const import *
from .pipeline_interface import PipelineInterface

_LOGGER = getLogger(__name__)


class LooperConfig(YacAttMap):
    def __init__(self, filepath=None, entries=None):
        """

        :param str filepath:
        :param Mapping entries:
        """
        super(LooperConfig, self).__init__(filepath=filepath, entries=entries)

    def get_pipeline_interface(self, protocol, raw=False):
        """

        :param str protocol:
        :param bool raw:
        :return PipelineInterface: pipeline interface object matched
            by the specified protocol
        """
        if PROTOMAP_KEY in self:
            if protocol in self[PROTOMAP_KEY]:
                return self[PROTOMAP_KEY][protocol] if raw else \
                    PipelineInterface(config=self[PROTOMAP_KEY][protocol])
        return None

    def add_protocol_mapping(self, protocol, loc):
        """

        :param str protocol: protocol key
        :param str loc: path to an existing pipeline interface file
        """
        path = expandpath(loc)
        if not os.path.exists(path):
            if not is_url(loc):
                _LOGGER.warning("Ignoring nonexistent pipeline interface "
                                "location: {}".format(loc))
                return
        else:
            if protocol in self[PROTOMAP_KEY]:
                _LOGGER.info("Overwriting existing protocol mapping with: "
                             "{}:{}".format(protocol, loc))
            self[PROTOMAP_KEY].update({protocol: loc})


def select_looper_config(filename=None, conf_env_vars=CFG_ENV_VARS, **kwargs):
    """
    Get path to looper configuration file.

    :param str filename: name/path of looper configuration file
    :param Iterable[str] conf_env_vars: names of environment
        variables to consider, a prioritized search list
    :return str: path to looper configuration file
    """
    return select_config(filename, conf_env_vars, **kwargs)

