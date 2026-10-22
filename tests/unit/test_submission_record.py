"""Which job_id_regex applies to a compute package, and what it matches."""

import re

import pytest

from looper.conductor import _job_id_regex
from looper.const import JOB_ID_REGEXES


@pytest.mark.parametrize(
    "compute,expected",
    [
        ({"submission_command": "sbatch"}, JOB_ID_REGEXES["sbatch"]),
        (
            {"submission_command": "/usr/bin/sbatch --parsable"},
            JOB_ID_REGEXES["sbatch"],
        ),
        ({"submission_command": "qsub"}, JOB_ID_REGEXES["qsub"]),
        ({"submission_command": "."}, None),
        ({"submission_command": "sh"}, None),
        ({"submission_command": "sbatch", "job_id_regex": "job (\\d+)"}, "job (\\d+)"),
        ({"submission_command": "sbatch", "job_id_regex": None}, None),
    ],
)
def test_job_id_regex_explicit_key_wins_else_default_by_command(compute, expected):
    assert _job_id_regex(compute) == expected


@pytest.mark.parametrize(
    "command,stdout,job_id",
    [
        ("sbatch", "Submitted batch job 12345\n", "12345"),
        ("qsub", 'Your job 777 ("x") has been submitted\n', "777"),
        ("qsub", 'Your job-array 778.1-3:1 ("x") has been submitted\n', "778"),
        ("bsub", "Job <42> is submitted to queue <normal>.\n", "42"),
    ],
)
def test_default_regexes_match_scheduler_output(command, stdout, job_id):
    assert re.search(JOB_ID_REGEXES[command], stdout).group(1) == job_id
