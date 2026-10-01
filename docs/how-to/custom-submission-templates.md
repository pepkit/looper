# How to create custom submission templates

Looper uses divvy compute packages to define how jobs are submitted. Each compute package pairs a submission template with a submission command. You can create your own packages to support any computing scenario.

!!! note "What you'll accomplish"
    Create a custom divvy compute package with your own submission template, and use it with looper.

!!! info "Prerequisites"
    - You have looper installed and working
    - You have a divvy config file (check with `divvy list`)
    - You are familiar with [configuring cluster computing](../user-tutorial/compute-settings.md)

## Steps

### 1. Create a submission template

Create a text file that serves as the skeleton for your job script. Use `{VARIABLE}` syntax for any values that should be filled in at run time. At minimum, include `{CODE}`, which looper populates with the pipeline command.

Common template variables:

- `{CODE}` -- the pipeline command (populated by looper)
- `{JOBNAME}` -- job name (populated by looper)
- `{LOGFILE}` -- log file path (populated by looper)
- `{MEM}`, `{CORES}`, `{TIME}`, `{PARTITION}` -- resource requests
- `{DOCKER_IMAGE}`, `{APPTAINER_IMAGE}`, `{APPTAINER_ARGS}`, `{DOCKER_ARGS}` -- container settings
- `{PRE_COMMAND}`, `{POST_COMMAND}` -- command hooks for pre/post execution steps
- `{BULKER_CRATE}` -- bulker crate identifier

You can also introduce your own custom variables (see the [SLURM with custom account](#example-slurm-with-a-custom-account-variable) example below).

### 2. Add a compute package to your divvy config

Open your divvy config file and add a new entry under `compute_packages`.

### 3. Set the `submission_template` to point to your template file

The path can be absolute or relative to the divvy config file.

### 4. Set the `submission_command` for this package

This is the command divvy uses to submit the generated script (e.g. `sh`, `sbatch`, `qsub`).

## Example: SLURM with a custom account variable

Suppose your cluster requires an `--account` flag on every job. Create a template that includes a custom `{ACCOUNT}` variable:

```bash title="divvy_templates/slurm_account_template.sub"
#!/bin/bash
#SBATCH --job-name='{JOBNAME}'
#SBATCH --output='{LOGFILE}'
#SBATCH --mem='{MEM}'
#SBATCH --cpus-per-task='{CORES}'
#SBATCH --time='{TIME}'
#SBATCH --partition='{PARTITION}'
#SBATCH --account='{ACCOUNT}'
#SBATCH --ntasks=1

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`

{PRE_COMMAND}

srun {CODE}

{POST_COMMAND}
```

Then register it in your divvy config, setting the `account` value as a package-level default:

```yaml title="divvy_config.yaml" hl_lines="5 6 7 8"
compute_packages:
  default:
    submission_template: divvy_templates/local_template.sub
    submission_command: sh
  slurm_account:
    submission_template: divvy_templates/slurm_account_template.sub
    submission_command: sbatch
    account: my_lab_allocation
```

Run with:

```shell
looper run --package slurm_account
```

You can override the account (or any other variable) at run time:

```shell
looper run --package slurm_account --compute account=other_allocation
```

!!! success "Key points"
    - Each compute package needs at least a `submission_template` and a `submission_command`.
    - Any `{VARIABLE}` in a template can be populated from the divvy config, the pipeline interface, the PEP config, or the `--compute` CLI flag.
    - Custom variables (like `{ACCOUNT}`) work the same way as built-in ones -- add them to the template and provide values through any of the standard sources.

## See also

- [Configuring cluster computing](../user-tutorial/compute-settings.md) -- tutorial on setting up compute environments
- [Customizing compute settings](../advanced-guide/advanced-computing.md) -- explanation of the nested template system
- [Running jobs in containers](containers.md) -- how to use Docker and Apptainer packages
