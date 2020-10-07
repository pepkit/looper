""" Model the connection between a pipeline and a project or executor. """

import os
import jsonschema
import pandas as pd

from collections import Mapping
from logging import getLogger
from warnings import warn

from attmap import PathExAttMap as PXAM
from eido import read_schema
from peppy import utils as peputil
from ubiquerg import expandpath, is_url
from yacman import load_yaml

from .const import *
from .utils import jinja_render_template_strictly
from .exceptions import InvalidResourceSpecificationException

__author__ = "Michal Stolarczyk"
__email__ = "michal@virginia.edu"

_LOGGER = getLogger(__name__)


@peputil.copy
class PipelineInterface(PXAM):
    """
    This class parses, holds, and returns information for a yaml file that
    specifies how to interact with each individual pipeline. This
    includes both resources to request for cluster job submission, as well as
    arguments to be passed from the sample annotation metadata to the pipeline

    :param str | Mapping config: path to file from which to parse
        configuration data, or pre-parsed configuration data.
    :param str pipeline_type: type of the pipeline,
        must be either 'sample' or 'project'.
    """
    def __init__(self, config, pipeline_type=None):
        super(PipelineInterface, self).__init__()

        if isinstance(config, Mapping):
            self.pipe_iface_file = None
            self.source = None
        else:
            _LOGGER.debug("Reading {} from: {}".
                          format(self.__class__.__name__, config))
            self.pipe_iface_file = config
            self.source = config
            config = load_yaml(config)
        self.update(config)
        self._validate(PIFACE_SCHEMA_SRC, flavor=pipeline_type)
        if "path" in self:
            warn(message="'path' specification as a top-level pipeline "
                         "interface key is deprecated and will be removed with "
                         "the next release. Please use 'paths' section "
                         "from now on.", category=DeprecationWarning)
            self._expand_paths(["path"])
        self._expand_paths(["compute", "dynamic_variables_script_path"])

    def render_var_templates(self, namespaces):
        """
        Render path templates under 'var_templates' in this pipeline interface.

        :param dict namespaces: namespaces to use for rendering
        """
        if VAR_TEMPL_KEY in self:
            for k, v in self[VAR_TEMPL_KEY].items():
                setattr(self[VAR_TEMPL_KEY], k,
                        jinja_render_template_strictly(v, namespaces))
        else:
            _LOGGER.debug(f"'{VAR_TEMPL_KEY}' section not found in the "
                          f"{self.__class__.__name__} object.")

    def get_pipeline_schemas(self, schema_key=INPUT_SCHEMA_KEY):
        """
        Get path to the pipeline schema.

        :param str schema_key: where to look for schemas in the pipeline iface
        :return str: absolute path to the pipeline schema file
        """
        schema_source = None
        if schema_key in self:
            schema_source = self[schema_key]
        if schema_source:
            _LOGGER.debug("Got schema source: {}".format(schema_source))
            if is_url(schema_source):
                return schema_source
            elif not os.path.isabs(schema_source):
                schema_source = os.path.join(
                    os.path.dirname(self.pipe_iface_file), schema_source)
        return schema_source

    def choose_resource_package(self, namespaces, file_size):
        """
        Select resource bundle for given input file size to given pipeline.

        :param float file_size: Size of input data (in gigabytes).
        :param Mapping[Mapping[str]] namespaces: namespaced variables to pass
            as a context for fluid attributes command rendering
        :return MutableMapping: resource bundle appropriate for given pipeline,
            for given input file size
        :raises ValueError: if indicated file size is negative, or if the
            file size value specified for any resource package is negative
        :raises InvalidResourceSpecificationException: if no default
            resource package specification is provided
        """
        def _file_size_ante(name, data):
            # Retrieve this package's minimum file size.
            # Retain backwards compatibility while enforcing key presence.
            try:
                fsize = float(data[FILE_SIZE_COLNAME])
            except KeyError:
                raise InvalidResourceSpecificationException(
                    "Required column '{}' does not exist in resource "
                    "specification TSV.".format(FILE_SIZE_COLNAME))
            # Negative file size is illogical and problematic for comparison.
            if fsize < 0:
                raise InvalidResourceSpecificationException(
                    "Found negative value () in '{}' column; package '{}'".
                        format(fsize, FILE_SIZE_COLNAME, name)
                )
            return fsize

        def _notify(msg):
            msg += " for pipeline"
            if self.pipe_iface_file is not None:
                msg += " in interface {}".format(self.pipe_iface_file)
            _LOGGER.debug(msg)

        def _load_dynamic_vars(pipeline):
            """
            Render command string (jinja2 template), execute it in a subprocess
            and return its result (JSON object) as a dict

            :param Mapping pipeline: pipeline dict
            :return Mapping: a dict with attributes returned in the JSON
                by called command
            """
            def _log_raise_latest():
                """ Log error info and raise latest handled exception """
                _LOGGER.error(
                    "Could not retrieve JSON via command: '{}'".format(
                        pipeline[COMPUTE_KEY][DYN_VARS_KEY]))
                raise
            json = None
            if COMPUTE_KEY in pipeline \
                    and DYN_VARS_KEY in pipeline[COMPUTE_KEY]:
                from warnings import warn
                from subprocess import check_output, CalledProcessError
                from json import loads
                from .utils import jinja_render_template_strictly
                warn(message="'dynamic_variables_command_template' feature is "
                             "deprecated and will be removed with the next "
                             "release. Please use 'pre_submit' feature from "
                             "now on.",
                     category=DeprecationWarning)
                try:
                    cmd = jinja_render_template_strictly(
                        template=pipeline[COMPUTE_KEY][DYN_VARS_KEY],
                        namespaces=namespaces
                    )
                    json = loads(check_output(cmd, shell=True))
                except CalledProcessError as e:
                    print(e.output)
                    _log_raise_latest()
                except Exception:
                    _log_raise_latest()
                else:
                    _LOGGER.debug(
                        "Loaded resources from JSON returned by a command for"
                        " pipeline '{}':\n{}".format(self.pipeline_name, json))
            return json

        def _load_size_dep_vars(piface):
            """
            Read the resources from a TSV provided in the pipeline interface

            :param looper.PipelineInterface piface: currently processed piface
            :param str section: section of pipeline interface to process
            :return pandas.DataFrame: resources
            """
            df = None
            if COMPUTE_KEY in piface \
                    and SIZE_DEP_VARS_KEY in piface[COMPUTE_KEY]:
                resources_tsv_path = piface[COMPUTE_KEY][SIZE_DEP_VARS_KEY]
                if not os.path.isabs(resources_tsv_path):
                    resources_tsv_path = os.path.join(
                        os.path.dirname(piface.pipe_iface_file),
                        resources_tsv_path)
                df = pd.read_csv(resources_tsv_path, sep='\t', header=0).\
                    fillna(float("inf"))
                df[ID_COLNAME] = df.index
                df.set_index(ID_COLNAME)
                _LOGGER.debug("Loaded resources ({}) for pipeline '{}':\n{}".
                              format(resources_tsv_path, piface.pipeline_name, df))
            else:
                _notify("No '{}' defined".format(SIZE_DEP_VARS_KEY))
            return df

        # Ensure that we have a numeric value before attempting comparison.
        file_size = float(file_size)
        assert file_size >= 0, ValueError("Attempted selection of resource "
                                         "package for negative file size: {}".
                                         format(file_size))

        fluid_resources = _load_dynamic_vars(self)
        if fluid_resources is not None:
            return fluid_resources
        resources_df = _load_size_dep_vars(self)
        resources_data = {}
        if resources_df is not None:
            resources = resources_df.to_dict('index')
            try:
                # Sort packages by descending file size minimum to return first
                # package for which given file size satisfies the minimum.
                resource_packages = sorted(
                    resources.items(),
                    key=lambda name_and_data: _file_size_ante(*name_and_data),
                    reverse=False)
            except ValueError:
                _LOGGER.error("Unable to use file size to prioritize "
                              "resource packages: {}".format(resources))
                raise

            # choose minimally-sufficient package
            for rp_name, rp_data in resource_packages:
                size_ante = _file_size_ante(rp_name, rp_data)
                if file_size <= size_ante:
                    _LOGGER.debug(
                        "Selected '{}' package with file size {}Gb for file "
                        "of size {}Gb.".format(rp_name, size_ante, file_size))
                    _LOGGER.debug("Selected resource package data:\n{}".
                                  format(rp_data))
                    resources_data = rp_data
                    break

        if COMPUTE_KEY in self:
            resources_data.update(self[COMPUTE_KEY])
        project = namespaces["project"]
        if LOOPER_KEY in project and COMPUTE_KEY in project[LOOPER_KEY] \
                and RESOURCES_KEY in project[LOOPER_KEY][COMPUTE_KEY]:
            # overwrite with values from project.looper.compute.resources
            resources_data.\
                update(project[LOOPER_KEY][COMPUTE_KEY][RESOURCES_KEY])
        return resources_data

    def _expand_paths(self, keys):
        """
        Expand paths defined in the pipeline interface file

        :param list keys: list of keys resembling the nested structure to get
            to the pipeline interface attributre to expand
        """
        def _get_from_dict(map, attrs):
            """
            Get value from a possibly nested mapping using a list of its attributes

            :param collections.Mapping map: mapping to retrieve values from
            :param Iterable[str] attrs: a list of attributes
            :return: value found in the the requested attribute or
                None if one of the keys does not exist
            """
            for a in attrs:
                try:
                    map = map[a]
                except KeyError:
                    return
            return map

        def _set_in_dict(map, attrs, val):
            """
            Set value in a mapping, creating a possibly nested structure

            :param collections.Mapping map: mapping to retrieve values from
            :param Iterable[str] attrs: a list of attributes
            :param val: value to set
            :return: value found in the the requested attribute or
                None if one of the keys does not exist
            """
            for a in attrs:
                if a == attrs[-1]:
                    map[a] = val
                    break
                map.setdefault(a, PXAM())
                map = map[a]

        raw_path = _get_from_dict(self, keys)
        if not raw_path:
            return
        split_path = raw_path.split(" ")
        if len(split_path) > 1:
            _LOGGER.warning(
                "Path ({}) contains spaces. Using the first part as path: {}".
                    format(raw_path, split_path[0]))
        path = split_path[0]
        pipe_path = expandpath(path)
        if not os.path.isabs(pipe_path) and self.pipe_iface_file:
            abs = os.path.join(os.path.dirname(
                self.pipe_iface_file), pipe_path)
            if os.path.exists(abs):
                _LOGGER.debug(
                    "Path relative to pipeline interface made absolute: {}".
                        format(abs))
                _set_in_dict(self, keys, abs)
                return
            _LOGGER.debug("Expanded path: {}".format(pipe_path))
            _set_in_dict(self, keys, pipe_path)

    def _validate(self, schema_src, exclude_case=False, flavor=None):
        """
        Generic function to validate object against a schema

        :param str schema_src: schema source to validate against, URL or path
        :param bool exclude_case: whether to exclude validated objects
            from the error. Useful when used ith large projects
        :param str flavor: type of the pipeline schema to use
        """
        schema_source = schema_src.format(flavor if flavor else "generic")
        schemas = read_schema(schema_source)
        for schema in schemas:
            try:
                jsonschema.validate(self, schema)
                _LOGGER.debug("Successfully validated {} against schema: {}".
                              format(self.__class__.__name__, schema_source))
            except jsonschema.exceptions.ValidationError as e:
                if not exclude_case:
                    raise e
                raise jsonschema.exceptions.ValidationError(e.message)