"""
Processed Project manipulation functions.
Will be moved to a separate package
"""
import os
from collections.abc import Mapping
from copy import copy
from logging import getLogger

from eido.const import *
from eido.exceptions import *
from peppy.project import Project
from peppy.sample import Sample
from pipestat import SCHEMA_TYPE_KEY, SchemaError
from ubiquerg import expandpath

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"

_LOGGER = getLogger(__name__)
PATH_KEY = "path"
THUMB_PATH_KEY = "thumbnail_path"
PATH_LIKE = [PATH_KEY, THUMB_PATH_KEY]


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
                elif k in PATH_LIKE:
                    try:
                        mapping[k] = expandpath(v.format(**dict(object.items())))
                    except Exception as e:
                        _LOGGER.warning(
                            f"Caught exception: {getattr(e, 'message', repr(e))}."
                            f"\nCould not populate template in schema: {v}"
                        )
                    else:
                        _LOGGER.debug(f"Populated: {mapping[k]}")
        return mapping

    for k, v in schema.items():
        if "value" not in v:
            continue
        if SCHEMA_TYPE_KEY not in v:
            raise SchemaError(
                f"'{SCHEMA_TYPE_KEY}' not found in '{k}' section "
                f"of the output schema"
            )
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
    for k, v in _populate_paths_in_schema(project.config, copy(schema)).items():
        if "value" in v:
            setattr(project, k, v["value"])
    return project


def get_project_outputs(project, schema):
    """
    Get project level outputs, where the path-like attributes are populated with
    project attributes

    :param peppy.Project project: project o get the set of outputs for
    :param Iterable[dict] schema: pipestat schema to source the outputs for
    :return attmap.PathExAttMap: mapping with populated path-like attributes
    """
    from attmap import PathExAttMap

    schema = schema[-1]  # use only first schema, in case there are imports
    populated = populate_project_paths(project, schema)
    return PathExAttMap({k: getattr(populated, k) for k in schema.keys()})
