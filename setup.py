#! /usr/bin/env python

import os
import sys

from setuptools import setup

# Additional keyword arguments for setup().
extra = {}


# Ordinary dependencies
DEPENDENCIES = []
with open("requirements/requirements-all.txt", "r") as reqs_file:
    for line in reqs_file:
        if not line.strip():
            continue
        # DEPENDENCIES.append(line.split("=")[0].rstrip("<>"))
        DEPENDENCIES.append(line)


# numexpr for pandas
try:
    import numexpr
except ImportError:
    # No numexpr is OK for pandas.
    pass
else:
    # pandas 0.20.2 needs updated numexpr; the claim is 2.4.6, but that failed.
    DEPENDENCIES.append("numexpr>=2.6.2")
extra["install_requires"] = DEPENDENCIES


# Additional files to include with package
def get_static(name, condition=None):
    static = [
        os.path.join(name, f)
        for f in os.listdir(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), name)
        )
    ]
    if condition is None:
        return static
    else:
        return [i for i in filter(lambda x: eval(condition), static)]


# scripts to be added to the $PATH
# scripts = get_static("scripts", condition="'.' in x")
# scripts removed (TO remove this)
scripts = None


with open("looper/_version.py", "r") as versionfile:
    version = versionfile.readline().split()[-1].strip("\"'\n")

with open("README.md") as f:
    long_description = f.read()

setup(
    name="looper",
    packages=["looper"],
    version=version,
    description="A pipeline submission engine that parses sample inputs and submits pipelines for each sample.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    keywords="bioinformatics, sequencing, ngs",
    url="https://github.com/pepkit/looper",
    author="Nathan Sheffield, Vince Reuter, Michal Stolarczyk, Johanna Klughammer, Andre Rendeiro",
    license="BSD2",
    entry_points={
        "console_scripts": [
            "looper = looper.cli_pydantic:main_cli",
            "divvy = looper.__main__:divvy_main",
        ],
    },
    scripts=scripts,
    package_data={"looper": ["submit_templates/*"]},
    include_package_data=True,
    test_suite="tests",
    tests_require=(["mock", "pytest"]),
    setup_requires=(
        ["pytest-runner"] if {"test", "pytest", "ptr"} & set(sys.argv) else []
    ),
    **extra
)
