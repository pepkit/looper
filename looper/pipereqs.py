""" Pipeline requirements declaration """

import os
from ubiquerg import expandpath, is_command_callable

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"

__all__ = ["create_pipeline_requirement", "PipelineRequirement",
           "RequiredExecutable", "RequiredPath"]


class PipelineRequirement(object):

    def __init__(self, req, check):
        def _checkattr(trait_attr, trait_name):
            if not hasattr(check, trait_attr):
                raise TypeError("Validator isn't {} ({})".
                                format(trait_name, type(check).__name__))
        self.req = req
        _checkattr("__call__", "callable")
        _checkattr("__hash__", "hashable")
        self.check = check

    def __eq__(self, other):
        return type(self) is type(other) and \
               self.req == other.req and self.check == other.check

    def __hash__(self):
        return hash((self.req, self.check))

    def __repr__(self):
        return "{}: {}".format(type(self).__name__, self.req)

    def _finalize_for_check(self):
        return expandpath(self.req)

    @property
    def satisfied(self):
        return self.check(self._finalize_for_check())


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

    def __init__(self, cmd, check=None):
        super(RequiredExecutable, self).__init__(cmd, check or is_command_callable)


def create_pipeline_requirement(req, typename, **kwargs):
    typename = typename or "executable"
    if typename == "executable":
        return RequiredExecutable(req, **kwargs)
    if typename == "file":
        return RequiredPath(req, folder=False)
    elif typename == "folder":
        return RequiredPath(req, folder=True)
    else:
        raise ValueError("Invalid requirement typename: '{}'".format(typename))
