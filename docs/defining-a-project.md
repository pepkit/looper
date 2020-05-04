# How to define a project

## Start with a basic PEP

Most pipelines require a unique way to organize samples, but `looper` subscribes to [standard Portable Encapsulated Project (PEP) format](http://pepkit.github.io). PEP is a standardized way to represent metadata about your project and each of its samples. If you follow this format, then your project can be read not only by `looper`, but also by other software, like the [pepr R package](http://github.com/pepkit/pepr), or the [peppy python package](http://github.com/pepkit/peppy). You should read the instructions on [how to create a PEP](https://pepkit.github.io/docs/simple_example/) to use with `looper`.

So, the first thing you should do is follow the [instructions for how to make a PEP](https://pepkit.github.io/docs/simple_example/). Once you've have a basic PEP created, the next section shows you [how to add looper-specific configuration to the PEP config file](project-config-looper.md), or you can jump ahead to [linking a project to a pipeline](linking-a-pipeline.md).

# Configure a PEP to work with looper

Once you have a basic [PEP config](https://pepkit.github.io/docs/project_config/) file, you can connect it to looper by adding a `looper` section:

##  Add a `looper` section

The basic PEP structure is generic and can be used for a variety of tools. To add information required to run looper, you'll need to add a `looper` section. The `looper` section can contain a few looper-specific attributes:


- `output_dir` - the folder where you want looper to store your results.
- `compute` - You can specify project-specific compute settings in a `compute` section, 
but it's often more convenient and consistent to specify this globally with a `pepenv` environment configuration. 
Instructions for doing so are at the [`pepenv` repository](https://github.com/pepkit/pepenv). 
If you do need project-specific control over compute settings (like submitting a certain project to a certain resource account), 
you can do this by specifying variables in a project config `compute` section, which will override global `pepenv` values for that project only.
- `command_extra`
- `pipeline_interfaces`
- `results_subdir`, default: `results_pipeline`
- `submission_subdir`, default: `submission`

Example:
```yaml
looper:
  compute:
    partition: project_queue_name
```
