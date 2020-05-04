# How to link a project to a pipeline

Looper links projects to pipelines through a file called the *pipeline interface*. If your pipeline is looper-compatible, all you have to do is point the samples to the pipeline interface files for any pipelines you want to run. We maintain a list of public [looper-compatible pipelines](https://github.com/pepkit/hello_looper/blob/master/looper_pipelines.md) that will get you started.

## Pointing your PEP to an existing pipeline interface file

 First, clone the pipeline repository. Inside your project config, set a `pipeline_interfaces` attribute on samples to point to the pipeline. There are 2 easy ways to do this: you can simply add a `pipeline_interfaces` column in the sample table; or, you can use an *append* modifier, like this:


```yaml
sample_modifiers:
  append:
    pipeline_interfaces: /path/to/pipeline_interface.yaml
```


The value for the `pipeline_interfaces` key should be the *absolute* path to the pipeline interface file.

Once your PEP is linked to the pipeline, you just need to make sure your project provides any sample metadata required by the pipeline. Such details are specific to each pipeline and should be defined somewhere in the pipeline's documentation.

# How to link to multiple pipelines

Looper decouples projects and pipelines, so you can have many projects using one pipeline, or many pipelines running on the same project. If you want to run more than one pipeline on a sample, you can simple add more than one pipeline interface, like this:

```yaml
sample_modifiers:
  append:
    pipeline_interfaces: [/path/to/pipeline_interface.yaml, /path/to/pipeline_interface2.yaml]
```

Looper will submit jobs for both of these pipelines.

If you have a project that contains samples of different types, then you can use an `imply` modifier to select which pipelines you want to run on which samples, like this:


```yaml
sample_modifiers:
  imply:
  	- if:
  		protocol: "RRBS"
	  then:
    	pipeline_interfaces: /path/to/pipeline_interface.yaml
    - if:
    	protocol: "ATAC"
      then:
        pipeline_interfaces: /path/to/pipeline_interface2.yaml
```


## Writing a new pipeline interface file.

Most users of pipelines will never need to create a new pipeline interface file. But if you do need to make a new pipeline looper-compatible, you do this by creating a `pipeline interface` file, which is explained in [Writing a pipeline interface](pipeline-interface.md).
