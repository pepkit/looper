# <img src="img/looper_logo.svg" class="img-header">

<p align="center">
<a href="https://pepkit.github.io/img/PEP-compatible-green.svg"><img src="https://pepkit.github.io/img/PEP-compatible-green.svg"></a>
<a href="https://github.com/pepkit/looper/actions/workflows/run-pytest.yml" alt="Run pytests"><img src="https://github.com/pepkit/looper/workflows/Run%20pytests/badge.svg"/></a>
<a href="https://img.shields.io/pypi/v/looper"><img src="https://img.shields.io/pypi/v/looper"></a>
<a href="https://github.com/pepkit/looper"><img src="https://img.shields.io/badge/source-github-354a75?logo=github"></a>
</p>

## What is looper?

Looper is a job submitting engine. Looper deploys arbitrary shell commands for each sample in a [standard PEP project](/spec/simple-example/). You can think of looper as providing a single user interface to running, monitoring, and managing all of your sample-intensive research projects the same way, regardless of data type or pipeline used.

## What makes looper better?

Looper **decouples job handling from the pipeline process**. In a typical pipeline, job handling (managing how individual jobs are submitted to a cluster) is delicately intertwined with actual pipeline commands (running the actual code for a single compute job). In contrast, the looper approach is modular: looper *only* manages job submission. This approach leads to several advantages compared with the traditional integrated approach:

1. pipelines do not need to independently re-implement job handling code, which is shared.
2. every project uses a universal structure, so datasets can move from one pipeline to another.
3. users must learn only a single interface that works with any project for any pipeline.
4. running just one or two samples/jobs is simpler, and does not require a  distributed compute environment.


# Features at-a-glance

<img src="img/modular.svg" class="img-bullet"> **Modular approach to job handling**. Looper completely divides job handling from pipeline processing. Now,  pipelines no longer need to worry about sample metadata parsing.

<img src="img/file_yaml.svg" class="img-bullet"> **The power of standard PEP format**. `Looper` inherits benefits of [PEP format](http://pepkit.github.io): For example, you only need to learn 1 way to format your project metadata, and it will work with any pipeline. PEP provides subprojects,  programmatic modifiers, loading in R with  [pepr](https://github.com/pepkit/pepr) or Python with [peppy](https://github.com/pepkit/peppy).

<img src="img/computing.svg" class="img-bullet"> **Universal parallelization implementation**. Looper's sample-level parallelization applies to all pipelines, so individual pipelines do not have to re-implement parallelization by sample. `Looper` also handles cluster submission on any cluster resource manager (SLURM, SGE, etc.), so your pipeline doesn't need to manage that, either.

<img src="img/flexible_pipelines.svg" class="img-bullet"> **Flexible pipelines**. Use looper with any pipeline, any library, in any domain. As long as you can run your pipeline with a shell command, looper can run it for you.

<img src="img/job_monitoring.svg" class="img-bullet"> **Job completion monitoring**. Looper is job-aware and will not submit new jobs for samples that are already running or finished, making it easy to add new samples to existing projects, or re-run failed samples.

<img src="img/resources.svg" class="img-bullet"> **Flexible resources**. Looper has an easy-to-use resource requesting scheme. With a few lines to define CPU, memory, clock time, or anything else, pipeline authors can specify different computational resources depending on the size of the input sample and pipeline to run. Or, just use a default if you don't want to mess with setup.

<img src="img/cli.svg" class="img-bullet">  **Command line interface**. Looper uses a command-line interface so you have total power at your fingertips.

<img src="img/HTML.svg" class="img-bullet">  **Beautiful linked result reports**. Looper automatically creates an internally linked, portable HTML report highlighting all results for your pipeline, for every pipeline.
For an html report example see: [PEPATAC Gold Summary](https://pepatac.databio.org/en/latest/files/examples/gold/gold_summary.html)

