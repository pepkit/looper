""" Tests for YAML rendition of Sample """

import itertools
import os

import pytest
import yaml
from peppy import OUTDIR_KEY, SAMPLE_NAME_COLNAME
from peppy import Sample as PSample
from peppy.sample import SAMPLE_YAML_EXT, SAMPLE_YAML_FILE_KEY
from ubiquerg import powerset

from looper import Project as LProject
from looper import Sample as LSample
from looper.const import OUTKEY
from looper.pipeline_interface import PL_KEY
from oldtests.conftest import (
    ANNOTATIONS_FILENAME,
    PIPELINE_INTERFACE_CONFIG_LINES,
    PIPELINE_INTERFACES_KEY,
    PIPELINE_TO_REQD_INFILES_BY_SAMPLE,
    PROJECT_CONFIG_LINES,
    SAMPLE_ANNOTATION_LINES,
    SAMPLE_SUBANNOTATIONS_KEY,
    write_temp,
)
from oldtests.helpers import process_protocols

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


TYPE_PARAM_NAME = "data_type"


def _assert_sample_file_exists(exp_filename, dirpath):
    """Check that an expected file is in a folder."""
    contents = os.listdir(dirpath)
    assert exp_filename in dirpath, "Contents of {}: {}".format(dirpath, contents)


def _get_exp_basic_sample_filename(n, _):
    """Get the expected name for a basic Sample YAML file."""
    return n + SAMPLE_YAML_EXT


def _get_exp_sample_subtype_filename(n, t):
    """Get the expected name for a Sample subtype YAML file."""
    return n + "_" + t.__name__ + SAMPLE_YAML_EXT


class PeppySampleSubtype(PSample):
    """Dummy class for subtyping Sample from peppy."""

    pass


class LooperSampleSubtype(LSample):
    """Dummy class for subtyping LooperSample."""

    pass


@pytest.fixture
def sample(request):
    """Build a Sample, perhaps parameterized in name and type."""
    name = (
        request.getfixturevalue("name")
        if "name" in request.fixturenames
        else "testsample"
    )
    build = (
        request.getfixturevalue(TYPE_PARAM_NAME)
        if TYPE_PARAM_NAME in request.fixturenames
        else LSample
    )
    return build({SAMPLE_NAME_COLNAME: name})


@pytest.mark.parametrize(
    [TYPE_PARAM_NAME, "get_exp"],
    [
        (PSample, _get_exp_basic_sample_filename),
        (LSample, _get_exp_basic_sample_filename),
        (PeppySampleSubtype, _get_exp_sample_subtype_filename),
        (LooperSampleSubtype, _get_exp_sample_subtype_filename),
    ],
)
def test_sample_yaml_file_exists(tmpdir, data_type, get_exp, sample):
    """Ensure Sample write-to-disk creates expected file."""
    folder = tmpdir.strpath
    exp_name = get_exp(sample.name, data_type)
    exp_path = os.path.join(folder, exp_name)
    assert not os.path.exists(exp_path)
    sample.to_yaml(subs_folder_path=folder)
    assert os.path.isfile(exp_path)


@pytest.mark.parametrize(
    TYPE_PARAM_NAME, [PSample, LSample, PeppySampleSubtype, LooperSampleSubtype]
)
def test_sample_yaml_includes_filepath(tmpdir, data_type, sample):
    """A Sample's disk representation includes key-value for that path."""
    fp = sample.to_yaml(subs_folder_path=tmpdir.strpath)
    assert os.path.isfile(fp)
    with open(fp, "r") as f:
        data = yaml.load(f, yaml.SafeLoader)
    assert SAMPLE_YAML_FILE_KEY in data
    assert fp == data[SAMPLE_YAML_FILE_KEY]


PIPEKEYS = list(PIPELINE_TO_REQD_INFILES_BY_SAMPLE.keys())
OUTA = "outa"
OUTB = "outb"
DUMMY_OUTPUTS = [("A", OUTA), ("B", OUTB)]
OUTPUT_COMBOS = [dict(c) for c in powerset(DUMMY_OUTPUTS)]
OUTPUT_SPECS = [
    dict(spec)
    for spec in itertools.product(
        *[[(pk, oc) for oc in OUTPUT_COMBOS] for pk in PIPEKEYS]
    )
]


@pytest.fixture
def prj(tmpdir, request):
    """Write annotations file, piface file, and prjcfg file, and provide Project instance."""
    testpath = tmpdir.strpath
    for pipe in PIPEKEYS:
        pipe_path = os.path.join(testpath, pipe)
        with open(pipe_path, "w"):
            print("Touching pipe file: {}".format(pipe_path))
    plif_file = os.path.join(testpath, "plif.yaml")
    anns_file = os.path.join(testpath, ANNOTATIONS_FILENAME)
    with open(plif_file, "w") as f:
        for l in PIPELINE_INTERFACE_CONFIG_LINES:
            f.write(l)
    with open(plif_file, "r") as f:
        plif_data = yaml.load(f, yaml.SafeLoader)
    outs_data = request.getfixturevalue("outs_by_pipe")
    for pk, outs in outs_data.items():
        if outs:
            plif_data[PL_KEY][pk][OUTKEY] = outs
    with open(plif_file, "w") as f:
        yaml.dump(plif_data, f)
    with open(anns_file, "w") as f:
        for l in SAMPLE_ANNOTATION_LINES:
            f.write(l.replace("testlib", "standard").replace("testngs", "ngs"))
    lines = [
        l.replace(
            "{}: test".format(OUTDIR_KEY), "{}: {}".format(OUTDIR_KEY, testpath)
        ).replace(
            "{}: pipelines".format(PIPELINE_INTERFACES_KEY),
            "{}: {}".format(PIPELINE_INTERFACES_KEY, plif_file),
        )
        for l in PROJECT_CONFIG_LINES
        if SAMPLE_SUBANNOTATIONS_KEY not in l
    ]
    conf_file = write_temp(lines, testpath, "conf.yaml")
    return LProject(conf_file)


@pytest.mark.parametrize("outs_by_pipe", OUTPUT_SPECS)
def test_sample_yaml_outputs_inclusion(prj, outs_by_pipe):
    import mock

    import looper

    protocols = {s.protocol for s in prj.samples}
    print("PROTOCOLS: {}".format(protocols))

    conductors, pipe_keys = process_protocols(prj, protocols)

    assert len(PIPEKEYS) > 0  # Pretest
    assert len(PIPEKEYS) == len(conductors)  # As many pipelines as conductors

    sample_pk_pairs = [(s, pipe_keys[s.protocol]) for s in prj.samples]
    multi_pipe_samples, sample_key_pairs = [], []
    for s, pks in sample_pk_pairs:
        if len(pks) == 1:
            sample_key_pairs.append((s, pks[0]))
        else:
            multi_pipe_samples.append((s, pks))
    if multi_pipe_samples:
        raise Exception(
            "Samples with non-1 number of pipeline keys: {}".format(multi_pipe_samples)
        )

    sample_conductor_pairs = [(s, conductors[pk]) for s, pk in sample_key_pairs]
    sample_yaml_pairs = []
    with mock.patch.object(
        looper.conductor, "_use_sample", return_value=True
    ), mock.patch.object(looper.conductor, "_check_argstring"):
        for s, c in sample_conductor_pairs:
            f = os.path.join(prj.submission_folder, s.generate_filename())
            assert not os.path.exists(f)
            c.add_sample(s)
            sample_yaml_pairs.append((s, f))
    missing = [(s.name, f) for s, f in sample_yaml_pairs if not os.path.isfile(f)]
    if missing:
        print("Project outdir contents: {}".format(os.listdir(prj.output_dir)))
        print(
            "Submission folder contents: {}".format(os.listdir(prj.submission_folder))
        )
        raise Exception("Samples missing YAML file: {}".format(missing))

    sample_expout_pairs = [(s, outs_by_pipe[pk]) for s, pk in sample_key_pairs]
    bads = []
    for (s, yaml_path), (_, xo) in zip(sample_yaml_pairs, sample_expout_pairs):
        with open(yaml_path, "r") as f:
            obsdat = yaml.load(f, yaml.SafeLoader)
        if xo:
            try:
                obs = obsdat[OUTKEY]
            except KeyError:
                bads.append((s, "Missing outputs key"))
            else:
                if obs != xo:
                    bads.append((s, xo, obs))
        else:
            if OUTKEY in obsdat:
                bads.append((s, "Unexpectedly found outputs in YAML"))
    if bads:
        pytest.fail("Unmet expectations: {}".format(bads))
