---
title: Pipeline interface specification
---

# Writing a pipeline interface

## Introduction

If you want to use looper to run samples in a PEP through an arbitrary shell command, you will need to write a pipeline interface. Here is a basic walkthrough to write a simple interface file. Once you've been through this, you can consult the formal [pipeline interface format specification](pipeline-interface-specification.md) for further details and reference. 

## Example

Let's start with a simple example:

```yaml
pipeline_name: RRBS
sample_pipeline:
    path: path/to/rrbs.py
    input_schema: path/to/rrbs_schema.yaml
    command_template: <
      {pipeline.path} "--input" {sample.data_path}
```

Pretty simple. The `pipeline_name` is arbitrary. It's used for messaging and identification. Ideally, it's unique to each pipeline. In this example, we define a single sample-level pipeline. Each `sample_pipeline` or `project_pipeline` section can have any of these components:


...

details pending
