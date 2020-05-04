---
title: Pipeline interface specification
---

<h1>Pipeline interface specification</h1>

Table of contents:

[TOC]

## Introduction

In order to run an arbitrary pipeline, we require a formal specification for how the pipeline is to be used. We define this using a *pipeline interface* file. It maps attributes of a PEP project or sample to CLI arguments. Thus, it defines the interface between the project metadata (the PEP) and the pipeline itself.

If you're using *existing* `looper`-compatible pipelines, you don't need to create a new interface; just [point your project at the one that comes with the pipeline](linking-a-pipeline.md). When creating *new* `looper`-compatible pipelines, you'll need to create a new pipeline interface file.



## Definitions of terms and components of a pipeline interface

A pipeline interface consists of up to 3 keys:

- `pipeline_name` - REQUIRED. A string identifying the pipeline.
- `sample_pipeline` - describes arguments and resources for a pipeline that runs once per sample
- `project_pipeline` - describes arguments and resources for a pipeline that runs once on the entire project

The pipeline interface should define either a single `sample_pipeline`, a single `project_pipeline`, or one of each. Let's start with a simple example:

```yaml
pipeline_name: RRBS
sample_pipeline:
    path: path/to/rrbs.py
    input_schema: path/to/rrbs_schema.yaml
    command_template: <
      {pipeline.path} "--input" {sample.data_path}
```

Pretty simple. The `pipeline_name` is arbitrary. It's used for messaging and identification. Ideally, it's unique to each pipeline. In this example, we define a single sample-level pipeline. Each `sample_pipeline` or `project_pipeline` section can have any of these components:

### path (REQUIRED)

Absolute or relative path to the script or command for this pipeline. Relative paths are considered **relative to your pipeline_interface file**. We strongly recommend using relative paths where possible to keep your pipeline interface file portable. You may also use shell environment variables (like `${HOME}`) in the `path`.

### input_schema (RECOMMENDED)

The input schema formally specifies the input for this pipeline. It is used for input data validation to ensure that input samples have the attributes and input files required by the pipeline. It can also document optional inputs and describe what they are. The input schema format is based on the extended [PEP JSON-schema validation framework](http://pep.databio.org/en/latest/howto_schema/), but adds some additional looper-specific capabilities. The available extended sections are:

- `required` (optional): A list of sample attributes (columns in the sample table) that **must be defined**
- `required_input_attrs` (optional): A list of sample attributes that point to **input files that must exist**.
- `input_attrs` (optional): A list of sample attributes that point to input files that are not necessarily required, but if they exist, should be counted in the total size calculation for requesting resources.
- `ngs_input_files` (optional): For pipelines using sequencing data, provide a list of sample attributes (annotation sheet column names) that will point to input files to be used for automatic detection of `read_length` and `read_type` sample attributes.

Here's an example:

```
description: A PEP for ATAC-seq samples for the PEPATAC pipeline.
imports: http://schema.databio.org/pep/2.0.0.yaml
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
          enum: ["ATAC", "ATAC-SEQ", "ATAC-seq", "DNase", "DNase-seq"]
        genome:
          type: string
          description: "Refgenie genome registry identifier"
        read_type:
          type: string
          description: "Is this single or paired-end data?"
          enum: ["SINGLE", "PAIRED"]
        read1:
          type: string
          description: "Fastq file for read 1"
        read2:
          type: string
          description: "Fastq file for read 2 (for paired-end experiments)"
      required:
        - sample_name
        - read1
        - genome
      required_input_attrs:
        - read1
      input_attrs:
        - read1
        - read2
required:
  - samples
```

### output_schema (RECOMMENDED)

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
        exact_bw:
          path: "aligned_{genome}_exact/{sample_name}_exact.bw"
          type: string
          description: "An exact bigwig file"
        aligned_bam: 
          path: "aligned_{genome}/{sample_name}_sort.bam"
          type: string
          description: "A sorted, aligned BAM file"
        peaks_bed: 
          path: "peak_calling_{genome}/{sample_name}_peaks.bed"
          type: string
          description: "Peaks in BED format"
  alignment_percent_file:
    title: "Alignment percent file"
    description: "Plots percent of total alignment to all pre-alignments and primary genome."
    thumbnail_path: "summary/{name}_alignmentPercent.png"
    path: "summary/{name}_alignmentPercent.pdf"
    type: image
  alignment_raw_file:
    title: "Alignment raw file"
    description: "Plots raw alignment rates to all pre-alignments and primary genome."
    thumbnail_path: "summary/{name}_alignmentRaw.png"
    path: "summary/{name}_alignmentRaw.pdf"
    type: image
  tss_file:
    title: "TSS enrichment file"
    description: "Plots TSS scores for each sample."
    thumbnail_path: "summary/{name}_TSSEnrichment.png"
    path: "summary/{name}_TSSEnrichment.pdf"
    type: image
  library_complexity_file:
    title: "Library complexity file"
    description: "Plots each sample's library complexity on a single plot."
    thumbnail_path: "summary/{name}_libComplexity.png"
    path: "summary/{name}_libComplexity.pdf"
    type: image
  consensus_peaks_file:
    title: "Consensus peaks file"
    description: "A set of consensus peaks across samples."
    thumbnail_path: "summary/{name}_consensusPeaks.png"
    path: "summary/{name}_consensusPeaks.narrowPeak"
    type: image
  counts_table:
    title: "Project peak coverage file"
    description: "Project peak coverages: chr_start_end X sample"
    path: "summary/{name}_peaks_coverage.tsv"
    type: link
```


### `command_template` (REQUIRED)

 a `jinja2` template that will create the actual command that should be run for each sample. 
In other words, it's a column name of your sample annotation sheet. Looper will find the value of this attribute for each sample and pass that to the pipeline as the value for that argument. 
For flag-like arguments that lack a value, you may specify `null` as the value (e.g. `"--quiet-mode": null`). 
These arguments are considered *required*, and `looper` will not submit a pipeline if a sample lacks an attribute that is specified as a value for an argument.

#### Command template variable namespaces

Within the `command_template`, you have access to variables from several sources. These variables are divided into namespaces depending on the variable source. You can access the values of these variables in the command template using the single-brace jinja2 template language syntax: `{namespace.variable}`. For example, looper automatically creates a variable called `job_name`, which you may want to pass as an argument to your pipeline. You can access this variable with `{looper.job_name}`. The available namespaces are listed below:

##### 1 `project`
All PEP config attributes.

##### 2 `sample`
All PEP post-processing sample attributes.

##### 3 `pipeline`
Everything under `pipeline` in the pipeline interface (for this pipeline).

##### 4 `looper` 

Automatic attributes created by looper:

- `job_name` -- automatic job name string made by concatenating the pipeline identifier and unique sample name.
- `output_folder` -- parent output folder provided in `project.looper.output_folder`
- `sample_output_folder` -- A sample-specific output folder derived from the ({output_folder}/{sample_name})
- `total_input_size`
- `pipeline_config`  (renamed from `config` to disambiguate with new `pep_config` ?)
- `pep_config` -- path to the PEP configuration file used for this looper run.
- `log_file`
- `command`

##### 5 `compute`

Variables populated from the `compute` priority list. The `compute` namespace has a unique behavior: it cascades settings from various levels, overriding default values with more specific ones. The source list in priority order is:

1. Looper CLI (`--compute` on-the-fly settings)
2. PEP config, `project.looper.compute` section
3. Pipeline interface, `pipeline.compute` section
4. Activated divvy compute package (`--settings` or `--compute-package`)

So, the compute namespace is first populated with any variables from the selected divvy compute package. It then updates this with settings given in the `compute` section of the pipeline interface. It then updates from the PEP `project.looper.compute`, and then finally anything passed to `--compute` on the looper CLI. This provides a way to module looper behavior at the level of a computing environment, a pipeline, a project, or a run -- in that order.

##### `samples`

For project-level pipelines, there is no `sample` namespace; instead, there is a `samples` (plural) namespace, which is a list of all the samples in the project. This can be useful if you need to iterate through all the samples.

#### Optional arguments

Any optional arguments can be accommodated using jinja2 syntax, like this. These will only be added to the command *if the specified attribute exists for the sample*. 

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

### compute (RECOMMENDED)

The compute section of the pipeline interface provides a way to set compute settings at the pipeline level. These variables can then be accessed in the command template. They can also be overridden by values in the PEP config, or on the command line. See the `compute` namespace under `command_template` above for details. One special attribute under `compute` is `size_dependent_variables`:

#### size_dependent_variables

Under `size_dependent_variables` you can specify a relative path to a tsv file defining variables that are modulated based on the total input file size for the run. This can be used to add any variables, but is typically used to add memory, CPU, and clock time to request, modulated by input file size.

Example:

```
sample_pipeline:
  path: pipelines/pepatac.py
  command_template: >
    {pipeline.path} ...
  compute:
    size_dependent_variables: resources-sample.tsv
```

The `resources-sample.tsv` file consists of a file with at least 1 column called `max_file_size`. Any other columns will then be added.

```
max_file_size cores mem time
0.001 1 8000  00-04:00:00
0.05  2 12000 00-08:00:00
0.5 4 16000 00-12:00:00
1 8 16000 00-24:00:00
10  16  32000 02-00:00:00
NaN 32  32000 04-00:00:00
```
Each row defines a "packages" of variable values. Think of it like a group of steps of increasing size. 
The row will be assigned to any samples whose input files range from 0 to the value in the `max_file_size` of that row. Then, each successive step is larger. 
Looper determines the size of your input file, and then iterates over the resource packages until it can't go any further. This file must include a final line with `NaN` in the `max_file_size` column, which serves as a catch-all for files larger than the largest specified file size. Add as many resource sets as you want. Looper will determine which resource package to use based on the `file_size` of the input file.  It will select the lowest resource package whose `file_size` attribute does not exceed the size of the input file. 

Because the partition or queue name is relative to your environment, we don't usually specify this in the `resources` section, but rather, in the `pepenv` config. 
So, `max_file_size: "5"` means 5 GB. This means that resource package only will be used if the input files total size is greater than 5 GB.

**More extensive example:**

```yaml
pipelines:
  rrbs:
    name: RRBS
    looper_args: True
    path: path/to/rrbs.py
    arguments:
      "--sample-name": sample_name
      "--genome": genome
      "--input": data_path
      "--single-or-paired": read_type

  rnaBitSeq.py:
    looper_args: True
    arguments:
      "--sample-name": sample_name
      "--genome": transcriptome
      "--input": data_path
      "--single-or-paired": read_type

  atacseq.py:
    arguments:
      "--sample-yaml": yaml_file
      "-I": sample_name
      "-G": genome
    looper_args: True
    outputs:
      smoothed_bw: "aligned_{sample.genome}/{sample.name}_smoothed.bw"
      pre_smoothed_bw: "aligned_{project.prealignments}/{sample.name}_smoothed.bw"
```


