---
title: Pipeline interface specification
---

# Writing a pipeline interface

## Introduction

If you want to use looper to run samples in a PEP through an arbitrary shell command, you will need to write a pipeline interface. Here is a basic walkthrough to write a simple interface file. Once you've been through this, you can consult the formal [pipeline interface format specification](pipeline-interface-specification.md) for further details and reference. 

## Example

Let's start with a simple example from the [hello_looper repository](https://github.com/pepkit/hello_looper):

```yaml
pipeline_name: count_lines
pipeline_type: sample
path: count_lines.sh  # relative to this pipeline_interface.yaml file
command_template: >
  {pipeline.path} {sample.file}
```

You can edit this to start your own interface. 

First, think of a unique name for your pipeline and put it in  `pipeline_name`. This will be used for messaging and identification.

Next, choose a `pipeline_type`, which can be either "sample" or "project". Most likely, you're writing a sample pipeline, but you can read more about [sample and project pipelines](pipeline-tiers.md) if you like. 

Next, we need to set the `path` to our script. This path is relative to the pipeline interface file, so you need to put the pipeline interface somewhere specific relative to the pipeline; perhaps in the same folder or in a parent folder.

Finally, populate the `command_template`. You can use the full power of Jinja2 python templates here, but most likely you'll just need to use a few variables using curly braces. In this case, we refer to the `count_lines.sh` script with `{pipeline.path}`, which points directly to the `path` variable defined above. Then, we use `{sample.file}` to refer to the `file` column in the sample table specified in the PEP. This pipeline thus takes a single positional command-line argument. You can make the command template much more complicated and refer to any sample or project attributes, as well as a bunch of [other variables made available by looper](variable-namespaces.md).

Now, you have a basic functional pipeline interface. There are many more advanced features you can use to make your pipeline more powerful, such as providing a schema to specify inputs or outputs, making input-size-dependent compute settings, and more. For complete details, consult the formal [pipeline interface format specification](pipeline-interface-specification.md).