""" Specific case tests for writing submission script """

from copy import deepcopy
import random
import pytest
from looper.divvy import ComputingConfiguration, select_divvy_config
from tests.divvytests.helpers import get_random_key

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


@pytest.mark.parametrize(
    "extras",
    [{}]
    + [
        {get_random_key(random.randint(1, 5)): random.randint(0, 100)} for _ in range(5)
    ],
)
def test_write_script_is_effect_free(tmpdir, extras):
    """Writing script doesn't change computing configuration."""
    dcc_filepath = select_divvy_config(None)
    cc = ComputingConfiguration.from_yaml_file(filepath=dcc_filepath)
    compute1 = deepcopy(cc["compute_packages"])
    cc.write_script(tmpdir.join(get_random_key(20) + ".sh").strpath, extras)
    assert cc["compute_packages"] == compute1
