# How to define a project

## 1. Start with a basic PEP

Looper projects extend the [standard Portable Encapsulated Project (PEP) format](http://pep.databio.org). Start by [creating a PEP](https://pepkit.github.io/docs/simple_example/). Once you have a basic PEP, you can connect it to looper by adding a `looper` section:

## 2. Add a looper section to your PEP

The `looper` section can contain a few looper-specific attributes:

- `output_dir` - parent folder where you want looper to store your results.
- `results_subdir` - subdirectory where pipeline results will be stored. Default: `results_pipeline`
- `submission_subdir` - subdirectory where job submission scripts will be stored. Default: `submission`
- `compute` - You can specify project-specific compute settings in a `compute` section, 
but it's often more convenient and consistent to specify this globally with a `pepenv` environment configuration. 
Instructions for doing so are at the [`pepenv` repository](https://github.com/pepkit/pepenv). 
If you do need project-specific control over compute settings (like submitting a certain project to a certain resource account), 
you can do this by specifying variables in a project config `compute` section, which will override global `pepenv` values for that project only.
- `command_extra` - a string you want to append to any project-level pipelines
- `pipeline_interfaces` - a list of pipeline interfaces for project-level pipelines

Example:
```yaml
looper:
  output_dir: /path/to/output
```

## 3. Link a pipeline to your project

### Understanding pipeline interfaces

Looper links projects to pipelines through a file called the *pipeline interface*. Any looper-compatible pipeline must provide a pipeline interface. To link the pipeline, you simply point each sample to the pipeline interfaces for any pipelines you want to run.

Looper pipeline interfaces can describe two types of pipeline: sample-level pipelines and project-level pipelines. A sample-level pipeline is executed with `looper run`, which runs individually on each sample. A project-level pipeline is executed with `looper runp`, which runs a single job on an entire project.

### Adding a sample-level pipeline interface

Sample pipelines are linked by adding a sample attribute called `pipeline_interfaces`. Inside your project config, set a `pipeline_interfaces` attribute on samples to point to the pipeline. There are 2 easy ways to do this: you can simply add a `pipeline_interfaces` column in the sample table, or you can use an *append* modifier, like this:

```yaml
sample_modifiers:
  append:
    pipeline_interfaces: /path/to/pipeline_interface.yaml
```


The value for the `pipeline_interfaces` key should be the *absolute* path to the pipeline interface file.

Once your PEP is linked to the pipeline, you just need to make sure your project provides any sample metadata required by the pipeline.

### Adding a project-level pipeline interface

For projects that have only one sample pipeline interface, the project pipeline interface will be automatically linked. But if you need to specify a particular project pipeline interface for some reason, project pipelines are linked by adding a project attribute, in the `looper` section, called `pipeline_interfaces`.

```
looper:
  pipeline_interfaces: [/path/to/project_pipeline_interface.yaml]
```

### How to link to multiple pipelines

Looper decouples projects and pipelines, so you can have many projects using one pipeline, or many pipelines running on the same project. If you want to run more than one pipeline on a sample, you can simple add more than one pipeline interface, like this:

```yaml
sample_modifiers:
  append:
    pipeline_interfaces: [/path/to/pipeline_interface.yaml, /path/to/pipeline_interface2.yaml]
```

Looper will submit jobs for both of these pipelines.

If you have a project that contains samples of different types, then you can use an `imply` modifier to select which pipelines you want to run on which samples, like this:


```yaml
sample_modifiers:
  imply:
  	- if:
  		protocol: "RRBS"
	  then:
    	pipeline_interfaces: /path/to/pipeline_interface.yaml
    - if:
    	protocol: "ATAC"
      then:
        pipeline_interfaces: /path/to/pipeline_interface2.yaml
```
