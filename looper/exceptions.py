""" Exceptions for specific looper issues. """


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"



class JobSubmissionException(Exception):
    """ Error type for when job submission fails. """


    def __init__(self, sub_cmd, script):
        self.script = script
        reason = "Error for command {} and script '{}'".\
                format(sub_cmd, self.script)
        super(JobSubmissionException, self).__init__(reason)
