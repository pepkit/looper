<img src="logo_looper.svg" alt="looper logo" height="70" align="left"/>

# Looper

[![Documentation Status](http://readthedocs.org/projects/looper/badge/?version=latest)](http://looper.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.org/pepkit/looper.svg?branch=master)](https://travis-ci.org/pepkit/looper)

`Looper` is a pipeline submission engine that reads [standard PEP format](http://pepkit.github.io) and maps sample inputs to any command-line tool. It provides a convenient interface for submitting pipelines for bioinformatics research projects with many samples. Looper was conceived to use [pypiper pipelines](https://github.com/epigen/pypiper/), but it is in fact compatible with any tool that can be run via the command line.

You can download the latest version of `looper` from the [releases page](https://github.com/pepkit/looper/releases).

The documentation is hosted at [Read the Docs](http://looper.readthedocs.org/). 

# Looper-compatible pipelines

You can find a list of pre-built pipelines in the [hello looper! repository](https://github.com/pepkit/hello_looper/blob/master/looper_pipelines.md).

# `Looper` and `pep`

`Looper` is built on the python [`pep`](http://github.com/pepkit/pep) package. `Looper` and `pep` were originally developed together as a single package, but `pep` has been extracted to make the projects more modular. `Looper` now imports `pep` for its sample input and processing, and `pep` can be used independently of `looper`.

# Quick start

Detailed instructions are in the [Read the Docs documentation](http://looper.readthedocs.org/), and that's the best place to start. To get running quickly, you can install the latest release and put the `looper` executable in your `$PATH`: 


```
pip install https://github.com/pepkit/looper/zipball/master
export PATH=$PATH:~/.local/bin
```

Looper supports Python 2.7 and Python 3, and has been tested only in Linux. To use looper with your project, you must define your project using [standard PEP project definition format](http://pepkit.github.io), which is a `yaml` config file passed as an argument to looper. To test, grab an [example PEP](https://pepkit.github.io/docs/example_PEPs/) and run it through looper with this command:

```bash
looper run project_config.yaml
```


# Installation troubleshooting

If you clone this repository and then an attempt at local installation, e.g. with `pip install --upgrade ./`, fails, this may be due to an issue with `setuptools` and `six`. A `FileNotFoundError` (Python 3) or an `IOError` (Python2), with a message/traceback about a nonexistent `METADATA` file means that this is even more likely the cause. To get around this, you can first manually `pip install --upgrade six` or `pip install six==1.11.0`, as upgrading from `six` from 1.10.0 to 1.11.0 resolves this issue, then retry the `looper` installation.


# Contributing
- After adding tests in `tests` for a new feature or a bug fix, please run the test suite.
- To do so, the only additional dependencies needed beyond those for the package can be 
installed with:

  ```pip install -r requirements/requirements-dev.txt```
  
- Once those are installed, the tests can be run with `pytest`. Alternatively, 
`python setup.py test` can be used.

