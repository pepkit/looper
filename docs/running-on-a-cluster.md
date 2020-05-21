# How to submit looper jobs to a cluster

By default, `looper` will build a shell script for each sample and then run it sequentially on the local computer. This is convenient for simple cases, but when it comes time to scale up, this is where `looper` really excels. Looper uses a powerful [concentric template system](concentric-templates.md) that enables looper to run jobs on any cluster resource manager (like SLURM, SGE, LFS, etc.) by simply setting up a template for it. The environment templates are managed by [divvy](http://code.databio.org/divvy).

## Overview and basic example of cluster computing

To configure `looper` for cluster computing, you just configure divvy. Divvy is automatically installed when you install looper. Briefly, first create a `divvy` computing configuration file using `divvy init`:

```bash
export DIVCFG="divvy_config.yaml"
divvy init -c $DIVCFG
```

Looper will now have access to your computing configuration. You can run `divvy list` to see what compute packages are available in this file. For example, you'll start with a package called 'slurm', which you can use with looper by calling `looper --package slurm`. For many systems (SLURM, SGE, LFS, etc), the default divvy configuration will work out of the box. If you need to tweak things, the template system is flexible and you can configure it to run in any compute environment. That's all there is to it. 

Complete details on how to configure divvy are described in the [divvy documentation](http://divvy.databio.org).

## Divvy config file locations

Looper will by default will look for the divvy configuration file in `$DIVCFG`, but you can override this by specifying a path to other file with `--divvy` argument, like this:

```bash
looper --divvy /path/to/env_cfg.yaml ...
```

