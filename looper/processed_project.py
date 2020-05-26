"""
Processed Project manipulation functions.
Will be moved to a separate package
"""
import os
from logging import getLogger

from eido.const import *
from eido.exceptions import *

from peppy.sample import Sample
from peppy.project import Project

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"

_LOGGER = getLogger(__name__)
PATH_KEY = "path"
THUMB_PATH_KEY = "thumbnail_path"
PATH_LIKE = [PATH_KEY, THUMB_PATH_KEY]


def _get_path_sect_keys(mapping, keys=[PATH_KEY]):
    """
    Get names of subsections in a mapping that contain collection of keys

    :param Mapping mapping: schema subsection to search for paths
    :param  Iterable[str] keys: collection of keys to check for
    :return Iterable[str]: collection of keys to path-like sections
    """
    return [k for k, v in mapping.items() if bool(set(keys) & set(mapping[k]))]


def _populate_paths(object, schema, check_exist):
    """
    Populate path-like object attributes with other object attributes
    based on a defined template, e.g. '/Users/x/test_{name}/{genome}_file.txt'

    :param Mapping object: object with attributes to populate path template with
    :param dict schema: schema with path attributes defined, e.g.
        output of read_schema function
    :param bool check_exist: whether the paths should be check for existence
    :return Mapping: object with path templates populated
    """
    if PROP_KEY not in schema:
        raise EidoSchemaInvalidError("Schema is missing properties section.")
    missing = []
    s = schema[PROP_KEY]
    path_sects = _get_path_sect_keys(s)
    for ps in path_sects:
        templ = s[ps][PATH_KEY]
        try:
            populated = templ.format(**dict(object.items()))
        except Exception as e:
            _LOGGER.warning("Caught exception: {}.\n"
                            "Could not populate path: {}".
                            format(getattr(e, 'message', repr(e)), templ))
        else:
            setattr(object, ps, populated)
            _LOGGER.debug("Path set to: {}".format(object[ps]))
            if check_exist and not os.path.exists(object[ps]):
                missing.append(object[ps])
    if missing:
        raise PathAttrNotFoundError("Path attributes not found:\n- {}".
                                    format("\n- ".join(missing)))


def populate_sample_paths(sample, schema, check_exist=False):
    """
    Populate path-like Sample attributes with other object attributes
    based on a defined template, e.g. '/Users/x/test_{name}/{genome}_file.txt'

    :param peppy.Sample sample: sample to populate paths in
    :param Iterable[dict] schema: schema with path attributes defined, e.g.
        output of read_schema function
    :param bool check_exist: whether the paths should be check for existence
    :return Mapping: Sample with path templates populated
    """
    if not isinstance(sample, Sample):
        raise TypeError("Can only populate paths in peppy.Sample objects")
    # schema = schema[-1]  # use only first schema, in case there are imports
    if PROP_KEY in schema and "samples" in schema[PROP_KEY]:
        _populate_paths(sample, schema[PROP_KEY]["samples"]["items"],
                        check_exist)


def populate_project_paths(project, schema, check_exist=False):
    """
    Populate path-like Project attributes with other object attributes
    based on a defined template, e.g. '/Users/x/test_{name}/{genome}_file.txt'

    :param peppy.Project project: project to populate paths in
    :param dict schema: schema with path attributes defined, e.g.
        output of read_schema function
    :param bool check_exist: whether the paths should be check for existence
    :return Mapping: Project with path templates populated
    """
    if not isinstance(project, Project):
        raise TypeError("Can only populate paths in peppy.Project objects")
    _populate_paths(project, schema, check_exist)


def get_project_outputs(project, schema):
    """
    Get project level outputs with path-like attributes populated with
    project attributes

    :param peppy.Project project:
    :param Iterable[dict] schema:
    :return attmap.PathExAttMap: mapping with populated path-like attributes
    """
    from attmap import PathExAttMap
    # if not any([isinstance(project, Project),
    #             issubclass(type(project), Project)]):
    #     raise TypeError("Can only populate paths in peppy.Project "
    #                     "objects or it subclasses")
    schema = schema[-1]  # use only first schema, in case there are imports
    if PROP_KEY not in schema:
        raise EidoSchemaInvalidError("Schema is missing properties section.")
    res = {}
    s = schema[PROP_KEY]
    path_sects = _get_path_sect_keys(s, keys=PATH_LIKE)
    for ps in path_sects:
        res[ps] = s[ps]
        for p in PATH_LIKE:
            try:
                res[ps][p] = s[ps][p].format(**dict(project.items()))
            except Exception as e:
                _LOGGER.debug("Caught exception: {}.\n Could not populate {} "
                              "path".format(p, str(e)))
    return PathExAttMap(res)
