"""Tests for the natural numbers range data type"""

import pytest
from hypothesis import given, strategies as st
from looper.utils import NatIntervalException, NatIntervalInclusive


def nondecreasing_pair_strategy(first_upper_bound):
    """Generate a pair of values in which first respects given upper bound and second is no more than first."""
    return st.tuples(st.integers(max_value=first_upper_bound), st.integers()).filter(
        lambda p: p[0] <= p[1]
    )


class NaturalRangePureConstructorTests:
    """Tests for direct use of natural range primary constructor"""

    @given(upper_bound=st.integers(min_value=1))
    def test_zero_is_prohibited(self, upper_bound):
        """Separate this case since it's an edge case."""
        with pytest.raises(NatIntervalException):
            NatIntervalInclusive(0, upper_bound)

    @given(bounds=nondecreasing_pair_strategy(first_upper_bound=0))
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

    @pytest.mark.parametrize("arg", ["0:0", ":0", "0:", "0-0", "-0", "0-"])
    def test_zero__does_not_parse(self, arg):
        with pytest.raises(NatIntervalException):
            NatIntervalInclusive.from_string(arg)

    @pytest.mark.skip(reason="not implemented")
    def test_one_sided_lower_parse_success(self):
        pass

    @pytest.mark.skip(reason="not implemented")
    def test_one_sided_upper_parse_success(self):
        pass

    @pytest.mark.skip(reason="not implemented")
    def test_one_sided_lower_parse_failure(self):
        pass

    @pytest.mark.skip(reason="not implemented")
    def test_one_sided_upper_parse_failure(self):
        pass

    @pytest.mark.skip(reason="not implemented")
    def test_two_sided_upper_parse_success(self):
        pass

    @pytest.mark.skip(reason="not implemented")
    def test_two_sided_lower_parse_failure(self):
        pass
