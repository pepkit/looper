""" Tests for interaction between Project, PipelineInterface, and Sample. """

import logging
import os
from functools import partial

import pytest

import looper
from oldtests.conftest import (
    NGS_SAMPLE_INDICES,
    NUM_SAMPLES,
    PIPELINE_TO_REQD_INFILES_BY_SAMPLE,
)
from oldtests.helpers import named_param

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.mark.usefixtures("write_project_files", "pipe_iface_config_file")
class SampleWrtProjectCtorTests:
    """Tests for `Sample` related to `Project` construction"""

    @named_param(
        argnames="sample_index",
        argvalues=(set(range(NUM_SAMPLES)) - NGS_SAMPLE_INDICES),
    )
    def test_required_inputs(self, proj, pipe_iface, sample_index):
        """A looper Sample's required inputs are based on pipeline."""
        # Note that this is testing only the non-NGS samples for req's inputs.
        expected_required_inputs = PIPELINE_TO_REQD_INFILES_BY_SAMPLE[
            "testpipeline.sh"
        ][sample_index]
        sample = proj.samples[sample_index]
        sample.set_pipeline_attributes(pipe_iface, "testpipeline.sh")
        observed_required_inputs = [os.path.basename(f) for f in sample.required_inputs]
        assert expected_required_inputs == observed_required_inputs
        (
            error_type,
            error_general,
            error_specific,
        ) = sample.determine_missing_requirements()
        assert error_type is None
        assert not error_general
        assert not error_specific

    @named_param(argnames="sample_index", argvalues=NGS_SAMPLE_INDICES)
    def test_ngs_pipe_ngs_sample(self, proj, pipe_iface, sample_index):
        """NGS pipeline with NGS input works just fine."""
        sample = proj.samples[sample_index]
        sample.set_pipeline_attributes(pipe_iface, "testngs.sh")
        expected_required_input_basename = os.path.basename(
            PIPELINE_TO_REQD_INFILES_BY_SAMPLE["testngs.sh"][sample_index][0]
        )
        observed_required_input_basename = os.path.basename(sample.required_inputs[0])
        (
            error_type,
            error_general,
            error_specific,
        ) = sample.determine_missing_requirements()
        assert error_type is None
        assert not error_general
        assert not error_specific
        assert 1 == len(sample.required_inputs)
        assert expected_required_input_basename == observed_required_input_basename

    @named_param(
        argnames="sample_index", argvalues=set(range(NUM_SAMPLES)) - NGS_SAMPLE_INDICES
    )
    @pytest.mark.parametrize(
        argnames="permissive",
        argvalues=[False, True],
        ids=lambda permissive: "permissive={}".format(permissive),
    )
    def test_ngs_pipe_non_ngs_sample(
        self, proj, pipe_iface, sample_index, permissive, tmpdir
    ):
        """An NGS-dependent pipeline with non-NGS sample(s) is dubious."""

        # Based on the test case's parameterization,
        # get the sample and create the function call to test.
        sample = proj.samples[sample_index]
        kwargs = {
            "pipeline_interface": pipe_iface,
            "pipeline_name": "testngs.sh",
            "permissive": permissive,
        }
        test_call = partial(sample.set_pipeline_attributes, **kwargs)

        # Permissiveness parameter determines whether
        # there's an exception or just an error message.
        if not permissive:
            with pytest.raises(TypeError):
                test_call()
        else:
            # Log to a file just for this test.

            # Get a logging handlers snapshot so that we can ensure that
            # we've successfully reset logging state upon test conclusion.
            import copy

            pre_test_handlers = copy.copy(looper._LOGGER.handlers)

            # Control the format to enable assertions about message content.
            logfile = tmpdir.join("captured.log").strpath
            capture_handler = logging.FileHandler(logfile, mode="w")
            logmsg_format = (
                "{%(name)s} %(module)s:%(lineno)d [%(levelname)s] > %(message)s "
            )
            capture_handler.setFormatter(logging.Formatter(logmsg_format))
            capture_handler.setLevel(logging.ERROR)
            looper._LOGGER.addHandler(capture_handler)

            # Execute the actual call under test.
            test_call()

            # Read the captured, logged lines and make content assertion(s).
            with open(logfile, "r") as captured:
                loglines = captured.readlines()
            assert 1 == len(loglines)
            assert "ERROR" in loglines[0]

            # Remove the temporary handler and assert that we've reset state.
            del looper._LOGGER.handlers[-1]
            assert pre_test_handlers == looper._LOGGER.handlers
