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

    # DEtermine delimiter and extension
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

    # Setup
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

    def mkdir(d):
        if not os.path.exists(d):
            os.makedirs(d)

    # Create project and ensure folder structure.
    p = Project(conf_path)
    mkdir(p.metadata[RESULTS_SUBDIR_KEY])
    mkdir(p.metadata[SUBMISSION_SUBDIR_KEY])
    map(lambda s: mkdir(sample_folder(p, s)), p.samples)
    return p


def validate_submission_count(project, conductors):
    """

    :param looper.Project project:
    :param Iterable[looper.conductor.SubmissionConductor] conductors: collection
        of submission conductors used
    """
    num_exp = len(project.samples)
    num_obs = _count_submissions(conductors)
    assert num_exp == num_obs, \
        "Expected {} submissions but tallied {}".format(num_exp, num_obs)



def validate_submission_scripts(project, _):
    """
    Check bijection between a project's samples and its submission scripts.

    :param looper.Project project:
    """
    scripts_by_sample = {s.name: _find_subs(project, s) for s in project.samples}
    assert len(project.samples) == len(scripts_by_sample)
    assert all(1 == len(scripts) for scripts in scripts_by_sample.values())


class ConductorBasicSettingsSubmissionScriptTests:
    """ Tests for writing of submission scripts when submission conductor has default settings """

    @staticmethod
    @pytest.mark.parametrize(["automatic", "max_cmds"], [(True, 1)])
    def test_single_sample_auto_conductor_new_sample_scripts(prj, automatic, max_cmds):
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
            conductors[pks[0]].add_sample(s)
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

        # Setup and sanity check that we have 1 sample per sample name to flag.
        preexisting = _collect_flags(prj)
        assert {} == preexisting, "Preexisting flag(s): {}".format(preexisting)
        flagged_samples = list(filter(
            lambda s: s.name in flagged_sample_names, prj.samples))
        assert len(flagged_sample_names) == len(flagged_samples), \
            "Expected {nexp} flagged samples ({exp}) but found {obsn} ({obs})".format(
                nexp=len(flagged_sample_names), exp=flagged_sample_names,
                obsn=len(flagged_samples),
                obs=", ".join(s.name for s in flagged_samples))
        conductors, pipe_keys = _process_base_pliface(prj)

        # Collect pipeline keys and names, ensuring just one pipeline per protocol.
        pks, pns = {}, {}
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

        # Place the flags.
        flag_files_made = []
        for s in flagged_samples:
            flag = "{}_{}_{}".format(pns[s.protocol], s.name, flag_name)
            flag_files_made.append(_mkflag(sample=s, prj=prj, flag=flag))
        assert all(os.path.isfile(f) for f in flag_files_made), \
            "Missing setup flag file(s): {}".format(
                ", ".join([f for f in flag_files_made if not os.path.isfile(f)]))

        # Trigger the automatic submissions.
        map(lambda s: conductors[pks[s.protocol]].add_sample(s), prj.samples)

        # Check the submission counts.
        num_unflagged = len(prj.samples) - len(flagged_sample_names)
        num_subs_obs = _count_submissions(conductors.values())
        assert num_unflagged == num_subs_obs, \
            "{} unflagged sample(s) but {} command submission(s); these should " \
            "match".format(num_unflagged, num_subs_obs)

        def flagged_subs():
            return [f for s in flagged_samples for f in _find_subs(prj, s)]

        # Pretest for presence of unflagged submissions and absence of flagged submissions.
        assert [] == flagged_subs(), "Submission script(s) for flagged " \
            "sample(s): {}".format(", ".join(flagged_subs()))
        all_subs = _find_subs(prj)
        assert len(all_subs) == num_unflagged, "Expected {} submission scripts " \
            "but found {}".format(num_unflagged, len(all_subs))

        # Write the skipped scripts and check their presence.
        map(lambda c: c.write_skipped_sample_scripts(), conductors.values())
        assert len(flagged_samples) == len(flagged_subs())
        assert len(prj.samples) == len(_find_subs(prj))
        # Writing skipped samples has no effect on submission count.
        num_subs_obs = _count_submissions(conductors.values())
        assert num_unflagged == num_subs_obs, \
            "{} unflagged sample(s) but {} command submission(s); these should " \
            "match".format(num_unflagged, num_subs_obs)

    @staticmethod
    @pytest.mark.parametrize(
        "flagged_sample_names",
        [combo for k in range(1, len(SAMPLE_METADATA_RECORDS)) for combo in
         map(list, itertools.combinations([n for n, _ in SAMPLE_METADATA_RECORDS], k))])
    @pytest.mark.parametrize("flag_name", [random.choice(FLAGS)])
    @pytest.mark.parametrize("validate", [validate_submission_count, validate_submission_scripts])
    def test_ignoring_flags(prj, flag_name, flagged_sample_names, validate):
        """ Script creation is automatic, and submission is counted. """
        preexisting = _collect_flags(prj)
        assert {} == preexisting, "Preexisting flag(s): {}".format(preexisting)
        flagged_samples = list(filter(
            lambda s: s.name in flagged_sample_names, prj.samples))
        assert len(flagged_sample_names) == len(flagged_samples), \
            "Expected {expn} flagged samples ({exp}) but found {obsn} ({obs})".format(
                expn=len(flagged_sample_names),
                exp=", ".join(flagged_sample_names), obsn=len(flagged_samples),
                obs=", ".join(s.name for s in flagged_samples))
        flag_files_made = list(map(
            partial(_mkflag, prj=prj, flag=flag_name), flagged_samples))
        assert all(os.path.isfile(f) for f in flag_files_made), \
            "Missing setup flag file(s): {}".format(
                ", ".join([f for f in flag_files_made if not os.path.isfile(f)]))
        preexisting = _collect_flags(prj)
        assert len(flagged_sample_names) == len(preexisting)
        assert set(flag_files_made) == set(itertools.chain(*preexisting.values()))
        conductors, pipe_keys = process_protocols(
            prj, set(PLIFACE_DATA["protocol_mapping"].keys()), ignore_flags=True)
        assert all(map(lambda c: c.ignore_flags, conductors.values())), \
            "Failed to establish precondition, that flags are to be ignored"
        for s in prj.samples:
            pks = pipe_keys[s.protocol]
            assert 1 == len(pks), \
                "Need exactly one pipeline key but got {} for protocol {}: {}".\
                format(len(pks), s.protocol, pks)
            conductors[pks[0]].add_sample(s)
        validate(prj, conductors.values())


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
    """ From array of conductors, accumulate submission count. """
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
    return glob.glob(os.path.join(project.metadata[SUBMISSION_SUBDIR_KEY], name_patt))


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
    """ Create a flag file. """
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
    """ Ensure dry_run is active for each conductor created """
    kwds = copy.deepcopy(kwargs)
    kwds["dry_run"] = True
    return looper.looper.process_protocols(prj, protocols, **kwds)
