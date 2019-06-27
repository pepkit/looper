""" Pipeline requirements declaration """

import os
from ubiquerg import expandpath, is_command_callable

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"

__all__ = ["create_pipeline_requirement", "PipelineRequirement",
           "RequiredExecutable", "RequiredPath"]


KEY_EXEC_REQ = "executable"
KEY_FILE_REQ = "file"
KEY_FOLDER_REQ = "folder"


class PipelineRequirement(object):
    """ Requirement that must be satisfied for a pipeline to run. """

    def __init__(self, req, check):
        """
        Create the requirement by specifying name/path and validation function.

        :param str req: the requirement to eventually verify
        :param function(str) check: how to perform the verification
        """
        def _checkattr(trait_attr, trait_name):
            if not hasattr(check, trait_attr):
                raise TypeError("Validator isn't {} ({})".
                                format(trait_name, type(check).__name__))
        self.req = req
        _checkattr("__call__", "callable")
        _checkattr("__hash__", "hashable")
        self.check = check

    def __eq__(self, other):
        """ Equality treats each instance as a product type. """
        return type(self) is type(other) and \
            self.req == other.req and self.check == other.check

    def __hash__(self):
        """ Hash as for product type. """
        return hash((self.req, self.check))

    def __repr__(self):
        """ Print type and requirement value> """
        return "{}: {}".format(type(self).__name__, self.req)

    def _finalize_for_check(self):
        """ Expand any user or env vars in requirement. """
        return expandpath(self.req)

    @property
    def satisfied(self):
        """
        Determine whether the requirement is satisfied acc. to the validation.

        :return bool: whether the requirement is satisfied acc. to the validation
        """
        return self.check(self._finalize_for_check())


class RequiredPath(PipelineRequirement):
    """ A single file or folder requirement """

    def __init__(self, p, check=None, folder=None):
        """
        Create the path requirement by specifying the path and how to verify.

        :param str p: the path on which to base the requirement
        :param function(str) -> bool check: how to verify the requirement;
            required if and only if no folder flag is given
        :param bool folder: whether the path is a folder (not file);
            required if and only if no validation function is provided
        :raise ValueError: if no validation strategy is specified, and no
            argument to folder parameter is given
        :raise TypeError: if no validation strategy is specified, and the
            argument to the folder parameter is not a Boolean
        """
        if (check is not None and folder is not None) or \
                (check is None and folder is None):
            raise ValueError(
                "Either validation function or folder flag--but not both--must "
                "be provided")
        if check is None:
            if type(folder) is not bool:
                raise TypeError("Folder flag must be boolean; got {}".
                                format(type(folder).__name__))
            check = os.path.isdir if folder else os.path.isfile
        super(RequiredPath, self).__init__(p, check)


class RequiredExecutable(PipelineRequirement):
    """ A requirement that should be executable as a command """

    def __init__(self, cmd, check=None):
        """
        Create the requirement by specifying the command and validation.

        :param str cmd: the command requirement to validate as executable
        :param function(str) -> bool check: how to verify that the command
            requirement is in fact satisfied by executability; defaults to
            the callability function in ubiquerg
        """
        super(RequiredExecutable, self).__init__(cmd, check or is_command_callable)


def create_pipeline_requirement(req, typename, **kwargs):
    """
    Create a single requirement instance for a pipeline

    :param str req: name/path that specifices the requirement, e.g. samtools
    :param str typename: keyword indicating the kind of requirement to be
        created
    :param dict kwargs: variable keyword arguments to the RequiredExecutable
        constructor
    :return looper.pipereqs.PipelineRequirement: requirement as named, and
        typed according to the keyword provided
    :raise ValueError: if the given typename is unrecognized, raise ValueError.
    """
    typename = typename or KEY_EXEC_REQ
    if typename == KEY_EXEC_REQ:
        return RequiredExecutable(req, **kwargs)
    if typename == KEY_FILE_REQ:
        return RequiredPath(req, folder=False)
    elif typename == KEY_FOLDER_REQ:
        return RequiredPath(req, folder=True)
    else:
        raise ValueError("Invalid requirement typename: '{}'".format(typename))
