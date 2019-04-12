# <img src="img/looper_logo.svg" class="img-header">

[![PEP compatible](http://pepkit.github.io/img/PEP-compatible-green.svg)](http://pepkit.github.io)

# Introduction

Looper is a pipeline submitting engine. Looper deploys any *command-line* pipeline across lots of samples that are organized in [standard PEP format](https://pepkit.github.io/docs/home/).

`Looper`'s key strength is that it **decouples sample handling from pipeline processing**. In a typical pipeline, sample handling (*e.g* submitting different samples to a cluster) is delicately intertwined with pipeline commands (running the actual code on a single sample). The `looper` approach is modular, following the [the unix principle](https://en.wikipedia.org/wiki/Unix_philosophy) by focusing only on handling samples. This approach alleviates several challenges with the traditional system:

1. running a pipeline on just one or two samples is simpler, and does not require a full-blown distributed compute environment.
2. pipelines do not need to independently re-implement sample handling code, which instead can be shared across many pipelines.
3. every project can use the same structure (e.g. the expected folder structure, file naming scheme, and sample annotation format), because the code that reads the project metadata is universal, so datasets can more easily be moved from one pipeline to another.

By dividing sample processing from pipelining, the sample processing code needs only be written once (and can thus be written well) -- that's what `looper` is. **The user interface can be made simple and intuitive, and a user must then learn only a single interface, which will work with any pipeline.**

## Installing

Releases are posted as [GitHub releases](https://github.com/pepkit/looper/releases), or you can install using `pip`:


```
pip install --user https://github.com/pepkit/looper/zipball/master
```

Update with:

```
pip install --user --upgrade https://github.com/pepkit/looper/zipball/master
```

If the `looper` executable in not automatically in your `$PATH`, add the following line to your `.bashrc` or `.profile`:

```
export PATH=~/.local/bin:$PATH
```

## Quick start

Now, to test `looper`, follow the [Hello Looper example repository](https://github.com/databio/hello_looper) by running this code and you're running your first looper project!


```
# download and unzip the hello_looper repository
wget https://github.com/databio/hello_looper/archive/master.zip
unzip master.zip

# Run looper:
cd hello_looper-master
looper run project/project_config.yaml
```

Detailed explanation of results is in the [Hello world tutorial](hello-world.md).
