"""Describe the container environment a job runs in (``--record-environment``).

Everything here is best effort: images are never pulled, no registry is
contacted, and whatever docker or bulker cannot answer is left out.
"""

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
from functools import lru_cache

from ubiquerg import expandpath

_LOGGER = logging.getLogger(__name__)

PROBE_TIMEOUT = 15  # seconds per docker/bulker call


def _run(*cmd: str) -> str | None:
    """Stdout of a command, or None if the tool is missing or the call fails."""
    if not shutil.which(cmd[0]):
        return None
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=PROBE_TIMEOUT, check=True
        ).stdout
    except (OSError, subprocess.SubprocessError) as e:
        _LOGGER.debug(f"{cmd[0]} failed: {e}")
        return None


@lru_cache(maxsize=None)
def image_digest(ref: str) -> str | None:
    """Digest ("sha256:...") of an image, or None if it cannot be resolved.

    A docker ref (optionally ``docker://``) is looked up in the local docker
    cache; a local image file (such as an apptainer .sif) is hashed.
    """
    ref = ref.removeprefix("docker://")
    if "://" not in ref and os.path.isfile(expandpath(ref)):
        sha = hashlib.sha256()
        with open(expandpath(ref), "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                sha.update(chunk)
        return "sha256:" + sha.hexdigest()
    out = _run("docker", "image", "inspect", "--format", "{{json .RepoDigests}}", ref)
    try:
        return json.loads(out)[0].split("@")[1]
    except (TypeError, ValueError, IndexError):
        return None


@lru_cache(maxsize=None)
def crate_info(crate: str) -> dict:
    """Bulker crate manifest digest and the images it maps to, if cached locally."""
    out = _run("bulker", "crate", "digest", crate, "--verbose") or ""
    digest = re.search(r"^crate-manifest-digest:\s+(\S+)", out, re.M)
    return {
        "crate_digest": digest.group(1) if digest else None,
        "images": re.findall(r"^\s+\S+\s+\S+\s+\((.+)\)\s*$", out, re.M),
    }


def describe_environment(compute: dict) -> dict:
    """Crate, images and digests for the containers named in compute settings."""
    env = {"crate": compute.get("bulker_crate") or None, "crate_digest": None}
    images = [compute[k] for k in ("docker_image", "apptainer_image") if compute.get(k)]
    if env["crate"]:
        info = crate_info(env["crate"])
        env["crate_digest"] = info["crate_digest"]
        images += [i for i in info["images"] if i not in images]
    env["images"] = images
    env["image_digests"] = {i: d for i in images if (d := image_digest(i))}
    return env
