"""
Processed Project manipulation functions.
Will be moved to a separate package
"""
import os
from logging import getLogger
from copy import copy
from collections.abc import Mapping

from eido.const import *
from eido.exceptions import *

from peppy.sample import Sample
from peppy.project import Project

from pipestat import SCHEMA_TYPE_KEY, SchemaError

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"

_LOGGER = getLogger(__name__)
PATH_KEY = "path"
THUMB_PATH_KEY = "thumbnail_path"
PATH_LIKE = [PATH_KEY, THUMB_PATH_KEY]


def _get_path_sect_keys(mapping, keys=[PATH_KEY, THUMB_PATH_KEY]):
    """
    Get names of subsections in a mapping that contain collection of keys

    :param Mapping mapping: schema subsection to search for paths
    :param  Iterable[str] keys: collection of keys to check for
    :return Iterable[str]: collection of keys to path-like sections
    """
    return [k for k, v in mapping.items() if bool(set(keys) & set(mapping[k]))]


def _populate_paths_in_schema(object, schema):
    """
    Populate path-like object attributes with other object attributes
    based on a defined template, e.g. '/Users/x/test_{name}/{genome}_file.txt'

    :param Mapping object: object with attributes to populate path template with
    :param dict schema: schema with path attributes defined, e.g.
        output of read_schema function
    :return Mapping: object with path templates populated
    """
    def _recurse_and_populate(mapping, object):
        """
        Recursively populate paths and thumbnail_paths templates in a mapping

        :param any mapping: a potential mapping with paths to populate
        :param Mapping object: object with attributes to populate path
            template with
        :return any: potentially populated object
        """
        if isinstance(mapping, Mapping):
            for k, v in mapping.items():
                if isinstance(v, Mapping):
                    _recurse_and_populate(v, object)
                elif k in ["path", "thumbnail_path"]:
                    try:
                        mapping[k] = v.format(**dict(object.items()))
                    except Exception as e:
                        _LOGGER.warning(
                            f"Caught exception: {getattr(e, 'message', repr(e))}."
                            f"\nCould not populate template in schema: {v}"
                        )
                    else:
                        _LOGGER.info(f"Populated: {mapping[k]}")
        return mapping

    for k, v in schema.items():
        if "value" not in v:
            continue
        if SCHEMA_TYPE_KEY not in v:
            raise SchemaError(f"'{SCHEMA_TYPE_KEY}' not found in '{k}' section "
                              f"of the output schema")
        schema[k] = _recurse_and_populate(v, object)
    return schema


def populate_sample_paths(sample, schema):
    """
    Populate path-like Sample attributes with other object attributes
    based on a defined template, e.g. '/Users/x/test_{name}/{genome}_file.txt'

    :param peppy.Sample sample: sample to populate paths in
    :param Iterable[dict] schema: schema with path attributes defined, e.g.
        output of read_schema function
    :return Mapping: Sample with path templates populated
    """
    # TODO: merge this and 'populate_project_paths' into one?
    if not isinstance(sample, Sample):
        raise TypeError("Can only populate paths in peppy.Sample objects")
    for k, v in _populate_paths_in_schema(sample, copy(schema)).items():
        if "value" in v:
            setattr(sample, k, v["value"])
    return sample


def populate_project_paths(project, schema):
    """
    Populate path-like Project attributes with other object attributes
    based on a defined template, e.g. '/Users/x/test_{name}/{genome}_file.txt'

    :param peppy.Project project: project to populate paths in
    :param dict schema: schema with path attributes defined, e.g.
        output of read_schema function
    :return Mapping: Project with path templates populated
    """
    if not isinstance(project, Project):
        raise TypeError("Can only populate paths in peppy.Project objects")
    for k, v in _populate_paths_in_schema(project.config, copy(schema)).items():
        if "value" in v:
            setattr(project, k, v["value"])
    return project


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
