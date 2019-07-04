# Cluster computing

By default, `looper` will build a shell script for each sample and then run each sample serially on the local computer. This is convenient for simple cases, because it doesn't require any extra configuration. When it comes time to scale up, no problem! This is where `looper` really excels, in large projects that require submitting these jobs to a cluster resource manager (like SLURM, SGE, LFS, etc.). Starting with version `0.11` (released in 2019), `looper` uses [divvy](http://code.databio.org/divvy) to manage computing resource configuration so that projects and pipelines can easily travel among environments.

`Divvy` uses a template system to build scripts for each job. To start, `divvy` includes a few built-in templates so you can run basic jobs without messing with anything, but the template system provides ultimate flexibility to customize your job scripts however you wish. This template system is how we can use looper to run jobs on any cluster resource manager, by simply setting up a template that fits our particular cluster manager.

## Overview and basic example of cluster computing

In a nutshell, to configure `looper` to use cluster computing, all you have to do is provide some information about your cluster setup. You create a `divvy` computing configuration file (`compute_config.yaml`) and point an environment variable (`DIVCFG`) to this file, and that's it! You then have access to any configured computing packages by using `looper --compute package`, where `package` can be any computing system you configure.

For example, here's a `compute_config.yaml` file that works with a SLURM environment:
```yaml
compute:
  default:
    submission_template: templates/local_template.sub
    submission_command: sh
  loc:
    submission_template: templates/local_template.sub
    submission_command: sh    
  slurm:
    submission_template: templates/slurm_template.sub
    submission_command: sbatch
    partition: queue_name
```

Each section within `compute` defines a "compute package" that can be activated. 
By default, the package named `default` will be used, You may then choose a different compute package on the fly by specifying the `--compute` option: ``looper run --compute PACKAGE``. In this case, `PACKAGE` could be either `loc` (which would do the same thing as the default, so doesn't change anything) or `slurm`, which would run the jobs on SLURM, from queue `queue_name`. You can make as many compute packages as you wish (for example, to submit to different SLURM partitions).

This is just an overview; when you're ready to configure your computing environment, head over to the [divvy docs](http://code.databio.org/divvy) to get the whole story.


## Using divvy with looper

What is the source of values used to populate the variables? Well, they are pooled together from several sources. Divvy uses a hierarchical system to collect data values from global and local sources, which enables you to re-use settings across projects and environments. To start, there are a few built-ins:

Built-in variables:

- `{CODE}` is a reserved variable that refers to the actual command string that will run the pipeline. `Looper` will piece together this command individually for each sample
- `{JOBNAME}` -- automatically produced by `looper` using the `sample_name` and the pipeline name.
- `{LOGFILE}` -- automatically produced by `looper` using the `sample_name` and the pipeline name.


Other variables are not automatically created by `looper` and are specified in a few different places:

*DIVCFG config file*. Variables that describes settings of a **compute environment** should go in the `DIVCFG` file. Any attributes in the activated compute package will be available to populate template variables. For example, the `partition` attribute is specified in many of our default `DIVCFG` files; that attribute is used to populate a template `{PARTITION}` variable. This is what enables pipelines to work in any compute environment, since we have no control over what your partitions are named. You can also use this to change SLURM queues on-the-fly.

*pipeline_interface.yaml*. Variables that are **specific to a pipeline** can be defined in the `pipeline interface` file. Variables in two different sections are available to templates: the `compute` and `resources` sections. The difference between the two is that the `compute` section is common to all samples, while the `resources` section varies based on sample input size. As an example of a variable pulled from the `compute` section, we defined in our `pipeline_interface.yaml` a variable pointing to the singularity or docker image that can be used to run the pipeline, like this:

```
compute:
  singularity_image: /absolute/path/to/images/image
```

Now, this variable will be available for use in a template as `{SINGULARITY_IMAGE}`. This makes sense to put in the `compute` section because it doesn't change for different sizes of input files. This path should probably be absolute, because a relative path will be interpreted as relative to the working directory where your job is executed (*not* relative to the pipeline interface).

The other pipeline interface section that is available to templates is `resources`. This section uses a list of *resource packages* that vary based on sample input size. We use these in existing templates to adjust the amount of resources we need to request from a resource manager like SLURM. For example: `{MEM}`, `{CORES}`, and `{TIME}` are all defined in this section, and they vary for different input file sizes.

[Read more about pipeline_interface.yaml here](pipeline-interface.md).

*project_config.yaml*. Finally, project-level variables can also be populated from the `compute` section of a project config file. We don't recommend using this and it is not yet well documented, but it would enable you to make project-specific compute changes (such as billing a particular project to a particular SLURM resource account).
