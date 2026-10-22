"""describe_environment: container refs from compute settings plus digests."""

import hashlib

import pytest

from looper import container_digests
from looper.container_digests import describe_environment

DIGEST = "sha256:" + "3f" * 32
BULKER_OUT = """crate-manifest-digest:  zR9kiCcE6JTSkfJI7H9hfEsj9SdgklqL
  abc123  samtools (quay.io/biocontainers/samtools:1.23)
  def456  bowtie2 (quay.io/biocontainers/bowtie2:2.5)
"""


@pytest.fixture
def fake_bin(tmp_path, monkeypatch):
    """PATH with only tmp_path/bin; returns a function that adds a fake tool."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    monkeypatch.setenv("PATH", str(bin_dir))
    container_digests.image_digest.cache_clear()
    container_digests.crate_info.cache_clear()

    def make_tool(name, body):
        tool = bin_dir / name
        tool.write_text(f"#!/bin/sh\n{body}\n")
        tool.chmod(0o755)

    return make_tool


def test_docker_and_bulker_supply_digests(fake_bin):
    fake_bin("docker", f"""echo '["foo/bar@{DIGEST}"]'""")
    fake_bin("bulker", f"printf '%s' '{BULKER_OUT}'")
    env = describe_environment(
        {"bulker_crate": "databio/pepatac:1.1.3", "docker_image": "foo/bar:1.0"}
    )
    assert env == {
        "crate": "databio/pepatac:1.1.3",
        "crate_digest": "zR9kiCcE6JTSkfJI7H9hfEsj9SdgklqL",
        "images": [
            "foo/bar:1.0",
            "quay.io/biocontainers/samtools:1.23",
            "quay.io/biocontainers/bowtie2:2.5",
        ],
        # the fake docker answers every ref with the same digest
        "image_digests": {
            "foo/bar:1.0": DIGEST,
            "quay.io/biocontainers/samtools:1.23": DIGEST,
            "quay.io/biocontainers/bowtie2:2.5": DIGEST,
        },
    }


def test_missing_tools_leave_refs_but_no_digests(fake_bin):
    env = describe_environment(
        {"bulker_crate": "databio/pepatac:1.1.3", "docker_image": "foo/bar:1.0"}
    )
    assert env == {
        "crate": "databio/pepatac:1.1.3",
        "crate_digest": None,
        "images": ["foo/bar:1.0"],
        "image_digests": {},
    }


def test_local_sif_is_hashed(fake_bin, tmp_path):
    sif = tmp_path / "img.sif"
    sif.write_bytes(b"not really a sif")
    env = describe_environment({"apptainer_image": str(sif)})
    expected = "sha256:" + hashlib.sha256(b"not really a sif").hexdigest()
    assert env["image_digests"] == {str(sif): expected}
