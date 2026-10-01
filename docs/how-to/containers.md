# How to run jobs in containers

Looper supports running pipelines inside containers. The recommended approach is to use [bulker](bulker.md), which manages lightweight, modular, single-tool containers. For pipelines that require a monolithic container (one large image containing the entire pipeline), looper also provides built-in Docker and Apptainer compute packages, described below.

!!! tip "Prefer bulker"
    If your pipeline supports bulker, use the built-in `bulker_local` or `bulker_slurm` packages instead. See [Using looper with bulker](bulker.md).

!!! note "What you'll accomplish"
    Configure looper to run pipeline jobs inside monolithic Docker or Apptainer containers.



## 1. Get your container image.

This could be a docker image (hosted on dockerhub), which you would download via `docker pull`, or it could be an `apptainer` image you have saved in a local folder. This is pipeline-specific, and you'll need to download the image recommended by the authors of the pipeline or pipelines you want to run.


## 2. Specify the image in your `pipeline_interface`

The `pipeline_interface.yaml` file will need a `compute` section for each pipeline that can be run in a container, specifying the image. For example:


```yaml title="pipeline_interface.yaml"
compute:
  apptainer_image: ${SIMAGES}myimage
  docker_image: databio/myimage
```

For apptainer images, you just need to make sure that the images indicated in the `pipeline_interface` are available in those locations on your system. For docker, make sure you have the docker images pulled.


## 3. Run with a built-in container package

Looper ships with built-in compute packages for Apptainer and Docker, so you don't need to create your own. Just select the appropriate package:

```shell
# Apptainer locally
looper run --package apptainer

# Apptainer on SLURM
looper run --package apptainer_slurm \
  --compute partition=standard time='04:00:00' cores='8' mem='16000'

# Docker locally
looper run --package docker
```

To pass extra arguments to the container runtime (e.g., bind mounts for apptainer), use `--compute`:

```shell
looper run --package apptainer_slurm \
  --compute partition=standard time='04:00:00' cores='8' mem='16000' \
  apptainer_args='-B /sfs/lustre:/sfs/lustre,/nm/t1:/nm/t1'
```

Or set these in your looper config to avoid typing them every time:

```yaml title=".looper.yaml"
cli:
  run:
    package: apptainer_slurm
    compute:
      partition: standard
      time: '04:00:00'
      cores: '8'
      mem: '16000'
      apptainer_args: -B /sfs/lustre:/sfs/lustre,/nm/t1:/nm/t1
```

## Available container packages

| Package | Runtime | Submission | Description |
|---------|---------|-----------|-------------|
| `apptainer` | Apptainer | `sh` (local) | Run in an apptainer container locally |
| `apptainer_slurm` | Apptainer | `sbatch` | Submit apptainer jobs to SLURM |
| `docker` | Docker | `sh` (local) | Run in a docker container locally |


!!! tip "Summary"
    - For modular, single-tool containers, use [bulker](bulker.md) -- it's the preferred approach.
    - For monolithic containers, use the Docker or Apptainer compute packages described above.
    - To looper, containers are just another computing environment setting. You can use the submission template to wrap the command in whatever boilerplate you want, which can be used either for cluster submission or for containers.
