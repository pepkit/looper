""" Pipeline requirements declaration """

import os

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"

__all__ = ["create_pipeline_requirement", "PipelineRequirement",
           "RequiredExecutable", "RequiredPath"]


class PipelineRequirement(object):

    def __init__(self, req, check):
        self.req = req
        if not hasattr(check, "__call__"):
            raise TypeError("Validator isn't callable ({})".
                            format(type(check).__name__))
        self.check = check

    @property
    def satisfied(self):
        return self.check(self.req)


class RequiredPath(PipelineRequirement):

    def __init__(self, p, check=None, folder=None):
        if check is None:
            if folder in [False, True]:
                check = os.path.isdir if folder else os.path.isfile
            else:
                raise ValueError(
                    "If no validation function is provided, folder argument "
                    "must be boolean; got {} ({})".format(
                        folder, type(folder).__name__))
        super(RequiredPath, self).__init__(p, check)


class RequiredExecutable(PipelineRequirement):

    def __init__(self, cmd, check=None, locs=None):
        if check is None:
            locs = locs or [os.getenv("PATH")]
            check = lambda c: any(c in l for l in locs)
        super(RequiredExecutable, self).__init__(cmd, check)



def create_pipeline_requirement(req, typename, **kwargs):
    if typename == "executable":
        return RequiredExecutable(req, **kwargs)
    if typename == "file":
        return RequiredPath(req, folder=False)
    elif typename == "folder":
        return RequiredPath(req, folder=True)
    else:
        raise ValueError("Invalid requirement typename: '{}'".format(typename))
