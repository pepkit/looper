""" Exceptions for specific looper issues. """

from abc import ABCMeta
import sys
if sys.version_info < (3, 3):
    from collections import Iterable
else:
    from collections.abc import Iterable

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"

_all__ = ["DuplicatePipelineKeyException",
          "InvalidResourceSpecificationException",
          "JobSubmissionException", "LooperError",
          "MissingPipelineConfigurationException",
          "PipelineInterfaceConfigError"]


class LooperError(Exception):
    """ Base type for custom package errors. """
    __metaclass__ = ABCMeta


class DuplicatePipelineKeyException(LooperError):
    """ Duplication of pipeline identifier precludes unique pipeline ref. """
    def __init__(self, key):
        super(DuplicatePipelineKeyException, self).__init__(key)


class InvalidResourceSpecificationException(LooperError):
    """ Pipeline interface resources--if present--needs default. """
    def __init__(self, reason):
        super(InvalidResourceSpecificationException, self).__init__(reason)


class JobSubmissionException(LooperError):
    """ Error type for when job submission fails. """

    def __init__(self, sub_cmd, script):
        self.script = script
        reason = "Error for command {} and script '{}'".\
                format(sub_cmd, self.script)
        super(JobSubmissionException, self).__init__(reason)


class MissingPipelineConfigurationException(LooperError):
    """ A selected pipeline needs configuration data. """
    def __init__(self, pipeline):
        super(MissingPipelineConfigurationException, self).__init__(pipeline)


class PipelineInterfaceConfigError(LooperError):
    """ Error with PipelineInterface config data during construction. """
    def __init__(self, context):
        """
        For exception context, provide message or collection of missing sections.

        :param str | Iterable[str] context:
        """
        if not isinstance(context, str) and isinstance(context, Iterable):
            context = "Missing section(s): {}".format(", ".join(context))
        super(PipelineInterfaceConfigError, self).__init__(context)
