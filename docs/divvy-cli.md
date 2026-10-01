# Divvy CLI reference

Divvy is looper's compute configuration tool. It writes job submission scripts that can be submitted to any computing resource (local, SLURM, SGE, etc.).

Divvy is installed automatically with looper.

## Commands

### divvy list

List available compute packages.

```console
divvy list [--config CONFIG]
```

| Option | Description |
|--------|-------------|
| `--config` | Path to divvy configuration file (default: uses `$DIVCFG` or built-in config) |

**Example:**

```console
$ divvy list
Available compute packages:

local
slurm
sge
apptainer
apptainer_slurm
bulker_local
bulker_slurm
default
docker
```

### divvy write

Write a job submission script from a template.

```console
divvy write --package PACKAGE [--settings SETTINGS] [--compute KEY=VALUE ...] [--outfile OUTFILE] [--config CONFIG]
```

| Option | Description |
|--------|-------------|
| `-p, --package` | Compute package to use (default: `default`) |
| `-s, --settings` | YAML file with job settings to populate the template |
| `-c, --compute` | Extra key=value variable pairs (can specify multiple) |
| `-o, --outfile` | Output file path for the generated script |
| `--config` | Path to divvy configuration file |

**Example:**

```console
divvy write --package slurm --settings job_settings.yaml --compute code="python run.py" jobname=myjob --outfile submit.sh
```

### divvy submit

Write a job submission script and submit it.

```console
divvy submit --package PACKAGE [--settings SETTINGS] [--compute KEY=VALUE ...] [--outfile OUTFILE] [--config CONFIG]
```

Takes the same options as `divvy write`, but also submits the script using the package's submission command.

**Example:**

```console
divvy submit --package slurm --settings job_settings.yaml --compute code="python run.py" --outfile submit.sh
```

### divvy init

Initialize a new divvy configuration file.

```console
divvy init --config CONFIG
```

| Option | Description |
|--------|-------------|
| `--config` | Path where the new config file will be created |

**Example:**

```console
divvy init --config ~/.divvy_config.yaml
```

### divvy inspect

Display the template for a compute package.

```console
divvy inspect --package PACKAGE [--config CONFIG]
```

| Option | Description |
|--------|-------------|
| `-p, --package` | Compute package to inspect (default: `default`) |
| `--config` | Path to divvy configuration file |

**Example:**

```console
$ divvy inspect --package slurm
#!/bin/bash
#SBATCH --job-name='{JOBNAME}'
#SBATCH --output='{LOGFILE}'
#SBATCH --mem='{MEM}'
#SBATCH --cpus-per-task='{CORES}'
#SBATCH --time='{TIME}'
#SBATCH --partition='{PARTITION}'
#SBATCH -m block
#SBATCH --ntasks=1

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`

{PRE_COMMAND}

{CODE}

{POST_COMMAND}
```

## Variable sources

Variables can come from three sources, in order of increasing priority:

1. **Compute package** - Defined in the divvy configuration file
2. **Settings file** - YAML file passed with `--settings`
3. **Command line** - Key=value pairs passed with `--compute`

Higher priority sources override lower priority sources.

## Settings file format

The settings file is a simple YAML file with key-value pairs:

```yaml
time: 4-0-0
logfile: results.log
cores: 6
partition: large_mem
mem: 16G
```

## Common template variables

These variables are commonly used in compute package templates:

| Variable | Description |
|----------|-------------|
| `{CODE}` | The command(s) to execute |
| `{JOBNAME}` | Name of the job |
| `{LOGFILE}` | Path to log file |
| `{MEM}` | Memory to request |
| `{CORES}` | Number of CPU cores |
| `{TIME}` | Wall time limit |
| `{PARTITION}` | Cluster partition/queue |
| `{PRE_COMMAND}` | Commands to run before the pipeline command (e.g., module loads, TMPDIR setup) |
| `{POST_COMMAND}` | Commands to run after the pipeline command (e.g., cleanup) |
| `{BULKER_CRATE}` | Bulker crate identifier for the bulker_slurm and bulker_local packages |
| `{APPTAINER_IMAGE}` | Apptainer container image path |
| `{APPTAINER_ARGS}` | Extra arguments passed to apptainer (e.g., bind mounts) |

## Environment variables

| Variable | Description |
|----------|-------------|
| `DIVCFG` | Default path to divvy configuration file |

## See also

- [Using divvy](using-divvy.md) - Tutorial on divvy usage
- [Configuring compute settings](user-tutorial/compute-settings.md) - How to configure looper for cluster computing
- [Running jobs in containers](how-to/containers.md) - Container-based compute packages
