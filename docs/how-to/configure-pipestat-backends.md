# How to configure pipestat back-ends

## Introduction

In the basic [pipestat tutorial](../user-tutorial/user-pipestat.md), we showed how to create a simple pipeline that could use pipestat to report results.
One of the powerful features of pipestat is that you can configure it to store results in different locations.
This document will cover more details about how to configure pipestat in looper:

!!! note "What you'll accomplish"
    Configure pipestat to store pipeline results in files, SQLite, PostgreSQL, or PEPhub.


## How looper configures pipestat

As looper processes samples and creates a job submission script, if `.looper.yaml` config file contains `pipestat` section, it creates a pipestat configuration file, which merges information found in 1. pipeline interface and 2. looper_config file.

Looper combines the necessary configuration data and writes a pipestat configuration for each pipeline interface. The configuration file is then used by the pipeline interface (and pipeline) to create a PipestatManager object. This instantiated PipestatManager object can then be used to report results.

To configure looper to use pipestat, you must

### 1. Add `pipestat` section to the looper config file.

The looper config file must contain a `pipestat` section.
This section must contain information on where to store results, which is either a file path for a results file, database credentials if using a PostgreSQL database backend, a SQLite path if using a SQLite database backend,or PEPhub registry path. Here are 4 examples showing how to configure pipestat to use different back-ends:

### File back-end

```yaml title=".looper.yaml" hl_lines="7"
pep_config: project_config_pipestat.yaml
output_dir: results
pipeline_interfaces:
  - ./pipeline_interface1_sample_pipestat.yaml
pipestat:
  flag_file_dir: output/results_pipeline
  results_file_path: tmp_pipestat_results.yaml
```

### Postgres SQL database back-end

```yaml title=".looper.yaml" hl_lines="7-14"
pep_config: project_config_pipestat.yaml 
output_dir: results
pipeline_interfaces:
  - ./pipeline_interface1_sample_pipestat.yaml
pipestat:
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

### SQLite database back-end

```yaml title=".looper.yaml" hl_lines="8"
pep_config: project_config_pipestat.yaml 
output_dir: results
pipeline_interfaces:
  - ./pipeline_interface.yaml
pipestat:
  flag_file_dir: output/results_pipeline
  database:
    sqlite_url: "sqlite:///yourdatabase.sqlite3"
```


### PEPhub back-end

```yaml title=".looper.yaml" hl_lines="7"
pep_config: project_config_pipestat.yaml # pephub registry path or local path
output_dir: results
pipeline_interfaces:
  - ./pipeline_interface1_sample_pipestat.yaml
pipestat:
  flag_file_dir: output/results_pipeline
  pephub_path: "databio/pipestat_demo:default"
```

### 2. The pipeline interface must include information required by pipestat such as pipeline_name and an output schema path:

```yaml title="pipeline_interface.yaml" hl_lines="1-2"
pipeline_name: example_pipestat_pipeline
output_schema: pipeline_pipestat/pipestat_output_schema.yaml
sample_interface:
  command_template: >
    python {looper.piface_dir}/count_lines.py {sample.file} {sample.sample_name} {pipestat.results_file}
```

Using the above information, Looper will construct the pipestat configuration file automatically. It will have the name `pipestat_config_{pipeline_name}.yaml` and be placed in the results output directory. It will contain the aggregation of pipestat relevant items found in the looper config file and the pipeline interface.

```yaml title="example of pipestat_config_count_lines.yaml"
results_file_path: /home/drc/GITHUB/hello_looper/hello_looper/pipestat_example/./results/count_lines/results.yaml
flag_file_dir: /home/drc/GITHUB/hello_looper/hello_looper/pipestat_example/./results/flags
output_dir: /home/drc/GITHUB/hello_looper/hello_looper/pipestat_example/./results
schema_path: /home/drc/GITHUB/hello_looper/hello_looper/pipestat_example/pipeline/pipestat_output_schema.yaml
pipeline_name: count_lines
```







!!! tip "Summary"
    - Configure pipestat through the `pipestat` section on the looper config.
    - You can control where the results of your pipeline are stored by configuring pipestat's back-end.



