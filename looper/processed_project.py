"""
Processed Project manipulation functions.
These functions are used to process pipestat-compatible schema,
but the report generation approach has changed.
"""

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"

# import os
# from collections.abc import Mapping
# from copy import copy
# from logging import getLogger

# from eido.const import *
# from eido.exceptions import *
# from peppy.project import Project
# from peppy.sample import Sample
# from pipestat import SCHEMA_TYPE_KEY, SchemaError
# from ubiquerg import expandpath

# _LOGGER = getLogger(__name__)
# PATH_KEY = "path"
# THUMB_PATH_KEY = "thumbnail_path"
# PATH_LIKE = [PATH_KEY, THUMB_PATH_KEY]


# def _populate_paths_in_schema(object, schema):
#     """
#     Populate path-like object attributes with other object attributes
#     based on a defined template, e.g. '/Users/x/test_{name}/{genome}_file.txt'

#     :param Mapping object: object with attributes to populate path template with
#     :param dict schema: schema with path attributes defined, e.g.
#         output of read_schema function
#     :return Mapping: object with path templates populated
#     """

#     def _recurse_and_populate(mapping, object):
#         """
#         Recursively populate paths and thumbnail_paths templates in a mapping

#         :param any mapping: a potential mapping with paths to populate
#         :param Mapping object: object with attributes to populate path
#             template with
#         :return any: potentially populated object
#         """
#         if isinstance(mapping, Mapping):
#             for k, v in mapping.items():
#                 if isinstance(v, Mapping):
#                     _recurse_and_populate(v, object)
#                 elif k in PATH_LIKE:
#                     try:
#                         mapping[k] = expandpath(v.format(**dict(object.items())))
#                     except Exception as e:
#                         _LOGGER.warning(
#                             f"Caught exception: {getattr(e, 'message', repr(e))}."
#                             f"\nCould not populate template in schema: {v}"
#                         )
#                     else:
#                         _LOGGER.debug(f"Populated: {mapping[k]}")
#         return mapping

#     for k, v in schema.items():
#         if "value" not in v:
#             continue
#         if SCHEMA_TYPE_KEY not in v:
#             raise SchemaError(
#                 f"'{SCHEMA_TYPE_KEY}' not found in '{k}' section "
#                 f"of the output schema"
#             )
#         schema[k] = _recurse_and_populate(v, object)
#     return schema


# def populate_sample_paths(sample, schema):
#     """
#     Populate path-like Sample attributes with other object attributes
#     based on a defined template, e.g. '/Users/x/test_{name}/{genome}_file.txt'

#     :param peppy.Sample sample: sample to populate paths in
#     :param Iterable[dict] schema: schema with path attributes defined, e.g.
#         output of read_schema function
#     :return Mapping: Sample with path templates populated
#     """
#     # TODO: merge this and 'populate_project_paths' into one?
#     if not isinstance(sample, Sample):
#         raise TypeError("Can only populate paths in peppy.Sample objects")
#     for k, v in _populate_paths_in_schema(sample, copy(schema)).items():
#         if "value" in v:
#             setattr(sample, k, v["value"])
#     return sample


# def populate_project_paths(project, schema):
#     """
#     Populate path-like Project attributes with other object attributes
#     based on a defined template, e.g. '/Users/x/test_{name}/{genome}_file.txt'

#     :param peppy.Project project: project to populate paths in
#     :param dict schema: schema with path attributes defined, e.g.
#         output of read_schema function
#     :return Mapping: Project with path templates populated
#     """
#     for k, v in _populate_paths_in_schema(project.config, copy(schema)).items():
#         if "value" in v:
#             setattr(project, k, v["value"])
#     return project


# def get_project_outputs(project, schema):
#     """
#     Get project level outputs, where the path-like attributes are populated with
#     project attributes

#     :param peppy.Project project: project o get the set of outputs for
#     :param Iterable[dict] schema: pipestat schema to source the outputs for
#     :return attmap.PathExAttMap: mapping with populated path-like attributes
#     """
#     from attmap import PathExAttMap

#     schema = schema[-1]  # use only first schema, in case there are imports
#     populated = populate_project_paths(project, schema)
#     return PathExAttMap({k: getattr(populated, k) for k in schema.keys()})
"""
Processed Project manipulation functions, required pipelines with no pipestat support (old schema)
"""
import os
from logging import getLogger

from eido.const import *
from eido.exceptions import *
from peppy.project import Project
from peppy.sample import Sample

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
            _LOGGER.warning(
                "Caught exception: {}.\n"
                "Could not populate path: {}".format(
                    getattr(e, "message", repr(e)), templ
                )
            )
        else:
            setattr(object, ps, populated)
            _LOGGER.debug("Path set to: {}".format(object[ps]))
            if check_exist and not os.path.exists(object[ps]):
                missing.append(object[ps])
    if missing:
        raise PathAttrNotFoundError(
            "Path attributes not found:\n- {}".format("\n- ".join(missing))
        )


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
        _populate_paths(sample, schema, check_exist)


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
    :return yacman.YAMLConfigManager: mapping with populated path-like attributes
    """
    from yacman import YAMLConfigManager

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
                _LOGGER.debug(
                    "Caught exception: {}.\n Could not populate {} "
                    "path".format(p, str(e))
                )
    return YAMLConfigManager(res)
