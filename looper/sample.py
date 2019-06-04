""" Extension of peppy.Sample to support looper-specific operations. """

import os
from operator import itemgetter
from peppy import Sample as PeppySample
from peppy import *
from peppy.const import *
from peppy.utils import get_logger
from ngstk import get_file_size, parse_ftype, \
    peek_read_lengths_and_paired_counts_from_bam

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"

__all__ = ["Sample"]

_LOGGER = get_logger(__name__)


class Sample(PeppySample):

    def __init__(self, series, prj=None):
        super(Sample, self).__init__(series, prj)

    def determine_missing_requirements(self):
        """
        Determine which of this Sample's required attributes/files are missing.

        :return (type, str): hypothetical exception type along with message
            about what's missing; null and empty if nothing exceptional
            is detected
        """

        null_return = (None, "", "")

        # set_pipeline_attributes must be run first.
        if not hasattr(self, "required_inputs"):
            _LOGGER.warning("You must run set_pipeline_attributes before "
                            "determine_missing_requirements")
            return null_return

        if not self.required_inputs:
            _LOGGER.debug("No required inputs")
            return null_return

        # First, attributes
        missing, empty = [], []
        for file_attribute in self.required_inputs_attr:
            _LOGGER.whisper("Checking '{}'".format(file_attribute))
            try:
                attval = getattr(self, file_attribute)
            except AttributeError:
                _LOGGER.whisper(
                    "Missing required input attribute '%s'", file_attribute)
                missing.append(file_attribute)
                continue
            if attval == "":
                _LOGGER.whisper(
                    "Empty required input attribute '%s'", file_attribute)
                empty.append(file_attribute)
            else:
                _LOGGER.whisper(
                    "'{}' is valid: '{}'".format(file_attribute, attval))

        if missing:
            reason_key = "Missing attribute"
            reason_detail = "Missing: {}".format(", ".join(missing))
            return AttributeError, reason_key, reason_detail

        if empty:
            reason_key = "Empty attribute"
            reason_detail = "Empty: {}".format(",".join(empty))
            return AttributeError, reason_key, reason_detail

        # Second, files
        missing_files = []
        for paths in self.required_inputs:
            _LOGGER.whisper("Text to split and check paths: '%s'", paths)
            # There can be multiple, space-separated values here.
            for path in paths.split(" "):
                _LOGGER.whisper("Checking path: '{}'".format(path))
                if not os.path.exists(path):
                    _LOGGER.whisper(
                        "Missing required input file: '{}'".format(path))
                    missing_files.append(path)

        if not missing_files:
            return null_return
        else:
            reason_key = "Missing file(s)"
            reason_detail = ", ".join(missing_files)
            return IOError, reason_key, reason_detail

    def set_pipeline_attributes(
            self, pipeline_interface, pipeline_name, permissive=True):
        """
        Set pipeline-specific sample attributes.

        Some sample attributes are relative to a particular pipeline run,
        like which files should be considered inputs, what is the total
        input file size for the sample, etc. This function sets these
        pipeline-specific sample attributes, provided via a PipelineInterface
        object and the name of a pipeline to select from that interface.

        :param PipelineInterface pipeline_interface: A PipelineInterface
            object that has the settings for this given pipeline.
        :param str pipeline_name: Which pipeline to choose.
        :param bool permissive: whether to simply log a warning or error
            message rather than raising an exception if sample file is not
            found or otherwise cannot be read, default True
        """

        # Settings ending in _attr are lists of attribute keys.
        # These attributes are then queried to populate values
        # for the primary entries.
        req_attr_names = [("ngs_input_files", "ngs_inputs_attr"),
                          ("required_input_files", REQUIRED_INPUTS_ATTR_NAME),
                          ("all_input_files", ALL_INPUTS_ATTR_NAME)]
        for name_src_attr, name_dst_attr in req_attr_names:
            _LOGGER.whisper("Value of '%s' will be assigned to '%s'",
                        name_src_attr, name_dst_attr)
            value = pipeline_interface.get_attribute(
                pipeline_name, name_src_attr)
            _LOGGER.whisper("Assigning '{}': {}".format(name_dst_attr, value))
            setattr(self, name_dst_attr, value)

        # Post-processing of input attribute assignments.
        # Ensure that there's a valid all_inputs_attr.
        if not getattr(self, ALL_INPUTS_ATTR_NAME):
            required_inputs = getattr(self, REQUIRED_INPUTS_ATTR_NAME)
            setattr(self, ALL_INPUTS_ATTR_NAME, required_inputs)
        # Convert attribute keys into values.
        if self.ngs_inputs_attr:
            _LOGGER.whisper("Handling NGS input attributes: '%s'", self.name)
            # NGS data inputs exit, so we can add attributes like
            # read_type, read_length, paired.
            self.ngs_inputs = self.get_attr_values("ngs_inputs_attr")

            set_rtype_reason = ""
            if not hasattr(self, "read_type"):
                set_rtype_reason = "read_type not yet set"
            elif not self.read_type or self.read_type.lower() \
                    not in VALID_READ_TYPES:
                set_rtype_reason = "current read_type is invalid: '{}'". \
                    format(self.read_type)
            if set_rtype_reason:
                _LOGGER.debug(
                    "Setting read_type for %s '%s': %s",
                    self.__class__.__name__, self.name, set_rtype_reason)
                self.set_read_type(permissive=permissive)
            else:
                _LOGGER.debug("read_type is already valid: '%s'",
                              self.read_type)
        else:
            _LOGGER.whisper("No NGS inputs: '%s'", self.name)

        # Assign values for actual inputs attributes.
        self.required_inputs = self.get_attr_values(REQUIRED_INPUTS_ATTR_NAME)
        self.all_inputs = self.get_attr_values(ALL_INPUTS_ATTR_NAME)
        _LOGGER.debug("All '{}' inputs: {}".format(self.name, self.all_inputs))
        self.input_file_size = get_file_size(self.all_inputs)

    def set_read_type(self, rlen_sample_size=10, permissive=True):
        """
        For a sample with attr `ngs_inputs` set, this sets the
        read type (single, paired) and read length of an input file.

        :param int rlen_sample_size: Number of reads to sample to infer read type,
            default 10.
        :param bool permissive: whether to simply log a warning or error message
            rather than raising an exception if sample file is not found or
            otherwise cannot be read, default True.
        """

        # TODO: determine how return is being used and standardized (null vs. bool)

        # Initialize the parameters in case there is no input_file, so these
        # attributes at least exist - as long as they are not already set!
        for attr in ["read_length", "read_type", "paired"]:
            if not hasattr(self, attr):
                _LOGGER.whisper("Setting null for missing attribute: '%s'",
                            attr)
                setattr(self, attr, None)

        # ngs_inputs must be set
        if not self.ngs_inputs:
            return False

        ngs_paths = " ".join(self.ngs_inputs)

        # Determine extant/missing filepaths.
        existing_files = list()
        missing_files = list()
        for path in ngs_paths.split(" "):
            if not os.path.exists(path):
                missing_files.append(path)
            else:
                existing_files.append(path)
        _LOGGER.debug("{} extant file(s): {}".
                      format(len(existing_files), existing_files))
        _LOGGER.debug("{} missing file(s): {}".
                      format(len(missing_files), missing_files))

        # For samples with multiple original BAM files, check all.
        files = list()
        check_by_ftype = {"bam": peek_read_lengths_and_paired_counts_from_bam,
                          "fastq": _check_fastq}
        for input_file in existing_files:
            try:
                file_type = parse_ftype(input_file)
                read_lengths, paired = check_by_ftype[file_type](
                    input_file, rlen_sample_size)
            except (KeyError, TypeError):
                message = "Input file type should be one of: {}".format(
                    check_by_ftype.keys())
                if not permissive:
                    raise TypeError(message)
                _LOGGER.error(message)
                return
            except NotImplementedError as e:
                if not permissive:
                    raise
                _LOGGER.warning(str(e))
                return
            except IOError:
                if not permissive:
                    raise
                _LOGGER.error("Input file does not exist or "
                              "cannot be read: %s", str(input_file))
                for feat_name in self._FEATURE_ATTR_NAMES:
                    if not hasattr(self, feat_name):
                        setattr(self, feat_name, None)
                return

            # Determine most frequent read length among sample.
            rlen, _ = sorted(read_lengths.items(), key=itemgetter(1))[-1]
            _LOGGER.log(5,
                        "Selected {} as most frequent read length from "
                        "sample read length distribution: {}".format(
                            rlen, read_lengths))

            # Decision about paired-end status is majority-rule.
            if paired > (rlen_sample_size / 2):
                read_type = "paired"
                paired = True
            else:
                read_type = "single"
                paired = False

            files.append([rlen, read_type, paired])

        # Check agreement between different files
        # if all values are equal, set to that value;
        # if not, set to None and warn the user about the inconsistency
        for i, feature in enumerate(self._FEATURE_ATTR_NAMES):
            feature_values = set(f[i] for f in files)
            if 1 == len(feature_values):
                feat_val = files[0][i]
            else:
                _LOGGER.whisper("%d values among %d files for feature '%s'",
                            len(feature_values), len(files), feature)
                feat_val = None
            _LOGGER.whisper("Setting '%s' on %s to %s",
                        feature, self.__class__.__name__, feat_val)
            setattr(self, feature, feat_val)

            if getattr(self, feature) is None and len(existing_files) > 0:
                _LOGGER.warning(
                    "Not all input files agree on '%s': '%s'", feature, self.name)


def _check_fastq(fastq, o):
    raise NotImplementedError(
        "Detection of read type/length for fastq input is not yet implemented.")
