# <img src="img/looper_logo.svg" class="img-header"> a pipeline submitting engine

[![PEP compatible](http://pepkit.github.io/img/PEP-compatible-green.svg)](http://pepkit.github.io)

## What is looper?

`Looper` is a pipeline submitting engine. `Looper` deploys any command-line pipeline for each sample in a project organized in [standard PEP format](https://pepkit.github.io/docs/home/). You can think of `looper` as providing a single user interface to running, summarizing, monitoring, and otherwise managing all of your sample-intensive research projects the same way, regardless of data type or pipeline used.

## What makes looper better?

`Looper`'s key strength is that it **decouples job handling from the pipeline process**. In a typical pipeline, job handling (managing how individual jobs are submitted to a cluster) is delicately intertwined with actual pipeline commands (running the actual code for a single compute job). The `looper` approach is modular, following the [the unix principle](https://en.wikipedia.org/wiki/Unix_philosophy): `looper` *only* manages job submission. This approach leads to several advantages compared with the traditional integrated approach:

1. running a pipeline on just one or two samples/jobs is simpler, and does not require a full-blown distributed compute environment.
2. pipelines do not need to independently re-implement job handling code, which is shared.
3. every project uses a universal structure (expected folders, file names, and sample annotation format), so datasets can more easily move from one pipeline to another.
4. users must learn only a single interface that works with any of their projects for any pipeline.


 

## Installing

Releases are posted as [GitHub releases](https://github.com/pepkit/looper/releases), or you can install using `pip`:


```console
pip install --user loopercli
```

Update with:

```console
pip install --user --upgrade loopercli
```

If the `looper` executable in not automatically in your `$PATH`, add the following line to your `.bashrc` or `.profile`:

```console
export PATH=~/.local/bin:$PATH
```

## Quick start

To test `looper`, follow the [Hello Looper example repository](https://github.com/databio/hello_looper) to run your first looper project:


```console
# download and unzip the hello_looper repository
wget https://github.com/databio/hello_looper/archive/master.zip
unzip master.zip

# Run looper:
cd hello_looper-master
looper run project/project_config.yaml
```

Detailed explanation of results is in the [Hello world tutorial](hello-world.md).
