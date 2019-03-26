""" Tests for submission script creation, content, etc. """

from collections import OrderedDict
import copy
from functools import partial
import glob
import itertools
import os
import random

import pytest
import yaml
from peppy import FLAGS
import looper
from looper.const import *
from looper.looper import Project
from looper.utils import  fetch_sample_flags, sample_folder
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
    pipe_iface_path = os.path.join(outdir, "pliface.yaml")
    with open(pipe_iface_path, 'w') as f:
        yaml.dump(PLIFACE_DATA, f)
    _touch_pipe_files(outdir, PLIFACE_DATA)
    metadata = {SAMPLE_ANNOTATIONS_KEY: anns,
                "output_dir": outdir, "pipeline_interfaces": pipe_iface_path}
    if subanns:
        metadata[SAMPLE_SUBANNOTATIONS_KEY] = subanns
    prjdat = {"metadata": metadata}
    with open(conf_path, 'w') as f:
        yaml.dump(prjdat, f)
    p = Project(conf_path)
    def mkdir(d):
        if not os.path.exists(d):
            os.makedirs(d)
    mkdir(p.metadata[RESULTS_SUBDIR_KEY])
    mkdir(p.metadata[SUBMISSION_SUBDIR_KEY])
    for s in p.samples:
        d = sample_folder(p, s)
        mkdir(d)
    return p


class ConductorBasicSettingsSubmissionScriptTests:
    """ Tests for writing of submission scripts when submission conductor has default settings """

    @staticmethod
    @pytest.mark.parametrize(["automatic", "max_cmds"], [(True, 1)])
    def test_single_sample_auto_conductor_new_sample_scripts(
            tmpdir, prj, automatic, max_cmds):
        """ Validate base/ideal case of submission conduction w.r.t. scripts. """
        samples = prj.samples
        conductors, pipe_keys = \
            process_protocols(prj, {s.protocol for s in samples})
        subdir = prj.metadata[SUBMISSION_SUBDIR_KEY]
        assert 0 == _count_files(subdir)
        for s in samples:
            pks = pipe_keys[s.protocol]
            assert 1 == len(pks), \
                "Multiple pipelines for sample {}: {}".format(s.name, pks)
            c = conductors[pks[0]]
            # DEBUG
            print("CONTENTS: {}".format(", ".join(os.listdir(tmpdir.strpath))))
            print("RESULTS: {}".format(", ".join(os.listdir(os.path.join(tmpdir.strpath, "results_pipeline")))))
            c.add_sample(s)
            sub_fn_suffix = s.name + ".sub"
            contents = os.listdir(subdir)
            assert 1 == len([f for f in contents if sub_fn_suffix in f]), \
                "No filename containing {} in {}; contents: {}".\
                format(sub_fn_suffix, subdir, contents)

    @staticmethod
    @pytest.mark.parametrize(
        "flagged_sample_names",
        [combo for k in range(1, len(SAMPLE_METADATA_RECORDS)) for combo in
         map(list, itertools.combinations([n for n, _ in SAMPLE_METADATA_RECORDS], k))])
    @pytest.mark.parametrize("flag_name", FLAGS)
    def test_not_ignoring_flags(prj, flag_name, flagged_sample_names):
        """ Script creation is via separate call, and there's no submission. """
        preexisting = _collect_flags(prj)
        assert {} == preexisting, "Preexisting flag(s): {}".format(preexisting)
        flagged_samples = list(filter(
            lambda s: s.name in flagged_sample_names, prj.samples))
        assert len(flagged_sample_names) == len(flagged_samples), \
            "Expected {nexp} flagged samples ({exp}) but found {obsn} ({obs})".format(
                nexp=len(flagged_sample_names), exp=flagged_sample_names,
                obsn=len(flagged_samples),
                obs=", ".join(s.name for s in flagged_samples))
        pks, pns = {}, {}
        conductors, pipe_keys = _process_base_pliface(prj)
        original_arg_string_methods = {}
        for k, c in conductors.items():
            original_arg_string_methods[k] = c.pl_iface.get_arg_string
            #conductors[k].pl_iface.get_arg_string = lambda *args, **kwargs: "testing"
        for s in prj.samples:
            prot = s.protocol
            ks = pipe_keys[prot]
            assert 1 == len(ks), \
                "Need exactly one pipeline key but got {} for protocol {}: {}". \
                    format(len(pks), s.protocol, pks)
            key = ks[0]

            if prot in pks and pks[prot] != key:
                raise Exception("Protocol {} already mapped to {}".format(prot, pks[prot]))
            pks[prot] = key
            name = PLIFACE_DATA["pipelines"][key][PIPE_NAME_KEY]
            if prot in pns and pns[prot] != name:
                raise Exception("Protocol {} already mapped to {}".format(prot, pns[prot]))
            pns[prot] = name
        flag_files_made = []
        for s in flagged_samples:
            flag = "{}_{}".format(pns[s.protocol], s.name)
            flag_files_made.append(_mkflag(sample=s, prj=prj, flag=flag))
        assert all(os.path.isfile(f) for f in flag_files_made), \
            "Missing setup flag file(s): {}".format(
                ", ".join([f for f in flag_files_made if not os.path.isfile(f)]))
        num_unflagged = len(prj.samples) - len(flagged_sample_names)
        for s in prj.samples:
            c = conductors[pks[s.protocol]]
            #c.pl_iface.get_arg_string = lambda *args, **kwargs: "testing"
            c.add_sample(s)
        num_subs_obs = _count_submissions(conductors.values())
        assert num_unflagged == num_subs_obs, \
            "{} unflagged sample(s) but {} command submission(s); these should " \
            "match".format(num_unflagged, num_subs_obs)
        def flagged_subs():
            return [f for s in flagged_samples for f in _find_subs(prj, s)]
        assert [] == flagged_subs(), "Submission script(s) for flagged " \
            "sample(s): {}".format(", ".join(flagged_subs()))
        all_subs = _find_subs(prj)
        assert len(all_subs) == num_unflagged, "Expected {} submission scripts " \
            "but found {}".format(num_unflagged, len(all_subs))
        print("CONDUCTORS: {}".format(conductors))
        for k, c in conductors.items():
            print("Writing skipped sample scripts: {}".format(k))
            c.write_skipped_sample_scripts()
        assert len(flagged_samples) == len(flagged_subs())
        assert len(prj.samples) == len(_find_subs(prj))

    @staticmethod
    @pytest.mark.skip("Not implemented")
    @pytest.mark.parametrize("flagged_sample_names",
        list(itertools.chain(*[
            list(itertools.combinations(SAMPLE_METADATA_RECORDS, k))
            for k in range(1, len(SAMPLE_METADATA_RECORDS))])))
    @pytest.mark.parametrize("flag_name", [random.choice(FLAGS)])
    def test_ignoring_flags(prj, flag_name, flagged_sample_names):
        """ Script creation is automatic, and submission is counted. """
        preexisting = _collect_flags(prj)
        assert {} == preexisting, "Preexisting flag(s): {}".format(preexisting)
        flagged_samples = list(filter(
            lambda s: s.name in flagged_sample_names, prj.samples))
        assert len(flagged_sample_names) == len(flagged_samples), \
            "Expected 2 flagged samples ({exp}) but found {obsn} ({obs})".format(
                exp=", ".join(flagged_sample_names), obsn=len(flagged_samples),
                obs=", ".join(s.name for s in flagged_samples))
        flag_files_made = list(map(
            partial(_mkflag, prj=prj, flag=flag_name), flagged_samples))
        assert all(os.path.isfile(f) for f in flag_files_made), \
            "Missing setup flag file(s): {}".format(
                ", ".join([f for f in flag_files_made if not os.path.isfile(f)]))
        preexisting = _collect_flags(prj)
        assert len(prj.samples) == len(preexisting)
        assert set(flag_files_made) == set(itertools.chain(*preexisting.values()))
        conductors, pipe_keys = process_protocols(
            prj, set(PLIFACE_DATA), ignore_flags=True)
        assert all(map(lambda c: c.ignore_flags, conductors.values())), \
            "Failed to establish precondition, that flags are to be ignored"
        for s in prj.samples:
            pks = pipe_keys[s.protocol]
            assert 1 == len(pks), \
                "Need exactly one pipeline key but got {} for protocol {}: {}".\
                format(len(pks), s.protocol, pks)
            conductors[pks[0]].add_sample(s)
        assert len(prj.samples) == _count_submissions(conductors.values())
        scripts_by_sample = {s.name: _find_subs(prj, s) for s in prj.samples}
        assert len(prj.samples) == len(scripts_by_sample)
        assert all(1 == len(scripts) for scripts in scripts_by_sample.values())

    @staticmethod
    @pytest.mark.skip("Not implemented")
    @pytest.mark.parametrize("ignore", [False, True])
    @pytest.mark.parametrize(
        "flagged_sample", [sn for sn, _ in SAMPLE_METADATA_RECORDS])
    def test_flagged_samples_are_submitted_iff_ignoring_flags(
            ignore, tmpdir, prj, flagged_sample):
        """ When flag exists, submission of a pipe/sample is conditional. """
        pass

    @staticmethod
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
    prj = Project(pcfg)

    conductors, pipe_keys = process_protocols(prj, set(protomap.keys()))

    # Conductors collection is keyed on pipeline, not protocol
    assert set(conductors.keys()) == set(protomap.values())
    # Collection of pipeline keys by protocol, not pipeline
    assert len(pipe_keys) == len(protomap)
    multi_pipes = [(p, ks) for p, ks in pipe_keys.items() if len(ks) > 1]
    assert [] == multi_pipes, "{} protocol(s) mapped to multiple pipelines: {}".\
        format(len(multi_pipes), multi_pipes)


def _collect_flags(project):
    """
    Collect by sample name any flag files within a project.

    :param looper.Project project: project for which to collect flags
    :return Mapping[str, Iterable[str]]: binding between sample name and
        collection of paths to flag files
    """
    acc = {}
    for s in project.samples:
        fs = fetch_sample_flags(project, s)
        if fs:
            acc[s.name] = fs
    return acc


def _count_files(p, *preds):
    """ Count the number of files immediately within folder that match predicate(s). """
    return sum(1 for f in os.listdir(p)
               if os.path.isfile(f) and all(map(lambda p: p(f), preds)))


def _count_submissions(conductors):
    return sum(c.num_cmd_submissions for c in conductors)


def _find_subs(project, sample=None):
    """
    Find submission script paths associated with a project.

    :param looper.Project project: project of interest
    :param peppy.Sample sample: specific sample of interest, optional
    :return list[str]: collection of filepaths, each of which is a path to
        (ostensibly) a submission script associated with the given project,
        and specific sample if provided
    """
    name_patt = "{}*.sub".format("*" + sample.name if sample else "")
    # DEBUG
    query = os.path.join(
        project.metadata[SUBMISSION_SUBDIR_KEY], name_patt)
    print("SEEKING: {}".format(query))
    return glob.glob(query)


def _process_base_pliface(prj, **kwargs):
    """
    Based on defined data here, create the submission conductors for a project.

    :param looper.Project prj: project for which submission conductors are
        to be created
    :return Mapping[str, looper.conductor.SubmissionConductor], Mapping[str, list[str]]:
        mapping from pipeline key to submission conductor, and mapping from
        protocol name to collection of keys for pipelines for that protocol
    """
    return process_protocols(
        prj, set(PLIFACE_DATA["protocol_mapping"].keys()), **kwargs)


def _mkflag(sample, prj, flag):
    fp = os.path.join(sample_folder(prj, sample), flag + ".flag")
    return _mkfile(fp, "Making flag for {}".format(sample.name))


def _mkfile(f, message=None):
    """ Create a new, empty file. """
    assert not os.path.exists(f), "File already exists: {}".format(f)
    with open(f, 'w'):
        if message:
            print("{}: {}".format(message, f))
    return f


def _touch_pipe_files(folder, pliface):
    """ Ensure existence of files at paths designated as pipeline interfaces. """
    for pipe in pliface["pipelines"].values():
        path = os.path.join(folder, pipe["path"])
        _mkfile(path, message="Writing pipe")


def process_protocols(prj, protocols, **kwargs):
    kwds = copy.deepcopy(kwargs)
    kwds["dry_run"] = True
    return looper.looper.process_protocols(prj, protocols, **kwds)
