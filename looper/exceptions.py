""" Exceptions for specific looper issues. """


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"



_all__ = ["InvalidResourceSpecificationException", "JobSubmissionException",
          "MissingPipelineConfigurationException"]



class InvalidResourceSpecificationException(Exception):
    """ Pipeline interface resources--if present--needs default. """
    def __init__(self, reason):
        super(InvalidResourceSpecificationException, self).__init__(reason)



class JobSubmissionException(Exception):
    """ Error type for when job submission fails. """


    def __init__(self, sub_cmd, script):
        self.script = script
        reason = "Error for command {} and script '{}'".\
                format(sub_cmd, self.script)
        super(JobSubmissionException, self).__init__(reason)


class MissingPipelineConfigurationException(Exception):
    """ A selected pipeline needs configuration data. """
    def __init__(self, pipeline):
        super(MissingPipelineConfigurationException, self).__init__(pipeline)
