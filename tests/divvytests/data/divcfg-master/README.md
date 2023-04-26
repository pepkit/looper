# 1. Overview of `divvy` configuration files

The `divcfg` repository contains [divvy](http://code.databio.org/divvy/) computing configuration files currently in use across several research computing environments (Stanford, NIH, UVA, CeMM, and Memorial Sloan-Kettering). These files describe computing environments so that any tool that uses `divvy` can run jobs in these environments. These files can be used as examples to help you set up cluster or containerized computing in your own environment.

# 2. Setting up your environment

## Using `divvy` in pre-configured environments

If you're at one of the following places, set-up is very simple. Here's a list of pre-configured computing environments:

   * `uva_rivanna.yaml`: [Rivanna cluster](http://arcs.virginia.edu/rivanna) at University of Virginia
   * `cemm.yaml`: Cluster at the Center for Molecular Medicine, Vienna
   * `nih_biowulf2.yaml`: [Biowulf2](https://hpc.nih.gov/docs/userguide.html) cluster at the NIH
   * `stanford_sherlock.yaml`: [Sherlock](http://sherlock.stanford.edu/mediawiki/index.php/Current_policies) cluster at Stanford
   * `ski-cer_lilac.yaml`: *lilac* cluster at Memorial Sloan Kettering
   * `local_containers.yaml`: A generic local desktop or server (with no cluster management system) that will use docker or singularity containers.

To configure `divvy` to use one of these, all you have to do is:

1. Clone this repository (*e.g.* `git clone https://github.com/pepkit/divcfg.git`)
2. Point the `$DIVCFG` environment variable to the appropriate config file by executing this command:
	```
	export DIVCFG=path/to/compute_config.yaml
	```
 	(Add this line to your `.profile` or `.bashrc` if you want it to persist).

3. Install divvy (*e.g.* `pip install --user --upgrade divvy`)

And that's it, you're done! You can run `divvy list` on the command line to show you available compute packages.

If the existing config files do not fit your environment, you will need to create a `divvy` config file to match your environment by following these instructions:

## Configuring a new environment

To configure a new environment, we'll follow the same steps, but just point at the default file, `compute_config.yaml`, which we will then edit to match your local computing environment.

1. Clone this repository  (*e.g.* `git clone https://github.com/pepkit/divcfg.git`)
2. Point the `$DIVCFG` environment variable to the **default config file** by executing this command:
  ```
  export DIVCFG=path/to/compute_config.yaml
  ```
  (Add this line to your `.profile` or `.bashrc` if you want it to persist).

3. Next, use `compute_config.yaml` as a starting point to configure your environment. If you're using SLURM and you're lucky, the only thing you will need to change is the `partition` variable, which should reflect your submission queue or partition name used by your cluster resource manager. To make more advanced changes, the documentation below will guide you through all components of the configuration.

4. Once you have it working, consider submitting your configuration file back to this repository with a pull request.


# 3. DIVCFG configuration explained

The `divvy` documentation includes detailed instructions for [how to write your own divvy configuration file](http://divvy.databio.org/en/latest/configuration/).

# What is divvy?

`Divvy` enables any tool to seamlessly switch between cluster resource managers (SGE, SLURM, *etc.*), linux containers (`docker`, `singularity`, *etc.*), or other computing environments.
