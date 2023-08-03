# Looper's concentric template system

## Introduction

To build job scripts, looper uses a 2-level template system consisting of an inner template wrapped by an outer template. The inner template is called a *command template*, which produces the individual commands to execute. The outer template is the *submission template*, which wraps the commands in environment handling code. This layered design allows us to decouple the computing environment from the pipeline, which improves portability.

## The command template

The command template is specified by a pipeline in the pipeline interface. A very basic command template could be something like this:

```console
pipeline_command {sample.input_file} --arg
```

In the simplest case, looper can run the pipeline by simply running these commands. This example contains no information about computing environment, such as SLURM submission directives.

## The submission template

To extend to submitting the commands to a cluster, we simply need to add some more information around the command above, specifying things like memory use, job name, *etc.* It may be tempting to add these details directly to the command template, causing the jobs to be submitted to SLURM instead of run directly. This *would* work; however, this would restrict the pipeline to *only* running via SLURM, since the submission code would be tightly coupled to the command code. Instead, looper retains flexibility by introducing a second template layer, the *submission template*. While the *command template* is specified by the pipeline interface, the *submission template* is specified at the level of the computing environment.  A submission template can also be as simple or complex as required. For a command to be run in a local computing environment, a basic template will suffice:

```console
#! /usr/bin/bash

{CODE}
```

A more complicated template could submit a job to a SLURM cluster:

```console
#!/bin/bash
#SBATCH --job-name='{JOBNAME}'
#SBATCH --output='{LOGFILE}'
#SBATCH --mem='{MEM}'
#SBATCH --cpus-per-task='{CORES}'
#SBATCH --time='{TIME}'
echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`

srun {CODE}
```

In these templates, the `{CODE}` variable is populated by the populated result of the command template -- that's what makes these templates concentric.

## The advantages of concentric templates

Looper first populates the command template, and then provides the output as a variable and used to populate the `{CODE}` variable in the submission template. This decoupling provides substantial advantages:

1. The commands can be run on any computing environment by simply switching the submission template.
2. The submission template can be used for any computing environment parameters, such as containers.
3. The submission template only has to be defined once *per environment*, so many pipelines can use them.
4. We can [group multiple individual commands](grouping-jobs.md) into a single submission script.
5. The submission template is universal and can be handled by dedicated submission template software.

## Looper and divvy

The last point about the submission template being universal is exactly what looper does. Looper uses [divvy](http://divvy.databio.org) to handle submission templates. Besides being useful for looper, this means the divvy submission templates can be used for interactive submission of jobs, or used by other software. It also means to configure looper to work with your computing environment, you just have to configure divvy.

## Populating templates

The task of running jobs can be thought of as simply populating the templates with variables. To do this, Looper provides [variables from several sources](variable-namespaces.md).
