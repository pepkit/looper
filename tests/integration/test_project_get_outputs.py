""" Tests for interaction between Project and PipelineInterface """

from collections import Counter
from copy import deepcopy
import os
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
""".format(n=WGBS_NAME).splitlines(False)

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
""".format(n=RRBS_NAME).splitlines(False)


PROTOMAP = {RRBS_NAME: RRBS_KEY, WGBS_NAME: WGBS_KEY, "EG": WGBS_KEY}
IFACE_LINES = {WGBS_KEY: WGBS_IFACE_LINES, RRBS_KEY: RRBS_IFACE_LINES}


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
        with open(fp, 'r') as f:
            return yaml.load(f, yaml.SafeLoader)

    outputs_by_pipe_key = outputs_by_pipe_key or dict()

    dat_by_key = {
        k: read_iface_data(tf, lines_group) for tf, (k, lines_group)
        in zip(temps, outputs_by_pipe_key.items())}
    for k, outs in outputs_by_pipe_key.items():
        dat_by_key[k][OUTKEY] = outs

    data = {PROTOMAP_KEY: pm or PROTOMAP, PL_KEY: dat_by_key}
    # DEBUG
    print("DATA:\n{}".format(data))

    with open(path_iface_file, 'w') as f:
        yaml.dump(data, f)

    return path_iface_file


def randconf(ext=".yaml"):
    """
    Randomly generate config filename.

    :param str ext: filename extension
    :return str: randomly generated string to function as filename
    """
    return randstr(LETTERS_AND_DIGITS, 15) + ext


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
def test_no_outputs(tmpdir, name_cfg_file, ifaces):
    """ Pipeline interfaces without outputs --> no Project outputs """
    cfg = tmpdir.join(name_cfg_file).strpath
    iface_paths = [tmpdir.join(randconf()).strpath for _ in ifaces]
    assert all(1 == n for n in Counter(iface_paths).values())
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
    assert {} == prj.get_outputs()


@pytest.mark.skip("not implemented")
def test_malformed_outputs():
    pass


@pytest.mark.skip("not implemented")
def test_only_subproject_has_pifaces():
    pass


@pytest.mark.skip("not implemented")
def test_only_subproject_has_outputs():
    pass


@pytest.mark.skip("not implemented")
def test_main_project_and_subproject_have_outputs():
    pass


@pytest.mark.skip("not implemented")
def test_no_samples_match_protocols_with_outputs():
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


def _write_and_build_prj(conf_file, conf_data):
    with open(conf_file, 'w') as f:
        yaml.dump(conf_data, f)
    return LP(conf_file)
