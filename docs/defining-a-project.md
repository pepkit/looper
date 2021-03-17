# How to define a project

## 1. Start with a basic PEP

To start, you need a project defined in the [standard Portable Encapsulated Project (PEP) format](http://pep.databio.org). Start by [creating a PEP](https://pep.databio.org/en/latest/simple_example/). 

## 2. Connect the PEP to looper 

### 2.1 Specify `output_dir`

Once you have a basic PEP, you can connect it to looper. Just provide the required looper-specific piece of information -- `output-dir`, a parent folder where you want looper to store your results. You do this by adding a `looper` section to your PEP. The `output_dir` key is expected in the top level of the `looper` section of the project configuration file. Here's an example:

```yaml
looper:
  output_dir: "/path/to/output_dir"
```

### 2.2 Configure pipestat

*We recommend to read the [pipestat documentation](https://pipestat.databio.org) to learn more about the concepts described in this section*

Additionally, you may configure pipestat, the tool used to manage pipeline results. Pipestat provides lots of flexibility, so there are multiple configuration options that you can provide in `looper.pipestat.sample` or `looper.pipestat.project`, depending on the pipeline level you intend to run. 

Please note that all the configuration options listed below *do not* specify the values passed to pipestat *per se*, but rather `Project` or `Sample` attribute names that hold these values. This way the pipestat configuration can change with pipeline submitted for every `Sample` if the PEP `sample_modifiers` are used.  

- `results_file_attribute`: name of the `Sample` or `Project` attribute that indicates the path to the YAML results file that will be used to report results into. Default value: `pipestat_results_file`, so the path will be sourced from either `Sample.pipestat_results_file` or `Project.pipestat_results_file`. If the path provided this way is not absolute, looper will make it relative to `{looper.output_dir}`.
- `namespace_attribute`: name of the `Sample` or `Project` attribute that indicates the namespace to report into. Default values: `sample_name` for sample-level pipelines `name` for project-level pipelines , so the path will be sourced from either `Sample.sample_name` or `Project.name`.
- `config_attribute`: name of the `Sample` or `Project` attribute that indicates the path to the pipestat configuration file. It's not needed in case the intended pipestat backend is the YAML results file mentioned above. It's required if the intended pipestat backend is a PostgreSQL database, since this is the only way to provide the database login credentials. Default value: `pipestat_config`, so the path will be sourced from either `Sample.pipestat_config` or `Project.pipestat_config`.

Non-configurable pipestat options:

- `schema_path`: never specified here, since it's sourced from `{pipeline.output_schema}`, that is specified in the pipeline interface file
- `record_identifier`: is automatically set to `{pipeline.pipeline_name}`, that is specified in the pipeline interface file


```yaml
name: "test123"
pipestat_results_file: "project_pipestat_results.yaml"
pipestat_config: "/path/to/project_pipestat_config.yaml"

sample_modifiers:
  append: 
    pipestat_config: "/path/to/pipestat_config.yaml"
    pipestat_results_file: "RESULTS_FILE_PLACEHOLDER"
  derive:
    attributes: ["pipestat_results_file"]
    sources:
      RESULTS_FILE_PLACEHOLDER: "{sample_name}/pipestat_results.yaml"

looper:
  output_dir: "/path/to/output_dir"
  # pipestat configuration starts here
  # the values below are defaults, so they are not needed, but configurable
  pipestat:
    sample:
      results_file_attribute: "pipestat_results_file"
      config_attribute: "pipestat_config"
      namespace_attribute: "sample_name"
    project:
      results_file_attribute: "pipestat_results_file"
      config_attribute: "pipestat_config"
      namespace_attribute: "name"
```
## 3. Link a pipeline to your project

Next, you'll need to point the PEP to the *pipeline interface* file that describes the command you want looper to run.

### Understanding pipeline interfaces

Looper links projects to pipelines through a file called the *pipeline interface*. Any looper-compatible pipeline must provide a pipeline interface. To link the pipeline, you simply point each sample to the pipeline interfaces for any pipelines you want to run.

Looper pipeline interfaces can describe two types of pipeline: sample-level pipelines or project-level pipelines. Briefly, a sample-level pipeline is executed with `looper run`, which runs individually on each sample. A project-level pipeline is executed with `looper runp`, which runs a single job *per pipeline* on an entire project. Typically, you'll first be interested in the sample-level pipelines. You can read in more detail in the [pipeline tiers documentation](pipeline-tiers.md).

### Adding a sample-level pipeline interface

Sample pipelines are linked by adding a sample attribute called `pipeline_interfaces`. There are 2 easy ways to do this: you can simply add a `pipeline_interfaces` column in the sample table, or you can use an *append* modifier, like this:

```yaml
sample_modifiers:
  append:
    pipeline_interfaces: "/path/to/pipeline_interface.yaml"
```

The value for the `pipeline_interfaces` key should be the *absolute* path to the pipeline interface file. The paths may also contain environment variables. Once your PEP is linked to the pipeline, you just need to make sure your project provides any sample metadata required by the pipeline.

### Adding a project-level pipeline interface

Project pipelines are linked in the `looper` section of the project configuration file:

```
looper:
  pipeline_interfaces: "/path/to/project_pipeline_interface.yaml"
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


## 5. Customize looper

That's all you need to get started linking your project to looper. But you can also customize things further. Under the `looper` section, you can provide a `cli` keyword to specify any command line (CLI) options from within the project config file. The subsections within this section direct the arguments to the respective `looper` subcommands. So, to specify, e.g. sample submission limit for a `looper run` command use:

```yaml
looper:
  output_dir: "/path/to/output_dir"
  cli:
    run:
      limit: 2
```

or, to pass this argument to any subcommand:

```yaml
looper:
  output_dir: "/path/to/output_dir"
  all:
    limit: 2
```

Keys in the `cli.<subcommand>` section *must* match the long argument parser option strings, so `command-extra`, `limit`, `dry-run` and so on. For more CLI options refer to the subcommands [usage](usage.md).