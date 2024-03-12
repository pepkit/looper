"""Tests for the validation of looper CLI use"""

import argparse
from typing import *

import pytest
from looper.const import (
    SAMPLE_SELECTION_ATTRIBUTE_OPTNAME,
    SAMPLE_EXCLUSION_OPTNAME,
    SAMPLE_INCLUSION_OPTNAME,
)
from tests.conftest import print_standard_stream, subp_exec, test_args_expansion
from looper.cli_pydantic import main


SUBCOMMANDS_WHICH_SUPPORT_SKIP_XOR_LIMIT = ["run", "destroy"]


def pytest_generate_tests(metafunc):
    if "dry_run" in metafunc.fixturenames:
        metafunc.parametrize("dry_run", [False, True])
    if "arbitrary_subcommand" in metafunc.fixturenames:
        metafunc.parametrize(
            "arbitrary_subcommand", SUBCOMMANDS_WHICH_SUPPORT_SKIP_XOR_LIMIT
        )


@pytest.mark.parametrize(
    "extra_args",
    [
        ["--limit", "2", "--skip", "1"],
        [
            "--limit",
            "1",
            f"--{SAMPLE_SELECTION_ATTRIBUTE_OPTNAME}",
            "toggle",
            f"--{SAMPLE_EXCLUSION_OPTNAME}",
            "F",
        ],
        [
            "--limit",
            "1",
            f"--{SAMPLE_SELECTION_ATTRIBUTE_OPTNAME}",
            "toggle",
            f"--{SAMPLE_INCLUSION_OPTNAME}",
            "T",
        ],
        [
            "--skip",
            "1",
            f"--{SAMPLE_SELECTION_ATTRIBUTE_OPTNAME}",
            "toggle",
            f"--{SAMPLE_EXCLUSION_OPTNAME}",
            "F",
        ],
        [
            "--skip",
            "1",
            f"--{SAMPLE_SELECTION_ATTRIBUTE_OPTNAME}",
            "toggle",
            f"--{SAMPLE_INCLUSION_OPTNAME}",
            "T",
        ],
    ],
)
def test_limit_and_skip_mutual_exclusivity(
    prep_temp_pep,
    arbitrary_subcommand,
    dry_run,
    extra_args,
):
    x = test_args_expansion(
        pth=prep_temp_pep, cmd=arbitrary_subcommand, appendix=extra_args, dry=dry_run
    )
    with pytest.raises(SystemExit):
        main(test_args=x)
