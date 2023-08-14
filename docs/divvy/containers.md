
# Configuring containers with divvy

The divvy template framework is a natural way to run commands in a container, for example, using `docker` or `singularity`. All we need to do is 1) design a template that will run the job in the container, instead of natively; and 2) create a new compute package that will use that template.

## A template for container runs

If you start up divvy without giving it a DIVCFG file, it will come with a few default compute packages that include templates for containers. You can also find these in [the divcfg repository](http://github.com/pepkit/divcfg), which includes these scenarios:

- singularity on SLURM
- singularity on localhost
- docker on localhost
- others

If you need a different system, looking at those examples should get you started toward making your own. To take a quick example, using singularity on SLURM combines the basic SLURM script template with these lines to execute the run in container:

```
singularity instance.start {SINGULARITY_ARGS} {SINGULARITY_IMAGE} {JOBNAME}_image
srun singularity exec instance://{JOBNAME}_image {CODE}
singularity instance.stop {JOBNAME}_image
```

This particular template uses some variables provided by different sources: `{JOBNAME}`, `{CODE}`, `{SINGULARITY_ARGS}` and `{SINGULARITY_IMAGE}`. These arguments could be defined at different places. For example, the `{SINGULARITY_IMAGE}` variable should point to a singularity image that could vary by pipeline, so it makes most sense to define this variable individually for each pipeline. So, any pipeline that provides a container should probably include a `singularity_image` attribute providing a place to point to the appropriate container image.

Of course, you will also need to make sure that you have access to `singularity` command from the compute nodes; on some clusters, you may need to add a `module load singularity` (or some variation) to enable it.

The `{SINGULARITY_ARGS}` variable comes just right after the `instance.start` command, and can be used to pass any command-line arguments to singularity. We use these, for example, to bind host disk paths into the container. **It is critical that you explicitly bind any file systems with data necessary for the pipeline so the running container can see those files**. The [singularity documentation](https://singularity.lbl.gov/docs-mount#specifying-bind-paths) explains this, and you can find other arguments detailed there. Because this setting describes something about the computing environment (rather than an individual pipeline or sample), it makes most sense to put it in the `DIVCFG` file for a particular compute package. The next section includes examples of how to use `singularity_args`.

If you're using [looper](http://looper.databio.org), the `{JOBNAME}` and `{CODE}` variables will be provided automatically by looper.

## Adding compute packages for container templates

To add a package for these templates to a `DIVCFG` file, we just add a new section. There are a few examples in this repository. A singularity example we use at UVA looks like this:

```
singularity_slurm:
  submission_template: templates/slurm_singularity_template.sub
  submission_command: sbatch
  singularity_args: --bind /sfs/lustre:/sfs/lustre,/nm/t1:/nm/t1
singularity_local:
  submission_template: templates/localhost_singularity_template.sub
  submission_command: sh
  singularity_args: --bind /ext:/ext
```

These singularity compute packages look just like the typical ones, but just change the `submission_template` to point to the new containerized templates described in the previous section, and then they add the `singularity_args` variable, which is what will populate the `{SINGULARITY_ARGS}` variable in the template. Here we've used these to bind (mount) particular file systems the container will need. You can use these to pass along any environment-specific settings to your singularity container.

With this setup, if you want to run a singularity container, just specify `--compute singularity_slurm` or `--compute singularity_local` and it will use the appropriate template. 

For another example, take a look at the basic `localhost_container.yaml` DIVCFG file, which describes a possible setup for running docker on a local computer:

```
compute:
  default:
    submission_template: templates/localhost_template.sub
    submission_command: sh
  singularity:
    submission_template: templates/localhost_singularity_template.sub
    submission_command: sh
    singularity_args: --bind /ext:/ext
  docker:
    submission_template: templates/localhost_docker_template.sub
    submission_command: sh
    docker_args: |
      --user=$(id -u) \
      --env="DISPLAY" \
      --volume ${HOME}:${HOME} \
      --volume="/etc/group:/etc/group:ro" \
      --volume="/etc/passwd:/etc/passwd:ro" \
      --volume="/etc/shadow:/etc/shadow:ro"  \
      --volume="/etc/sudoers.d:/etc/sudoers.d:ro" \
      --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
      --workdir="`pwd`" \
```

Notice the `--volume` arguments, which mount disk volumes from the host into the container. This should work out of the box for most docker users.
