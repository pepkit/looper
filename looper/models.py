"""
Project Models
=======================

Workflow explained:
    - Create a Project object
        - Samples are created and added to project (automatically)

In the process, Models will check:
    - Project structure (created if not existing)
    - Existence of csv sample sheet with minimal fields
    - Constructing a path to a sample's input file and checking for its existence
    - Read type/length of samples (optionally)

Example:

.. code-block:: python

    from models import Project
    prj = Project("config.yaml")
    # that's it!

Explore:

.. code-block:: python

    # see all samples
    prj.samples
    # get fastq file of first sample
    prj.samples[0].fastq
    # get all bam files of WGBS samples
    [s.mapped for s in prj.samples if s.protocol == "WGBS"]

    prj.metadata.results  # results directory of project
    # export again the project's annotation
    prj.sheet.write(os.path.join(prj.metadata.output_dir, "sample_annotation.csv"))

    # project options are read from the config file
    # but can be changed on the fly:
    prj = Project("test.yaml")
    # change options on the fly
    prj.config["merge_technical"] = False
    # annotation sheet not specified initially in config file
    prj.add_sample_sheet("sample_annotation.csv")

"""

# TODO: perhaps update examples based on removal of guarantee of some attrs.
# TODO: the examples changes would involve library and output_dir.

from collections import \
    Counter, defaultdict, Iterable, Mapping, MutableMapping, namedtuple, \
    OrderedDict as _OrderedDict
from functools import partial
import glob
import inspect
import itertools
import logging
from operator import itemgetter
import os as _os
import sys
if sys.version_info < (3, 0):
    from urlparse import urlparse
else:
    from urllib.parse import urlparse
import warnings

import pandas as _pd
import yaml

from . import IMPLICATIONS_DECLARATION, SAMPLE_NAME_COLNAME
from .utils import \
    add_project_sample_constants, alpha_cased, check_bam, check_fastq, \
    expandpath, get_file_size, grab_project_data, import_from_source, \
    is_command_callable, parse_ftype, partition, sample_folder, \
    standard_stream_redirector


# TODO: decide if we want to denote functions for export.
__functions__ = []
__classes__ = ["AttributeDict", "PipelineInterface", "Project",
               "ProtocolInterface", "ProtocolMapper", "Sample"]
__all__ = __functions__ + __classes__


COMPUTE_SETTINGS_VARNAME = "PEPENV"
DEFAULT_COMPUTE_RESOURCES_NAME = "default"
DATA_SOURCE_COLNAME = "data_source"
SAMPLE_ANNOTATIONS_KEY = "sample_annotation"
DATA_SOURCES_SECTION = "data_sources"
SAMPLE_EXECUTION_TOGGLE = "toggle"
COL_KEY_SUFFIX = "_key"
VALID_READ_TYPES = ["single", "paired"]
REQUIRED_INPUTS_ATTR_NAME = "required_inputs_attr"
ALL_INPUTS_ATTR_NAME = "all_inputs_attr"

ATTRDICT_METADATA = {"_force_nulls": False, "_attribute_identity": False}

_LOGGER = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    _LOGGER.addHandler(logging.NullHandler())



def check_sheet(sample_file, dtype=str):
    """
    Check if csv file exists and has all required columns.

    :param str sample_file: path to sample annotations file.
    :param type dtype: data type for CSV read.
    :raises IOError: if given annotations file can't be read.
    :raises ValueError: if required column(s) is/are missing.
    """
    # Although no null value replacements or supplements are being passed,
    # toggling the keep_default_na value to False solved an issue with 'nan'
    # and/or 'None' as an argument for an option in the pipeline command
    # that's generated from a Sample's attributes.
    #
    # See https://github.com/epigen/looper/issues/159 for the original issue
    # and https://github.com/epigen/looper/pull/160 for the pull request
    # that resolved it.
    df = _pd.read_table(sample_file, sep=None, dtype=dtype,
                        index_col=False, engine="python", keep_default_na=False)
    req = [SAMPLE_NAME_COLNAME]
    missing = set(req) - set(df.columns)
    if len(missing) != 0:
        raise ValueError(
            "Annotation sheet ('{}') is missing column(s): {}; has: {}".
                format(sample_file, missing, df.columns))
    return df



def copy(obj):
    def copy(self):
        """
        Copy self to a new object.
        """
        from copy import deepcopy

        return deepcopy(self)
    obj.copy = copy
    return obj



def fetch_samples(proj, inclusion=None, exclusion=None):
    """
    Collect samples of particular protocol(s).

    Protocols can't be both positively selected for and negatively
    selected against. That is, it makes no sense and is not allowed to
    specify both inclusion and exclusion protocols. On the other hand, if
    neither is provided, all of the Project's Samples are returned.
    If inclusion is specified, Samples without a protocol will be excluded,
    but if exclusion is specified, protocol-less Samples will be included.

    :param Project proj: the Project with Samples to fetch
    :param Iterable[str] | str inclusion: protocol(s) of interest;
        if specified, a Sample must
    :param Iterable[str] | str exclusion: protocol(s) to include
    :return list[Sample]: Collection of this Project's samples with
        protocol that either matches one of those in inclusion, or either
        lacks a protocol or does not match one of those in exclusion
    :raise TypeError: if both inclusion and exclusion protocols are
        specified; TypeError since it's basically providing two arguments
        when only one is accepted, so remain consistent with vanilla Python2
    """

    # Intersection between inclusion and exclusion is nonsense user error.
    if inclusion and exclusion:
        raise TypeError("Specify only inclusion or exclusion protocols, "
                         "not both.")

    if not inclusion and not exclusion:
        # Simple; keep all samples.  In this case, this function simply
        # offers a list rather than an iterator.
        return list(proj.samples)

    # Ensure that we're working with sets.
    def make_set(items):
        if isinstance(items, str):
            items = [items]
        return {alpha_cased(i) for i in items}

    # Use the attr check here rather than exception block in case the
    # hypothetical AttributeError would occur in alpha_cased; we want such
    # an exception to arise, not to catch it as if the Sample lacks "protocol"
    if not inclusion:
        # Loose; keep all samples not in the exclusion.
        def keep(s):
            return not hasattr(s, "protocol") or \
                   alpha_cased(s.protocol) not in make_set(exclusion)
    else:
        # Strict; keep only samples in the inclusion.
        def keep(s):
            return hasattr(s, "protocol") and \
                   alpha_cased(s.protocol) in make_set(inclusion)

    return list(filter(keep, proj.samples))



def include_in_repr(attr, klazz):
    """
    Determine whether to include attribute in an object's text representation.

    :param str attr: attribute to include/exclude from object's representation
    :param str | type klazz: name of type or type itself of which the object
        to be represented is an instance
    :return bool: whether to include attribute in an object's
        text representation
    """
    classname = klazz.__name__ if isinstance(klazz, type) else klazz
    return attr not in \
           {"Project": ["sheet", "interfaces_by_protocol"]}[classname]



def is_url(maybe_url):
    """
    Determine whether a path is a URL.

    :param str maybe_url: path to investigate as URL
    :return bool: whether path appears to be a URL
    """
    return urlparse(maybe_url).scheme != ""



def merge_sample(sample, merge_table, data_sources=None, derived_columns=None):
    """
    Use merge table data to augment/modify Sample.

    :param Sample sample: sample to modify via merge table data
    :param merge_table: data with which to alter Sample
    :param Mapping data_sources: collection of named paths to data locations,
        optional
    :param Iterable[str] derived_columns: names of columns for which
        corresponding Sample attribute's value is data-derived, optional
    :return Set[str]: names of columns that were merged
    """

    merged_attrs = {}

    if merge_table is None:
        _LOGGER.log(5, "No data for sample merge, skipping")
        return merged_attrs

    if SAMPLE_NAME_COLNAME not in merge_table.columns:
        raise KeyError(
            "Merge table requires a column named '{}'.".
                format(SAMPLE_NAME_COLNAME))

    _LOGGER.debug("Merging Sample with data sources: {}".
                  format(data_sources))
    
    # Hash derived columns for faster lookup in case of many samples/columns.
    derived_columns = set(derived_columns or [])
    _LOGGER.debug("Merging Sample with derived columns: {}".
                  format(derived_columns))

    sample_name = getattr(sample, SAMPLE_NAME_COLNAME)
    sample_indexer = merge_table[SAMPLE_NAME_COLNAME] == sample_name
    this_sample_rows = merge_table[sample_indexer]
    if len(this_sample_rows) == 0:
        _LOGGER.debug("No merge rows for sample '%s', skipping", sample.name)
        return merged_attrs
    _LOGGER.log(5, "%d rows to merge", len(this_sample_rows))
    _LOGGER.log(5, "Merge rows dict: {}".format(this_sample_rows.to_dict()))

    # For each row in the merge table of this sample:
    # 1) populate any derived columns
    # 2) derived columns --> space-delimited strings
    # 3) update the sample values with the merge table
    # Keep track of merged cols,
    # so we don't re-derive them later.
    merged_attrs = {key: "" for key in this_sample_rows.columns}
    
    for _, row in this_sample_rows.iterrows():
        rowdata = row.to_dict()

        # Iterate over column names to avoid Python3 RuntimeError for
        # during-iteration change of dictionary size.
        for attr_name in this_sample_rows.columns:
            if attr_name == SAMPLE_NAME_COLNAME or \
                            attr_name not in derived_columns:
                _LOGGER.log(5, "Skipping merger of attribute '%s'", attr_name)
                continue

            attr_value = rowdata[attr_name]

            # Initialize key in parent dict.
            col_key = attr_name + COL_KEY_SUFFIX
            merged_attrs[col_key] = ""
            rowdata[col_key] = attr_value
            data_src_path = sample.locate_data_source(
                    data_sources, attr_name, source_key=rowdata[attr_name],
                    extra_vars=rowdata)  # 1)
            rowdata[attr_name] = data_src_path

        _LOGGER.log(5, "Adding derived columns")
        
        for attr in derived_columns:
            
            # Skip over any attributes that the sample lacks or that are
            # covered by the data from the current (row's) data.
            if not hasattr(sample, attr) or attr in rowdata:
                _LOGGER.log(5, "Skipping column: '%s'", attr)
                continue
            
            # Map key to sample's value for the attribute given by column name.
            col_key = attr + COL_KEY_SUFFIX
            rowdata[col_key] = getattr(sample, attr)
            # Map the col/attr name itself to the populated data source 
            # template string.
            rowdata[attr] = sample.locate_data_source(
                    data_sources, attr, source_key=getattr(sample, attr),
                    extra_vars=rowdata)

        # TODO: this (below) is where we could maintain grouped values
        # TODO (cont.): as a collection and defer the true merger.

        # Since we are now jamming multiple (merged) entries into a single
        # attribute on a Sample, we have to join the individual items into a
        # space-delimited string and then use that value as the Sample
        # attribute. The intended use case for this sort of merge is for
        # multiple data source paths associated with a single Sample, hence
        # the choice of space-delimited string as the joined-/merged-entry
        # format--it's what's most amenable to use in building up an argument
        # string for a pipeline command.
        for attname, attval in rowdata.items():
            if attname == SAMPLE_NAME_COLNAME or not attval:
                _LOGGER.log(5, "Skipping KV: {}={}".format(attname, attval))
                continue
            _LOGGER.log(5, "merge: sample '%s'; '%s'='%s'",
                        str(sample.name), str(attname), str(attval))
            if attname not in merged_attrs:
                new_attval = str(attval).rstrip()
            else:
                new_attval = "{} {}".format(merged_attrs[attname], str(attval)).strip()
            merged_attrs[attname] = new_attval  # 2)
            _LOGGER.log(5, "Stored '%s' as value for '%s' in merged_attrs",
                        new_attval, attname)

    # If present, remove sample name from the data with which to update sample.
    merged_attrs.pop(SAMPLE_NAME_COLNAME, None)

    _LOGGER.log(5, "Updating Sample {}: {}".format(sample.name, merged_attrs))
    sample.update(merged_attrs)  # 3)
    sample.merged_cols = merged_attrs
    sample.merged = True

    return sample



def process_pipeline_interfaces(pipeline_interface_locations):
    """
    Create a ProtocolInterface for each pipeline location given.

    :param Iterable[str] pipeline_interface_locations: locations, each of
        which should be either a directory path or a filepath, that specifies
        pipeline interface and protocol mappings information. Each such file
        should be have a pipelines section and a protocol mappings section
        whereas each folder should have a file for each of those sections.
    :return Mapping[str, Iterable[ProtocolInterface]]: mapping from protocol
        name to interface(s) for which that protocol is mapped
    """
    interface_by_protocol = defaultdict(list)
    for pipe_iface_location in pipeline_interface_locations:
        if not _os.path.exists(pipe_iface_location):
            _LOGGER.warn("Ignoring nonexistent pipeline interface "
                         "location: '%s'", pipe_iface_location)
            continue
        proto_iface = ProtocolInterface(pipe_iface_location)
        for proto_name in proto_iface.protomap:
            _LOGGER.log(5, "Adding protocol name: '%s'", proto_name)
            interface_by_protocol[alpha_cased(proto_name)].append(proto_iface)
    return interface_by_protocol



# Collect PipelineInterface, Sample type, pipeline path, and script with flags.
SubmissionBundle = namedtuple(
    "SubmissionBundle",
    field_names=["interface", "subtype", "pipeline", "pipeline_with_flags"])
SUBMISSION_BUNDLE_PIPELINE_KEY_INDEX = 2

