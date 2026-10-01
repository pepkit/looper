



<!-- # How to submit jobs to a cluster with <img src="../../img/divvy_logo.svg" height="25"> -->

# Configuring compute settings

## Introduction

So far, we’ve been running jobs with Looper in the simplest way -- sequentially on the local computer.
While this approach works, Looper truly shines when you need to scale up and submit jobs to a compute cluster.

To facilitate this, Looper integrates a tool called `divvy`, which handles job submission configuration.
`Divvy` is automatically installed alongside Looper but can also be used independently.
By leveraging Divvy, Looper provides a powerful [nested template system](../advanced-guide/advanced-computing.md) that simplifies running jobs on any cluster resource manager (e.g., SLURM, SGE, LFS) using templates. 
Switching between different computing environments is also seamless.
The best part is that this setup works for any Looper-compatible pipeline.
Once you’ve configured your computing environment to your liking, Looper will help you deploy any pipeline in the same way.

In this tutorial, we’ll show you how to configure Looper and Divvy, giving you full control over your computing resources.
You'll learn how the templates work, and how you can customize them to fit just about any computing scenario.
To demonstrate, we'll show you how to configure looper to submit jobs to a SLURM cluster.
If you have a different system, you can edit templates and use a similar approach for any cluster resource manager.



!!! success "Learning objectives"
    - How does looper actually run jobs?
    - How can submit my jobs to a cluster instead of running them locally?
    - What is looper's nested template system and how can I use it to have total control over my compute settings?
    - Can I submit my pipeline to different types of clusters or in different computing environments?
    - How do I specify required resources like time or number of cores for a cluster job?




<!-- 
## What is `divvy`?

![Connect](../img/divvy-connect.svg)


Divvy allows you to populate job submission scripts by integrating job-specific settings with separately configured computing environment settings.
Divvy helps you toggle among computing resources.

Without `divvy`, tools are tied to a particular compute resource setup. This makes it difficult to transfer to different environments. For tools that can run in multiple environments, each one must be configured separately. In contrast, `divvy`-compatible tools can run on any computing resource. **Users configure their computing environment once, and all divvy-compatible tools will use this same configuration.** -->



## How looper job submission works

To start, let's go deeper into the details of how jobs are run in the simple case. We'll stay in the `pep_derived_attrs` workspace created in the previous tutorial. If you need to, you can download the folder from the [hello looper repository](https://github.com/pepkit/hello_looper).

Two arguments you can pass to `looper run` for testing are these:

- `--dry-run`/`-d`. In dry-run mode, looper will create job scripts, but will not actually run them.
- `--limit`/`-l`. This will limit the number of samples looper submits.

To demonstrate, run looper using these arguments:

```sh
cd pep_derived_attrs
looper run -d -l 1
```

If you run this, you should see output similar to this:

```console hl_lines="6"
Command: run
Using looper config (.looper.yaml).
## [1 of 3] sample: mexico; pipeline: count_lines
Writing script to /home/nsheff/code/hello_looper/pep_derived_attrs/results/submission/count_lines_mexico.sub
Job script (n=1; 0.00Gb): /home/nsheff/code/hello_looper/pep_derived_attrs/results/submission/count_lines_mexico.sub
Dry run, not submitted
```

Notice that:

- only 1 sample was processed (because we used `-l 1`)
- A job script was created, but not submitted (because we used `-d`)

This brings up a key point about how looper works.
It does not really *run* commands directly.
Instead, it creates a *job script*, and then executes that script.
This is true even in the simplest case, with the default compute settings.
Let's look more closely at the script looper created:

```sh
cat results/submission/count_lines_mexico.sub 
```

``` title="results/submission/count_lines_mexico.sub" hl_lines="9"
#!/bin/bash

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`



{
pipeline/count_lines.sh data/mexico.txt
} | tee /home/nsheff/code/hello_looper/pep_derived_attrs/results/submission/count_lines_mexico.log


```

Let's see how looper is creating this file.
You may recognize the highlighted line, because we've seen it before in the earlier tutorials.
It's the command we specified for how to run the pipeline, and it's coming from the *pipeline interface* file.

Recall in the first tutorial we created a `pipeline/pipeline_interface.yaml`, with this content:

```yaml  title="pipeline/pipeline_interface.yaml" hl_lines="4"
pipeline_name: count_lines
sample_interface:
  command_template: >
    pipeline/count_lines.sh {sample.file_path}
```

The `command_template`, after populating the variable for the first sample, becomes `pipeline/count_lines.sh data/mexico.txt ` -- the line highlighted in the submission script.

But where is the rest of the submission script coming from? It's not hard coded looper boilerplate -- this is actually coming from a different template that can be configured with divvy.
It's called the *submission template*, and what we're seeing here is the default submission template divvy uses when nothing else is specified.

Here's the default submission template provided by divvy:

```sh title="localhost_template.sub"
#!/bin/bash

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`

{PRE_COMMAND}

{
{CODE}
} | tee {LOGFILE}

{POST_COMMAND}
```

This template has several variables, which are populated by looper. The `{CODE}` slot is the one being populated from the pipeline interface's `command_template` variable. The `{LOGFILE}` variable is a special variable provided by looper. `{PRE_COMMAND}` and `{POST_COMMAND}` are optional hooks for running commands before and after the pipeline (they default to empty). You can ignore the details for now.

So, these are the steps looper takes to create the final job submission script:

1. It uses the `command_template` from the pipeline interface, populating it with any sample-specific information specified (like `{sample.file_path}`)
2. It takes the resulting value and uses it to populate the `{CODE}` variable in the `submission_template`.
3. It writes the final template to a file, named after the pipeline and sample.


!!! tip "Key point"
    - Looper isn't running anything directly. Rather, it's creating a script (called a submission script), and then it executes that.
    - If you use dry run mode, then it just creates the script without executing it.
    - The submission script is created in two steps, with two templates. First, the command is constructed, using the pipeline interface. Then, this command is inserted into a submission template provided by divvy. This two-layered template system is what we call looper's [nested template system](../advanced-guide/advanced-computing.md), and it provides a lot of  powerful benefits.


Next, we'll learn how to change the submission template, so that the job gets submitted to a cluster instead of run locally.


## Configuring looper for cluster submission

### Initializing divvy configuration

To configure `divvy` (and therefore `looper`) for cluster computing, first create a `divvy` computing configuration file using `divvy init`. Looper looks for the divvy configuration file in the environment variable `$DIVCFG`, so it's best to set that up to point to your divvy configuration file, so you don't have to provide it every time you run `looper`. This `init` command will create a default config file, along with a folder of computing templates:

```bash
export DIVCFG="divvy_config.yaml"
divvy init --config $DIVCFG
```

Looper will now have access to your computing configuration. Add the `export...` line to your `.bashrc` or `.profile` to ensure the `DIVCFG` variable persists for future command-line sessions. 
You can override the `DIVCFG` environment variable by specifying a path with `--divvy` argument, like this:

```bash
looper run
  --divvy /path/to/divvy_cfg.yaml ...
```

On a fresh init, `divvy` comes pre-loaded with some built-in compute packages, which you can explore by typing `divvy list`. This will display the available compute packages:

```{console}
divvy list
```


```{console}
Divvy config: divvy_config.yaml

docker
default
apptainer_slurm
apptainer
local
slurm
sge
bulker_local
bulker_slurm
```


For example, there's a package called 'slurm'. The template for this package looks a little different from the one we saw above:

```sh title="slurm_template.sub"
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

This template includes directives that are understood by the SLURM scheduler (that's what the `#SBATCH lines are`). So the resulting submission file is going to be a SLURM script, rather than simply a shell script.

So let's re-run looper but as we did before, but this time using this new package. You select a package in a `looper run` command with the `--package` argument:

```bash
looper run -d -l 1 \
  --package slurm
```

Now when we view the resulting submission script, we get a very different result:

```sh title="results/submission/count_lines_mexico.sub"
#!/bin/bash
#SBATCH --job-name='count_lines_mexico'
#SBATCH --output='/home/nsheff/code/hello_looper/pep_derived_attrs/results/submission/count_lines_mexico.log'
#SBATCH --mem='{MEM}'
#SBATCH --cpus-per-task='{CORES}'
#SBATCH --time='{TIME}'
#SBATCH --partition='{PARTITION}'
#SBATCH -m block
#SBATCH --ntasks=1

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`



pipeline/count_lines.sh data/mexico.txt

```


Of course, the template has changed to the slurm template.
The `{CODE}` variable was correctly populated, same as before, from the pipeline interface's `command_template` field.
But the other variables, like `{MEM}` and `{TIME}`, have not been populated.
Why not? Because we haven't provided looper any values for these variables.
So, how do we tell looper what to use?

### Parameterizing job templates through the command-line

The simplest way is that we can provide them on the command line using `--compute`, *e.g.*:


``` {.console .copy}
looper run -d -l 1 \
  --package slurm  \
  --compute partition=standard time='01-00:00:00' cores='32' mem='32000'
```

This command will populate the variables as you expect:


```sh title="results/submission/count_lines_mexico.sub"
#!/bin/bash
#SBATCH --job-name='count_lines_mexico'
#SBATCH --output='/home/nsheff/code/hello_looper/pep_derived_attrs/results/submission/count_lines_mexico.log'
#SBATCH --mem='32000'
#SBATCH --cpus-per-task='32'
#SBATCH --time='01-00:00:00'
#SBATCH --partition='standard'
#SBATCH -m block
#SBATCH --ntasks=1

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`



pipeline/count_lines.sh data/mexico.txt

```


### Parameterizing job templates through the looper config


It can be annoying to provide compute parameters every time you want to run your jobs. 
It's convenient to store those settings somewhere.
Luckily, looper provides a solution to this exact problem!
You can specify any command-line arguments through the looper config by adding a `cli` section.
For example, if we want to add these compute settings, we could do it like this:

```yaml title=".looper.yaml" hl_lines="5 6 7 8 9 10 11"
pep_config: metadata/pep_config.yaml
output_dir: results
pipeline_interfaces:
  - pipeline/pipeline_interface.yaml
cli:
  run:
    compute: 
      partition: standard
      time: '01-00:00:00'
      cores: '32'
      mem: '32000'
```

This works for other arguments as well. For example, if we want `looper run` to default to only running a single sample and using the `slurm` package, we could add these lines to our looper config:

```yaml title=".looper.yaml" hl_lines="7 8"
pep_config: metadata/pep_config.yaml
output_dir: results
pipeline_interfaces:
  - pipeline/pipeline_interface.yaml
cli:
  run:
    limit: 1
    package: slurm
    compute: 
      partition: standard
      time: '01-00:00:00'
      cores: '32'
      mem: '32000'
```

Now, we could override these by passing `-p` or `-l` on the command line.
Putting default arguments into the looper config `cli` section allows you to avoid having to type your common settings every time.
It also makes it easier to parameterize the pipeline differently for different projects.

### Parameterizing job templates through the pipeline interface

Sometimes, you want the pipeline to be parameterized globally, so you don't have to worry about re-parameterizing it for different projects.
You can also provide compute settings in the pipeline interface.
Let's add a `compute` section in the pipeline interface file, like this:


```yaml  title="pipeline/pipeline_interface.yaml" hl_lines="5 6 7 8 9"
pipeline_name: count_lines
sample_interface:
  command_template: >
    pipeline/count_lines.sh {sample.file_path}
compute:
  partition: standard
  time: '01-00:00:00'
  cores: '32'
  mem: '32000'
```

Now, with this new pipeline interface, you can leave off the `--compute` argument to `looper run`, as we did before, but the variables will be populated from the pipeline interface:

``` {.console .copy}
looper run -d -l 1 \  # this works!
  --package slurm  \
```

Parameterizing through the pipeline interface is useful if the parameters are going to be the same for this pipeline, regardless of the project. But sometimes, you need to set the parameters separately for each project...


!!! warning
    One problem with all of these methods is that they just provide the same compute parameters for every sample.
    What if your samples are widely different in input file size, and therefore require different parameters?
    If you need to change the parameters by sample, you can solve the problem through pipeline interface [size-dependent variables](../developer-tutorial/pipeline-interface-specification.md#size_dependent_variables). In many cases, the samples are roughly similar, so a single parameterization for the whole project will suffice.

So, there are several ways to provide compute parameters.
Why do we need all these different places to provide compute parameters?

Because different people/roles will be editing different things.

- the pipeline author is not necessarily the same as the person running the pipeline.
- the pipeline author may want to provide some basic compute guidance, which can do so in the pipeline interface. 
- the person running might way to configure something for the workspace as a whole. These go in the `.looper.yaml` file.
- but for a one-off run, that's different from normal, you can override with the `--compute` command-line argument.



## The submission command

There's one final important point about how looper job submission happens.
To looper, different compute packages are really not that different; if we pick the `slurm` package, mostly, it just means we're using a different template.
But there is one other very important difference: for the local package, looper needs to submit the job using `sh`, whereas for the slurm package, looper submits the job with `sbatch` -- the command used to assign a task to the SLURM scheduler.
This *submission command* is actually part of the compute package, and something you can specify if you create your own package.
For these built-in packages, the submission commands are already appropriately populated.


## Custom compute packages
For many use cases, the built-in packages will be sufficient.
But a great thing about looper is that these compute packages are totally customizable.
You can edit the templates, and even create your own custom compute packages.
This allows you to tailor divvy/looper to any compute environment.
See [How to create custom submission templates](../how-to/custom-submission-templates.md) for step-by-step instructions, or the [advanced computing guide](../advanced-guide/advanced-computing.md) for a deeper explanation of the nested template system.



!!! tip "Summary"
    - Looper runs jobs by creating job scripts and then running them.
    - You can control the job script by choosing a different submission package
    - You can view the list of available compute packages with `divvy list` and choose one with `looper run --package` or `-p`.
    - You pass parameters to the submission template in several ways, such as the pipeline interface, the looper config, or on the command line with `--compute`.

