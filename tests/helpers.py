""" Test utilities. """

from functools import partial
import random
import string
import numpy as np
import pytest


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


LETTERS_AND_DIGITS = string.ascii_letters + string.digits


def assert_entirely_equal(observed, expected):
    """ Accommodate equality assertion for varied data, including NaN. """
    try:
        assert observed == expected
    except AssertionError:
        assert np.isnan(observed) and np.isnan(expected)
    except ValueError:
        assert (observed == expected).all()


def build_pipeline_iface(from_file, folder, data):
    """
    Homogenize PipelineInterface build over both in-memory and on-disk data.

    :param bool from_file: whether to route the construction through disk
    :param str folder: folder in which to create config file if via disk
    :param Mapping data: raw PI config data
    :return looper.PipelineInterface: the new PipelineInterface instance
    """
    import os, yaml
    from looper import PipelineInterface
    assert type(from_file) is bool
    if from_file:
        fp = os.path.join(folder, "pipeline_interface.yaml")
        with open(fp, 'w') as f:
            yaml.dump(data, f)
        data = fp
    return PipelineInterface(data)


def named_param(argnames, argvalues):
    """
    Parameterize a test case and automatically name/label by value

    :param str argnames: Single parameter name; this is only named in the
        plural for concordance with the pytest parameter to which it maps.
    :param Iterable[object] argvalues: Collection of arguments to the
        indicated parameter (argnames)
    :return functools.partial: Wrapped version of the call to the pytest
        test case parameterization function, for use as decorator.
    """
    return partial(pytest.mark.parametrize(argnames, argvalues,
                   ids=lambda arg: "{}={}".format(argnames, arg)))


def randstr(pool, size):
    """
    Generate random string of given size/length.

    :param Iterable[str] pool: collection of characters from which to sample
        (with replacement)
    :param int size: nunber of characters
    :return str: string built by concatenating randomly sampled characters
    :raise ValueError: if size is not a positive integer
    """
    if size < 1:
        raise ValueError("Must build string of positive integral length; got "
                         "{}".format(size))
    return "".join(random.choice(pool) for _ in range(size))


def randconf(ext=".yaml"):
    """
    Randomly generate config filename.

    :param str ext: filename extension
    :return str: randomly generated string to function as filename
    """
    return randstr(LETTERS_AND_DIGITS, 15) + ext


def remove_piface_requirements(data):
    """
    Remove the requirements declaration section from all mappings.

    :param Mapping data: (likely nested) mappings
    :return Mapping: same as input, but with requirements keys removed
    """
    from collections import Mapping
    from looper.pipeline_interface import PIPELINE_REQUIREMENTS_KEY as REQS_KEY
    def go(m, acc):
        for k, v in m.items():
            if k == REQS_KEY:
                continue
            acc[k] = go(v, {}) if isinstance(v, Mapping) else v
        return acc
    return go(data, {})


class ReqsSpec(object):
    """ Basically a namedtuple but with type validation. """

    def __init__(self, reqs, exp_valid, exp_unmet):
        """
        This is used for PipelineInterface requirements specification testing.

        :param str | Iterable[str] | Mapping[str, str] reqs: pipeline
            requirements specification, either for entire interface or for
            a specific pipeline
        :param Iterable[str] exp_valid: expected satisfied requirements
        :param Iterable[str] exp_unmet: expected unmet requirements
        """
        def proc_exp(exp_val):
            types = (tuple, list, set)
            if not isinstance(exp_val, types):
                raise TypeError(
                    "Illegal type of expected value ({}); must be one of: {}".
                    format(type(exp_val).__name__,
                           ", ".join(map(lambda t: t.__name__, types))))
            return set(exp_val)
        self.exp_valid = proc_exp(exp_valid or [])
        self.exp_valid = proc_exp(exp_unmet or [])
        self.reqs = reqs
