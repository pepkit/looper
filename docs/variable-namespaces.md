# Looper template system and namespace variables

## Looper's concentric template system

Looper uses a 2-level template system consisting of an inner template wrapped by an outer template. The inner template is called a *command template*, which produces the individual commands to execute. The outer template is the *submission template*, which wraps the commands in environment handling code. This layered design makes looper flexible, allowing us to decouple settings of the computing environment from the pipeline, which improves portability.

The command template is specified at the level of the pipeline. Each pipeline provides a template for how its command should be constructed. These templates do not need to contain any information about computing environment. A simple command template could be something like this:

```
command_template: command {sample.input_file}
```

The submission template is specified at the level of the computing environment. This way, it only has to be defined once per environment, and all pipelines can make use the same configuration. A submission template can be similarly simple. For a command to be run in a local computing environment, a basic script will suffice:

```
#! /usr/bin/bash

{command}
```

This template can then be enriched with environment computing options, such as cluster submission or linux container parameters. In this example, the command template is populated first, and then provided as a variable and used to populate the `{command}` variable in the submission template.


## Populating the templates

Looper's task can be thought of as simply populating the given templates. To do this, Looper pools variables from several sources: 

1. the PEP, which provides information on the project and samples, 
2. the divvy config file, which provides information on the computing environment,
3. the pipeline interface, which provides information on the pipeline to run.

Variables from these sources are used to populate the templates to construct the commands to run. To keep things organized, looper groups the variables into namespaces. These namespaces are used first to populate the command template, which produces a built command. This command is then treated as a variable in itself, which is pooled with the other variables to populate the submission template.

Looper provides 6 variable namespaces for populating the templates:

## 1. project
The `project` namespace contains all PEP config attributes. For example, if you have a config file like this:

```
pep_version: 2.0.0
my_variable: 123
```

Then `project.my_variable` would have value `123`. You can use the project namespace to refer to any information in the project. You can use `project.looper` to refer to any attributes in the `looper` section of the PEP.

## 2. sample or samples

For sample-level pipelines, the `sample` namespace contains all PEP post-processing sample attributes for the given sample. For project-level pipelines, looper constructs a single job for an entire project, so there is no `sample` namespace; instead, there is a `samples` (plural) namespace, which is a list of all the samples in the project. This can be useful if you need to iterate through all the samples.

## 3. pipeline

Everything under `pipeline` in the pipeline interface for this pipeline.

## 4. looper

The `looper` namespace consists of automatic variables created by looper:

- `job_name` -- job name made by concatenating the pipeline identifier and unique sample name.
- `output_folder` -- parent output folder provided in `project.looper.output_folder`
- `sample_output_folder` -- A sample-specific output folder ({output_folder}/{sample_name})
- `total_input_size` -- The sum of file sizes for all files marked as input files in the input schema
- `pipeline_config` -- renamed from `config` to disambiguate with new `pep_config` ? Not sure what this is.
- `pep_config` -- path to the PEP configuration file used for this looper run.
- `log_file` -- an automatically created log file path, to be stored in the looper submission subdirectory
- `command` -- the result of populating the command template

The `looper.command` value enables the two-layer template system, whereby the output of the command template is used as input to the submission template.

## 5. compute

The `compute` namespace consists of a group of variables relevant for computing resources. The `compute` namespace has a unique behavior: it aggregates variables from several sources in a priority order, overriding values with more specific ones as priority increases. The list of variable sources in priority order is:

1. Looper CLI (`--compute` or `--settings` for on-the-fly settings)
2. PEP config, `project.looper.compute` section
3. Pipeline interface, `pipeline.compute` section
4. Activated divvy compute package (`--package` CLI argument)

So, the compute namespace is first populated with any variables from the selected divvy compute package. It then updates this with settings given in the `compute` section of the pipeline interface. It then updates from the PEP `project.looper.compute`, and then finally anything passed to `--compute` on the looper CLI. This provides a way to module looper behavior at the level of a computing environment, a pipeline, a project, or a run -- in that order.

