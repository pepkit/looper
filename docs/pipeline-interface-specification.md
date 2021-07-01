---
title: Pipeline interface specification
---

<h1>Pipeline interface specification</h1>

Table of contents:

[TOC]

## Introduction

In order to run an arbitrary pipeline, we require a formal specification for how the pipeline is to be used. We define this using a *pipeline interface* file. It maps attributes of a PEP project or sample to the pipeline CLI arguments. Thus, it defines the interface between the project metadata (the PEP) and the pipeline itself.

If you're using *existing* `looper`-compatible pipelines, you don't need to create a new interface; just [point your project at the one that comes with the pipeline](defining-a-project.md). When creating *new* `looper`-compatible pipelines, you'll need to create a new pipeline interface file.



## Overview of pipeline interface components

A pipeline interface may contain the following keys:

- `pipeline_name` (REQUIRED) - A string identifying the pipeline,
- `pipeline_type` (REQUIRED) - A string indicating a pipeline type: "sample" (for `run`) or "project" (for `runp`),
- `command_template` (REQUIRED) - A [Jinja2](https://jinja.palletsprojects.com/en/2.11.x/) template used to construct a pipeline command command to run.
- `linked_pipeline_interfaces` (OPTIONAL) - A collection of paths to sample pipeline interfaces related to this pipeline interface (used only in project pipeline interfaces for `looper report` purposes).
- `input_schema` (RECOMMENDED) - A [PEP Schema](http://eido.databio.org) formally defining *required inputs* for the pipeline
- `output_schema` (RECOMMENDED) - A schema describing the *outputs* of the pipeline
- `compute` (RECOMMENDED) - Settings for computing resources
- `var_templates` (RECOMMENDED) - A mapping of [Jinja2](https://jinja.palletsprojects.com/en/2.11.x/) templates and corresponding names, typically used to encode submission-specific paths that can be submission-specific
- `pre_submit` (OPTIONAL) - A mapping that defines the pre-submission tasks to be executed

The pipeline interface should define either a sample pipeline or a project pipeline. Here's a simple example:

```yaml
pipeline_name: RRBS
pipeline_type: sample
var_templates:
  pipeline: "{looper.piface_dir}/pipelines/pipeline1.py"
  sample_info: "{looper.piface_dir}/{sample.name}/info.txt"
input_schema: path/to/rrbs_schema.yaml
command_template: {pipeline.var_templates.path} --input {sample.data_path} --info {pipeline.sample_info.path}
```

Pretty simple. The `pipeline_name` is arbitrary. It's used for messaging and identification. Ideally, it's unique to each pipeline. In this example, we define a single sample-level pipeline.

## Details of pipeline interface components

### pipeline_name

The pipeline name is arbitrary. It should be unique for each pipeline. Looper uses it for a few things:

1. to construct the `job_name` variable (accessible via `{ looper.job_name }`). See [variable namespaces](variable-namespaces.md) for more details.

2. to check for flags. For pipelines that produce flags, looper will be aware of them and not re-submit running jobs.

### pipeline_type

Looper can run 2 kinds of pipeline: *sample pipelines* run once per sample; *project pipelines* run once per project. The type of pipeline must be specified in the pipeline interface as `pipeline_type: sample` or `pipeline_type: project`.

### command_template

The command template is the most critical part of the pipeline interface. It is a [Jinja2](https://jinja.palletsprojects.com/) template for the command to run for each sample. Within the `command_template`, you have access to variables from several sources. These variables are divided into namespaces depending on the variable source. You can access the values of these variables in the command template using the single-brace jinja2 template language syntax: `{namespace.variable}`. For example, looper automatically creates a variable called `job_name`, which you may want to pass as an argument to your pipeline. You can access this variable with `{looper.job_name}`. The available namespaces are described in detail in [looper variable namespaces](variable-namespaces.md).

Because it's based on Jinja2, command templates are extremely flexible. For example, optional arguments can be accommodated using Jinja2 syntax, like this:

```
command_template: >
  {pipeline.path}
  --sample-name {sample.sample_name}
  --genome {sample.genome}
  --input {sample.read1}
  --single-or-paired {sample.read_type}
  {% if sample.read2 is defined %} --input2 {sample.read2} {% endif %}
  {% if sample.peak_caller is defined %} --peak-caller {sample.peak_caller} {% endif %}
  {% if sample.FRIP_ref is defined %} --frip-ref-peaks {sample.FRIP_ref} {% endif %}
```

Arguments wrapped in Jinja2 conditionals will only be added *if the specified attribute exists for the sample*.

### linked_pipeline_interfaces

*Only project pipeline interfaces will respect this attribute*

Since the sample and project pipeline interfaces are completely separate this is the only way to link them together. This attribute is used by `looper report` to organize the produced HTML reports into groups, i.e. project-level report will list linked sample-level reports.

```
linked_pipeline_interfaces:
  - ../pipeline_interface.yaml
  - /home/john/test/pipeline_interface1.yaml
```

The paths listed in `linked_pipeline_interfaces` are considered relative to the pipeline interface, unless they are absolute.


### input_schema

The input schema formally specifies the *input processed by this pipeline*. The input schema serves 2 related purposes:

1. **Validation**. Looper uses the input schema to ensure that the project fulfills all pipeline requirements before submitting any jobs. Looper uses the PEP validation tool, [eido](http://eido.databio.org), to validate input data by ensuring that input samples have the attributes and input files required by the pipeline. Looper will only submit a sample pipeline if the sample validates against the pipeline's input schema.

2. **Description**. The input schema is also useful to describe the inputs, including both required and optional inputs, thereby providing a standard way to describe a pipeline's inputs. In the schema, the pipeline author can describe exactly what the inputs mean, making it easier for users to learn how to structure a project for the pipeline.

Details for how to write a schema in in [writing a schema](http://eido.databio.org/en/latest/writing-a-schema/). The input schema format is an extended [PEP JSON-schema validation framework](http://pep.databio.org/en/latest/howto_validate/), which adds several capabilities, including

- `required` (optional): A list of sample attributes (columns in the sample table) that **must be defined**
- `required_files` (optional): A list of sample attributes that point to **input files that must exist**.
- `files` (optional): A list of sample attributes that point to input files that are not necessarily required, but if they exist, should be counted in the total size calculation for requesting resources.

If no `input_schema` is included in the pipeline interface, looper will not be able to validate the samples and will simply submit each job without validation.

### output_schema

The output schema formally specifies the *output produced by this pipeline*. It is used by downstream tools to that need to be aware of the products of the pipeline for further visualization or analysis. Like the input schema, it is based on JSON-schema, but *must* follow the [pipestat schema specification](http://pipestat.databio.org/en/latest/pipestat_specification/#pipestat-schema).

Here is an example output schema:

```yaml
number_of_things:
  type: integer
  multipleOf: 10
  minimum: 20
  description: "Number of things, min 20, multiple of 10"
smooth_bw:
  type: file
  value:
    path: "aligned_{genome}/{sample_name}_smooth.bw"
    title: "A smooth bigwig file"
  description: "This stores a bigwig file path"
peaks_bed:
  type: file
  value:
    path: "peak_calling_{genome}/{sample_name}_peaks.bed"
    title: "Peaks in BED format"
  description: "This stores a BED file path"
collection_of_things:
  type: array
  items:
    type: string
  description: "This stores collection of strings"
output_object:
  type: object
  properties:
    GC_content_plot:
      type: image
    genomic_regions_plot:
      type: image
  value:
    GC_content_plot:
      path: "gc_content_{sample_name}.pdf"
      thumbnail_path: "gc_content_{sample_name}.png"
      title: "Plot of GC content"
    genomic_regions_plot:
      path: "genomic_regions_{sample_name}.pdf"
      thumbnail_path: "genomic_regions_{sample_name}.png"
      title: "Plot of genomic regions"
  required:
    - GC_content
  description: "Object output with plots, the GC content plot is required"
```
Looper uses the output schema in its `report` function, which produces a browsable HTML report summarizing the pipeline results. The output schema provides the relative locations to sample-level and project-level outputs produced by the pipeline, which looper can then integrate into the output results. If the output schema is not included, the `looper report` will be unable to locate and integrate the files produced by the pipeline and will therefore be limited to simple statistics.

### compute

The compute section of the pipeline interface provides a way to set compute settings at the pipeline level. These variables can then be accessed in the command template. They can also be overridden by values in the PEP config, or on the command line. See the [looper variable namespaces](variable-namespaces.md) for details.

There is one reserved attribute under `compute` with specialized behavior -- `size_dependent_variables` which we'll now describe in detail.

#### size_dependent_variables

The `size_dependent_variables`  section lets you specify variables with values that are modulated based on the total input file size for the run. This is typically used to add variables for memory, CPU, and clock time to request, if they depend on the input file size. Specify variables by providing a relative path to a `.tsv` file that defines the variables as columns, with input sizes as rows.

The pipeline interface simply points to a `tsv` file:

```yaml
pipeline_type: sample
var_templates:
  path: pipelines/pepatac.py
command_template: >
  {pipeline.var_templates.path} ...
compute:
  size_dependent_variables: resources-sample.tsv
```

The `resources-sample.tsv` file consists of a file with at least 1 column called `max_file_size`. Add any other columns you wish, each one will represent a new attribute added to the `compute` namespace and available for use in your command template. Here's an example:

```tsv
max_file_size cores mem time
0.001 1 8000  00-04:00:00
0.05  2 12000 00-08:00:00
0.5 4 16000 00-12:00:00
1 8 16000 00-24:00:00
10  16  32000 02-00:00:00
NaN 32  32000 04-00:00:00
```

This example will add 3 variableS: `cores`, `mem`, and `time`, which can be accessed via `{compute.cores}`, `{compute.mem}`, and `{compute.time}`. Each row defines a "packages" of variable values. Think of it like a group of steps of increasing size. For a given job, looper calculates the total size of the input files (which are defined in the `input_schema`). Using this value, looper then selects the best-fit row by iterating over the rows until the calculated input file size does not exceed the `max_file_size` value in the row. This selects the largest resource package whose `max_file_size` attribute does not exceed the size of the input file. Max file sizes are specified in GB, so `5` means 5 GB.

This final line in the resources `tsv` must include `NaN` in the `max_file_size` column, which serves as a catch-all for files larger than the largest specified file size. Add as many resource sets as you want.

#### var_templates

This section can consist of multiple variable templates that are rendered and can be reused. The namespaces available to the templates are listed in [variable namespaces](variable-namespaces.md) section. Please note that the variables defined here (even if they are paths) are arbitrary and are *not* subject to be made relative. Therefore, the pipeline interface author needs take care of making them portable (the `{looper.piface_dir}` value comes in handy!).

#### pre_submit

This section can consist of two subsections: `python_funcions` and/or `command_templates`, which specify the pre-submission tasks to be run before the main pipeline command is submitted. Please refer to the [pre-submission hooks system](pre-submission-hooks.md) section for a detailed explanation of this feature and syntax.

## Validating a pipeline interface

A pipeline interface can be validated using JSON Schema against [schema.databio.org/pipelines/pipeline_interface.yaml](http://schema.databio.org/pipelines/pipeline_interface.yaml). Looper automatically validates pipeline interfaces at submission initialization stage.
