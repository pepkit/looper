# How to link a project to a pipeline

One of the advantages of looper is that it decouples projects and pipelines, so you can have many projects that all use the same pipeline, or many pipelines running on the same project. This modular connection between pipelines and projects happens through a file called the `pipeline interface`. 

**If you're using one or more existing looper-compatible pipelines**, all you have to do is point your project config file at the `pipeline interface` files for any pipelines your project needs. For most casual users of pipelines, that's all you'll need to do;  you'll never need to create a new `pipeline interface` file. 

But **if you need to make a new pipeline looper-compatible**, you do this by creating a `pipeline interface` file for the pipeline. This lets the pipeline author tell looper how to run the pipeline. This is explained in [Writing a pipeline interface](pipeline-interface.md).

Many projects will require only existing pipelines that are already looper-compatible. We maintain a (growing) list of public [looper-compatible pipelines](https://github.com/pepkit/hello_looper/blob/master/looper_pipelines.md) that will get you started. The list includes pipelines for experiments covering transcription (RNA-seq), chromatin accessibility (ATAC-seq), DNA methylation (RRBS and WGBS), and chromatin interaction and binding (HiChIP).

To use one of these pipelines, first clone the desired code repository. Then, use the `pipeline_interfaces` key in the `metadata` section of a project config file to point your project to that `pipeline_interface` file:

```yaml
  metadata:
    pipeline_interfaces: /path/to/cloned/pipeline_interface.yaml
```

The value for the `pipeline_interfaces` key should be the *absolute* path to the pipeline interface file. After that, you just need to make sure your project definition provides all the necessary sample metadata required by the pipeline you want to use. For example, you will need to make sure your sample annotation sheet specifies the correct value under `protocol` that your linked pipeline understands. 
Such details are specific to each pipeline and should be defined somewhere in the pipeline's documentation, e.g. in a `README` file.

You can also [link more than one pipeline](linking-multiple-pipelines.md).
