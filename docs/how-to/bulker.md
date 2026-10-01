# How to use looper with bulker

[Bulker](https://bulker.io) is a multi-container environment manager that provides containerized CLI tools via lightweight shim scripts. Looper ships with built-in compute packages for running bulker-activated pipelines, both locally and on SLURM clusters.

!!! note "What you'll accomplish"
    Run a bulker-activated pipeline locally or on a SLURM cluster using looper's built-in bulker compute packages.

!!! info "Prerequisites"
    - Looper is installed and working
    - Bulker is installed and you have a crate manifest for your pipeline

## 1. Specify the bulker crate in your pipeline interface

The pipeline author specifies which bulker crate to use in the `compute` section of the pipeline interface:

```yaml title="pipeline_interface.yaml"
pipeline_name: my_pipeline
sample_interface:
  command_template: >
    my_tool {sample.input_file}
compute:
  bulker_crate: bulker/demo:default
```

## 2. Run locally with bulker_local

To run bulker-activated pipelines on your local machine:

```shell
looper run --package bulker_local
```

This activates the bulker crate and runs the pipeline command inside the bulker environment. The submission command is `sh`, so jobs run sequentially in the current shell.

## 3. Submit to SLURM with bulker_slurm

To submit bulker-activated pipelines to a SLURM cluster:

```shell
looper run --package bulker_slurm \
  --compute partition=standard time='04:00:00' cores='8' mem='16000'
```

This uses the built-in `bulker_slurm` template, which handles SLURM submission headers and bulker activation automatically.

## 4. Use pre-commands for environment setup

On many HPC systems, bulker needs additional setup before it can run — for example, loading a module or setting `TMPDIR` to a shared scratch location. Use `pre_command` for this:

```shell
looper run --package bulker_slurm \
  --compute partition=standard time='04:00:00' cores='8' mem='16000' \
  pre_command='export TMPDIR=/scratch/$USER/tmp && mkdir -p $TMPDIR && module load apptainer'
```

Or set it in your looper config so you don't have to type it every time:

```yaml title=".looper.yaml"
pep_config: pep_config.yaml
output_dir: results
pipeline_interfaces:
  - pipeline/pipeline_interface.yaml
cli:
  run:
    package: bulker_slurm
    compute:
      partition: standard
      time: '04:00:00'
      cores: '8'
      mem: '16000'
      pre_command: >
        export TMPDIR=/scratch/$USER/tmp && mkdir -p $TMPDIR && module load apptainer
```

## Available bulker packages

| Package | Submission | Description |
|---------|-----------|-------------|
| `bulker_local` | `sh` | Run bulker-activated pipelines locally |
| `bulker_slurm` | `sbatch` | Submit bulker-activated pipelines to SLURM |

## Appendix: Built-in bulker templates

### bulker_local template

```bash title="localhost_bulker_template.sub"
#!/bin/bash

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`

{PRE_COMMAND}

eval "$(bulker activate -e {BULKER_CRATE})"

{
  {CODE}
} | tee {LOGFILE} -i

{POST_COMMAND}
```

### bulker_slurm template

```bash title="bulker_slurm_template.sub"
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

eval "$(bulker activate -e {BULKER_CRATE})"

{CODE}

{POST_COMMAND}
```

## See also

- [Configuring cluster computing](../user-tutorial/compute-settings.md) -- tutorial on compute settings
- [Custom submission templates](custom-submission-templates.md) -- create your own compute packages
- [Running jobs in containers](containers.md) -- Docker and Apptainer packages
