---
title: Pipeline interface specification
---

<h1>Pipeline interface specification</h1>

Table of contents:

[TOC]

## Introduction

To run an arbitrary pipeline, we require a formal specification for how the pipeline is run.
We define this using a *pipeline interface* file.
It maps attributes of a PEP project or sample to the pipeline CLI arguments.
Thus, it defines the interface between the project metadata (the PEP) and the pipeline itself.

## Overview of pipeline interface components

A pipeline interface may contain the following keys:

- `pipeline_name` (REQUIRED) - A string identifying the pipeline.
- `sample_interface` OR `project_interface` (REQUIRED) - which will hold the  `command_template` (REQUIRED) variable with a [Jinja2](https://jinja.palletsprojects.com/) template used to construct a pipeline command to run.
- `input_schema` (RECOMMENDED) - A [PEP Schema](https://pep.databio.org/eido/) formally defining *required inputs* for the pipeline
- `output_schema` (RECOMMENDED) - A schema describing the *outputs* of the pipeline, for pipestat-compatible pipelines.
- `compute` (RECOMMENDED) - Settings for computing resources
- `var_templates` (OPTIONAL) - A mapping of [Jinja2](https://jinja.palletsprojects.com/) templates and corresponding names, typically used to parameterize plugins
- `pre_submit` (OPTIONAL) - A mapping that defines the pre-submission tasks to be executed.
- `inject_env_vars` (OPTIONAL) - Environment variables to inject into submission scripts.
- `pipestat_config_required` (OPTIONAL) - Set to `false` to disable pipestat config handoff validation.

## Example pipeline interface

```yaml  title="pipeline_interface.yaml"
pipeline_name: RRBS
var_templates:
  pipeline: "{looper.piface_dir}/pipeline1.py"
  sample_info: "{looper.piface_dir}/{sample.name}/info.txt"
input_schema: path/to/rrbs_schema.yaml
sample_interface:
  command_template: >
    {pipeline.var_templates.pipeline} --input {sample.data_path} --info {pipeline.sample_info.path}
```


## Details of pipeline interface components

### pipeline_name

The `pipeline_name` is arbitrary. It should be unique for each pipeline. 
Looper uses it for a few things:

1. to construct the `job_name` variable (accessible via `{ looper.job_name }`). See [looper variable namespaces in advanced computing](../advanced-guide/advanced-computing.md) for more details.

2. to check for flags. For pipelines that produce flags, looper will be aware of them and not re-submit running jobs.

3. to communicate with the user. In log files, or on the screen, this name will be the string used to identify the pipeline to the user.

### sample_interface and project_interface

Looper can run 2 kinds of pipeline: *sample pipelines* run once per sample; *project pipelines* run once per project.
The pipeline interface should define either a `sample_interface`, a `project_interface`, or both.
You must nest the `command_template` under a `sample_interface` or `project_interface` key to let looper know at which level to run the pipeline.

When a user invokes `looper run`, looper reads data under `sample_interface` and will create one job template per sample.
In contrast, when a user invokes `looper runp`, looper reads data under `project_interface` and  creates one job per project (one job total). 

The only other difference is that the sample-level command template has access to the `{sample.<attribute>}` namespace, whereas the project-level command template has access to the `{samples}` array.



### command_template

The command template is the most critical part of the pipeline interface. It is a [Jinja2](https://jinja.palletsprojects.com/) template for the command to run for each sample. Within the `command_template`, you have access to variables from several sources. These variables are divided into namespaces depending on the variable source. You can access the values of these variables in the command template using the single-brace jinja2 template language syntax: `{namespace.variable}`. For example, looper automatically creates a variable called `job_name`, which you may want to pass as an argument to your pipeline. You can access this variable with `{looper.job_name}`. The available namespaces are described in detail in the [advanced computing guide](../advanced-guide/advanced-computing.md).

Because it's based on Jinja2, command templates are extremely flexible. For example, optional arguments can be accommodated using Jinja2 syntax, like this:

```yaml title="pipeline_interface.yaml"
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

The arguments wrapped in these Jinja2 conditionals will only be added if the specified attribute exists for the sample.


### input_schema

The input schema formally specifies the *input processed by this pipeline*. The input schema serves 2 related purposes:

1. **Validation**. Looper uses the input schema to ensure that the project fulfills all pipeline requirements before submitting any jobs. Looper uses the PEP validation tool, [eido](/eido/), to validate input data by ensuring that input samples have the attributes and input files required by the pipeline. Looper will only submit a sample pipeline if the sample validates against the pipeline's input schema.

2. **Description**. The input schema is also useful to describe the inputs, including both required and optional inputs, thereby providing a standard way to describe a pipeline's inputs. In the schema, the pipeline author can describe exactly what the inputs mean, making it easier for users to learn how to structure a project for the pipeline.

Details for how to write a schema in [writing a schema](https://pep.databio.org/eido/writing-a-schema/). The input schema format is an extended [PEP JSON-schema validation framework](https://pep.databio.org/spec/howto-validate/), which adds several capabilities, including

- `required` (optional): A list of sample attributes (columns in the sample table) that **must be defined**
- `tangible` (optional): A list of sample attributes that point to **input files that must exist**.
- `sizing` (optional): A list of sample attributes that point to input files that are not necessarily required, but if they exist, should be counted in the total size calculation for requesting resources.

If no `input_schema` is included in the pipeline interface, looper will not be able to validate the samples and will simply submit each job without validation.

Here is an example input schema:

```yaml title="Example input_schema.yaml"
description: A PEP for ATAC-seq samples for the PEPATAC pipeline.
imports:
  - http://schema.databio.org/pep/2.0.0.yaml
properties:
  samples:
    type: array
    items:
      type: object
      properties:
        sample_name: 
          type: string
          description: "Name of the sample"
        organism: 
          type: string
          description: "Organism"
        protocol: 
          type: string
          description: "Must be an ATAC-seq or DNAse-seq sample"
        genome:
          type: string
          description: "Refgenie genome registry identifier"
        read_type:
          type: string
          description: "Is this single or paired-end data?"
          enum: ["SINGLE", "PAIRED"]
        read1:
          anyOf:
            - type: string
              description: "Fastq file for read 1"
            - type: array
              items:
                type: string
        read2:
          anyOf:
            - type: string
              description: "Fastq file for read 2 (for paired-end experiments)"
            - type: array
              items:
                type: string
      tangible:
        - read1
      sizing:
        - read1
        - read2
      required:
        - sample_name
        - protocol
        - read1
        - genome
required:
  - samples
```


### output_schema

The output schema formally specifies the *output produced by this pipeline*. It is used by downstream tools to that need to be aware of the products of the pipeline for further visualization or analysis. Beginning with Looper 1.6.0 and Pipestat 0.6.0, the output schema is a JSON-schema: [pipestat schema specification](https://pep.databio.org/pipestat/pipestat-specification/).

Here is an example output schema:

```yaml title="Example output_schema.yaml"
title: An example output schema
description: A pipeline that uses pipestat to report sample and project level results.
type: object
properties:
  pipeline_name: "default_pipeline_name"
  samples:
    type: array
    items:
      type: object
      properties:
        number_of_things:
          type: integer
          description: "Number of things"
        percentage_of_things:
          type: number
          description: "Percentage of things"
        name_of_something:
          type: string
          description: "Name of something"
        switch_value:
          type: boolean
          description: "Is the switch on or off"
        md5sum:
          type: string
          description: "MD5SUM of an object"
          highlight: true
        collection_of_images:
          description: "This store collection of values or objects"
          type: array
          items:
            properties:
                prop1:
                  description: "This is an example file"
                  $ref: "#/$defs/file"
        output_file_in_object:
          type: object
          properties:
            prop1:
              description: "This is an example file"
              $ref: "#/$defs/file"
            prop2:
              description: "This is an example image"
              $ref: "#/$defs/image"
          description: "Object output"
        output_file_in_object_nested:
          type: object
          description: First Level
          properties:
            prop1:
              type: object
              description: Second Level
              properties:
                prop2:
                  type: integer
                  description: Third Level
        output_file:
          $ref: "#/$defs/file"
          description: "This a path to the output file"
        output_image:
          $ref: "#/$defs/image"
          description: "This a path to the output image"
$defs:
  image:
    type: object
    object_type: image
    properties:
      path:
        type: string
      thumbnail_path:
        type: string
      title:
        type: string
    required:
      - path
      - thumbnail_path
      - title
  file:
    type: object
    object_type: file
    properties:
      path:
        type: string
      title:
        type: string
    required:
      - path
      - title
```
Looper uses the output schema in its `report` function, which produces a browsable HTML report summarizing the pipeline results. The output schema provides the relative locations to sample-level and project-level outputs produced by the pipeline, which looper can then integrate into the output results. If the output schema is not included, the `looper report` will be unable to locate and integrate the files produced by the pipeline and will therefore be limited to simple statistics.

### compute

The compute section of the pipeline interface provides a way to set compute settings at the pipeline level. These variables can then be accessed in the command template. They can also be overridden by values in the PEP config, or on the command line. 

There is one reserved attribute under `compute` with specialized behavior -- `size_dependent_variables` which we'll now describe in detail.

#### size_dependent_variables

The `size_dependent_variables`  section lets you specify variables with values that are modulated based on the total input file size for the run. This is typically used to add variables for memory, CPU, and clock time to request, if they depend on the input file size. Specify variables by providing a relative path to a `.tsv` file that defines the variables as columns, with input sizes as rows.

The pipeline interface simply points to a `tsv` file:

```yaml
pipeline_type: sample
var_templates:
  pipeline: {looper.piface_dir}/pepatac.py
command_template: >
  {pipeline.var_templates.pipeline} ...
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

This example will add 3 variables: `cores`, `mem`, and `time`, which can be accessed via `{compute.cores}`, `{compute.mem}`, and `{compute.time}`. Each row defines a "packages" of variable values. Think of it like a group of steps of increasing size. For a given job, looper calculates the total size of the input files (which are defined in the `input_schema`). Using this value, looper then selects the best-fit row by iterating over the rows until the calculated input file size does not exceed the `max_file_size` value in the row. This selects the largest resource package whose `max_file_size` attribute does not exceed the size of the input file. Max file sizes are specified in GB, so `5` means 5 GB.

This final line in the resources `tsv` must include `NaN` in the `max_file_size` column, which serves as a catch-all for files larger than the largest specified file size. Add as many resource sets as you want.

#### var_templates

This section can consist of variable templates that are rendered and can be reused.
The namespaces available to the templates are listed in [advanced computing](../advanced-guide/advanced-computing.md) section.

The use of `var_templates` is for parameterizing pre-submission functions with parameters that require template rendering. This is an advanced use case.

Beginning with Looper 1.9.0, var_templates can also be nested:

```yaml
var_templates:
  refgenie_plugin:
    config_path: "..."
  custom_template_plugin:
     config_path: "..."
```

#### pre_submit

This section can consist of two subsections: `python_functions` and/or `command_templates`, which specify the pre-submission tasks to be run before the main pipeline command is submitted. Please refer to the [pre-submission hooks system](pre-submission-hooks.md) section for a detailed explanation of this feature and syntax.

### inject_env_vars

The `inject_env_vars` section allows you to inject environment variables into submission scripts. This is useful for passing configuration to pipelines without modifying the command template. Keys are environment variable names, values are Jinja2 templates that will be rendered with the available namespaces.

```yaml
pipeline_name: my_pipeline
output_schema: output_schema.yaml
inject_env_vars:
  PIPESTAT_CONFIG: "{pipestat.config_file}"
  MY_CUSTOM_VAR: "{looper.output_dir}/config.yaml"
sample_interface:
  command_template: >
    python pipeline.py
```

These variables are exported at the top of each submission script before the pipeline command runs. This works for both direct execution and cluster submission.

This is particularly useful for pipestat-compatible pipelines, where you can pass the pipestat config via the `PIPESTAT_CONFIG` environment variable instead of a CLI argument.

### pipestat_config_required

When a pipeline interface declares `output_schema` (indicating pipestat compatibility), looper validates that the pipestat configuration is actually passed to the pipeline. This validation ensures the pipeline will receive the merged config that looper creates.

Looper accepts two handoff mechanisms:

1. **CLI argument**: Use `{pipestat.config_file}` (or any `{pipestat.*}` variable) in your `command_template`
2. **Environment variable**: Set `PIPESTAT_CONFIG` in the `inject_env_vars` section

If neither mechanism is detected, looper raises an error with guidance on how to fix it.

To disable this validation (if your pipeline handles pipestat configuration differently), set:

```yaml
pipestat_config_required: false
```

## Validating a pipeline interface

A pipeline interface can be validated using JSON Schema against [schema.databio.org/pipelines/pipeline_interface.yaml](http://schema.databio.org/pipelines/pipeline_interface.yaml). Looper automatically validates pipeline interfaces at submission initialization stage.
