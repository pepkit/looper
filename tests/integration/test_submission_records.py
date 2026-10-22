"""Submission records (<job_name>.submission.json) written by looper run/runp."""

import glob
import json
import os
import shutil

import pytest
from yaml import dump, safe_load

from looper.cli_pydantic import main
from looper.const import PIPELINE_INTERFACES_KEY
from looper.divvy import select_divvy_config
from tests.integration.conftest import get_outdir, mod_yaml_data
from tests.integration.conftest import test_args_expansion as _args_expansion

DIGEST = "sha256:" + "3f" * 32


def _make_exe(path, body):
    path.write_text("#!/bin/bash\n" + body + "\n")
    path.chmod(0o755)
    return str(path)


@pytest.fixture
def fake_divvy(tmp_path):
    """Divvy config with a fake sbatch (new job id per call), a failing one,
    and a local package."""
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    counter = bin_dir / "counter"
    counter.write_text("100")
    fake_sbatch = _make_exe(
        bin_dir / "fake_sbatch.sh",
        f"n=$(( $(cat {counter}) + 1 )); echo $n > {counter}\n"
        'echo "Submitted batch job $n"',
    )
    fake_fail = _make_exe(bin_dir / "fake_fail.sh", 'echo "sbatch: error: bad"\nexit 1')

    default_cfg = select_divvy_config(None)
    shutil.copytree(
        os.path.join(os.path.dirname(default_cfg), "divvy_templates"),
        tmp_path / "divvy_templates",
    )
    with open(default_cfg) as f:
        adapters = safe_load(f)["adapters"]
    slurm_t = "divvy_templates/slurm_template.sub"
    local = {
        "submission_template": "divvy_templates/localhost_template.sub",
        "submission_command": ".",
    }
    cfg = {
        "adapters": adapters,
        "compute_packages": {
            "default": local,
            "fakelocal": local,
            "fakeslurm": {
                "submission_template": slurm_t,
                "submission_command": fake_sbatch,
                "job_id_regex": r"Submitted batch job (\d+)",
            },
            "fakefail": {
                "submission_template": slurm_t,
                "submission_command": fake_fail,
                "job_id_regex": r"Submitted batch job (\d+)",
            },
        },
    }
    cfg_path = tmp_path / "divvy_config.yaml"
    with open(cfg_path, "w") as f:
        dump(cfg, f)
    return str(cfg_path)


@pytest.fixture
def fake_docker(tmp_path, monkeypatch):
    """Fake docker first on PATH; returns the file it logs its calls to."""
    bin_dir = tmp_path / "dockerbin"
    bin_dir.mkdir()
    calls = tmp_path / "docker.calls"
    _make_exe(
        bin_dir / "docker", f'echo "$@" >> {calls}\necho \'["foo/bar@{DIGEST}"]\''
    )
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    return calls


def _run(tp, divvy, pkg, cmd="run", extra=(), dry=False):
    args = ["--divvy", divvy, "--package", pkg, *extra]
    return main(test_args=_args_expansion(tp, cmd, args, dry=dry))


def _records(tp):
    paths = glob.glob(os.path.join(get_outdir(tp), "submission", "*.submission.json"))
    return {os.path.basename(p): json.load(open(p)) for p in sorted(paths)}


def _only_pipeline1(tp):
    with mod_yaml_data(tp) as config_data:
        config_data[PIPELINE_INTERFACES_KEY] = [config_data[PIPELINE_INTERFACES_KEY][0]]


def test_run_writes_record_with_job_id_per_sample(prep_temp_pep, fake_divvy, capsys):
    tp = prep_temp_pep
    _only_pipeline1(tp)
    _run(tp, fake_divvy, "fakeslurm")
    records = _records(tp)
    assert sorted(records) == [
        f"PIPELINE1_sample{i}.submission.json" for i in (1, 2, 3)
    ]
    rec = records["PIPELINE1_sample1.submission.json"]
    rec.pop("submitted_at")
    script = os.path.join(get_outdir(tp), "submission", "PIPELINE1_sample1.sub")
    assert rec == {
        "job_name": "PIPELINE1_sample1",
        "job_id": rec["job_id"],
        "pid": None,
        "samples": ["sample1"],
        "pipeline": "PIPELINE1",
        "compute_package": "fakeslurm",
        "submission_command": safe_load(open(fake_divvy))["compute_packages"][
            "fakeslurm"
        ]["submission_command"],
        "script": script,
        "submit_stdout": f"Submitted batch job {rec['job_id']}\n",
        "returncode": 0,
    }
    assert {r["job_id"] for r in records.values()} == {"101", "102", "103"}
    # the submit output is still shown to the user
    assert capsys.readouterr().out.count("Submitted batch job") == 3


def test_dry_run_writes_no_record(prep_temp_pep, fake_divvy):
    tp = prep_temp_pep
    _run(tp, fake_divvy, "fakeslurm", dry=True)
    assert _records(tp) == {}


def test_lumped_job_gets_one_record_listing_its_samples(prep_temp_pep, fake_divvy):
    tp = prep_temp_pep
    _only_pipeline1(tp)
    _run(tp, fake_divvy, "fakeslurm", extra=["--lump-n", "2"])
    samples = sorted(r["samples"] for r in _records(tp).values())
    assert samples == [["sample1", "sample2"], ["sample3"]]


def test_runp_record_has_no_samples(prep_temp_pep, fake_divvy):
    tp = prep_temp_pep
    _run(tp, fake_divvy, "fakeslurm", cmd="runp")
    records = _records(tp)
    assert len(records) == 2
    assert all(r["samples"] == [] and r["job_id"] for r in records.values())


def test_local_run_records_pid_instead_of_job_id(prep_temp_pep, fake_divvy):
    tp = prep_temp_pep
    _only_pipeline1(tp)
    _run(tp, fake_divvy, "fakelocal")
    for rec in _records(tp).values():
        assert rec["job_id"] is None
        assert rec["submit_stdout"] is None
        assert isinstance(rec["pid"], int)
        assert rec["returncode"] == 0


def test_failed_submission_still_writes_record(prep_temp_pep, fake_divvy):
    tp = prep_temp_pep
    _only_pipeline1(tp)
    with pytest.raises(SystemExit):
        _run(tp, fake_divvy, "fakefail")
    for rec in _records(tp).values():
        assert rec["returncode"] == 1
        assert rec["job_id"] is None
        assert rec["submit_stdout"] == "sbatch: error: bad\n"


def test_record_environment_flag_adds_environment_block(
    prep_temp_pep, fake_divvy, fake_docker
):
    tp = prep_temp_pep
    _only_pipeline1(tp)
    extra = ["--compute", "docker_image=foo/bar:1.0", "--record-environment"]
    _run(tp, fake_divvy, "fakelocal", extra=extra)
    for rec in _records(tp).values():
        assert rec["environment"] == {
            "crate": None,
            "crate_digest": None,
            "images": ["foo/bar:1.0"],
            "image_digests": {"foo/bar:1.0": DIGEST},
        }
    # one probe for the whole run
    assert fake_docker.read_text().count("\n") == 1


def test_record_environment_compute_setting(prep_temp_pep, fake_divvy, fake_docker):
    tp = prep_temp_pep
    _only_pipeline1(tp)
    extra = [
        "--compute",
        "docker_image=foo/bar:1.0",
        "--compute",
        "record_environment=true",
    ]
    _run(tp, fake_divvy, "fakelocal", extra=extra)
    records = _records(tp)
    assert records
    assert all(
        r["environment"]["image_digests"] == {"foo/bar:1.0": DIGEST}
        for r in records.values()
    )


def test_environment_off_by_default(prep_temp_pep, fake_divvy, fake_docker):
    tp = prep_temp_pep
    _only_pipeline1(tp)
    _run(tp, fake_divvy, "fakelocal", extra=["--compute", "docker_image=foo/bar:1.0"])
    assert all("environment" not in r for r in _records(tp).values())
    assert not fake_docker.exists()
