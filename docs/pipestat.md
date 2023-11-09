# Pipestat

Starting with version 1.4.0, looper supports additional functionality for [pipestat](http://pipestat.databio.org/)-compatible pipelines. Pipestat-compatible pipelines will allow you to use looper to do 2 things:

1. monitor the status of pipeline runs
2. summarize the results of pipelines

For non-pipestat-compatible pipelines, you can still use looper to run pipelines, but you won't be able to use `looper report` or `looper check` to manage their output.

## Pipestat configuration overview
Starting with version 1.6.0 configuring looper to work with pipestat has changed.

Now, Looper will obtain pipestat configurations data from two sources:
1. pipeline interface
2. looper_config file

Looper will combine the necessary configuration data and write a new pipestat configuration file named `looper_pipestat_config.yaml` which looper will place in its output directory. Pipestat then uses this configuration file to create the required PipestatManager objects. See [Hello_Looper](https://github.com/pepkit/hello_looper) for a specific example.

Briefly, the Looper config file must contain a pipestat field. A project name must be supplied if running a project level pipeline. The user must also supply a file path for a results file if using a local file backend or database credentials if using a postgresql database backend. 

```yaml
pep_config: project_config_pipestat.yaml # pephub registry path or local path
output_dir: output
sample_table: annotation_sheet.csv
pipeline_interfaces:
  sample:  ./pipeline_interface1_sample_pipestat.yaml
  project: ./pipeline_interface1_project_pipestat.yaml
looper:
  all:
    output_dir: output
sample_modifiers:
  append:
    attr: "val"
  derive:
    attributes: [read1, read2]
    sources:
      SRA_1: "{SRR}_1.fastq.gz"
      SRA_2: "{SRR}_2.fastq.gz"
pipestat:
  project_name: TEST_PROJECT_NAME
  results_file_path: tmp_pipestat_results.yaml
  flag_file_dir: output/results_pipeline
  database:
    dialect: postgresql
    driver: psycopg2
    name: pipestat-test
    user: postgres
    password: pipestat-password
    host: 127.0.0.1
    port: 5432
```
And the pipeline interface must include information required by pipestat such as pipeline_name, pipeline_type, and an output schema path:
```yaml
pipeline_name: example_pipestat_pipeline
pipeline_type: sample
schema_path: pipeline_pipestat/pipestat_output_schema.yaml
command_template: >
  python {looper.piface_dir}/count_lines.py {sample.file} {sample.sample_name} {pipestat.results_file}

```




### Pipestat Configuration for Looper Versions 1.4.0-1.5.0
Note: The instructions below are for older versions of Looper.

Generally, pipestat configuration comes from 3 sources, with the following priority:

1. `PipestatManager` constructor
2. Pipestat configuration file
3. Environment variables

In looper, only 1 and 2 are available, and can be specified via the project or sample attributes. Pipestat environment variables are *intentionally not supported* to ensure looper runs are reproducible -- otherwise, jobs configured in one computing environment could lead to totally different configuration and errors in other environments.

## Usage

The `PipestatManager` constructor attributes mentioned in the previous section are sourced from either sample attributes (for `looper run`) or project attributes ( for`looper runp`). One of the attributes can be used to specify the [pipestat configuration file](http://pipestat.databio.org/en/latest/config/), which is the other way of configuring pipestat.

The *names* of the attributes can be adjusted in the PEP configuration file. Let's take a pipestat namespace as an example: by default the value for the namespace is taken from `Sample.sample_name` but can be changed with `looper.pipestat.sample.namespace_attribute` in the PEP configuration file, like so:

```yaml
looper:
  pipestat:
    sample:
      namespace_attribute: custom_attribute
```

Now the value for the pipestat namespace will be sourced from `Sample.custom_attribute` rather than `Sample.sample_name`.

Similarly, a project-level pipestat namespace can be configured with `looper.pipestat.project.namespace_attribute`:

```yaml
looper:
  pipestat:
    project:
      namespace_attribute: custom_attribute
```

Now the value for the pipestat namespace will be sourced from `Project.custom_attribute` rather than `Project.name`.

Naturally, this configuration procedure can be applied to other pipestat options. The only exception is pipestat results schema, which is never specified here, since it's sourced from the `output_schema` attribute of the pipeline interface.

```yaml
looper:
  pipestat:
    sample:
      results_file_attribute: pipestat_results_file
      config_attribute: pipestat_config
      namespace_attribute: sample_name
    project:
      results_file_attribute: pipestat_results_file
      config_attribute: pipestat_config
      namespace_attribute: name
```

Again, the values above are defaults -- not needed, but configurable.

## Examples

To make the pipestat configuration rules more clear let's consider the following pipestat configuration setups.

### **Example 1:** All configuration as sample attributes

In this case the pipestat configuration options are sourced only from the sample attributes. Namely, `pipestat_results_file` and `custom_namespace`.

#### PEP config

```yaml
pep_version: 2.0.0
sample_table: sample_table.csv
sample_modifiers:
  append:
    pipestat_results_file: $HOME/my_results_file.yaml
  derive:
    attributes: [custom_namespace]
    sources:
      namespace: "{sample_name}_pipelineX"
looper:
  pipestat:
    sample:
      namespace_attribute: "custom_namespace"
```

#### PEP sample table (`sample_table.csv`)

```csv
sample_name,custom_namespace
sample1,namespace
```

### **Example 2:** A mix of pipestat configuration sources

In this case the pipestat configuration options are sourced from both sample attributes and pipestat configuration file.

Looper sourced the value for pipestat namespace from `Sample.sample_name` and database login credentials from the pipestat configuration file.

#### PEP config

```yaml
pep_version: 2.0.0
sample_table: sample_table.csv
sample_modifiers:
  append:
    pipestat_config: pipestat_config.yaml
```

#### PEP sample table (`sample_table.csv`)

```csv
sample_name
sample1
```

#### Pipestat configuration file (`pipestat_config.yaml`)

```yaml
database:
  name: database_name
  user: user_name
  password: user_password
  host: localhost
  port: 5432
  dialect: postgresql
  driver: psycopg2
```
