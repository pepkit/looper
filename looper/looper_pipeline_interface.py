""" PipelineInteface type specific to looper """

import pep

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"



class PipelineInterface(pep.PipelineInterface):
    """ Provide looper-specific functionality on PipelineInterface """


    def uses_looper_args(self, pipeline_name):
        """
        Determine whether the indicated pipeline uses looper arguments.

        :param pipeline_name: name of a pipeline of interest
        :type pipeline_name: str
        :return: whether the indicated pipeline uses looper arguments
        :rtype: bool
        """
        config = self._select_pipeline(pipeline_name)
        return "looper_args" in config and config["looper_args"]
