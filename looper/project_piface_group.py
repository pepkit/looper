""" Group of Project's PipelineInterface instances """

import sys
from logging import getLogger
if sys.version_info < (3, 3):
    from collections import Mapping
else:
    from collections.abc import Mapping
from .pipeline_interface import PipelineInterface, PROTOMAP_KEY
from .const import GENERIC_PROTOCOL_KEY, COLLATORS_KEY, COLLATOR_MAPPINGS_KEY, \
    ALL_COLL_KEYS

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


_LOGGER = getLogger(__name__)


class ProjectPifaceGroup(object):
    """ Collection of PipelineInterface instances and lookup-by-protocol. """

    def __init__(self, piface=None):
        """
        Create the group, either empty or with initial data.
        
        :param str | Mapping | looper.PipelineInterface piface: either pipeline
            interface file, pipeline interface, or interface-defining mapping
        """
        self._interfaces = []
        self._indices_by_protocol = {}
        piface and self.update(piface)

    def __repr__(self):
        msg = type(self).__name__
        try:
            protos = self.protocols
        except (KeyError, AttributeError):
            pass
        else:
            msg += "\n Protocols: {}".format(", ".join(protos))
        try:
            coll_protos = self.collator_protocols
        except (KeyError, AttributeError):
            pass
        else:
            msg += "\n Collator protocols: {}".format(", ".join(coll_protos))
        msg += "\nInterfaces:" + "\n - " + \
               "\n - ".join([pi.__str__() for pi in self._interfaces])
        return msg

    def __eq__(self, other):
        """
        Instances are equivalent iff interfaces and protocol mappings are.
        
        :param looper.project_piface_group.ProjectPifaceGroup other: the group 
            to compare to this one
        :return bool: whether this group is equivalent to the compared one
        """
        return isinstance(other, ProjectPifaceGroup) and \
            self._interfaces == other._interfaces and \
            self._indices_by_protocol == other._indices_by_protocol

    def __ne__(self, other):
        """ Leverage the overridden equivalence operator. """
        return not self == other

    def __getitem__(self, item):
        """
        Retrieve interfaces for given protocol name.
        
        :param str item: name of protocol for which to fetch interfaces.
        :return Iterable[looper.PipelineInterface]: 
        """
        if item not in self._indices_by_protocol.keys():
            if GENERIC_PROTOCOL_KEY in self._indices_by_protocol.keys():
                item = GENERIC_PROTOCOL_KEY
            else:
                _LOGGER.error("Neither '{}' nor '{}' found in known protocols".
                              format(item, GENERIC_PROTOCOL_KEY))
                return []
        return [self._interfaces[i] for i in self._indices_by_protocol[item]]

    def __iter__(self):
        """
        Iteration is over the interfaces.
        
        :return Iterable[looper.PipelineInterface]: iterator over this group's 
            PipelineInterface instances
        """
        return iter(self._interfaces)

    def __len__(self):
        """
        Group size is the number of interfaces.
        
        :return int: number of interfaces in this group
        """
        return sum(1 for _ in iter(self))

    def collators(self, protocol):
        """
        Return all collators stored in this group and associated with the
        selected protocol

        :return Iterable[attamp.PathExtAttMap]: list of collator mappings
        """
        collators = {}
        for interface in self._interfaces:
            if all(e in interface for e in ALL_COLL_KEYS):
                if protocol in interface[COLLATOR_MAPPINGS_KEY]:
                    coll_hits = interface[COLLATOR_MAPPINGS_KEY][protocol]
                elif protocol == GENERIC_PROTOCOL_KEY:
                    coll_hits = interface[COLLATOR_MAPPINGS_KEY].values()
                else:
                    continue
                coll_hits = [coll_hits] \
                    if isinstance(coll_hits, str) else coll_hits
                for match in coll_hits:
                    if match in interface[COLLATORS_KEY]:
                        collators.update({match: interface})
        return collators

    @property
    def protocols(self):
        """
        Get the collection of names of protocols mapping into this group.

        :return list[str]: collection of protocol names that map to at least
            one pipeline represented by an interface in this group
        """
        return [p for p in self._indices_by_protocol]

    @property
    def collator_protocols(self):
        """
        Get the collection of names of collator protocols within this group.

        :return list[str]: collection of protocol names that map to at least
            one pipeline represented by an interface in this group
        """
        return sum([interface[COLLATOR_MAPPINGS_KEY].keys()
                    for interface in self
                    if COLLATOR_MAPPINGS_KEY in interface], [])

    def update(self, piface):
        """
        Add a pipeline interface to this group.
        
        :param str | Mapping | looper.PipelineInterface piface: either pipeline
            interface file, pipeline interface, or interface-defining mapping
        :return looper.project_piface_group.ProjectPifaceGroup: updated instance
        :raise TypeError: if the argument to the piface parameter is neither
            text (filepath) nor a PipelineInterface or Mapping; additional
            exception cases may arise from ensuing attempt to create a
            PipelineInterface from the argument if the argument itself is not
            already a PipelineInterface.
        """
        if isinstance(piface, PipelineInterface):
            _LOGGER.debug("Interface group argument is already an interface.")
        elif isinstance(piface, (str, Mapping)):
            piface = PipelineInterface(piface)
        elif not isinstance(piface, PipelineInterface):
            raise TypeError(
                "Update value must be {obj}-defining filepath or {obj} itself; "
                "got {argtype}".format(
                    obj=PipelineInterface.__name__, argtype=type(piface)))
        assert isinstance(piface, PipelineInterface)
        for curr in self._interfaces:
            if curr == piface:
                _LOGGER.whisper("Found existing {} match: {}".format(
                    PipelineInterface.__class__.__name__, piface))
                break
        else:
            self._interfaces.append(piface)
            i = len(self._interfaces) - 1
            for p in piface[PROTOMAP_KEY]:
                self._indices_by_protocol.setdefault(p, []).append(i)
        return self
