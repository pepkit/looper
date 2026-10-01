# Using divvy

!!! success "Learning objectives"
    - What is divvy?
    - How can I use it in the CLI?
    - How can I use divvy in the python API?
    - How can I use divvy to submit one-off jobs?


Previously you may have read about using divvy for running job in [containers](how-to/containers.md) or on [clusters](advanced-guide/advanced-computing.md).

Let's recap what is divvy and why it exists.

## What is divvy?
<img src="../img/divvy-merge.svg" alt="" style="float:left; margin-right:40px" width="250px">

Divvy is a submodule of looper, and it allows you to populate job submission scripts by integrating job-specific settings with separately configured computing environment settings. Divvy makes software portable, so users may easily toggle among any computing resource (laptop, cluster, cloud).
  

## What makes divvy better?

Tools require a particular compute resource setup. For example, one pipeline requires SLURM, another requires AWS, and yet another just runs directly on your laptop. This makes it difficult to transfer to different environments. For tools that can run in multiple environments, each one must be configured separately.

<img src="../img/divvy-connect.svg" alt="" style="float:right; margin-left:40px" width="400px">
Instead, divvy-compatible tools can run on any computing resource. Users configure their computing environment once, and all divvy-compatible tools will use this same configuration.

Divvy reads a standard configuration file describing available compute resources and then uses a simple template system to write custom job submission scripts. Computing resources are organized as compute packages, which users select, populate with values, and build scripts for compute jobs.

### Quick start with CLI

divvy comes installed with looper, so ensure you have the newest version of looper installed: `pip install looper`

Let's first use `divvy list` to show us our available computing packages:

```shell
divvy list
```

```console title="CLI output"
Using default divvy config. You may specify in env var: ['DIVCFG']
Using divvy config: /path/to/site-packages/looper/default_config/divvy_config.yaml
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

Note that divvy will default to a `divvy_config.yaml` if none is provided via the environment variable DIVCFG. This default config is provided by looper.

We can look at one of the above templates. You can find where divvy stores its templates by running `divvy list` and checking the config path, then looking in the `divvy_templates` subdirectory:

```shell
cat $(python -c "import looper; print(looper.__path__[0])")/default_config/divvy_templates/slurm_template.sub
```

```commandline title="CLI output"
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

Remember that compute packages use nested templates to wrap the pipeline  `{CODE}` provided by looper's pipeline interface. More can be read here: [advanced computing](advanced-guide/advanced-computing.md)

Divvy allows you to write your own submission script via the CLI. However, you will need a way to tell divvy the compute settings. One way is to use an input settings file.

Let's create one now:
```sh
touch my_job_settings.yaml
```

Add these settings:

```yaml title="my_job_settings.yaml"
time: 4-0-0
logfile: results.log
cores: 6
partition: large_mem
mem: 16G
```

Now that you have this setting file you can write a new submission script using `divvy write`:

```sh
divvy write --package slurm  --settings my_job_settings.yaml --compute sample=sample1  --outfile submit_script.sub
```

This will produce the `submit_script.sub` file.

```shell
cat submit_script.sub
```

```commandline title="CLI output"
#!/bin/bash
#SBATCH --job-name='{JOBNAME}'
#SBATCH --output='results.log'
#SBATCH --mem='16G'
#SBATCH --cpus-per-task='6'
#SBATCH --time='4-0-0'
#SBATCH --partition='large_mem'
#SBATCH -m block
#SBATCH --ntasks=1

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`

{PRE_COMMAND}

{CODE}

{POST_COMMAND}
```

We populated several variables, like `{LOGFILE}` and `{TIME}`, from the `settings.yaml` file. However, the `{CODE}` and `{JOBNAME}` variables are still unpopulated, so this submission script is incomplete. To remedy this, we'll use `divvy`'s command-line variable passing: any non-interpreted arguments passed to `divvy` are assumed to be variables to populate the template. These command-line variables are considered highest priority and so will override any values in the more distant locations. For example:

```shell
divvy write --package slurm  --settings my_job_settings.yaml  --compute sample=sample1 code=run-this-cmd jobname=12345  --outfile submit_script.sub
```

Now if we look at the file:
```commandline title="CLI output"
#!/bin/bash
#SBATCH --job-name='12345'
#SBATCH --output='results.log'
#SBATCH --mem='16G'
#SBATCH --cpus-per-task='6'
#SBATCH --time='4-0-0'
#SBATCH --partition='large_mem'
#SBATCH -m block
#SBATCH --ntasks=1

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`



run-this-cmd

```

Now we have a complete script, which we can run with `sbatch test.sub`. Notice also that the `time` variable uses the one provided on the CLI rather than the one provided in the `settings.yaml` file, because the CLI has a higher priority.

Variables can come from these 3 sources, in order of increasing priority: 1) compute package (defined in the `divvy` configuration file and selected with the `-p` or `--package` argument); 2) `settings.yaml` file, passed with `-s` or `--settings`; 3) any additional variables passed on the command line as key-value pairs to `-c`.

Finally, you can submit these jobs using `divvy submit`.

```sh
divvy submit --package slurm  --settings my_job_settings.yaml  --compute sample=sample1 code=run-this-cmd jobname=12345  --outfile submit_script.sub
```

Note, `slurm` requires `sbatch` to work which will be found HPCs and not my local machine. However, I can use the `local` template to run jobs locally!

```sh
divvy submit --package local  --settings my_job_settings.yaml --compute sample=sample1 code=run-this-cmd jobname=12345  --outfile submit_script.sub
```

### Using the Python API for divvy

You can also call divvy from a python script. You'll need to provide a path to a divvy config file:

```python title="divvy_usage.py"
import looper
import looper.divvy as divvy
import os

# Get the path to looper's default divvy config
config_path = os.path.join(os.path.dirname(looper.__file__), "default_config", "divvy_config.yaml")

# Now create a ComputingConfiguration object
dcc = divvy.ComputingConfiguration.from_yaml_file(filepath=config_path)

```

Once a ComputingConfiguration object has been created, you can see the default compute package as well as the associated submission script:

```python title="sub section of divvy_usage.py"

# Print default compute package to terminal
print(dcc.compute)

# Access the submission template associated with the compute package.
with open(dcc.compute['submission_template']) as f:
    print(f.read())

```

```console title="console output"
submission_template: /path/to/site-packages/looper/default_config/divvy_templates/localhost_template.sub
submission_command: .

#!/bin/bash

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`

{
{CODE}
} | tee {LOGFILE}
```

You can also populate the submission script via the API:

```python title="sub section of divvy_usage.py"

# Populate and create a local submission script
dcc.write_script("test_local.sub", [{"code": "run-this-command", "logfile": "logfile.txt"}])

# Take a look at the newly populated submission template
with open("test_local.sub") as f:
    print(f.read())

```

```console title="console output"

Writing script to ./test_local.sub

#!/bin/bash

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`

{
run-this-command
} | tee logfile.txt

```

You can also activate a computing package via the API:

```python title="sub section of divvy_usage.py"
# You can also activate a package
print(dcc.activate_package("slurm"))

```

```console title="console output"

Activating compute package 'slurm'

```

Finally, you can also submit jobs:

```python title="sub section of divvy_usage.py"
dcc.submit(output_path="test_local.sub")
```

Here is the final completed script used for this tutorial:


```python title="divvy_usage.py"
import looper
import looper.divvy as divvy
import os

config_path = os.path.join(os.path.dirname(looper.__file__), "default_config", "divvy_config.yaml")
dcc = divvy.ComputingConfiguration.from_yaml_file(filepath=config_path)

# Print default compute package to terminal
print(dcc.compute)

# Access the submission template associated with the compute package.
with open(dcc.compute['submission_template']) as f:
    print(f.read())

# Populate and create a local submission script
dcc.write_script("test_local.sub", [{"code": "run-this-command", "logfile": "logfile.txt"}])

# Take a look at the newly populated submission template
with open("test_local.sub") as f:
    print(f.read())

# You can also activate a package
dcc.activate_package("slurm")

# You can also submit jobs 
dcc.submit(output_path="test_local.sub")

```