# The divvy configuration file

At the heart of `divvy` is a the *divvy configuration file*, or `DIVCFG` for short. This is a `yaml` file that specifies a user's available *compute packages*. Each compute package represents a computing resource; for example, by default we have a package called `local` that populates templates to simple run jobs in the local console, and another package called `slurm` with a generic template to submit jobs to a SLURM cluster resource manager. Users can customize compute packages as much as needed. 

## Configuration file priority lookup

When `divvy` starts, it checks a few places for the `DIVCFG` file. First, the user may may specify a `DIVCFG` file when invoking `divvy` either from the command line or from within python. If the file is not provided, `divvy` will next look file in the `$DIVCFG` environment variable. If it cannot find one there, then it will load a default configuration file with a few basic compute packages. We recommend setting the `DIVCFG` environment variable as the most convenient use case.

## Customizing your configuration file

The easiest way to customize your computing configuration is to edit the default configuration file. To get a fresh copy of the default configuration, use `divvy init custom_divvy_config.yaml`. This will create for you a config file along with a folder containing all the default templates.

Here is an example `divvy` configuration file:

```{console}
compute_packages:
  default:
    submission_template: templates/local_template.sub
    submission_command: sh
  local:
    submission_template: templates/local_template.sub
    submission_command: sh
  develop_package:
    submission_template: templates/slurm_template.sub
    submission_command: sbatch
    partition: develop
  big:
    submission_template: templates/slurm_template.sub
    submission_command: sbatch
    partition: bigmem
```

The sub-sections below `compute_packages` each define a *compute package* that can be activated. `Divvy` uses these compute packages to determine how to submit your jobs. If you don't specify a package to activate, `divvy` uses the package named `default`. You can make your default whatever you like. You can activate any other compute package __on the fly__ by calling the `activate_package` function from python, or using the `--package` command-line option.

You can make as many compute packages as you wish, and name them whatever you wish. You can also add whatever attributes you like to the compute package. There are only two required attributes: each compute package must specify the `submission_command` and `submission_template` attributes. 

### The `submission_command` attribute

The `submission_command` attribute is the string your cluster resource manager uses to submit a job. For example, in our compute package named `develop_package`, we've set `submission_command` to `sbatch`. We are telling divvy that submitting this job should be done with: `sbatch submission_script.txt`.

### The `submission_template` attribute

Each compute package specifies a path to a template file (`submission_template`). The template file provides a skeleton that `divvy` will populate with job-specific attributes. These paths can be relative or absolute; relative paths are considered *relative to the DIVCFG file*. Let's explore what template files look like next.

## Template files

Each compute package must point to a template file with the `submission_template` attribute. These template files are typically stored relative to the `divvy` configuration file. Template files are taken by `divvy`, populated with job-specific information, and then run as scripts. Here's an example of a generic SLURM template file:

```{bash}
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

srun {CODE}
```

Template files use variables (*e.g.* `{VARIABLE}`), which will be populated independently for each job. If you want to make your own templates, you should check out the default templates (in the [submit_templates](https://github.com/pepkit/divcfg/tree/master/templates) folder). Many users will not need to tweak the template files, but if you need to, you can also create your own templates, giving `divvy` ultimate flexibility to work with any compute infrastructure in any environment. To create a custom template, just follow the examples. Then, point to your custom template in the `submission_template` attribute of a compute package in your `DIVCFG` config file.



## Resources

You may notice that the compute config file does not specify resources to request (like memory, CPUs, or time). Yet, these are required in order to submit a job to a cluster. **Resources are not handled by the divcfg file** because they not relative to a particular computing environment; instead they vary by pipeline and sample. As such, these items should be provided elsewhere. 
