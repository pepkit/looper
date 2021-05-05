""" Tests for collision between CLI- and Project-specified pipe args """

import copy
import itertools
import os

import pytest
import yaml
from divvy import DEFAULT_COMPUTE_RESOURCES_NAME as DEF_RES
from peppy.const import *
from peppy.utils import count_repeats
from ubiquerg import powerset

from looper import PipelineInterface, Project, SubmissionConductor
from looper.pipeline_interface import PL_KEY, PROTOMAP_KEY
from oldtests.helpers import randconf

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


ALL_PIPE_FLAGS = {"--random", "--arbitrary", "--does-not-matter"}


def generate_flags_partitions(flags):
    """
    Generate all partitions of a CLI flag options.

    Each partition will be such that each flag is either designated for CLI
    specification or for project config specification, but not both.

    :param Iterable[str] flags: collection of flag-like options to partition
    :return Iterable[(str, dict[str, NoneType])]: collection of pairs in which
        first component of each pair is collection of flags for CLI-like
        specification simulation, and second component is specification of
        remaining flags as pipeline args for project config
    """
    return [(ps, {f: None for f in flags if f not in ps}) for ps in powerset(flags)]


def generate_overlaps(singles, mapped):
    """
    Generate improper partitions, i.e. those with some overlap between subsets.

    :param Iterable[str] singles: collection of flag-like option names
    :param dict[str, NoneType] mapped: flag-like option name mapped to null
    :return Iterable[(str, dict[str, NoneType])]: collection of pairs in which
        first component of each pair is collection of flags for CLI-like
        specification simulation, and second component is specification of
        remaining flags as pipeline args for project config
    """
    common = set(singles) & set(mapped.keys())
    assert set() == common, "Nonempty intersection: {}".format(", ".join(common))
    singles_update = [
        list(singles) + list(m) for m in powerset(mapped.keys(), min_items=1)
    ]
    mapped_update = [{f: None for f in fs} for fs in powerset(singles, min_items=1)]
    aug_maps = []
    for mx in mapped_update:
        m = copy.copy(mapped)
        m.update(mx)
        aug_maps.append(m)
    return [(s, mapped) for s in singles_update] + [(singles, m) for m in aug_maps]


def generate_full_flags_cover(flags):
    """
    Generate all paritions of flags, both with and without overlaps.

    Each partition is binary, designating each flag-like option for either
    CLI-like specification simulation or for pipeline args project config
    specification (or both in the case of a partition with a nonempty
    intersection of the parts).

    :param Iterable[str] flags: collection of flag-like options to partition
    :return Iterable[(str, dict[str, NoneType])]: collection of pairs in which
        first component of each pair is collection of flags for CLI-like
        specification simulation, and second component is specification of
        remaining flags as pipeline args for project config
    """
    partition = generate_flags_partitions(flags)
    overlappings = [generate_overlaps(s, m) for s, m in partition]
    return partition + list(itertools.chain(*overlappings))


@pytest.fixture
def prj_dat(request, tmpdir):
    """Project config data for a test case"""
    prj_dat = {METADATA_KEY: {OUTDIR_KEY: tmpdir.strpath}}
    if PIPE_ARGS_SECTION in request.fixturenames:
        pipe_args = request.getfixturevalue(PIPE_ARGS_SECTION)
        if type(pipe_args) is not dict:
            raise TypeError(
                "Pipeline arguments must be a dictionary; got {}".format(
                    type(pipe_args)
                )
            )
        prj_dat[PIPE_ARGS_SECTION] = pipe_args
    return prj_dat


@pytest.mark.parametrize(
    ["cli_flags", "pipe_args_data"], generate_full_flags_cover(ALL_PIPE_FLAGS)
)
def test_flag_like_option(tmpdir, cli_flags, pipe_args_data, prj_dat):
    """Collision of flag-like options adds each only once."""

    # Pretest
    assert (
        len(cli_flags) > 0 or len(pipe_args_data) > 0
    ), "Invalid test case parameterization -- empty flags and pipeline args"
    reps = count_repeats(cli_flags)
    assert [] == reps, "Unexpected duplicate flags: {}".format(reps)

    # Build and validate Project.
    pipe_key = "arbitrary-testpipe"
    prj_dat[PIPE_ARGS_SECTION] = {pipe_key: pipe_args_data}
    temproot = tmpdir.strpath
    prj_cfg = os.path.join(temproot, randconf())
    prj = _write_and_build_prj(prj_cfg, prj_dat)
    assert prj_dat[PIPE_ARGS_SECTION] == prj[PIPE_ARGS_SECTION].to_map()

    # Build the submission conductor.
    pi_data = {
        PROTOMAP_KEY: {GENERIC_PROTOCOL_KEY: pipe_key},
        PL_KEY: {
            pipe_key: {
                DEF_RES: {
                    "file_size": "0",
                    "cores": "1",
                    "mem": "1000",
                    "time": "0-01:00:00",
                }
            }
        },
    }
    pi = PipelineInterface(pi_data)
    conductor = SubmissionConductor(
        pipe_key, pi, cmd_base="", prj=prj, extra_args=cli_flags
    )
    _, addl_args_text = conductor._cmd_text_extra(0)
    assert set(addl_args_text.split(" ")) == ALL_PIPE_FLAGS


def _write_and_build_prj(fp, d):
    """
    Write project config file and build Project.

    :param str fp: path to config file
    :param dict d: project config data
    :return looper.Project: newly built Project instance
    """
    with open(fp, "w") as f:
        yaml.dump(d, f)
    return Project(fp)
