"""Tests for determination of desired sample range"""

from itertools import chain
import pytest
from hypothesis import given, strategies as st
from looper.utils import (
    NatIntervalException,
    desired_samples_range_limited,
    desired_samples_range_skipped,
)


@pytest.mark.parametrize(
    "arg_and_limit",
    [
        ("2:3", 1),
        ("2-3", 1),
        ("1,3", 2),
        ("1,3", 4),
        ("1;3", 2),
        ("1;3", 4),
        ("1/3", 2),
        ("1/3", 4),
        ("1 3", 2),
        ("1 3", 4),
        ("", 10),
        (":", 10),
        ("-", 10),
        (" - ", 10),
        (" : ", 10),
    ],
)
@pytest.mark.parametrize(
    "func", [desired_samples_range_limited, desired_samples_range_skipped]
)
def test_invalid_input__raise_expected_error(arg_and_limit, func):
    arg, num_samples = arg_and_limit
    with pytest.raises(NatIntervalException):
        func(arg, num_samples)


def assert_iterable_equality(obs, exp):
    assert list(obs) == list(exp)


@pytest.mark.parametrize(
    ["arg", "num_samples", "func", "expected"],
    [
        ("2-6", 4, desired_samples_range_limited, range(2, 5)),
        ("3:6", 8, desired_samples_range_limited, range(3, 7)),
        ("4", 3, desired_samples_range_limited, range(1, 4)),
        ("4", 6, desired_samples_range_limited, range(1, 5)),
        ("2:6", 4, desired_samples_range_skipped, range(1, 2)),
        ("3-6", 8, desired_samples_range_skipped, chain(range(1, 3), range(7, 9))),
        ("4", 3, desired_samples_range_skipped, []),
        ("4", 6, desired_samples_range_skipped, range(5, 7)),
    ],
)
def test_valid_input__yields_correct_range(arg, num_samples, func, expected):
    observed = func(arg, num_samples=num_samples)
    assert_iterable_equality(obs=observed, exp=expected)
