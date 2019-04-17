# Configure a PEP to work with looper

Once you have a basic [PEP config](https://pepkit.github.io/docs/project_config/) file, you can add some special sections to control `looper` features. In addition to the main sections, `looper` adds these sections:

### Project config section: `pipeline_config`

Occasionally, a particular project needs to run a particular flavor of a pipeline. 
Rather than creating an entirely new pipeline, you can parameterize the differences with a **pipeline config** file, 
and then specify that file in the **project config** file.

**Example**:

```yaml
pipeline_config:
  # pipeline configuration files used in project.
  # Key string must match the _name of the pipeline script_ (including extension)
  # Relative paths are relative to this project config file.
  # Default (null) means use the generic config for the pipeline.
  rrbs.py: null
  # Or you can point to a specific config to be used in this project:
  wgbs.py: wgbs_flavor1.yaml
```

This will instruct `looper` to pass `-C wgbs_flavor1.yaml` to any invocations of wgbs.py (for this project only). 
Your pipelines will need to understand the config file (which will happen automatically if you use pypiper).


### Project config section: `pipeline_args`
Sometimes a project requires tweaking a pipeline, but does not justify a completely separate **pipeline config** file. 
For simpler cases, you can use the `pipeline_args` section, which lets you specify command-line parameters via the project config. 
This lets you fine-tune your pipeline, so it can run slightly differently for different projects.

**Example**:

```yaml
pipeline_args:
  rrbs.py:  # pipeline identifier: must match the name of the pipeline script
    # here, include all project-specific args for this pipeline
    "--flavor": simple
    "--flag": null
```

For flag-like options (options without parameters), you should set the value to the yaml keyword `null`. 
Looper will pass the key to the pipeline without a value. 
The above specification will now (for *this project only*) pass `--flavor simple` and `--flag` whenever `rrbs.py` is run.
This is a way to control (and record!) project-level pipeline arg tuning. The only keyword here is `pipeline_args`; 
all other variables in this section are specific to particular pipelines, command-line arguments, and argument values.

### Project config section: `compute`
You can specify project-specific compute settings in a `compute` section, 
but it's often more convenient and consistent to specify this globally with a `pepenv` environment configuration. 
Instructions for doing so are at the [`pepenv` repository](https://github.com/pepkit/pepenv). 
If you do need project-specific control over compute settings (like submitting a certain project to a certain resource account), 
you can do this by specifying variables in a project config `compute` section, which will override global `pepenv` values for that project only.

```yaml
compute:
  partition: project_queue_name
```

### Project config section: `track_configurations`
***Warning***: The `track_configurations` section is for making UCSC trackhubs. 
This is a work in progress that is functional, but ill-documented, so for now it should be used with caution.

### Project config complete example
```yaml
metadata:
  # Relative paths are considered relative to this project config file.
  # Typically, this project config file is stored with the project metadata
  # sample_annotation: one-row-per-sample metadata
  sample_annotation: table_experiments.csv
  # sample_subannotation: input for samples with more than one input file
  sample_subannotation: table_merge.csv
  # compare_table: comparison pairs or groups, like normalization samples
  compare_table: table_compare.csv
  # output_dir: the parent, shared space for this project where results go
  output_dir: /fhgfs/groups/lab_bock/shared/projects/example
  # results and submission subdirs are subdirectories under parent output_dir
  # results: where output sample folders will go
  # submission: where cluster submit scripts and log files will go
  results_subdir: results_pipeline
  submission_subdir: submission
  # pipeline_interfaces: the pipeline_interface.yaml file or files for Looper pipelines
  # scripts (and accompanying pipeline config files) for submission.
  pipeline_interfaces: /path/to/shared/projects/example/pipeline_interface.yaml


data_sources:
  # Ideally, specify the ABSOLUTE PATH of input files using variable path expressions.
  # Alternatively, a relative path will be with respect to the project config file's folder.
  # Entries correspond to values in the data_source column in sample_annotation table.
  # {variable} can be used to replace environment variables or other sample_annotation columns.
  # If you use {variable} codes, you should quote the field so python can parse it.
  bsf_samples: "$RAWDATA/{flowcell}/{flowcell}_{lane}_samples/{flowcell}_{lane}#{BSF_name}.bam"
  encode_rrbs: "/path/to/shared/data/encode_rrbs_data_hg19/fastq/{sample_name}.fastq.gz"


implied_columns:
# supported genomes/transcriptomes and organism -> reference mapping
organism:
  human:
    genome: hg38
    transcriptome: hg38_cdna
  mouse:
    genome: mm10
    transcriptome: mm10_cdna

pipeline_config:
  # pipeline configuration files used in project.
  # Default (null) means use the generic config for the pipeline.
  rrbs: null
  # Or you can point to a specific config to be used in this project:
  # rrbs: rrbs_config.yaml
  # wgbs: wgbs_config.yaml
  # cgps: cpgs_config.yaml
```
