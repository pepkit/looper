""" Tests for submission script creation, content, etc. """

from collections import OrderedDict
import os
import pytest
import yaml
from looper import PipelineInterface
from looper.conductor import SubmissionConductor
from looper.const import *
from looper.looper import Project, process_protocols
from peppy import ASSAY_KEY, SAMPLE_ANNOTATIONS_KEY, SAMPLE_NAME_COLNAME, \
    SAMPLE_SUBANNOTATIONS_KEY

__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


WGBS_PIPE = "wgbs.py"
ATAC_PIPE = "pepatac.py"
PIPE_NAME_KEY = "name"
PIPE_PATH_KEY = "path"
PIPE_RESOURCES_KEY = "resources"
SAMPLE_METADATA_HEADER = [SAMPLE_NAME_COLNAME, ASSAY_KEY]
ASSAYS = ["WGBS", "WGBS",  "ATAC", "ATAC"]
SAMPLE_METADATA_RECORDS = [("sample" + str(i), p) for i, p in enumerate(ASSAYS)]
DEFAULT_RESOURCES = {
    "file_size": "0", "cores": "1", "mem": "4000", "time": "00-01:00:00"}
DEFAULT_RESOURCES_KEY = "default"
ATAC_SPEC = {
    PIPE_NAME_KEY: "PEPATAC", PIPE_PATH_KEY: ATAC_PIPE,
    PIPE_RESOURCES_KEY: {DEFAULT_RESOURCES_KEY: DEFAULT_RESOURCES}
}
WGBS_SPEC = {
    PIPE_NAME_KEY: "WGBS", PIPE_PATH_KEY: WGBS_PIPE,
    PIPE_RESOURCES_KEY: {DEFAULT_RESOURCES_KEY: DEFAULT_RESOURCES}
}
PIPE_SPECS = {"pepatac.py": ATAC_SPEC, "wgbs.py": WGBS_SPEC}
PLIFACE_DATA = {
    "protocol_mapping": {"ATAC": ATAC_PIPE, "WGBS": WGBS_PIPE},
    "pipelines": PIPE_SPECS
}


def sample_writer(request):
    """
    Create a function with which to write sample/subsample records.

    :return function: how to write sample/subsample records
    """
    try:
        sep = request.getfixturevalue("cfg_sep")
    except Exception:
        sep = None
    sep = sep or "\t"
    if sep in [", ", ","]:
        ext = ".csv"
    elif sep == "\t":
        ext = ".tsv"
    else:
        ext = ".txt"
    def write(folder, records):
        anns = os.path.join(folder, "psa" + ext)
        def go(recs, fp):
            with open(fp, 'w') as f:
                f.write(os.linesep.join(sep.join(r) for r in recs))
        if records[0] != SAMPLE_METADATA_HEADER:
            records = [SAMPLE_METADATA_HEADER] + records
        go(records, anns)
        try:
            subannotation_data = request.getfixturevalue("subannotation_data")
        except Exception:
            return anns, None
        subanns = os.path.join(folder, "subanns" + ext)
        go(subannotation_data, subanns)
        return anns, subanns
    return write


@pytest.fixture(scope="function")
def prj(request, tmpdir):
    """ Provide requesting test case with a project instance. """
    outdir = tmpdir.strpath
    anns, subanns = sample_writer(request)(outdir, SAMPLE_METADATA_RECORDS)
    conf_path = os.path.join(outdir, "prj.yaml")
    metadata = {SAMPLE_ANNOTATIONS_KEY: anns, "output_dir": outdir}
    if subanns:
        metadata[SAMPLE_SUBANNOTATIONS_KEY] = subanns
    prjdat = {"metadata": metadata}
    with open(conf_path, 'w') as f:
        yaml.dump(prjdat, f)
    return Project(conf_path)


@pytest.fixture(scope="function")
def pliface():
    """ Basic pipeline interface to share across test cases """
    return PipelineInterface(PLIFACE_DATA)


@pytest.fixture(scope="function")
def conductors(request):
    """ Submission conductor """
    kwargs = {"pipeline_interface": pliface, "prj": prj}
    for k in ["cmd_base", "dry_run", "ignore_flags",
              "max_cmds", "max_size", "automatic"]:
        try:
            v = request.getfixturevalue(k)
        except Exception:
            continue
        if v is not None:
            kwargs[k] = v
    return {pl: SubmissionConductor(pipeline_key=pl, **kwargs)
            for pl in pliface.pipelines.keys()}


@pytest.mark.parametrize(["automatic", "max_cmds"], [(True, 1)])
def test_single_sample_auto_conductor_new_sample_scripts(
        tmpdir, prj, automatic, max_cmds):
    """ Validate base/ideal case of submission conduction w.r.t. scripts. """
    samples = prj.samples
    conductors, pipe_keys = process_protocols(prj, {s.protocol for s in samples})
    subdir = tmpdir.join(prj.metadata[SUBMISSION_SUBDIR_KEY]).strpath
    assert 0 == _count_files(subdir)
    for s in samples:
        pks = pipe_keys[s.protocol]
        assert 1 == len(pks), \
            "Multiple pipelines for sample {}: {}".format(s.name, pks)
        c = conductors[pks[0]]
        c.add_sample(s)
        exp_sub = os.path.join(subdir, s.name + ".sub")
        assert os.path.isfile(exp_sub)


@pytest.mark.skip("Not implemented")
def test_new_samples_get_scripts(tmpdir):
    """ Base case; a new/'fresh' sample should get a submission script. """
    pass


@pytest.mark.skip("Not implemented")
def test_flagged_samples_get_scripts(tmpdir):
    """ Sample with a status flag can still has script written. """
    pass


@pytest.mark.skip("Not implemented")
def test_troubled_samples_get_no_script(tmpdir):
    """ Sample for which argstring creation fails gets no sript. """
    pass


def test_convergent_protocol_mapping_keys(tmpdir):
    """ Similarly-named protocols do not result in multiple pipelines. """
    protomap = OrderedDict([
        ("WGBS", WGBS_PIPE), ("wgbs", WGBS_PIPE), ("ATAC-SEQ", ATAC_PIPE),
        ("ATACseq", ATAC_PIPE), ("ATAC-seq", ATAC_PIPE)])
    records = [("sample" + str(i), p) for i, p in enumerate(protomap)]
    outdir = tmpdir.strpath
    sep, ext = "\t", ".tsv"
    anns_path = os.path.join(outdir, "anns" + ext)
    records = [SAMPLE_METADATA_HEADER] + records
    with open(anns_path, 'w') as f:
        f.write(os.linesep.join(sep.join(r) for r in records))
    pliface_data = {"protocol_mapping": dict(protomap), "pipelines": PIPE_SPECS}
    pliface_filepath = os.path.join(outdir, "pipes.yaml")
    with open(pliface_filepath, 'w') as f:
        yaml.dump(pliface_data, f)
    metadata = {"output_dir": outdir, SAMPLE_ANNOTATIONS_KEY: anns_path,
                "pipeline_interfaces": pliface_filepath}
    _touch_pipe_files(tmpdir.strpath, pliface_data)
    prjdat = {"metadata": metadata}
    pcfg = tmpdir.join("prj.yaml").strpath
    with open(pcfg, 'w') as f:
        yaml.dump(prjdat, f)
    # DEBUG
    with open(anns_path, 'r') as f:
        print("SAMPLE LINES:\n{}".format(f.readlines()))
    prj = Project(pcfg)

    # DEBUG
    print("INTERFACES BY PROTOCOL: {}".format(prj.interfaces_by_protocol))

    conductors, pipe_keys = process_protocols(prj, protomap.keys())
    # Conductors collection is keyed on pipeline, not protocol
    assert set(conductors.keys()) == set(protomap.values())
    # Collection of pipeline keys by protocol, not pipeline
    assert len(pipe_keys) == len(protomap)
    multi_pipes = [(p, ks) for p, ks in pipe_keys.items() if len(ks) > 1]
    assert [] == multi_pipes, "{} protocol(s) mapped to multiple pipelines: {}".\
        format(len(multi_pipes), multi_pipes)


def _count_files(p, *preds):
    return sum(1 for f in os.listdir(p)
               if os.path.isfile(f) and all(map(lambda p: p(f), preds)))


def _touch_pipe_files(folder, pliface):
    for pipe in pliface["pipelines"].values():
        path = os.path.join(folder, pipe["path"])
        with open(path, 'w'):
            print("Writing pipe: {}".format(path))
