# Configuration files

Looper uses [YAML](http://www.yaml.org/) configuration files for several purposes.
It's designed to be organized, modular, and very configurable, so there are several configuration files.
We've organized these files so that each handle a different level of infrastructure

- Environment
- Project
- Pipeline

This makes the system very adaptable and portable, but for a newcomer, it is easy to map each to its purpose.
So, here's an explanation of each for you to use as a reference until you are familiar with the whole ecosystem.
Which ones you need to know about will depend on whether you're a pipeline *user* (running pipelines on your project)
or a pipeline *developer* (building your own pipeline).


## Pipeline users

Users (non-developers) of pipelines only need to be aware of one or two config files.

### Project configuration

[**project config**](defining-a-project.md) -- this file is specific to each project and contains information about the project's metadata, where the processed files should be saved, and other variables that allow to configure the pipelines specifically for this project. It follows the standard Portable Encapsulated Project format, or PEP for short.

### Environment configuration

[**environment config**](http://divvy.databio.org/en/latest/configuration/) -- if you are planning to submit jobs to a cluster, then you need to be aware of environment configuration. This task is farmed out to [divvy](http://divvy.databio.org/en/latest/), a computing resource configuration manager. Follow the divvy documentation to learn about ways to tweak the computing environment settins according to your needs.

That should be all you need to worry about as a pipeline user. If you need to adjust compute resources or want to develop a pipeline or have more advanced project-level control over pipelines, you'll need knowledge of the config files used by pipeline developers.


## Pipeline developers

### Pipeline configuration

If you want to make pipeline compatible with looper, tweak the way looper interacts with a pipeline for a given project,
or change the default cluster resources requested by a pipeline, you need to know about a configuration file that coordinates linking pipelines to a project. This happens via the [pipeline interface file](pipeline-interface-specification.md).

Finally, if you're using [the pypiper framework](https://github.com/databio/pypiper) to develop pipelines,
it uses a pipeline-specific configuration file, which is detailed in the [pypiper documentation](http://pypiper.readthedocs.io/en/latest/advanced.html#pipeline-config-files).

Essentially, each pipeline may provide a configuration file describing where software is,
and parameters to use for tasks within the pipeline. This configuration file is by default named like pipeline name,
with a `.yaml` extension instead of `.py`. For example, by default `rna_seq.py` looks for an accompanying `rna_seq.yaml` file.
