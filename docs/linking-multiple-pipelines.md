# How to link to multiple pipelines

If you have a project that contains samples of different types, then you may need to **link more than one pipeline** to your project. You do this by simply adding other `pipeline interface` files to a list in the `metadata.pipeline_interfaces` field, like this:

```yaml
  metadata:
    pipeline_interfaces: [/path/pipeline_interface1.yaml, /path/pipeline_interface2.yaml]
```


In this case, for a given sample, looper will first look in `pipeline_interface1.yaml` to see if appropriate pipeline exists for this sample type. If it finds one, it will use this pipeline (or set of pipelines, as specified in the `protocol_mappings` section of the ``pipeline_interface.yaml` file). Having submitted a suitable pipeline it will ignore the pipeline_interface2.yaml interface. However if there is no suitable pipeline in the first interface, looper will check the second and, if it finds a match, will submit that. If no suitable pipelines are found in any of the interfaces, the sample will be skipped as usual.

If your project contains samples with different protocols, you can use this to run several different pipelines. For example, if you have ATAC-seq, RNA-seq, and ChIP-seq samples in your project, you may want to include a `pipeline interface` for 3 different pipelines, each accepting one of those protocols. In the event that more than one of the `pipeline interface` files provide pipelines for the same protocol, looper will only submit the pipeline from the first interface. Thus, this list specifies a *priority order* to pipeline repositories.

