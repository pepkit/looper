""" Tests for interaction between Project and PipelineInterface """

from collections import Counter
from copy import deepcopy
import itertools
import os
import random
import string
import pytest
import yaml
from looper import Project as LP
from looper.const import *
from looper.pipeline_interface import PL_KEY, PROTOMAP_KEY
from attmap import AttMap
from peppy.const import *
from tests.helpers import randstr, LETTERS_AND_DIGITS

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


MAIN_META_KEY = "main_meta"
SUBS_META_KEY = "subs_meta"
SECTION_BY_FIXTURE = {
    MAIN_META_KEY: METADATA_KEY, SUBS_META_KEY: SUBPROJECTS_SECTION}
BASE_META = {OUTDIR_KEY: "arbitrary"}
DECLARED_OUTPUTS = {"smooth_bw": "a_{sample.name}/b_{sample.protocol}.txt",
                    "unalign": "u_{sample.name}_{sample.protocol}.txt"}
WGBS_NAME = "WGBS"
RRBS_NAME = "RRBS"
WGBS_KEY = "wgbs"
RRBS_KEY = "rrbs"

PROTO_NAMES = {WGBS_KEY: WGBS_NAME, RRBS_KEY: RRBS_NAME}

WGBS_IFACE_LINES = """
name: {n}
path: src/wgbs.py
required_input_files: [data_source]
ngs_input_files: [data_source]
arguments:
  "--sample-name": sample_name
  "--genome": genome
  "--input": data_source
  "--single-or-paired": read_type
resources:
  default:
    file_size: "0"
    cores: "4"
    mem: "4000"
    time: "0-02:00:00"
""".format(n=WGBS_NAME).splitlines(True)

RRBS_IFACE_LINES = """
name: {n}
path: src/rrbs.py
required_input_files: [data_source]
all_input_files: [data_source, read1, read2]
ngs_input_files: [data_source, read1, read2]
arguments:
  "--sample-name": sample_name
  "--genome": genome
  "--input": data_source
  "--single-or-paired": read_type
resources:
  default:
    file_size: "0"
    cores: "4"
    mem: "4000"
    time: "0-02:00:00"      
""".format(n=RRBS_NAME).splitlines(True)


PROTOMAP = {RRBS_NAME: RRBS_KEY, WGBS_NAME: WGBS_KEY, "EG": WGBS_KEY}
IFACE_LINES = {WGBS_KEY: WGBS_IFACE_LINES, RRBS_KEY: RRBS_IFACE_LINES}


def pytest_generate_tests(metafunc):
    """ Test case generation and parameterization for this module. """
    skip_empty_flag = "skip_sample_less"
    if skip_empty_flag in metafunc.fixturenames:
        metafunc.parametrize(skip_empty_flag, [False, True])


def augmented_metadata(metadata, extra=None):
    """ Augment base metadata with additional data. """
    assert METADATA_KEY not in metadata, \
        "Found {k} in metadata argument itself; pass just the data/values to " \
        "use as {k}, not the whole mapping".format(k=METADATA_KEY)
    m = AttMap({METADATA_KEY: BASE_META})
    m[METADATA_KEY] = m[METADATA_KEY].add_entries(metadata)
    return m.add_entries(extra or {}).to_map()


def get_conf_data(req):
    """
    Get Project config data for a test case.

    :param pytest.FixtureRequest req: test case requesting Project config data
    :return dict: Project config data
    """
    m = {key: req.getfixturevalue(fix) for fix, key
         in SECTION_BY_FIXTURE.items() if fix in req.fixturenames}
    return m


def randconf(ext=".yaml"):
    """
    Randomly generate config filename.

    :param str ext: filename extension
    :return str: randomly generated string to function as filename
    """
    return randstr(LETTERS_AND_DIGITS, 15) + ext


@pytest.fixture(scope="function")
def prj(request, tmpdir):
    """ Provide a test case with a Project instance. """
    conf_file = tmpdir.join(randconf()).strpath
    return _write_and_build_prj(conf_file, conf_data=get_conf_data(request))


@pytest.mark.parametrize(MAIN_META_KEY, [BASE_META])
def test_no_pifaces(prj, main_meta):
    """ No pipeline interfaces --> the outputs data mapping is empty."""
    assert {} == prj.get_outputs()


@pytest.mark.parametrize("name_cfg_file", [randconf()])
@pytest.mark.parametrize("ifaces", [
    [{WGBS_KEY: WGBS_IFACE_LINES}], [{RRBS_KEY: RRBS_IFACE_LINES}],
    [{WGBS_KEY: WGBS_IFACE_LINES}, {RRBS_KEY: RRBS_IFACE_LINES}]])
def test_no_outputs(tmpdir, name_cfg_file, ifaces, skip_sample_less):
    """ Pipeline interfaces without outputs --> no Project outputs """
    cfg = tmpdir.join(name_cfg_file).strpath
    iface_paths = [tmpdir.join(randconf()).strpath for _ in ifaces]
    rep_paths = _find_reps(iface_paths)
    assert [] == rep_paths, "Repeated temp filepath(s): {}".format(rep_paths)
    for data, path in zip(ifaces, iface_paths):
        with open(path, 'w') as f:
            yaml.dump(data, f)
    md = deepcopy(BASE_META)
    md[PIPELINE_INTERFACES_KEY] = iface_paths

    # DEBUG
    print("Metadata: {}".format(md))

    for path, data in zip(iface_paths, ifaces):
        _write_iface_file(path, data)
    prj = _write_and_build_prj(cfg, {METADATA_KEY: md})
    assert {} == prj.get_outputs(skip_sample_less)


@pytest.mark.parametrize("name_cfg_file", [randconf()])
@pytest.mark.parametrize(["ifaces", "prot_pool"], [
    ([{WGBS_KEY: WGBS_IFACE_LINES}], [WGBS_NAME]),
    ([{RRBS_KEY: RRBS_IFACE_LINES}], [RRBS_NAME]),
    ([{WGBS_KEY: WGBS_IFACE_LINES}, {RRBS_KEY: RRBS_IFACE_LINES}],
     [WGBS_NAME, RRBS_NAME])])
@pytest.mark.parametrize("declared_outputs", [None, ["out1", "out2"]])
def test_malformed_outputs(
        tmpdir, name_cfg_file, ifaces, prot_pool,
        declared_outputs, skip_sample_less):
    """ Invalid outputs declaration format is exceptional. """

    cfg = tmpdir.join(name_cfg_file).strpath

    iface_paths = [tmpdir.join(randconf()).strpath for _ in ifaces]
    rep_paths = _find_reps(iface_paths)
    assert [] == rep_paths, "Repeated temp filepath(s): {}".format(rep_paths)

    for data, path in zip(ifaces, iface_paths):
        with open(path, 'w') as f:
            yaml.dump(data, f)
    md = deepcopy(BASE_META)
    md[PIPELINE_INTERFACES_KEY] = iface_paths

    anns_file = tmpdir.join("anns.csv").strpath
    assert not os.path.exists(anns_file)
    sample_protos = [random.choice(prot_pool) for _ in range(10)]
    sample_names = [randstr(string.ascii_letters, 20) for _ in sample_protos]
    repeated_sample_names = _find_reps(sample_names)
    assert [] == repeated_sample_names, \
        "Repeated sample names: {}".format(repeated_sample_names)
    anns_data = [(SAMPLE_NAME_COLNAME, ASSAY_KEY)] + \
                list(zip(sample_names, sample_protos))
    with open(anns_file, 'w') as f:
        f.write("\n".join("{0},{1}".format(*pair) for pair in anns_data))
    md[SAMPLE_ANNOTATIONS_KEY] = anns_file

    # DEBUG
    print("Metadata: {}".format(md))

    keyed_outputs = {pk: declared_outputs for pk in
                     [k for pi in ifaces for k in pi.keys()]}
    for path, data in zip(iface_paths, ifaces):
        _write_iface_file(path, data, outputs_by_pipe_key=keyed_outputs)
    prj = _write_and_build_prj(cfg, {METADATA_KEY: md})
    print("TABLE below:\n{}".format(prj.sample_table))
    with pytest.raises(AttributeError):
        # Should fail on .items() call during outputs determination.
        print("Outputs: {}".format(prj.get_outputs(skip_sample_less)))


@pytest.mark.parametrize("ifaces", [
    [{WGBS_KEY: WGBS_IFACE_LINES}], [{RRBS_KEY: RRBS_IFACE_LINES}],
    [{WGBS_KEY: WGBS_IFACE_LINES}, {RRBS_KEY: RRBS_IFACE_LINES}]])
@pytest.mark.parametrize("declared_outputs",
    [{n: DECLARED_OUTPUTS for n in [RRBS_NAME, WGBS_NAME]}])
def test_only_subproject_has_outputs(tmpdir, ifaces, declared_outputs):
    """ Activation state affects status of Project's outputs. """

    cfg = tmpdir.join(randconf()).strpath

    iface_paths = [tmpdir.join(randconf()).strpath for _ in ifaces]
    assert [] == _find_reps(iface_paths), \
        "Repeated temp filepath(s): {}".format(_find_reps(iface_paths))

    for data, path in zip(ifaces, iface_paths):
        with open(path, 'w') as f:
            yaml.dump(data, f)
    md = deepcopy(BASE_META)
    md[PIPELINE_INTERFACES_KEY] = iface_paths

    sp_ifaces_paths = [tmpdir.join(randconf()).strpath for _ in ifaces]
    assert [] == _find_reps(sp_ifaces_paths), \
        "Repeated temp filepath(s): {}".format(_find_reps(sp_ifaces_paths))
    iface_path_intersect = set(sp_ifaces_paths) & set(iface_paths)
    assert set() == iface_path_intersect, \
        "Nonempty main/subs iface path intersection: {}".\
        format(", ".join(iface_path_intersect))

    # DEBUG
    print("Metadata: {}".format(md))

    used_iface_keys = set(itertools.chain(*[pi.keys() for pi in ifaces]))
    keyed_outputs = {pk: declared_outputs[PROTO_NAMES[pk]]
                     for pk in used_iface_keys}
    for path, data in zip(iface_paths, ifaces):
        _write_iface_file(path, data)
    for path, data in zip(sp_ifaces_paths, ifaces):
        _write_iface_file(path, data, outputs_by_pipe_key=keyed_outputs)

    sp_name = "testing_subproj"
    prj = _write_and_build_prj(cfg, {
        METADATA_KEY: md,
        SUBPROJECTS_SECTION: {
            sp_name: {
                METADATA_KEY: {
                    PIPELINE_INTERFACES_KEY: sp_ifaces_paths
                }
            }
        }
    })

    # DEBUG
    print("TABLE below:\n{}".format(prj.sample_table))

    assert len(prj.get_outputs(False)) == 0
    assert {} == prj.get_outputs(False)
    prj.activate_subproject(sp_name)
    assert len(prj.get_outputs(False)) > 0
    exp = {pipe_name: {k: (v, []) for k, v in outs.items()}
           for pipe_name, outs in declared_outputs.items()
           if pipe_name in {PROTO_NAMES[k] for k in used_iface_keys}}
    print("EXP: {}".format(exp))
    assert exp == prj.get_outputs(False)


@pytest.mark.skip("not implemented")
@pytest.mark.parametrize("ifaces", [
    [{WGBS_KEY: WGBS_IFACE_LINES}], [{RRBS_KEY: RRBS_IFACE_LINES}],
    [{WGBS_KEY: WGBS_IFACE_LINES}, {RRBS_KEY: RRBS_IFACE_LINES}]])
@pytest.mark.parametrize("declared_outputs",
    [{n: DECLARED_OUTPUTS for n in [RRBS_NAME, WGBS_NAME]}])
def test_only_main_project_has_outputs(tmpdir, ifaces, declared_outputs):
    """ Activation state affects status of Project's outputs. """

    cfg = tmpdir.join(randconf()).strpath

    iface_paths = [tmpdir.join(randconf()).strpath for _ in ifaces]
    assert [] == _find_reps(iface_paths), \
        "Repeated temp filepath(s): {}".format(_find_reps(iface_paths))

    for data, path in zip(ifaces, iface_paths):
        with open(path, 'w') as f:
            yaml.dump(data, f)
    md = deepcopy(BASE_META)
    md[PIPELINE_INTERFACES_KEY] = iface_paths

    sp_ifaces_paths = [tmpdir.join(randconf()).strpath for _ in ifaces]
    assert [] == _find_reps(sp_ifaces_paths), \
        "Repeated temp filepath(s): {}".format(_find_reps(sp_ifaces_paths))
    iface_path_intersect = set(sp_ifaces_paths) & set(iface_paths)
    assert set() == iface_path_intersect, \
        "Nonempty main/subs iface path intersection: {}". \
            format(", ".join(iface_path_intersect))

    sp_name = "testing_subproj"
    md[SUBPROJECTS_SECTION] = {sp_name: {
        METADATA_KEY: {PIPELINE_INTERFACES_KEY: sp_ifaces_paths}}}

    # DEBUG
    print("Metadata: {}".format(md))

    keyed_outputs = {
        pk: declared_outputs[pk] for pk in
        set(itertools.chain(*[pi.keys() for pi in ifaces]))}
    for path, data in zip(iface_paths, ifaces):
        _write_iface_file(path, data, outputs_by_pipe_key=keyed_outputs)
    for path, data in zip(sp_ifaces_paths, ifaces):
        _write_iface_file(path, data)

    prj = _write_and_build_prj(cfg, {METADATA_KEY: md})

    # DEBUG
    print("TABLE below:\n{}".format(prj.sample_table))

    assert len(prj.get_outputs(False)) > 0
    assert {PROTO_NAMES[k]: outs for k, outs in declared_outputs.items()} == \
           prj.get_outputs(False)
    prj.activate_subproject(sp_name)
    assert len(prj.get_outputs(False)) == 0
    assert {} == prj.get_outputs(False)


@pytest.mark.skip("not implemented")
def test_main_project_and_subproject_have_outputs():
    """ Activation state affects status of Project's outputs. """
    pass


@pytest.mark.skip("not implemented")
def test_no_samples_match_protocols_with_outputs(skip_sample_less):
    pass


@pytest.mark.skip("not implemented")
def test_pipeline_identifier_collision_same_data():
    pass


@pytest.mark.skip("not implemented")
def test_pipeline_identifier_collision_different_data():
    pass


@pytest.mark.skip("not implemented")
def test_sample_collection_accuracy():
    pass


@pytest.mark.skip("not implemented")
def test_protocol_collection_accuracy():
    pass


def _find_reps(objs):
    """
    Find (and count) repeated objects

    :param Iterable[object] objs: collection of objects in which to seek
        repeated elements
    :return list[(object, int)]: collection of pairs in which first component
        of each is a repeated object, and the second is duplication count
    """
    return [(o, n) for o, n in Counter(objs).items() if n > 1]


def _write_and_build_prj(conf_file, conf_data):
    """
    Write Project config data and create the instance.

    :param str conf_file: path to file to write
    :param Mapping conf_data: Project config data
    :return looper.Project: new Project instance
    """
    with open(conf_file, 'w') as f:
        yaml.dump(conf_data, f)
    return LP(conf_file)


def _write_iface_file(
        path_iface_file, lines_group_by_pipe_key,
        outputs_by_pipe_key=None, pm=None):
    """
    Write a pipeline interface file.

    :param str path_iface_file: path to the file to write
    :param Mapping[str, Iterable[str]] lines_group_by_pipe_key: binding between
        pipeline key and collection of lines that encode its specific
        configuration data
    :param Mapping[str, Mapping[str, str]] outputs_by_pipe_key: binding between
        pipeline key and mapping from output type/kind name to path template
    :param Mapping[str, str] pm: protocol mapping
    :return str: path to the file written
    """

    folder = os.path.dirname(path_iface_file)
    temps = [os.path.join(folder, randconf()) for _ in lines_group_by_pipe_key]

    def read_iface_data(fp, lines):
        with open(fp, 'w') as f:
            for l in lines:
                f.write(l)
        try:
            with open(fp, 'r') as f:
                return yaml.load(f, yaml.SafeLoader)
        except yaml.scanner.ScannerError:
            with open(fp, 'r') as f:
                for l in f.readlines():
                    print(l)
                raise

    outputs_by_pipe_key = outputs_by_pipe_key or dict()

    dat_by_key = {
        k: read_iface_data(tf, lines_group) for tf, (k, lines_group)
        in zip(temps, lines_group_by_pipe_key.items())}
    # DEBUG
    print("DAT BY K: {}".format(dat_by_key))
    for k, outs in outputs_by_pipe_key.items():
        if k not in dat_by_key:
            continue
        dat_by_key[k][OUTKEY] = outs

    data = {PROTOMAP_KEY: pm or PROTOMAP, PL_KEY: dat_by_key}
    # DEBUG
    print("DATA: {}".format(data))

    with open(path_iface_file, 'w') as f:
        yaml.dump(data, f)

    return path_iface_file
