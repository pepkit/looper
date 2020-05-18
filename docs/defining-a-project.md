# How to define a project

## 1. Start with a basic PEP

In the simplest case all you need is a project defined in the [standard Portable Encapsulated Project (PEP) format](http://pep.databio.org). Start by [creating a PEP](https://pepkit.github.io/docs/simple_example/). 

## 2. Connect the PEP to looper 

Once you have a basic PEP, you can connect it to looper. Just provide two required looper-specific pieces of information: 

- `output-dir`: parent folder where you want looper to store your results (always required)
- `pipeline-interfaces`: a list of pipeline interfaces (conditionally required)

You can do this in two ways:

### Provide the information as arguments to the `looper` command

One possibility is to provide required information on the command line, for example:

```bash
looper run project_config.yaml --output-dir /path/to/output_dir --pipeline-interfaces /path/to/pipeline_interface.yaml
```

For more CLI options refer to the subcommands [usage](usage.md)

### Add a `looper` section to your PEP

The `looper` section can contain *all command line options*. The subsections within this section direct the argumets to the respective `looper` subcommands. So, to specify the output directory and pipeline interfaces for a `looper run` command use:

```yaml
looper:
  run:
    output-dir: "/path/to/output_dir"
    pipeline-interfaces: "/path/to/pipeline_interface.yaml"
```

or, to pass the arguments to any subcommand:

```yaml
looper:
  all:
    output-dir: "/path/to/output_dir"
    pipeline-interfaces: "/path/to/pipeline_interface.yaml"
```

<!-- - `output_dir` - parent folder where you want looper to store your results.
- `results_subdir` - subdirectory where pipeline results will be stored. Default: `results_pipeline`
- `submission_subdir` - subdirectory where job submission scripts will be stored. Default: `submission`
- `compute.resources` - You can specify project-specific compute settings in a `compute` section, 
but it's often more convenient and consistent to specify this globally with a `divcfg` environment configuration. 
Instructions for doing so are at the [`divcfg` repository](https://github.com/pepkit/divcfg). 
If you do need project-specific control over compute settings (like submitting a certain project to a certain resource account), 
you can do this by specifying variables in a project config `compute.resources` section, which will override global `divcfg` values for that project only.
- `command_extra` - a string you want to append to any project-level pipelines
- `pipeline_interfaces` - a list of pipeline interfaces for project-level pipelines -->

## 3. Link a pipeline to your project

### Understanding pipeline interfaces

Looper links projects to pipelines through a file called the *pipeline interface*. Any looper-compatible pipeline must provide a pipeline interface. To link the pipeline, you simply point each sample to the pipeline interfaces for any pipelines you want to run.

Looper pipeline interfaces can describe two types of pipeline: sample-level pipelines or project-level pipelines. A sample-level pipeline is executed with `looper run`, which runs individually on each sample. A project-level pipeline is executed with `looper runp`, which runs a single job *per pipeline* on an entire project.

### Adding a sample-level pipeline interface

Sample pipelines are linked by adding a sample attribute called `pipeline_interfaces`. There are 2 easy ways to do this: you can simply add a `pipeline_interfaces` column in the sample table, or you can use an *append* modifier, like this:

```yaml
sample_modifiers:
  append:
    pipeline_interfaces: "/path/to/pipeline_interface.yaml"
```

Alternatively, you can provide this information as described in "Connect the PEP to looper" section, add `pipeline-interfaces` to the `looper` section to the project configuration file or using command line interface. This will override any pipeline interfaces defined like above:

```yaml
looper:
  run:
    pipeline-interfaces: "/path/to/pipeline_interface.yaml"
```

The value for the `pipeline_interfaces` key should be the *absolute* path to the pipeline interface file. The paths can consist of environment variables.

Once your PEP is linked to the pipeline, you just need to make sure your project provides any sample metadata required by the pipeline.

### Adding a project-level pipeline interface

Project pipelines are linked by providing the abosolute path to the desired file as an argument to the `looper runp` command:

```bash
looper runp project_config.yaml --pipeline-interfaces /path/to/project_pipeline_interface.yaml
```

 or in the `looper` section in project configuration file. Please note that the specified subsection is `runp`:

```
looper:
  runp:
    pipeline-interfaces: "/path/to/project_pipeline_interface.yaml"
```

### How to link to multiple pipelines

Looper decouples projects and pipelines, so you can have many projects using one pipeline, or many pipelines running on the same project. If you want to run more than one pipeline on a sample, you can simply add more than one pipeline interface, like this:

```yaml
sample_modifiers:
  append:
    pipeline_interfaces: ["/path/to/pipeline_interface.yaml", "/path/to/pipeline_interface2.yaml"]
```

Looper will submit jobs for both of these pipelines.

If you have a project that contains samples of different types, then you can use an `imply` modifier in your PEP to select which pipelines you want to run on which samples, like this:


```yaml
sample_modifiers:
  imply:
    - if:
        protocol: "RRBS"
      then:
        pipeline_interfaces: "/path/to/pipeline_interface.yaml"
    - if:
        protocol: "ATAC"
      then:
        pipeline_interfaces: "/path/to/pipeline_interface2.yaml"
```
