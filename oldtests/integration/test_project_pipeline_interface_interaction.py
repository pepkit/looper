""" Tests regarding interaction between Project and PipelineInterface """

import itertools
import os
from copy import deepcopy

import pytest
import yaml
from peppy import (
    CONSTANTS_DECLARATION,
    DATA_SOURCES_SECTION,
    DERIVATIONS_DECLARATION,
    OUTDIR_KEY,
    SAMPLE_ANNOTATIONS_KEY,
)
from ubiquerg import powerset

import oldtests
from looper import Project
from looper.const import PIPELINE_REQUIREMENTS_KEY
from looper.pipeline_interface import PL_KEY, PROTOMAP_KEY
from looper.pipereqs import KEY_EXEC_REQ, KEY_FILE_REQ, KEY_FOLDER_REQ
from looper.project_piface_group import ProjectPifaceGroup
from oldtests.helpers import build_pipeline_iface

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


GOOD_EXEC_REQS_DATA = [(r, KEY_EXEC_REQ) for r in ["ls", "date"]]
GOOD_PATH_REQS_DATA = [("$HOME", KEY_FOLDER_REQ), (__file__, KEY_FILE_REQ)]
GOOD_REQS_MAPS = [
    dict(c) for c in powerset(GOOD_PATH_REQS_DATA + GOOD_EXEC_REQS_DATA, nonempty=True)
]
GOOD_REQS_LISTS = [
    list(c) for c in powerset([r for r, _ in GOOD_EXEC_REQS_DATA], nonempty=True)
]

BAD_EXEC_REQS_DATA = [(r, KEY_EXEC_REQ) for r in [__file__, "$HOME"]]
BAD_PATH_REQS_DATA = [("not-a-file", KEY_FILE_REQ), ("notdir", KEY_FOLDER_REQ)]
BAD_REQS_MAPS = list(
    map(dict, powerset(BAD_EXEC_REQS_DATA + BAD_PATH_REQS_DATA, nonempty=True))
)
BAD_REQS_LISTS = list(
    map(list, powerset([r for r, _ in BAD_PATH_REQS_DATA], nonempty=True))
)

ANNS_FILE_NAME = "anns.csv"
DATA_FOLDER_PATH = os.path.join(os.path.dirname(oldtests.__file__), "data")
INTERFACE_FILEPATH = os.path.join(DATA_FOLDER_PATH, "methyl_piface.yaml")

"""
{source_key}:
  src1: "{{basedir}}/data/{{sample_name}}.txt"
  src2: "{{basedir}}/data/{{sample_name}}-bamfile.bam"
"""

PROJECT_CONFIG_LINES = """metadata:
  {tab_key}: {anns_file}
  {outkey}: test

{const_key}:
  genome: mm10
""".format(
    outkey=OUTDIR_KEY,
    tab_key=SAMPLE_ANNOTATIONS_KEY,
    anns_file=ANNS_FILE_NAME,
    derivations_key=DERIVATIONS_DECLARATION,
    source_key=DATA_SOURCES_SECTION,
    const_key=CONSTANTS_DECLARATION,
).splitlines(
    True
)

BSSEQ_PROTO = "BS"

SAMPLE_ANNOTATION_LINES = """sample_name,protocol,file,file2
a,{p},src1,src2
b,{p},src1,src2
c,{p},src1,src2
d,{p},src1,src2
""".format(
    p=BSSEQ_PROTO
).splitlines(
    True
)


@pytest.fixture
def methyl_config():
    """Return parse of on-disk PipelineInterface file."""
    with open(INTERFACE_FILEPATH, "r") as f:
        return yaml.load(f, yaml.SafeLoader)


@pytest.fixture
def project(tmpdir):
    """Provide test case with a project instance."""
    srcdir = os.path.join(tmpdir.strpath, "src")
    os.makedirs(srcdir)
    with open(os.path.join(srcdir, "wgbs.py"), "w"), open(
        os.path.join(srcdir, "rrbs.py"), "w"
    ):
        pass
    conf_file = tmpdir.join("prjcfg.yaml").strpath
    with open(conf_file, "w") as f:
        for l in PROJECT_CONFIG_LINES:
            f.write(l)
    with open(tmpdir.join(ANNS_FILE_NAME).strpath, "w") as f:
        for l in SAMPLE_ANNOTATION_LINES:
            f.write(l)
    return Project(conf_file)


@pytest.mark.parametrize(
    ["good_reqs", "bad_reqs"],
    itertools.product(GOOD_REQS_LISTS + GOOD_REQS_MAPS, BAD_REQS_LISTS + BAD_REQS_MAPS),
)
@pytest.mark.parametrize(
    ["good_proto", "bad_proto"], [("WGBS", "RRBS"), ("RRBS", "WGBS")]
)
def test_submission_bundle_construction(
    tmpdir, project, methyl_config, good_reqs, bad_reqs, good_proto, bad_proto
):
    """Verify behavior of pipeline-specific requirements."""
    print("TMPDIR CONTENTS: {}".format(os.listdir(tmpdir.strpath)))
    good_pipe = methyl_config[PROTOMAP_KEY][good_proto]
    bad_pipe = methyl_config[PROTOMAP_KEY][bad_proto]
    data = deepcopy(methyl_config)
    print("DATA: {}".format(data))
    data[PL_KEY][good_pipe][PIPELINE_REQUIREMENTS_KEY] = good_reqs
    data[PL_KEY][bad_pipe][PIPELINE_REQUIREMENTS_KEY] = bad_reqs
    iface_group = ProjectPifaceGroup()
    pi = build_pipeline_iface(from_file=True, folder=tmpdir.strpath, data=data)
    iface_group.update(pi)
    project.interfaces = iface_group
    obs_good = project.build_submission_bundles(good_proto)
    obs_bad = project.build_submission_bundles(bad_proto)
    print(
        "GOOD PIPE REQS: {}".format(data[PL_KEY][good_pipe][PIPELINE_REQUIREMENTS_KEY])
    )
    print("BAD PIPE REQS: {}".format(data[PL_KEY][bad_pipe][PIPELINE_REQUIREMENTS_KEY]))
    assert 1 == len(obs_good)
    assert pi == obs_good[0][0]
    assert [] == obs_bad


@pytest.mark.parametrize(
    ["reqs", "check"],
    [
        (rs, lambda bundles: all(bool(b) for _, b in bundles))
        for rs in GOOD_REQS_MAPS + GOOD_REQS_LISTS
    ]
    + [
        (rs, lambda bundles: not any(bool(b) for _, b in bundles))
        for rs in BAD_REQS_MAPS + BAD_REQS_LISTS
    ],
)
def test_submission_bundle_construction_top_level_reqs(
    tmpdir, project, methyl_config, reqs, check
):
    """Bundle can be built for each protocol iff top-level requirments are met."""

    # Add the requirements.
    data = deepcopy(methyl_config)
    data[PIPELINE_REQUIREMENTS_KEY] = reqs

    # Build the interface.
    iface_group = ProjectPifaceGroup()
    pi = build_pipeline_iface(from_file=True, folder=tmpdir.strpath, data=data)
    assert PIPELINE_REQUIREMENTS_KEY in pi

    # Ensure test is meaningful.
    proto_count = len(pi.protocol_mapping)
    assert proto_count > 0

    # Include the interface with the project.
    iface_group.update(pi)
    project.interfaces = iface_group

    # Build the bundles.
    bundles = [(p, project.build_submission_bundles(p)) for p in pi.protocol_mapping]

    assert proto_count == len(bundles)  # protocol/bundle bijection
    assert {p for p, _ in bundles} == set(pi[PROTOMAP_KEY])  # accurate bundle labeling

    # Requirements-specific validation of the resulting bundles
    assert check(bundles)
