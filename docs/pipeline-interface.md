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

Pretty simple. The `pipeline_name` is totally arbitrary; it's just used for messaging and identification. You can set it to whatever you want. Ideally, it's unique to each pipeline.

Each of the `sample_pipeline` or `project_pipeline` sections can have any of these components:

### path (REQUIRED)

Absolute or relative path to the script for this pipeline. Relative paths are considered **relative to your pipeline_interface file**. We strongly recommend using relative paths where possible to keep your pipeline interface file portable. You may also use shell environment variables (like `${HOME}`) in the `path`.

### input_schema (RECOMMENDED)

- `required_input_files` (optional): A list of sample attributes (annotation sheets column names) that will point to input files that must exist.
- `all_input_files` (optional): A list of sample attributes (annotation sheet column names) that will point to input files that are not required, but if they exist, should be counted in the total size calculation for requesting resources.
- `ngs_input_files` (optional): For pipelines using sequencing data, provide a list of sample attributes (annotation sheet column names) that will point to input files to be used for automatic detection of `read_length` and `read_type` sample attributes.

### output_schema (RECOMMENDED)

- `outputs`: key-value pairs in which each key is a name for a kind of output file (or group of them) that a pipeline may produce, and the value is a template template for a path that will be populated by sample variables


### `command_template` (REQUIRED)

 a `jinja2` template that will create the actual command that should be run for each sample. 
In other words, it's a column name of your sample annotation sheet. Looper will find the value of this attribute for each sample and pass that to the pipeline as the value for that argument. 
For flag-like arguments that lack a value, you may specify `null` as the value (e.g. `"--quiet-mode": null`). 
These arguments are considered *required*, and `looper` will not submit a pipeline if a sample lacks an attribute that is specified as a value for an argument.


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

Here, you can use a special s

#### size_dependent_variables

Under `size_dependent_variables` you can specify a relative path to a tsv file that outlines variables that are modulated based on the total input file size for the sample. This can be used to add any variables, but is typically used to add  memory, CPU, and clock time to request, modulated by input file size.

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
    resources:
      default:
        file_size: "0"
        cores: "4"
        mem: "4000"
        time: "2-00:00:00"
      high:
        file_size: "4"
        cores: "6"
        mem: "4000"
        time: "2-00:00:00"

  rnaBitSeq.py:
    looper_args: True
    arguments:
      "--sample-name": sample_name
      "--genome": transcriptome
      "--input": data_path
      "--single-or-paired": read_type
    resources:
      default:
        file_size: "0"
        cores: "6"
        mem: "6000"
        time: "2-00:00:00"

  atacseq.py:
    arguments:
      "--sample-yaml": yaml_file
      "-I": sample_name
      "-G": genome
    looper_args: True
    resources:
      default:
        file_size: "0"
        cores: "4"
        mem: "8000"
        time: "08:00:00"
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