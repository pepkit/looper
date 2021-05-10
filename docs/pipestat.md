# Pipestat

Starting with version 1.3.1, looper natively supports pipestat, a tool that standardizes reporting of pipeline results. It provides 1) a standard specification for how pipeline outputs should be stored; and 2) an implementation to easily write results to that format from within Python or from the command line. The user configures results to be stored either in a YAML-formatted file or a relational database.

We recommend  browsing the [pipestat documentation](http://pipestat.databio.org/) to learn more about it.

## Pipestat configuration overview

Generally, pipestat configuration comes from 3 sources, with the following priority:

1. `PipestatManager` constructor
2. Pipestat configuration file
3. Environment variables

In looper only configuration sources 1. and 2. are available and can be specified via the project or sample attributes.

Pipestat environment variables are *intentionally not supported*. This design decision was dictated by looper runs reproducibility -- jobs configured in one computing environment could lead to totally different configuration and errors in other environments.

## Usage

The `PipestatManager` constructor attributes mentioned in the previous section are sourced from either sample or project attributes, depending on the looper command executed (`looper run`, `looper runp` etc.).

The *names* of the attributes can be configured in the PEP configuration file. Let's take a pipestat namespace as an example: by default the value for the namespace is taken from `Sample.sample_name` but can be changed with `looper.pipestat.sample.namespace_attribute` in the PEP configuration file, like so:

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

Natuarally, this configuration procedure can be applied to other pipestat options. The only exception is pipestat results schema, which is never specified here, since it's sourced from the `output_schema` attribute of the pipeline interface.

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

PEP config:

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

PEP sample table (`sample_table.csv`):

```csv
sample_name,custom_namespace
sample1,namespace
```

### **Example 2:** A mix of pipestat configuration sources

In this case the pipestat configuration options are sourced from both sample attributes and pipestat configuration file.

Looper sourced the value for pipestat namespace from `Sample.sample_name` and database login credentials from the pipestat configuration file.

PEP config:

```yaml
pep_version: 2.0.0
sample_table: sample_table.csv
sample_modifiers:
  append:
    pipestat_config: pipestat_config.yaml
```

PEP sample table (`sample_table.csv`):

```csv
sample_name
sample1
```

Pipestat configuration file (`pipestat_config.yaml`):

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
