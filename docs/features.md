# Features and benefits

[cli]: img/cli.svg
[computing]: img/computing.svg
[flexible_pipelines]: img/flexible_pipelines.svg
[job_monitoring]: img/job_monitoring.svg
[resources]: img/resources.svg
[subprojects]: img/subprojects.svg
[collate]: img/collate.svg
[file_yaml]: img/file_yaml.svg
[html]: img/HTML.svg
[modular]: img/modular.svg


![modular][modular] **Modular approach to job handling** 

Looper **completely divides job handling from pipeline processing**. This modular approach simplifies the pipeline-building process because pipelines no longer need to worry about sample metadata parsing. 

![file_yaml][file_yaml] **The power of standard PEP format**

`Looper` inherits a bunch of advantages from [standard PEP format](http://pepkit.github.io): For example, **you only need to learn 1 way to format your project metadata, and it will work with any pipeline**. PEP format allows **subprojects**, which make it easy to define two very similar projects without duplicating project metadata. It also makes your project immediate compatible with other tools in pepkit; for example, you can import all your sample metadata (and pipeline results) in an R or python analysis environment with the [pepr](https://github.com/pepkit/pepr) R package or the [peppy](https://github.com/pepkit/peppy) python package. Using PEP's *derived attributes* makes projects portable. You can use it to collate samples with input files on different file systems or from different projects, with different naming conventions. This makes it easy to share projects across compute environments or individuals without having to change sample annotations to point at different places.


![computing][computing] **Universal parallelization implementation**

Looper's sample-level parallelization applies to all pipelines, so individual pipelines do not need reinvent the wheel. This allows looper to provide a convenient interface for submitting pipelines either to local compute or to any cluster resource manager, so individual pipeline authors do not need to worry about cluster job submission at all. If you don't change any settings, looper will simply run your jobs serially. But Looper employs [divvy](http://code.databio.org/divvy) to let you process your pipelines on any cluster resource manager (SLURM, SGE, etc.). Looper also allows you to specify compute queue/partition on-the-fly, by passing the ``--compute`` parameter to your call to ``looper run``, making flexible if you have complex resource needs.

![flexible_pipelines][flexible_pipelines] **Flexible pipelines** 

Use looper with any pipeline, any library, in any domain. We designed it to work with [pypiper](http://code.databio.org/pypiper), but **looper has an infinitely flexible command-line argument system that will let you configure it to work with any script (pipeline) that accepts command-line arguments**. You can also configure looper to submit multiple pipelines per sample.


![job_monitoring][job_monitoring] **Job completion monitoring**  

Looper is job-aware and will not submit new jobs for samples that are already running or finished, making it easy to add new samples to existing projects, or re-run failed samples.


![resources][resources] **Flexible resources**  

Looper has an easy-to-use resource requesting scheme. With a few lines to define CPU, memory, clock time, or anything else, pipeline authors can specify different computational resources depending on the size of the input sample and pipeline to run. Or, just use a default if you don't want to mess with setup.

![cli][cli] **Command line interface**

Looper uses a command-line interface so you have total power at your fingertips.

![html][html] **Beautiful linked result reports**

Looper automatically creates an internally linked, portable HTML report highlighting all results for your pipeline, for every pipeline.

