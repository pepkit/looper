# How to link a project to a pipeline

One of the advantages of looper is that it decouples projects and pipelines, so you can have many projects that all use the same pipeline, or many pipelines running on the same project. This modular connection between pipelines and projects happens through a file called the `pipeline interfaces`. The `pipeline interfaces` tell `looper` how to run the pipeline.

**If you're using existing looper-compatible pipelines**, all you have to do is point the samples to the `pipeline interface` files for any pipelines you want to run on them (see instructions below). For most casual users of pipelines, that's all you'll need to do;  you'll never need to create a new `pipeline interface` file. But **if you do need to make a new pipeline looper-compatible**, you do this by creating a `pipeline interface` file, which is explained in [Writing a pipeline interface](pipeline-interface.md).

## Pointing your PEP to an existing pipeline interface file

Many projects will require only existing pipelines that are already looper-compatible. We maintain a list of public [looper-compatible pipelines](https://github.com/pepkit/hello_looper/blob/master/looper_pipelines.md) that will get you started. To use one of these pipelines, first clone the desired code repository. Then, set a `pipeline_interfaces` attribute on the sample. There are 2 easy ways to do this: you can simply add a `pipeline_interfaces` column in the sample table; or, you can use an *append* modifier, like this:


```yaml
sample_modifiers:
  append:
    pipeline_interfaces: /path/to/pipeline_interface.yaml
```


The value for the `pipeline_interfaces` key should be the *absolute* path to the pipeline interface file. After that, you just need to make sure your project definition provides all the necessary sample metadata required by the pipeline you want to use. For example, you will need to make sure your sample annotation sheet specifies the correct value under `protocol` that your linked pipeline understands. Such details are specific to each pipeline and should be defined somewhere in the pipeline's documentation, e.g. in a `README` file.

You can also [link more than one pipeline](linking-multiple-pipelines.md).
