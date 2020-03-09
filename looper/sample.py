""" Extension of peppy.Sample to support looper-specific operations. """

import os
from operator import itemgetter
from logging import getLogger
from peppy import Sample as PeppySample
from ngstk import get_file_size, parse_ftype, \
    peek_read_lengths_and_paired_counts_from_bam
from .const import *

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"

__all__ = ["Sample"]

_LOGGER = getLogger(__name__)


class Sample(PeppySample):

    def __init__(self, series, prj=None):
        super(Sample, self).__init__(series, prj)

    def generate_filename(self, delimiter="_"):
        """
        Create a name for file in which to represent this Sample.

        This uses knowledge of the instance's subtype, sandwiching a delimiter
        between the name of this Sample and the name of the subtype before the
        extension. If the instance is a base Sample type, then the filename
        is simply the sample name with an extension.

        :param str delimiter: what to place between sample name and name of
            subtype; this is only relevant if the instance is of a subclass
        :return str: name for file with which to represent this Sample on disk
        """
        base = self.sample_name if type(self) is Sample else \
            "{}{}{}".format(self.sample_name, delimiter, type(self).__name__)
        return "{}{}".format(base, SAMPLE_YAML_EXT)

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
                _LOGGER.debug("Setting null for missing attribute: '%s'",
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
                _LOGGER.debug("%d values among %d files for feature '%s'",
                            len(feature_values), len(files), feature)
                feat_val = None
            _LOGGER.debug("Setting '%s' on %s to %s",
                        feature, self.__class__.__name__, feat_val)
            setattr(self, feature, feat_val)

            if getattr(self, feature) is None and len(existing_files) > 0:
                _LOGGER.warning(
                    "Not all input files agree on '%s': '%s'", feature, self.sample_name)


def _check_fastq(fastq, o):
    raise NotImplementedError(
        "Detection of read type/length for fastq input is not yet implemented.")
