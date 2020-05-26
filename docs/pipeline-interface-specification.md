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
- `path` (RECOMMENDED) - The path to the pipeline script, relative to the pipeline interface. 
- `input_schema` (RECOMMENDED) - A [PEP Schema](http://eido.databio.org) formally defining *required inputs* for the pipeline
- `output_schema` (RECOMMENDED) - A schema describing the *outputs* of the pipeline
- `compute` (RECOMMENDED) - Settings for computing resources
- `sample_yaml_path` (OPTIONAL) - Path to sample yaml files produced by looper.

The pipeline interface should define either a sample pipeline or a project pipeline. Here's a simple example:

```yaml
pipeline_name: RRBS
pipeline_type: sample
path: path/to/rrbs.py
input_schema: path/to/rrbs_schema.yaml
command_template: {pipeline.path} --input {sample.data_path}
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

### path

Absolute or relative path to the script or command for this pipeline. Relative paths are considered **relative to your pipeline_interface file**. We strongly recommend using relative paths where possible to keep your pipeline interface file portable. You may also use shell environment variables (like `${HOME}`) in the `path`. You can then use this variable to refer to the pipeline command to execute by using `{pipeline.path}` in the `command_template`.

The `path` attribute is not necessary; it is possible to simply include the relative path to the pipeline inside the `command_template` directly. However, we recommend using `path` instead, and then referring to it in the command_template using `{pipeline.path}`, because this indicates more clearly what the base script of the pipeline is.

### input_schema

The input schema formally specifies the *input processed by this pipeline*. The input schema serves 2 related purposes:

1. **Validation**. Looper uses the input schema to ensure that the project fulfills all pipeline requirements before submitting any jobs. Looper uses the PEP validation tool, [eido](http://eido.databio.org), to validate input data by ensuring that input samples have the attributes and input files required by the pipeline. Looper will only submit a sample pipeline if the sample validates against the pipeline's input schema.

2. **Description**. The input schema is also useful to describe the inputs, including both required and optional inputs, thereby providing a standard way to describe a pipeline's inputs. In the schema, the pipeline author can describe exactly what the inputs mean, making it easier for users to learn how to structure a project for the pipeline.

Details for how to write a schema in in [writing a schema](http://eido.databio.org/en/master/writing-a-schema/). The input schema format is an extended [PEP JSON-schema validation framework](http://pep.databio.org/en/latest/howto_validate/), which adds several capabilities, including 

- `required` (optional): A list of sample attributes (columns in the sample table) that **must be defined**
- `required_files` (optional): A list of sample attributes that point to **input files that must exist**.
- `files` (optional): A list of sample attributes that point to input files that are not necessarily required, but if they exist, should be counted in the total size calculation for requesting resources.

If no `input_schema` is included in the pipeline interface, looper will not be able to validate the samples and will simply submit each job without validation.

### output_schema

The output schema formally specifies the *output produced by this pipeline*. It is used by downstream tools to that need to be aware of the products of the pipeline for further visualization or analysis. Like the input schema, it is based on the extended [PEP JSON-schema validation framework](http://pep.databio.org/en/latest/howto_schema/), but adds looper-specific capabilities. The base schema has two *properties* sections, one that pertains to the project, and one that pertains to the samples. The *properties* sections for both sample and project will recognize these attributes: 

- `title`, following the base JSON-schema spec.
- `description`, following the base JSON-schema spec.
- `path`, used to specify a relative path to an output file. The value in the `path` attribute is a template for a path that will be populated by sample variables. Sample variables can be used in the template using brace notation, like `{sample_attribute}`.
- `thumbnail_path`, templates similar to the `path` attribute, but used to specify a thumbnail output version.
- `type`, the data type of this output. Can be one of: link, image, file.

The attributes added under the *Project properties* section are assumed to be project-level outputs, whereas attributes under the `samples` object are sample-level outputs. Here is an example output schema:

```
description: objects produced by PEPPRO pipeline.
properties:
  samples:
    type: array
    items:
      type: object
      properties:
        smooth_bw: 
          path: "aligned_{genome}/{sample_name}_smooth.bw"
          type: string
          description: "A smooth bigwig file"
        aligned_bam: 
          path: "aligned_{genome}/{sample_name}_sort.bam"
          type: string
          description: "A sorted, aligned BAM file"
        peaks_bed: 
          path: "peak_calling_{genome}/{sample_name}_peaks.bed"
          type: string
          description: "Peaks in BED format"
  tss_file:
    title: "TSS enrichment file"
    description: "Plots TSS scores for each sample."
    thumbnail_path: "summary/{name}_TSSEnrichment.png"
    path: "summary/{name}_TSSEnrichment.pdf"
    type: image
  counts_table:
    title: "Project peak coverage file"
    description: "Project peak coverages: chr_start_end X sample"
    path: "summary/{name}_peaks_coverage.tsv"
    type: link
```

Looper uses the output schema in its `report` function, which produces a browsable HTML report summarizing the pipeline results. The output schema provides the relative locations to sample-level and project-level outputs produced by the pipeline, which looper can then integrate into the output results. If the output schema is not included, the `looper report` will be unable to locate and integrate the files produced by the pipeline and will therefore be limited to simple statistics.

### compute

The compute section of the pipeline interface provides a way to set compute settings at the pipeline level. These variables can then be accessed in the command template. They can also be overridden by values in the PEP config, or on the command line. See the [looper variable namespaces](variable-namespaces.md) for details. 

There are two reserved attributes under  `compute` with specialized behavior: `size_dependent_variables` and `dynamic_variables_command_template`, which we'll now describe in detail.

#### size_dependent_variables

The `size_dependent_variables`  section lets you specify variables with values that are modulated based on the total input file size for the run. This is typically used to add variables for memory, CPU, and clock time to request, if they depend on the input file size. Specify variables by providing a relative path to a `.tsv` file that defines the variables as columns, with input sizes as rows.

The pipeline interface simply points to a `tsv` file:

```yaml
pipeline_type: sample
path: pipelines/pepatac.py
command_template: >
  {pipeline.path} ...
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

#### dynamic_variables_command_template

The size-dependent variables is a convenient system to modulate computing variables based on file size, but it is not flexible enough to allow modulated compute variables on the basis of other sample attributes. For a more flexible version, looper provides the `dynamic_variables_command_template`. The dynamic variables command template specifies a Jinja2 template to construct a system command run in a subprocess. This command template has available all of the namespaces in the primary command template. The command should return a JSON object, which is then used to populate submission templates. This allows you to specify computing variables that depend on any attributes of a project, sample, or pipeline, which can be used for ultimate flexibility in computing.

Example:

```
pipeline_type: sample
path: pipelines/pepatac.py
command_template: >
  {pipeline.path} ...
compute:
  dynamic_variables_command_template: python script.py --arg {sample.attribute}
```


### sample_yaml_path

Looper produces a yaml file that represents the sample. By default the file is saved in submission directory in `{sample.sample_name}.yaml`. You can override the default by specifying a `sample_yaml_path` attribute in the pipeline interface:

```
sample_yaml_path: {sample.sample_name}.yaml
```

This attribute, like the `command_template`, has access to any of the looper namespaces, in case you want to use them in the names of your sample yaml files.

## Validating a pipeline interface

A pipeline interface can be validated using JSON Schema against [schema.databio.org/pipelines/pipeline_interface.yaml](http://schema.databio.org/pipelines/pipeline_interface.yaml). 
