# Features and benefits

[cli]: ../img/cli.svg
[computing]: ../img/computing.svg
[flexible_pipelines]: ../img/flexible_pipelines.svg
[job_monitoring]: ../img/job_monitoring.svg
[resources]: ../img/resources.svg
[subprojects]: ../img/subprojects.svg
[collate]: ../img/collate.svg
[file_yaml]: ../img/file_yaml.svg
[html]: ../img/HTML.svg
[modular]: ../img/modular.svg


![modular][modular] **Modular approach to sample handling** 
	Looper **completely divides sample handling from pipeline processing**. This modular approach simplifies the pipeline-building process because pipelines no longer need to worry about sample metadata parsing. 

![file_yaml][file_yaml] **Standardized project format**
	Looper subscribes to a single, standardized project metadata format called `standard PEP format <http://pepkit.github.io>`_. This means **you only need to learn 1 way to format your project metadata, and it will work with any pipeline**. You can also use the `pepr <https://github.com/pepkit/pepr>`_ R package or the `peppy <https://github.com/pepkit/peppy>`_ python package to import all your sample metadata (and pipeline results) in an R or python analysis environment.

![computing][computing] **Universal parallelization implementation**
	Looper's sample-level parallelization applies to all pipelines, so individual pipelines do not need reinvent the wheel. This allows looper to provide a convenient interface for submitting pipelines either to local compute or to any cluster resource manager, so individual pipeline authors do not need to worry about cluster job submission at all.If you don't change any settings, looper will simply run your jobs serially. But Looper includes a template system that will let you process your pipelines on any cluster resource manager (SLURM, SGE, etc.). We include default templates for SLURM and SGE, but it's easy to add your own as well. Looper also gives you a way to determine which compute queue/partition to submit on-the-fly, by passing the ``--compute`` parameter to your call to ``looper run``, making it simple to use by default, but very flexible if you have complex resource needs.

![flexible_pipelines][flexible_pipelines] **Flexible pipelines** 
	Use looper with any pipeline, any library, in any domain. We designed it to work with `pypiper <http://pypiper.readthedocs.io/>`_, but **looper has an infinitely flexible command-line argument system that will let you configure it to work with  any script (pipeline) that accepts command-line arguments**. You can also configure looper to submit multiple pipelines per sample.

![subprojects][subprojects] **Subprojects**
	Subprojects make it easy to define two very similar projects without duplicating project metadata.

![job_monitoring][job_monitoring] **Job completion monitoring**  
	Looper is job-aware and will not submit new jobs for samples that are already running or finished, making it easy to add new samples to existing projects, or re-run failed samples.

![collate][collate] **Flexible input files** 
	Looper's *derived column* feature makes projects portable. You can use it to collate samples with input files on different file systems or from different projects, with different naming conventions. How it works: you specify a variable filepath like ``/path/to/{sample_name}.txt``, and looper populates these file paths on the fly using metadata from your sample sheet. This makes it easy to share projects across compute environments or individuals without having to change sample annotations to point at different places.

![resources][resources] **Flexible resources**  
	Looper has an easy-to-use resource requesting scheme. With a few lines to define CPU, memory, clock time, or anything else, pipeline authors can specify different computational resources depending on the size of the input sample and pipeline to run. Or, just use a default if you don't want to mess with setup.

![cli][cli] **Command line interface**
	Looper uses a command-line interface so you have total power at your fingertips.

![html][html] **Beautiful linked result reports**
	Looper automatically creates an internally linked, portable HTML report highlighting all results for your pipeline, for every pipeline.

