""" Model the connection between a pipeline and a project or executor. """

import os
import jsonschema
import pandas as pd

from collections import Mapping
from logging import getLogger

from attmap import PathExAttMap as PXAM
from eido import read_schema
from peppy import utils as peputil
from ubiquerg import expandpath, is_url
from yacman import load_yaml

from .const import *
from .exceptions import InvalidResourceSpecificationException

_LOGGER = getLogger(__name__)


@peputil.copy
class PipelineInterface2(PXAM):
    """
    This class parses, holds, and returns information for a yaml file that
    specifies how to interact with each individual pipeline. This
    includes both resources to request for cluster job submission, as well as
    arguments to be passed from the sample annotation metadata to the pipeline

    :param str | Mapping config: path to file from which to parse
        configuration data, or pre-parsed configuration data.
    """
    def __init__(self, config):
        super(PipelineInterface2, self).__init__()

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
        self._expand_pipeline_paths()
        self._validate(PIFACE_SCHEMA_URL)

    def get_pipeline_schema(self, section, schema_key=INPUT_SCHEMA_KEY):
        """
        Get path to the pipeline schema.

        :param str section: pipeline name
        :param str schema_key: where to look for schemas in the pipeline iface
        :return str: absolute path to the pipeline schema file
        """
        schema_source = None
        if schema_key in self[section]:
            schema_source = self[section][schema_key]
        if schema_source:
            _LOGGER.debug("Got schema source: {}".format(schema_source))
            if is_url(schema_source):
                return schema_source
            elif not os.path.isabs(schema_source):
                schema_source = os.path.join(
                    os.path.dirname(self.pipe_iface_file), schema_source)
        return schema_source

    def choose_resource_package(self, section, namespaces, file_size):
        """
        Select resource bundle for given input file size to given pipeline.

        :param str section: name of the section in piface.
        :param float file_size: Size of input data (in gigabytes).
        :param Mapping[Mapping[str]] namespaces: namespaced variables to pass
            as a context for fluid attributes command rendering
        :param bool collate: Whether a collate job is to be submitted (runs on
            the project level, rather that on the sample level)
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
            msg += " for pipeline '{}'".format(section)
            if self.pipe_iface_file is not None:
                msg += " in interface {}".format(self.pipe_iface_file)
            _LOGGER.debug(msg)

        def _load_fluid_attrs(pipeline):
            """
            Render command string (jinja2 template), execute it in a subprocess
            and its result (JSON object) as a dict

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
                from subprocess import check_output, CalledProcessError
                from json import loads
                from .utils import jinja_render_cmd_strictly
                try:
                    cmd = jinja_render_cmd_strictly(
                        cmd_template=pipeline[COMPUTE_KEY][DYN_VARS_KEY],
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

        def _load_size_dep_vars(piface, section):
            """
            Read the resources from a TSV provided in the pipeline interface

            :param looper.PipelineInterface piface: currently processed piface
            :param str section: section of pipeline interface to process
            :return pandas.DataFrame: resources
            """
            df = None
            pipeline = piface[section]
            if COMPUTE_KEY in pipeline \
                    and SIZE_DEP_VARS_KEY in pipeline[COMPUTE_KEY]:
                resources_tsv_path = pipeline[COMPUTE_KEY][SIZE_DEP_VARS_KEY]
                if not os.path.isabs(resources_tsv_path):
                    resources_tsv_path = os.path.join(
                        os.path.dirname(piface.pipe_iface_file),
                        resources_tsv_path)
                df = pd.read_csv(resources_tsv_path, sep='\t', header=0).fillna(0)
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

        fluid_resources = _load_fluid_attrs(self[section])
        if fluid_resources is not None:
            return fluid_resources
        resources_df = _load_size_dep_vars(self, section)
        resources_data = {}
        if resources_df is not None:
            resources = resources_df.to_dict('index')
            try:
                # Sort packages by descending file size minimum to return first
                # package for which given file size satisfies the minimum.
                resource_packages = sorted(
                    resources.items(),
                    key=lambda name_and_data: _file_size_ante(*name_and_data),
                    reverse=True)
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

        if COMPUTE_KEY in self[section]:
            resources_data.update(self[section][COMPUTE_KEY])

        project = namespaces["project"]
        if COMPUTE_KEY in project[LOOPER_KEY] \
                and RESOURCES_KEY in project[LOOPER_KEY][COMPUTE_KEY]:
            # overwrite with values from project.looper.compute.resources
            resources_data.\
                update(project[LOOPER_KEY][COMPUTE_KEY][RESOURCES_KEY])
        return resources_data

    def _expand_pipeline_paths(self):
        """
        Expand path to each pipeline in pipelines and collators subsection
        of pipeline interface
        """
        for section in [SAMPLE_PL_KEY, PROJECT_PL_KEY]:
            raw_path = self[section]["path"]
            split_path = raw_path.split(" ")
            if len(split_path) > 1:
                _LOGGER.warning(
                    "Pipeline path ({}) contains spaces. Use command_template "
                    "section to construct the pipeline command. Using the first"
                    " part as path: {}".format(raw_path, split_path[0]))
            path = split_path[0]
            pipe_path = expandpath(path)
            if not os.path.isabs(pipe_path) and self.pipe_iface_file:
                abs = os.path.join(os.path.dirname(
                    self.pipe_iface_file), pipe_path)
                if os.path.exists(abs):
                    _LOGGER.debug(
                        "Pipeline path relative to pipeline interface"
                        " made absolute: {}".format(abs))
                    self[section]["path"] = abs
                    continue
                _LOGGER.debug("Expanded path: {}".format(pipe_path))
                self[section]["path"] = pipe_path

    def _validate(self, schema_url, exclude_case=False):
        """
        Generic function to validate object against a schema

        :param str schema_url: URL to the schema to validate against
        :param bool exclude_case: whether to exclude validated objects
            from the error. Useful when used ith large projects
        """
        schema = read_schema(schema_url)
        try:
            jsonschema.validate(self, schema)
            _LOGGER.debug("Successfully validated {} against schema: {}".
                          format(self.__class__.__name__, schema))
        except jsonschema.exceptions.ValidationError as e:
            if not exclude_case:
                raise e
            raise jsonschema.exceptions.ValidationError(e.message)