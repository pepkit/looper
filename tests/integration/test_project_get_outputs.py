""" Tests for interaction between Project and PipelineInterface """

from collections import Counter, namedtuple
from copy import deepcopy
import itertools
import os
import random
import string
import pytest
import yaml
from looper import Project as LP
from looper.const import *
from looper.exceptions import DuplicatePipelineKeyException
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

WGBS_IFACE_LINES = """name: {n}
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

RRBS_IFACE_LINES = """name: {n}
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

RNASEQ = "RNA-seq"
KALLISTO_ABUNDANCES_KEY = "abundances"
KALLISTO_ABUNDANCES_TEMPLATE = "{sample.name}_isoforms.txt"


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
    assert exp == prj.get_outputs(False)


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

    # DEBUG
    print("Metadata: {}".format(md))

    used_iface_keys = set(itertools.chain(*[pi.keys() for pi in ifaces]))
    keyed_outputs = {pk: declared_outputs[PROTO_NAMES[pk]]
                     for pk in used_iface_keys}
    for path, data in zip(iface_paths, ifaces):
        _write_iface_file(path, data, outputs_by_pipe_key=keyed_outputs)
    for path, data in zip(sp_ifaces_paths, ifaces):
        _write_iface_file(path, data)

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

    assert len(prj.get_outputs(False)) > 0
    exp = {pipe_name: {k: (v, []) for k, v in outs.items()}
           for pipe_name, outs in declared_outputs.items()
           if pipe_name in {PROTO_NAMES[k] for k in used_iface_keys}}
    assert exp == prj.get_outputs(False)
    prj.activate_subproject(sp_name)
    assert len(prj.get_outputs(False)) == 0
    assert {} == prj.get_outputs(False)


def test_multiple_project_units_have_declare_interfaces_with_outputs(tmpdir):
    """ Activation state affects status of Project's outputs. """

    # Generate config filepaths.
    iface_paths = set()
    while len(iface_paths) < 3:
        iface_paths.add(tmpdir.join(randconf()).strpath)
    iface_paths = list(iface_paths)

    # Collect the Project config data.
    main_iface_file, sp_iface_files = iface_paths[0], iface_paths[1:]
    sp_files = dict(zip(["sp1", "sp2"], sp_iface_files))
    prj_dat = {
        METADATA_KEY: {
            OUTDIR_KEY: tmpdir.strpath,
            PIPELINE_INTERFACES_KEY: main_iface_file
        },
        SUBPROJECTS_SECTION: {n: {METADATA_KEY: {PIPELINE_INTERFACES_KEY: f}}
                              for n, f in sp_files.items()}
    }

    # Generate Project config filepath and create Project.
    conf_file = make_temp_file_path(folder=tmpdir.strpath, known=iface_paths)
    for f, (lines_spec, outs_spec) in zip(
            iface_paths,
            [({WGBS_KEY: WGBS_IFACE_LINES}, {WGBS_KEY: DECLARED_OUTPUTS}),
             ({RRBS_KEY: RRBS_IFACE_LINES}, {RRBS_KEY: DECLARED_OUTPUTS}),
             ({WGBS_KEY: WGBS_IFACE_LINES, RRBS_KEY: RRBS_IFACE_LINES},
              {WGBS_KEY: DECLARED_OUTPUTS, RRBS_KEY: DECLARED_OUTPUTS})]):
        _write_iface_file(f, lines_group_by_pipe_key=lines_spec,
                          outputs_by_pipe_key=outs_spec)

    prj = _write_and_build_prj(conf_file, prj_dat)

    # DEBUG
    print("TMPDIR contents:\n{}".format("\n".join(
        os.path.join(tmpdir.strpath, f) for f in os.listdir(tmpdir.strpath))))

    def observe(p):
        return p.get_outputs(False)

    def extract_just_path_template(out_res):
        return {pipe_name: {k: v for k, (v, _) in outs.items()}
                for pipe_name, outs in out_res.items()}

    assert {WGBS_NAME: DECLARED_OUTPUTS} == extract_just_path_template(observe(prj))
    prj.activate_subproject("sp1")
    assert {RRBS_NAME: DECLARED_OUTPUTS} == extract_just_path_template(observe(prj))
    prj.activate_subproject("sp2")
    assert {pn: DECLARED_OUTPUTS for pn in [WGBS_NAME, RRBS_NAME]} == \
           extract_just_path_template(observe(prj))


@pytest.mark.parametrize("noskip", [False, True])
@pytest.mark.parametrize("protocols", 
    [[], [random.choice(["INVALID", "NULL"]) for _ in range(10)]])
@pytest.mark.parametrize("declared_outputs",
    [{n: DECLARED_OUTPUTS for n in [RRBS_NAME, WGBS_NAME]}])
def test_no_samples_match_protocols_with_outputs(
        tmpdir, noskip, protocols, declared_outputs):
    """ get_outputs behavior is sensitive to protocol match and skip flag. """
    temproot = tmpdir.strpath
    path_iface_file = tmpdir.join(randconf()).strpath
    prj_cfg = make_temp_file_path(folder=temproot, known=[path_iface_file])
    prj_dat = {
        METADATA_KEY: {
            OUTDIR_KEY: temproot,
            PIPELINE_INTERFACES_KEY: path_iface_file
        }
    }
    if protocols:
        anns_file = make_temp_file_path(
            folder=temproot, known=[path_iface_file, prj_cfg])
        anns_data = [("sample{}".format(i), p) for i, p in enumerate(protocols)] 
        with open(anns_file, 'w') as f:
            for n, p in [(SAMPLE_NAME_COLNAME, ASSAY_KEY)] + anns_data:
                f.write("{},{}\n".format(n, p))
        prj_dat[METADATA_KEY][SAMPLE_ANNOTATIONS_KEY] = anns_file
    _write_iface_file(
        path_iface_file, {WGBS_KEY: WGBS_IFACE_LINES, RRBS_KEY: RRBS_IFACE_LINES},
        outputs_by_pipe_key={PROTOMAP[n]: DECLARED_OUTPUTS for n in declared_outputs.keys()})
    prj = _write_and_build_prj(prj_cfg, prj_dat)
    exp = {
        pipe_name: {
            path_key: (path_temp, [])
            for path_key, path_temp in decl_outs.items()}
        for pipe_name, decl_outs in declared_outputs.items()
    } if noskip else {}
    assert exp == prj.get_outputs(not noskip)


@pytest.mark.parametrize("protomap", [None, PROTOMAP])
@pytest.mark.parametrize("include_outputs", [False, True])
def test_pipeline_identifier_collision_same_data(tmpdir, protomap, include_outputs):
    """ Interface data that differs from another with same identifier is unexceptional. """

    temproot = tmpdir.strpath
    lines_groups = {WGBS_KEY: WGBS_IFACE_LINES, RRBS_KEY: RRBS_IFACE_LINES}
    outputs = {k: DECLARED_OUTPUTS for k in lines_groups.keys()} \
        if include_outputs else None

    def write_iface(f, pm):
        _write_iface_file(f, lines_groups, outputs, pm)

    iface_file_1 = os.path.join(temproot, "piface1.yaml")
    write_iface(iface_file_1, protomap)
    iface_file_2 = os.path.join(temproot, "piface2.yaml")
    write_iface(iface_file_2, protomap)

    prj_dat = {
        METADATA_KEY: {
            OUTDIR_KEY: tmpdir.strpath,
            PIPELINE_INTERFACES_KEY: [iface_file_1, iface_file_2]
        }
    }
    prj = _write_and_build_prj(os.path.join(temproot, "pc.yaml"), prj_dat)
    exp = {n: {k: (v, []) for k, v in DECLARED_OUTPUTS.items()}
           for n in [WGBS_NAME, RRBS_NAME]} if include_outputs else {}
    assert exp == prj.get_outputs(skip_sample_less=False)


@pytest.mark.parametrize("protomap", [None, PROTOMAP])
@pytest.mark.parametrize("include_outputs", [False, True])
@pytest.mark.parametrize("rep_key", [WGBS_KEY, RRBS_KEY])
def test_pipeline_identifier_collision_different_data(
        tmpdir, include_outputs, protomap, skip_sample_less, rep_key):
    """ Interface data that differs from another with same identifier is exceptional. """
    temproot = tmpdir.strpath

    def write_iface(f, lines_group):
        out_by_key = {k: DECLARED_OUTPUTS for k in lines_group} \
            if include_outputs else None
        _write_iface_file(f, lines_group, out_by_key, pm=protomap)

    iface_file_1 = os.path.join(temproot, "piface1.yaml")
    write_iface(iface_file_1, {rep_key: WGBS_IFACE_LINES})
    iface_file_2 = os.path.join(temproot, "piface2.yaml")
    write_iface(iface_file_2, {rep_key: RRBS_IFACE_LINES})

    def observe():
        prj_cfg = os.path.join(temproot, "pc.yaml")
        prj_dat = {
            METADATA_KEY: {
                OUTDIR_KEY: tmpdir.strpath,
                PIPELINE_INTERFACES_KEY: [iface_file_1, iface_file_2]
            }
        }
        return _write_and_build_prj(prj_cfg, prj_dat).get_outputs(skip_sample_less)

    try:
        observe()
    except Exception as e:
        pytest.fail("Unexpected exception: {}".format(e))

    write_iface(iface_file_1, {rep_key: WGBS_IFACE_LINES[1:]})
    write_iface(iface_file_2, {rep_key: RRBS_IFACE_LINES[1:]})

    # DEBUG
    def print_iface(fp):
        with open(fp, 'r') as f:
            return yaml.load(f, yaml.SafeLoader)

    # DEBUG
    print("First interface contents (below):\n{}\n".format(print_iface(iface_file_1)))
    print("Second interface contents (below):\n{}".format(print_iface(iface_file_2)))

    with pytest.raises(DuplicatePipelineKeyException):
        observe()


def test_sample_collection_accuracy(tmpdir, skip_sample_less, rna_pi_lines):
    """ Names of samples collected for each pipeline are as expected. """
    temproot = tmpdir.strpath
    samples = [("sampleA", WGBS_NAME), ("sample2", "HiChIP"),
               ("sampleC", RNASEQ), ("sample4", "ATAC"),
               ("sampleE", WGBS_NAME), ("sample6", "HiChIP"),
               ("sampleG", RNASEQ), ("sample8", "ATAC")]
    iface_files = list(get_temp_paths(2, temproot))
    anns_file = make_temp_file_path(
        temproot, iface_files,
        generate=lambda: "".join(randstr(LETTERS_AND_DIGITS, 20)) + ".csv")
    with open(anns_file, 'w') as f:
        f.write("\n".join("{},{}".format(*pair) for pair in
                          [(SAMPLE_NAME_COLNAME, ASSAY_KEY)] + samples))
    _write_iface_file(
        iface_files[0],
        lines_group_by_pipe_key={WGBS_KEY: WGBS_IFACE_LINES},
        outputs_by_pipe_key={WGBS_KEY: DECLARED_OUTPUTS}, pm=PROTOMAP)
    with open(iface_files[1], 'w') as f:
        for l in rna_pi_lines:
            f.write(l)
    prj_dat = {
        METADATA_KEY: {
            SAMPLE_ANNOTATIONS_KEY: anns_file,
            OUTDIR_KEY: tmpdir.strpath,
            PIPELINE_INTERFACES_KEY: iface_files
        }
    }
    prj_cfg = make_temp_file_path(temproot, iface_files + [anns_file])
    prj = _write_and_build_prj(prj_cfg, prj_dat)
    kallisto_outputs = {KALLISTO_ABUNDANCES_KEY: KALLISTO_ABUNDANCES_TEMPLATE}
    exp = {
        WGBS_NAME: {k: (v, [sn for sn, pn in samples if pn == WGBS_NAME]) for k, v in DECLARED_OUTPUTS.items()},
        RNA_PIPES["kallisto"].name: {
            KALLISTO_ABUNDANCES_KEY: (
                KALLISTO_ABUNDANCES_TEMPLATE,
                [sn for sn, prot in samples if prot == RNASEQ]
            ) for k, v in kallisto_outputs.items()
        }
    }
    assert exp == prj.get_outputs(skip_sample_less)


@pytest.mark.skip("not implemented")
def test_protocol_collection_accuracy(tmpdir):
    """ Names of protocols collected for each pipeline are as expected. """
    pass


def get_temp_paths(n, folder, known=None, generate=randconf):
    """
    Generate unique tempfile paths pointing to within a particular folder.

    :param int n: number of paths to generate
    :param str folder: path to folder into which randomly generated filepaths
        should point
    :param Iterable[str] known: collection of filepaths to prohibit a
        match to for a newly generated path
    :param function() -> str generate: how to randomly generate a filename
    :return Iterable[str]: collection of unique tempfile paths pointing to
        within a particular folder.
    """
    paths = set()
    known = set(known or [])
    gen = lambda pool: make_temp_file_path(folder, pool, generate)
    while len(paths) < n:
        p = gen(known)
        known.add(p)
        paths.add(p)
    return paths


def make_temp_file_path(folder, known, generate=randconf):
    """
    Generate a new tempfile path.

    :param str folder: path to folder that represents parent of path to
        generate, i.e. the path to the folder to which a randomized filename
        is to be joined
    :param Iterable[str] known: collection of current filePATHs
    :param function() -> str generate: how to generate fileNAME
    :return str: randomly generated filepath that doesn't match a known value
    """
    while True:
        fp = os.path.join(folder, generate())
        if fp not in known:
            return fp


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
    for k, outs in outputs_by_pipe_key.items():
        if k not in dat_by_key:
            continue
        dat_by_key[k][OUTKEY] = outs

    data = {PROTOMAP_KEY: pm or PROTOMAP, PL_KEY: dat_by_key}
    with open(path_iface_file, 'w') as f:
        yaml.dump(data, f)

    return path_iface_file


class PipeSpec(object):
    """ Pipeline key and name """
    def __init__(self, key, name=None):
        assert "" != os.path.splitext(key)[1]
        self.key = key
        self.name = name or key.rstrip(".py")


RNA_PIPES = {"kallisto": PipeSpec("rnaKallisto.py"),
             "tophat": PipeSpec("rnaTopHat.py"),
             "bitseq": PipeSpec("rnaBitSeq.py")}


@pytest.fixture(scope="function")
def rna_pi_lines():
    return """protocol_mapping:
  {rnaseq_proto_name}: [{bs_name}, {kall_name}, {th_name}]
  SMART: [{bs_name}, {th_name}]

pipelines:
  {bs_key}:
    name: {bs_name}
    path: src/rnaBitSeq.py
    arguments:
      "--sample-name": sample_name
      "--genome": transcriptome
      "--input": data_source
      "--single-or-paired": read_type
    required_input_files: [data_source]
    ngs_input_files: [data_source]    
    resources:
      default:
        file_size: "0"
        cores: "6"
        mem: "36000"
        time: "2-00:00:00"
      large:
        file_size: "4"
        cores: "6"
        mem: "44000"
        time: "2-00:00:00"

  {th_key}:
    name: {th_name}
    path: src/rnaTopHat.py
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
        cores: "2"
        mem: "60000"
        time: "7-00:00:00"

  {kall_key}:
    name: {kall_name}
    path: src/rnaKallisto.py
    required_input_files: [data_source]
    ngs_input_files: [data_source]
    arguments:
      "--sample-yaml": yaml_file
      "--sample-name": sample_name
      "--input": data_source
      "--single-or-paired": read_type
    optional_arguments:
      "--input2": read2
      "--fragment-length": fragment_length
      "--fragment-length-sdev": fragment_length_sdev
    outputs:
      {abundances_key}: \"{abundances_val}\"
    resources:
      default:
        cores: "2"
        mem: "4000"
        time: "0-6:00:00"
      normal:
        min_file_size: "3"    
        cores: "2"
        mem: "8000"
        time: "0-12:00:00"
""".format(
    rnaseq_proto_name=RNASEQ,
    bs_key=RNA_PIPES["bitseq"].key, bs_name=RNA_PIPES["bitseq"].name,
    th_key=RNA_PIPES["tophat"].key, th_name=RNA_PIPES["tophat"].name,
    kall_key=RNA_PIPES["kallisto"].key, kall_name=RNA_PIPES["kallisto"].name,
    abundances_key=KALLISTO_ABUNDANCES_KEY,
    abundances_val=KALLISTO_ABUNDANCES_TEMPLATE).splitlines(True)
