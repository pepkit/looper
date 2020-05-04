# How to link to multiple pipelines

If you have a project that contains samples of different types, then you may need to **link more than one pipeline** to your project. You do this by simply adding other `pipeline interface` files to a list in the `metadata.pipeline_interfaces` field, like this:

```yaml
  metadata:
    pipeline_interfaces: [/path/pipeline_interface1.yaml, /path/pipeline_interface2.yaml]
```


In this case, for a given sample, looper will first look in `pipeline_interface1.yaml` to see if appropriate pipeline exists for this sample type. If it finds one, it will use this pipeline (or set of pipelines, as specified in the `protocol_mappings` section of the ``pipeline_interface.yaml` file). Having submitted a suitable pipeline it will ignore the pipeline_interface2.yaml interface. However if there is no suitable pipeline in the first interface, looper will check the second and, if it finds a match, will submit that. If no suitable pipelines are found in any of the interfaces, the sample will be skipped as usual.

If your project contains samples with different protocols, you can use this to run several different pipelines. For example, if you have ATAC-seq, RNA-seq, and ChIP-seq samples in your project, you may want to include a `pipeline interface` for 3 different pipelines, each accepting one of those protocols. In the event that more than one of the `pipeline interface` files provide pipelines for the same protocol, looper will only submit the pipeline from the first interface. Thus, this list specifies a *priority order* to pipeline repositories.


## How to map different pipelines to different samples

In the earlier version of looper, the pipeline interface file specified a `protocol_mappings` section. This mapped sample `protocol` (the assay type, sometimes called "library" or "library strategy") to one or more pipeline program.  This section specifies that samples of protocol `RRBS` will be mapped to the pipeline specified by key `rrbs_pipeline`. 
 




## Protocol mapping section

The `protocol_mapping` section explains how looper should map from a sample protocol 
(like `RNA-seq`, which is a column in your annotation sheet) to a particular pipeline (like `rnaseq.py`), or group of pipelines. 
Here's how to build `protocol_mapping`:

**Case 1:** one protocol maps to one pipeline. Example: `RNA-seq: rnaseq.py`
Any samples that list "RNA-seq" under `library` will be run using the `rnaseq.py` pipeline. 
You can list as many library types as you like in the protocol mapping, 
mapping to as many pipelines as you configure in your `pipelines` section.

Example:
    
```yaml
protocol_mapping:
    RRBS: rrbs.py
    WGBS: wgbs.py
    EG: wgbs.py
    ATAC: atacseq.py
    ATAC-SEQ: atacseq.py
    CHIP: chipseq.py
    CHIP-SEQ: chipseq.py
    CHIPMENTATION: chipseq.py
    STARR: starrseq.py
    STARR-SEQ: starrseq.py
```

**Case 2:** one protocol maps to multiple *independent* pipelines. 
    
Example:

```yaml
protocol_mapping
  Drop-seq: quality_control.py, dropseq.py
```

You can map multiple pipelines to a single protocol if you want samples of a type to kick off more than one pipeline run.
The basic formats for independent pipelines (i.e., they can run concurrently):

Example A:
```yaml
protocol_mapping:
    SMART-seq:  >
      rnaBitSeq.py -f,
      rnaTopHat.py -f
```


Example B:
```yaml
protocol_mapping:
  PROTOCOL: [pipeline1, pipeline2, ...]
```

**Case 3:** a protocol runs one pipeline which depends on another.

*Warning*: This feature (pipeline dependency) is not implemented yet. This documentation describes a protocol that may be implemented in the future, if it is necessary to have dependency among pipeline submissions.

Use *semicolons to indicate dependency*.

Example:
```yaml
protocol_mapping:
    WGBSQC: >
      wgbs.py;
      (nnm.py, pdr.py)
```