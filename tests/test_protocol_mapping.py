""" Tests for ability to map protocol(s) to pipeline(s) """

import pytest
from looper import SAMPLE_NAME_COLNAME
from peppy import Sample


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"



@pytest.mark.skip("Not implemented")
class SubmissionBundleProtocolMappingTests:
    """ Project must be able to resolve PipelineInterface from protocol. """


    @pytest.fixture
    def sample(self):
        return Sample({SAMPLE_NAME_COLNAME: "basic_sample"})


    @pytest.fixture
    def pipeline_interface(self):
        pass


    @pytest.fixture
    def sheet(self):
        pass


    @pytest.fixture
    def prj(self):
        pass


    @pytest.mark.parametrize(argnames="has_generic", argvalues=[False, True])
    def test_no_match(self, has_generic, sample):
        """ No specific protocol match allows generic match if present. """
        sample.protocol = ""


    @pytest.mark.parametrize(argnames="priority", argvalues=[False, True])
    def test_priority(self, priority, sample):
        """ Flag determines behavior when multiple interfaces map protocol. """
        pass
