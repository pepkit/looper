""" Model interface between executor, protocols, and pipelines. """

import inspect
import logging
import os
import sys
if sys.version_info < (3, 3):
    from collections import Mapping
else:
    from collections.abc import Mapping

import yaml

from .pipeline_interface import PipelineInterface
from peppy.sample import Sample
from peppy.utils import alpha_cased, copy, is_command_callable, \
    import_from_source, standard_stream_redirector


_LOGGER = logging.getLogger(__name__)



class ProtocolInterface(object):
    """ PipelineInterface and ProtocolMapper for a single pipelines location.

    This class facilitates use of pipelines from multiple locations by a
    single project. Also stored are path attributes with information about
    the location(s) from which the PipelineInterface and ProtocolMapper came.

    :param interface_data_source: location (e.g., code repository) of pipelines
    :type interface_data_source: str | Mapping

    """

    SUBTYPE_MAPPING_SECTION = "sample_subtypes"


    def __init__(self, interface_data_source):
        super(ProtocolInterface, self).__init__()

        if isinstance(interface_data_source, Mapping):
            # TODO: for implementation, we need to determine pipelines_path.
            raise NotImplementedError(
                    "Raw Mapping as source of {} data is not yet supported".
                    format(self.__class__.__name__))
            _LOGGER.debug("Creating %s from raw Mapping",
                          self.__class__.__name__)
            self.source = None
            self.pipe_iface_path = None
            for name, value in self._parse_iface_data(interface_data_source):
                setattr(self, name, value)

        elif os.path.isfile(interface_data_source):
            # Secondary version that passes combined yaml file directly,
            # instead of relying on separate hard-coded config names.
            _LOGGER.debug("Creating %s from file: '%s'",
                          self.__class__.__name__, interface_data_source)
            self.source = interface_data_source
            self.pipe_iface_path = self.source
            self.pipelines_path = os.path.dirname(self.source)

            with open(interface_data_source, 'r') as interface_file:
                iface = yaml.load(interface_file)
            try:
                iface_data = self._parse_iface_data(iface)
            except Exception:
                _LOGGER.error("Error parsing data from pipeline interface "
                              "file: %s", interface_data_source)
                raise
            for name, value in iface_data:
                setattr(self, name, value)

        elif os.path.isdir(interface_data_source):
            _LOGGER.debug("Creating %s from files in directory: '%s'",
                          self.__class__.__name__, interface_data_source)
            self.source = interface_data_source
            self.pipe_iface_path = os.path.join(
                    self.source, "config", "pipeline_interface.yaml")
            self.pipelines_path = os.path.join(self.source, "pipelines")

            self.pipe_iface = PipelineInterface(self.pipe_iface_path)
            self.protomap = ProtocolMapper(os.path.join(
                    self.source, "config", "protocol_mappings.yaml"))

        else:
            raise ValueError("Alleged pipelines location '{}' exists neither "
                             "as a file nor as a folder.".
                             format(interface_data_source))


    def __repr__(self):
        return "ProtocolInterface from '{}'".format(self.source or "Mapping")




@copy
class ProtocolMapper(Mapping):
    """
    Map protocol/library name to pipeline key(s). For example, "WGBS" --> wgbs.

    :param mappings_input: data encoding correspondence between a protocol
        name and pipeline(s)
    :type mappings_input: str | Mapping

    """
    def __init__(self, mappings_input):
        if isinstance(mappings_input, Mapping):
            mappings = mappings_input
            self.filepath = None
        else:
            # Parse file mapping protocols to pipeline(s).
            with open(mappings_input, 'r') as mapfile:
                mappings = yaml.load(mapfile)
            self.filepath = mappings_input
        self.mappings = {alpha_cased(k): v for k, v in mappings.items()}


    def __getitem__(self, protocol_name):
        """ Indexing syntax is on protocol name. """
        return self.mappings[protocol_name]

    def __iter__(self):
        """ Iteration is over the protocol names. """
        return iter(self.mappings)

    def __len__(self):
        """ The interface size is the number of protocol names supported. """
        return len(self.mappings)


    def __repr__(self):
        source = self.filepath or "mapping"
        num_protocols = len(self.mappings)
        protocols = ", ".join(self.mappings.keys())
        return "{} from {}, with {} protocol(s): {}".format(
                self.__class__.__name__, source, num_protocols, protocols)
