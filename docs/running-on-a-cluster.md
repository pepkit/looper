# How to submit looper jobs to a cluster

By default, `looper` will build a shell script for each sample and then run it sequentially on the local computer. This is convenient for simple cases, but when it comes time to scale up, this is where `looper` really excels. Looper uses [divvy](http://code.databio.org/divvy) to manage computing configuration so projects and pipelines can easily travel among environments.

`Divvy` uses a template system to build scripts for each job. This enables looper to run jobs on any cluster resource manager (like SLURM, SGE, LFS, etc.) by simply setting up a template for it.

## Overview and basic example of cluster computing

To configure `looper` for cluster computing, you must provide information about your cluster setup. First, create a `divvy` computing configuration file. You can create a generic config file using `divvy init`:

```
export DIVCFG="divvy_config.yaml"
divvy init -c $DIVCFG
```

Looper will now have access to your computing configuration. You can run `divvy list` to see what compute packages are available. For example, you'll start with a package called 'slurm', which you can use with looper by calling `looper --package slurm`. That's all there is to it. 

For many systems, the default templates will work out of the box. If you need to tweak things, the template system is flexible and you can configure it to run in any compute environment. For more details, head over to the [divvy documentation](http://divvy.databio.org).
