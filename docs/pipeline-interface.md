---
title: Pipeline interface specification
---

<h1>Pipeline interface specification</h1>

Table of contents:

[TOC]

## Introduction

In order to run an arbitrary pipeline, we require a formal specification for how the pipeline is to be used. We define this using a *pipeline interface* file. It maps attributes of a PEP project or sample to CLI arguments. Thus, it defines the interface between the project metadata (the PEP) and the pipeline itself. The pipeline interface file is created by a pipeline author.

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

The input schema formally specifies the input data for this pipeline. It is based on the extended [PEP JSON-schema validation framework](http://pep.databio.org/en/latest/howto_schema/), but adds some additional looper-specific capabilities. With this schema it is possible to tag sample attributes, as required, as pointing to required or optional input files. Here's an example:

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

The available extended sections are:

- `required` (optional): A list of sample attributes that must be defined on the sample
- `required_input_attrs` (optional): A list of sample attributes (annotation sheet column names) that will point to input files that must exist.
- `input_attrs` (optional): A list of sample attributes (annotation sheet column names) that will point to input files that are not necessarily required, but if they exist, should be counted in the total size calculation for requesting resources.
- `ngs_input_files` (optional): For pipelines using sequencing data, provide a list of sample attributes (annotation sheet column names) that will point to input files to be used for automatic detection of `read_length` and `read_type` sample attributes.

### output_schema (RECOMMENDED)

The output schema formally specifies the output produced by this pipeline. Like the input schema, it is based on the extended [PEP JSON-schema validation framework](http://pep.databio.org/en/latest/howto_schema/), but adding some looper-specific capabilities

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
          description: "Test sample property"
        exact_bw:
          path: "aligned_{genome}_exact/{sample_name}_exact.bw"
          type: string
          description: "Test sample property"
        aligned_bam: 
          path: "aligned_{genome}/{sample_name}_sort.bam"
          type: string
          description: "Test sample property"
        peaks_bed: 
          path: "peak_calling_{genome}/{sample_name}_peaks.bed"
          type: string
          description: "Test sample property"
        summits_bed: 
          path: "peak_calling_{genome}/{sample_name}_summits.bed"
          type: string
          description: "Test sample property"
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

The base schema has two *properties* sections, one that pertains to the project, and one that pertains to the samples. In each case, these sections follow the base JSON-schema format, but add a few additional capabitiles, as described below. The *properties* sections for both sample and project will recognize these attributes: 

- `title`, following the base JSON-schema spec.
- `description`, following the base JSON-schema spec.
- `path` This attribute can be used to specify a relative path to output files represing each output sample attribute. The name of the attribute is the name of a kind of output file (or group of them) that a pipeline may produce, and the value in the `path` attribute is a template for a path that will be populated by sample variables. Sample variables can be used in these template using brace notation, like `{sample_attribute}`.
- `thumbnail_path`, templates similar to the `path` attribute, but used to specify a thumbnail output version.
- `type`, can be one of: link, image, file.

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

1. activated divvy compute package
2. pipeline.compute section
3. project.looper.compute
4. looper CLI

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



## How to map different pipelines to different samples

In the earlier version of looper, the pipeline interface file specified a `protocol_mappings` section. This mapped sample `protocol` (the assay type, sometimes called "library" or "library strategy") to one or more pipeline program.  This section specifies that samples of protocol `RRBS` will be mapped to the pipeline specified by key `rrbs_pipeline`. 
 


If you're using *existing* `looper`-compatible pipelines, you don't need to create a new interface; just [point your project at the one that comes with the pipeline](linking-a-pipeline.md). When creating *new* `looper`-compatible pipelines, you'll need to create a new pipeline interface file. Regardless of what pipelines you use, you will need to tell looper how to communicate with your pipeline. 




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