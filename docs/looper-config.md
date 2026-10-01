# Looper configuration file

The `.looper.yaml` file configures looper for your project. It specifies where to find your samples, pipelines, and how to run them.

## Basic example

```yaml
pep_config: ./project_config.yaml
output_dir: ./results
pipeline_interfaces:
  - ./pipeline/pipeline_interface.yaml
```

## Complete reference

### Required settings

| Key | Type | Description |
|-----|------|-------------|
| `pep_config` | string | Path to PEP config file (YAML or CSV) or PEPhub registry path |
| `output_dir` | string | Directory for pipeline outputs |
| `pipeline_interfaces` | list | Paths to pipeline interface YAML files |

### Pipestat configuration

The `pipestat` section configures result reporting. All keys are optional.

```yaml
pipestat:
  project_name: my_project
  results_file_path: results.yaml
  flag_file_dir: results/flags
```

| Key | Type | Description |
|-----|------|-------------|
| `project_name` | string | Project name for results tracking |
| `results_file_path` | string | Path to YAML file for storing results |
| `flag_file_dir` | string | Directory for status flag files |
| `pephub_path` | string | PEPhub registry path for results storage |

#### Database backends

For PostgreSQL, use a nested `database` section:

```yaml
pipestat:
  project_name: my_project
  database:
    dialect: postgresql
    driver: psycopg2
    name: pipestat-db
    user: postgres
    password: ${POSTGRES_PASSWORD}
    host: 127.0.0.1
    port: 5432
```

Environment variables can be used anywhere in the config with `${VAR}` syntax. This is recommended for sensitive values like passwords.

For PEPhub:

```yaml
pipestat:
  pephub_path: "databio/myproject:results"
```

## PEP config sources

The `pep_config` value can be:

1. **Local YAML file**: `./project_config.yaml`
2. **Local CSV file**: `./samples.csv` (simple projects)
3. **PEPhub registry path**: `databio/myproject:default`

## Examples

### Minimal configuration

```yaml
pep_config: samples.csv
output_dir: results
pipeline_interfaces:
  - pipeline_interface.yaml
```

### With pipestat (file backend)

```yaml
pep_config: ./metadata/project_config.yaml
output_dir: ./results
pipeline_interfaces:
  - ./pipeline/pipeline_interface.yaml
pipestat:
  project_name: my_project
  results_file_path: results.yaml
  flag_file_dir: results/flags
```

### From PEPhub

```yaml
pep_config: databio/example_project:default
output_dir: ./results
pipeline_interfaces:
  - ./pipeline/pipeline_interface.yaml
```

## Environment variables

You can use environment variables anywhere in the config file with `${VAR}` syntax. This is useful for:

- Keeping secrets out of config files (database passwords, API keys)
- Making configs portable across machines (paths, hostnames)

```yaml
pipestat:
  database:
    password: ${DB_PASSWORD}
    host: ${DB_HOST}
```

### Looper environment variables

- `DIVCFG` - Path to divvy configuration file (for compute settings)

## See also

- [Pipeline interface specification](developer-tutorial/pipeline-interface-specification.md)
- [Configuring pipestat](user-tutorial/user-pipestat.md)
- [Configuring compute settings](user-tutorial/compute-settings.md)
