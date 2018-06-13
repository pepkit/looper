.. _containers:

How to run jobs in a linux container
=============================================

Looper uses a template system to build scripts for each job. To start, looper includes a few built-in templates so you can run basic jobs without messing with anything, but the template system provides ultimate flexibility to customize your job scripts however you wish. This template system is how we can use looper to run jobs on any cluster resource manager, by simply setting up a template that fits our particular cluster manager. We can also exploit the template system to run any job in a linux container (for example, using docker or singularity).

Here is a guide on how to run a job in a container:

1. Get your container image. This could be a docker image (hosted on dockerhub), which you would download via `docker pull`, or it could be a `singularity` image you have saved in a local folder. This is pipeline-specific, and you'll need to download the image recommended by the authors of the pipeline or pipelines you want to run.


2. Specify the location of the image for your pipeline. Looper will need to know what image you are planning to use. Probably, the author of the pipeline has already done this for you by specifying the image in the `pipeline_interface.yaml` file. That `yaml` file will need a `compute` section for each pipeline that can be run in a container, specifying the location of the container. For example:



.. code-block:: yaml

    compute:
      singularity_image: ${SIMAGES}myimage
      docker_image: databio/myimage


For singularity images, you just need to make sure that the images indicated in the `pipeline_interface` are available in those locations on your system. For docker, make sure you have the docker images pulled.


3. Configure your `PEPENV`. Looper will need a computing environment configuration that provides templates that work with the container system of your choice. This just needs to be set up once for your compute environment,  which would enable you to run any pipeline in a container (as long as you have an image). You should set up the PEPENV compute environment configuration by following instructions in the `pepenv readme <https://github.com/pepkit/pepenv>`_. If it's not already container-aware, you will just need to add a new container-aware "compute package" to your PEPENV file. Here's an example of how to add one for using singularity in a SLURM environment:

.. code-block:: yaml

  singularity_slurm:
    submission_template: templates/slurm_singularity_template.sub
    submission_command: sbatch
    singularity_args: -B /sfs/lustre:/sfs/lustre,/nm/t1:/nm/t1

In `singularity_args` you'll need to pass any mounts or other settings to be passed to singularity. The actual `slurm_singularity_template.sub` file looks something like this. Notice how these values will be used to populate a template that will run the pipeline in a container.

.. code-block:: bash

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


Now, to use singularity, you just need to activate this compute package in the usual way, which is using the `compute` argument: ``looper run --compute singularity_slurm``. More detailed instructions can be found in the `pepenv readme <https://github.com/pepkit/pepenv>`_ under `containers`.



