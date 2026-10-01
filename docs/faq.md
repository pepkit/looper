# FAQ


## What kind of pipelines can `looper` run?

`Looper` can run samples through *any pipeline that runs on the command line*. The flexible [pipeline interface](developer-tutorial/pipeline-interface-specification.md) file allows `looper` to execute arbitrary shell commands. A pipeline may consist of scripts in languages like Perl, Python, or bash, or it may be built with a particular framework. Typically, we use Python pipelines built using the [`pypiper` package](https://pep.databio.org/pypiper/), which provides some additional power to `looper`, but that's optional.


## Why isn't the `looper` executable available on `PATH`?

By default, Python packages are installed to `~/.local/bin`.
You can add that location to your path by appending it (`export PATH=$PATH:~/.local/bin`).

## How can I run my jobs on a cluster?

Looper uses the external package [divvy](advanced-guide/advanced-computing.md) for cluster computing, making it flexible enough to use with any cluster resource environment. Please see the [tutorial on cluster computing with looper and divvy](user-tutorial/compute-settings.md).


## What's the difference between `looper` and `pypiper`?

[`pypiper`](https://pep.databio.org/pypiper/) is a more traditional workflow-building framework; it helps you build pipelines to process individual samples. [`looper`](https://pep.databio.org/looper/) is completely pipeline-agnostic, and has nothing to do with individual processing steps; it operates groups of samples (as in a project), submitting the appropriate pipeline(s) to a cluster or server (or running them locally). The two projects are independent and can be used separately, but they are most powerful when combined. They complement one another, together constituting a comprehensive pipeline management system.

## Why isn't a sample being processed by a pipeline (`Not submitting, flag found: ['*_<status>.flag']`)?

When using the `run` subcommand, for each sample being processed `looper` first checks for *"flag" files* in the sample's designated output folder for flag files (which can be `_completed.flag`, or `_running.flag`, or `_failed.flag`). 	Typically, we don't want to resubmit a job that's already running or already finished, so by default, `looper` **will *not* submit a job when it finds a flag file**. This is what the message above is indicating.

If you do want to re-run a sample (maybe you've updated the pipeline, or you want to restart a failed attempt), pass the `--ignore-flags` option to `looper`; this will skip the flag check **for *all* samples**. If you only want to re-run a few specific samples, delete the flag files for those samples, then use `looper run` as normal.

You may be interested in the [usage docs](usage.md) for the `looper rerun` command, which runs any failed samples.

## How can I resubmit a subset of jobs that failed?

As of version `0.11`, you can use `looper rerun` to submit only jobs with a `failed` flag. By default, `looper` will *not* submit a job that has already run. If you want to restart a sample (maybe you've updated the pipeline, or you want to restart a failed attempt), you can either use `looper rerun` to restart only failed jobs, or pass `--ignore-flags`, which will **resubmit *all* samples**. For more specificity, delete the flag files for the samples you want to restart, then use `looper run` as normal.

## Why are computing resources defined in the pipeline interface file instead of in the `divvy` computing configuration file?

You may notice that the compute config file does not specify resources to request (like memory, CPUs, or time). Yet, these are required in order to submit a job to a cluster. **Resources are not handled by the divcfg file** because they not relative to a particular computing environment; instead they vary by pipeline and sample. As such, these items should be defined at other stages.

Resources defined in the `pipeline_interface.yaml` file that connects looper to a pipeline. The reason for this is that pipeline developers are the most likely to know what sort of resources their pipeline requires, so they are in the best position to define the resources requested. For more information on how to adjust resources, see the `compute` section of the [pipeline interface page](developer-tutorial/pipeline-interface-specification.md).

## Which configuration file has which settings?

There's information on the initial [tutorial page](user-tutorial/initialize.md).
