"""Tests for looper's cleaning functionality"""

import argparse
import pytest
from looper.looper import Cleaner
from looper import Project


def build_namespace(**kwargs):
    """Create an argparse namespace with given key-value pairs."""
    ns = argparse.Namespace()
    for opt, arg in kwargs.items():
        setattr(ns, opt, arg)
    return ns


DRYRUN_OR_NOT_PREVIEW = [
    pytest.param(args, preview, id=param_name)
    for args, preview, param_name in [
        (build_namespace(dry_run=False), False, "not_preview__only"),
        (build_namespace(dry_run=True), False, "dry_run__only"),
        (build_namespace(dry_run=True), True, "dry_run__and__not_preview"),
    ]
]


@pytest.mark.parametrize(["args", "preview"], DRYRUN_OR_NOT_PREVIEW)
def test_cleaner_does_not_crash(args, preview, prep_temp_pep):
    prj = Project(prep_temp_pep)
    prj._samples = []
    clean = Cleaner(prj)
    try:
        retcode = clean(args=args, preview_flag=preview)
    except Exception as e:
        pytest.fail(f"Cleaning call hit error: {e}")
    else:
        assert retcode == 0
