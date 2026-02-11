"""Tests for the natural numbers range data type"""

from typing import *
import pytest
from hypothesis import given, strategies as st
from looper.utils import NatIntervalException, NatIntervalInclusive


gen_pos_int = st.integers(min_value=1)
gen_opt_int = st.one_of(st.integers(), st.none())


def is_non_pos(opt_int: Optional[int]) -> bool:
    """Determine whether the given value is non-positive (and non-null)."""
    return opt_int is not None and opt_int < 1


def pytest_generate_tests(metafunc):
    if "legit_delim" in metafunc.fixturenames:
        metafunc.parametrize("legit_delim", [":", "-"])


def nondecreasing_pair_strategy(**kwargs):
    """Generate a pair of values in which first respects given upper bound and second is no more than first."""
    return st.tuples(st.integers(**kwargs), st.integers(**kwargs)).filter(
        lambda p: p[0] <= p[1]
    )


class NaturalRangePureConstructorTests:
    """Tests for direct use of natural range primary constructor"""

    @given(upper_bound=gen_pos_int)
    def test_zero_is_prohibited(self, upper_bound):
        """Separate this case since it's an edge case."""
        with pytest.raises(NatIntervalException):
            NatIntervalInclusive(0, upper_bound)

    @given(bounds=nondecreasing_pair_strategy(max_value=0))
    def test_non_positive_is_prohibited(self, bounds):
        lo, hi = bounds
        with pytest.raises(NatIntervalException):
            NatIntervalInclusive(lo, hi)

    @given(bounds=st.tuples(st.integers(), st.integers()).filter(lambda p: p[0] > p[1]))
    def test_upper_less_than_lower__fails_as_expected(self, bounds):
        lo, hi = bounds
        with pytest.raises(NatIntervalException):
            NatIntervalInclusive(lo, hi)


class NaturalRangeFromStringTests:
    """Tests for parsing of natural number range from text, like CLI arg"""


@pytest.mark.parametrize(
    "arg_template", ["0{sep}0", "{sep}0", "0{sep}", "0{sep}0", "{sep}0", "0{sep}"]
)
@given(upper_bound=gen_pos_int)
def test_from_string__zero__does_not_parse(arg_template, legit_delim, upper_bound):
    arg = arg_template.format(sep=legit_delim)
    with pytest.raises(NatIntervalException):
        NatIntervalInclusive.from_string(arg, upper_bound=upper_bound)


@given(upper_bound=st.integers())
def test_from_string__just_delimiter__does_not_parse(legit_delim, upper_bound):
    with pytest.raises(NatIntervalException):
        NatIntervalInclusive.from_string(legit_delim, upper_bound=upper_bound)


@given(
    lo_hi_upper=st.tuples(gen_opt_int, gen_opt_int, st.integers()).filter(
        lambda t: (t[0] is not None or t[1] is not None)
        and any(is_non_pos(n) for n in t)
    )
)
def test_from_string__nonpositive_values__fail_with_expected_error(
    lo_hi_upper, legit_delim
):
    lo, hi, upper_bound = lo_hi_upper
    if lo is None and hi is None:
        raise ValueError("Both lower and upper bound generated are null.")
    if lo is None:
        arg = legit_delim + str(hi)
    elif hi is None:
        arg = str(lo) + legit_delim
    else:
        arg = str(lo) + legit_delim + str(hi)
    with pytest.raises(NatIntervalException):
        NatIntervalInclusive.from_string(arg, upper_bound=upper_bound)


@pytest.mark.parametrize("arg", ["1,2", "1;2", "1_2", "1/2", "1.2", "1~2"])
@given(upper_bound=st.integers(min_value=3))
def test_from_string__illegal_delimiter__fail_with_expected_error(arg, upper_bound):
    with pytest.raises(NatIntervalException):
        NatIntervalInclusive.from_string(arg, upper_bound=upper_bound)


@given(
    lower_and_limit=st.tuples(st.integers(), st.integers()).filter(
        lambda p: p[1] < p[0]
    )
)
def test_from_string__one_sided_lower_with_samples_lt_bound__fails(
    lower_and_limit, legit_delim
):
    lower, limit = lower_and_limit
    arg = str(lower) + legit_delim
    with pytest.raises(NatIntervalException):
        NatIntervalInclusive.from_string(arg, upper_bound=limit)


@given(lower_and_upper=nondecreasing_pair_strategy(min_value=1))
def test_from_string__one_sided_lower_with_samples_gteq_bound__succeeds(
    lower_and_upper, legit_delim
):
    lo, upper_bound = lower_and_upper
    exp = NatIntervalInclusive(lo, upper_bound)
    arg = str(lo) + legit_delim
    obs = NatIntervalInclusive.from_string(arg, upper_bound=upper_bound)
    assert obs == exp


@given(upper_and_limit=nondecreasing_pair_strategy(min_value=1))
def test_from_string__one_sided_upper_with_samples_gteq_bound__succeeds(
    upper_and_limit, legit_delim
):
    upper, limit = upper_and_limit
    exp = NatIntervalInclusive(1, upper)
    arg = legit_delim + str(upper)
    obs = NatIntervalInclusive.from_string(arg, upper_bound=limit)
    assert obs == exp


@given(
    upper_and_limit=st.tuples(
        st.integers(min_value=1), st.integers(min_value=1)
    ).filter(lambda p: p[1] < p[0])
)
def test_from_string__one_sided_upper_with_samples_lt_bound__uses_bound(
    upper_and_limit, legit_delim
):
    upper, limit = upper_and_limit
    exp = NatIntervalInclusive(1, limit)
    arg = legit_delim + str(upper)
    obs = NatIntervalInclusive.from_string(arg, upper_bound=limit)
    assert obs == exp


@given(
    lower_upper_limit=st.tuples(gen_pos_int, gen_pos_int, gen_pos_int).filter(
        lambda t: t[1] < t[0] or t[2] < t[0]
    )
)
def test_from_string__two_sided_parse_upper_lt_lower(lower_upper_limit, legit_delim):
    lo, hi, lim = lower_upper_limit
    arg = str(lo) + legit_delim + str(hi)
    with pytest.raises(NatIntervalException):
        NatIntervalInclusive.from_string(arg, upper_bound=lim)


@given(
    lo_hi_limit=st.tuples(st.integers(min_value=2), gen_pos_int, gen_pos_int).filter(
        lambda t: t[2] < t[0] <= t[1]
    )
)
def test_from_string__two_sided_parse_upper_gteq_lower_with_upper_limit_lt_lower(
    lo_hi_limit, legit_delim
):
    lo, hi, limit = lo_hi_limit
    arg = str(lo) + legit_delim + str(hi)
    with pytest.raises(NatIntervalException):
        NatIntervalInclusive.from_string(arg, upper_bound=limit)


@given(
    lo_hi_limit=st.tuples(gen_pos_int, gen_pos_int, gen_pos_int).filter(
        lambda t: t[0] < t[2] < t[1]
    )
)
def test_from_string__two_sided_parse_upper_gteq_lower_with_upper_limit_between_lower_and_upper(
    lo_hi_limit,
    legit_delim,
):
    lo, hi, limit = lo_hi_limit
    exp = NatIntervalInclusive(lo, limit)
    arg = str(lo) + legit_delim + str(hi)
    obs = NatIntervalInclusive.from_string(arg, upper_bound=limit)
    assert obs == exp


@given(
    lo_hi_upper=st.tuples(gen_pos_int, gen_pos_int, gen_pos_int).filter(
        lambda t: t[0] <= t[1] <= t[2]
    )
)
def test_from_string__two_sided_parse_upper_gteq_lower_with_upper_limit_gteq_upper(
    lo_hi_upper, legit_delim
):
    lo, hi, upper_bound = lo_hi_upper
    exp = NatIntervalInclusive(lo, hi)
    arg = f"{str(lo)}{legit_delim}{str(hi)}"
    obs = NatIntervalInclusive.from_string(arg, upper_bound=upper_bound)
    assert obs == exp
