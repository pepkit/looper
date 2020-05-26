# How to run jobs in a linux container

Because `looper` uses `divvy` for computing configuration, running jobs in containers is easy! `Divvy` can use the same template system to do either cluster computing or to run jobs in linux containers (for example, using `docker` or `singularity`). You can even run jobs in a container *on a cluster*.

All you need to do is follow the same instructions as in [running jobs on a cluster](running-on-a-cluster.md), but use templates that run those jobs in containers. To see examples of how to do this, refer to the [divvy docs on running containers](http://divvy.databio.org/en/latest/containers/).


## Overview 

Here is a quick guide to get you started using containers with `looper`:

### 1. Get your container image. 

This could be a docker image (hosted on dockerhub), which you would download via `docker pull`, or it could be a `singularity` image you have saved in a local folder. This is pipeline-specific, and you'll need to download the image recommended by the authors of the pipeline or pipelines you want to run.


### 2. Specify the image in your `pipeline_interface`

The `pipeline_interface.yaml` file will need a `compute` section for each pipeline that can be run in a container, specifying the image. For example:


```yaml
compute:
  singularity_image: ${SIMAGES}myimage
  docker_image: databio/myimage
```

For singularity images, you just need to make sure that the images indicated in the `pipeline_interface` are available in those locations on your system. For docker, make sure you have the docker images pulled.


### 3. Configure your `DIVCFG`. 

`Divvy` will need templates that work with the container. This just needs to be set up once for your compute environment, which would enable you to run any pipeline in a container (as long as you have an image). You should set up the DIVCFG compute environment configuration by following instructions in the [DIVCFG readme](https://github.com/pepkit/divcfg). If it's not already container-aware, you will just need to add a new container-aware "compute package" to your DIVCFG file. Here's an example of how to add one for using singularity in a SLURM environment:

```yaml
singularity_slurm:
  submission_template: templates/slurm_singularity_template.sub
  submission_command: sbatch
  singularity_args: -B /sfs/lustre:/sfs/lustre,/nm/t1:/nm/t1
```

In `singularity_args` you'll need to pass any mounts or other settings to be passed to singularity. The actual `slurm_singularity_template.sub` file looks something like this:

```bash
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

singularity instance.start {SINGULARITY_ARGS} {SINGULARITY_IMAGE} {JOBNAME}_image
srun singularity exec instance://{JOBNAME}_image {CODE}

singularity instance.stop {JOBNAME}_image
```

Notice how these values will be used to populate a template that will run the pipeline in a container. Now, to use singularity, you just need to activate this compute package in the usual way, which is using the `package` argument: ``looper run --package singularity_slurm``. 
