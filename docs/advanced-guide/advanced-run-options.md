# Advanced run options

## Introduction

The basic tutorials showed you how to use `looper run` with the defaults, and introduced a few of the arguments, like `--dry-run` and `--limit`.
The computing tutorial covered some arguments related to computing resources, like `--package` and `--compute`.
There are many other arguments to `looper run` that can help you control how looper creates and submits jobs.
Let's introduce some of the more advanced capabilities of `looper run`.

!!! success "Learning objectives"
    - What are some of the more advanced options for `looper run`?
    - How do I submit a job for the *entire project*, instead of a separate job for each sample?
    - How can I submit different pipelines for different samples?
    - How can I adjust pipeline arguments on-the-fly?
    - What if I want to submit multiple samples in a single job?
    - Can I exclude certain samples from a run?


## Grouping many jobs into one

By default, `looper` will translate each row in your `sample_table` into a single job. But perhaps you are running a project with tens of thousands of rows, and each job only takes mere minutes to run; in this case, you'd rather just submit a single job to process many samples. `Looper` makes this easy with the `--lump` and `--lump-n` command line arguments.

### Lumping jobs by job count: `--lump-n`

It's quite simple: if you want to run 100 samples in a single job submission script, just tell looper `--lump-n 100`.

### Lumping jobs by input file size: `--lump`

But what if your samples are quite different in terms of input file size? For example, your project may include many small samples, which you'd like to lump together with 10 jobs to 1, but you also have a few control samples that are very large and should have their own dedicated job. If you just use `--lump-n` with 10 samples per job, you could end up lumping your control samples together, which would be terrible. To alleviate this problem, `looper` provides the `--lump` argument, which uses input file size to group samples together. By default, you specify an argument in number of gigabytes. Looper will go through your samples and accumulate them until the total input file size reaches your limit, at which point it finalizes and submits the job. This will keep larger files in independent runs and smaller files grouped together.

### Lumping jobs by job count: `--lump-j`

If you want to split your samples across a specific number of jobs, use `--lump-j`. For example, `--lump-j 10` will distribute all your samples evenly across 10 jobs.


## Running project-level pipelines

### What are project-level pipelines?

The tutorials assume you're running a pipeline where you're trying to run one job per sample, *i.e.* the samples are independent, and you want to do the same thing to each of them. This is the most common use case for looper. 

But sometimes, you're interested in running a job on an entire project. This could be a pipeline that integrates data across *all* the samples, or one that will summarize the results of your independent sample pipeline runs. In this case, you really only need to submit a single job. Looper's main benefit is handling the boilerplate needed to construct the submission scripts and submit a separate job for each sample. But looper *also* provides some help for the task of submitting a single job for the whole project.

So, there are really two *types* of pipelines looper can submit. The typical ones, which need one job per sample, we call *sample-level* pipelines. For many use cases, that's all you need to worry about. The broader level, which need one job for the whole project, we call *project-level* pipelines. 

### Split-apply-combine

One of the most common uses of a project-level pipeline is to summarize or aggregate the results of the sample-level pipeline. This approach essentially employs looper as an implementation of the [MapReduce](https://en.wikipedia.org/wiki/MapReduce) programming model, which applies a *split-apply-combine* strategy. We *split* the project into samples and *apply* the first tier of processing (the *sample* pipeline). We then *combine* the results in the second tier of processing (the *project* pipeline). Looper doesn't require you to use this two-stage system, but it does make it easy to do so. Many pipelines operate only at the sample level and leave the downstream cross-sample analysis to the user.

### How to run a project-level pipeline

The usual `looper run` command runs sample-level pipelines. This will create a separate job for each sample. Pipeline interfaces defining a sample pipeline do so under the  `sample_interface` attribute.

Project pipelines are run with `looper runp` (where the *p* stands for *project*). The interface specifies that it is a project pipeline by using the `project_interface` attribute. Running a project pipeline operates in almost exactly the same way as the sample pipeline, with 2 key differences:

1. First, instead of a separate command for every sample, `looper runp` creates a single command  for the project (per pipeline).
2. Second, the command template cannot access the `sample` namespace representing a particular sample, since it's not running on a particular sample; instead, it will have access to a `samples` (plural) namespace, which contains all the attributes from all the samples.

In a typical workflow, a user will first run the samples individually using `looper run`, and then, if the pipeline provides one, will run the project component using `looper runp` to summarize to aggregate the results into a project-level output.

Example of a pipeline interface containing a sample-level interface AND a project-level interface:
```yaml
pipeline_name: example_pipeline
output_schema: pipestat_output_schema.yaml
sample_interface:
  command_template: >
    count_lines.sh {sample.file} {sample.sample_name}
project_interface:
  command_template: >
    count_lines_project.sh "data/*.txt"
```


## Running multiple pipelines

To run more than one pipeline, specify multiple pipeline interfaces in the looper config file:

```yaml
pep_config: pephub::databio/looper:default
output_dir: "$HOME/hello_looper-master/output"
pipeline_interfaces:
  - "$HOME/hello_looper-master/pipeline/pipeline_interface"
  - "$HOME/hello_looper-master/project/pipeline"
```

You can also link to the pipeline interface with a sample attribute. If you want the same pipeline to run on all samples, it's as easy as using an `append` modifier like this:

```yaml
sample_modifiers:
  append:
    pipeline_interfaces: "test.yaml"
```

But if you want to submit different samples to different pipelines, depending on a sample attribute, like `protocol`, you can use an implied attribute:

```yaml
sample_modifiers:
  imply:
    - if:
        protocol: [PRO-seq, pro-seq, GRO-seq, gro-seq] # OR
      then:
        pipeline_interfaces: ["peppro.yaml"]
```

This approach uses only functionality of PEPs to handle the connection to pipelines as sample attributes, which provides full control and power using the familiar sample modifiers. It completely eliminates the need for re-inventing this complexity within looper, which eliminated the protocol mapping section to simplify the looper pipeline interface files. You can read more about the rationale of this change in [issue 244](https://github.com/pepkit/looper/issues/244#issuecomment-611154594).

## Modulating pipeline by sample

If you have a project that contains samples of different types, you may want to submit a different pipeline for each sample.
Usually, we think of looper as running the same pipeline for each sample.
The best way to solve this problem is to split your sample table up into different tables, and then run a different pipeline on each.
But if you really want to, you can actually modulate the pipeline by sample attributes.
You can use an `imply` modifier in your PEP to select which pipelines you want to run on which samples, like this:


```yaml
sample_modifiers:
  imply:
    - if:
        protocol: "RRBS"
      then:
        pipeline_interfaces: "/path/to/pipeline_interface.yaml"
    - if:
        protocol: "ATAC"
      then:
        pipeline_interfaces: "/path/to/pipeline_interface2.yaml"
```

A more complicated example taken from [PEPATAC](https://pepatac.databio.org/en/latest/) of a `project_config.yaml` file:

```yaml
pep_version: 2.0.0
sample_table: tutorial.csv

sample_modifiers:
  derive:
    attributes: [read1, read2]
    sources:
      # Obtain tutorial data from http://big.databio.org/pepatac/ then set
      # path to your local saved files
      R1: "${TUTORIAL}/tools/pepatac/examples/data/{sample_name}_r1.fastq.gz"
      R2: "${TUTORIAL}/tools/pepatac/examples/data/{sample_name}_r2.fastq.gz"
  imply:
    - if: 
        organism: ["human", "Homo sapiens", "Human", "Homo_sapiens"]
      then: 
        genome: hg38
        prealignment_names: ["rCRSd"]
        deduplicator: samblaster # Default. [options: picard]
        trimmer: skewer          # Default. [options: pyadapt, trimmomatic]
        peak_type: fixed         # Default. [options: variable]
        extend: "250"            # Default. For fixed-width peaks, extend this distance up- and down-stream.
        frip_ref_peaks: None     # Default. Use an external reference set of peaks instead of the peaks called from this run
```


## Passing extra command-line arguments

Occasionally, a particular project needs to run a particular flavor of a pipeline. How can you  adjust pipeline arguments for just this project? You can use looper *command extras* to solve this problem. Command extras let you pass any string on to the pipeline, which will be appended to the command.

There are 2 ways to use command extras: for sample pipelines, or for project pipelines:

### 1. Sample pipeline command extras


#### Adding sample command extras via sample attributes

Looper uses a reserved sample attribute called `command_extras`, which you can set using general PEP sample modifiers however you wish. For example, if your extras are the same for all samples you could use an `append` modifier:


```yaml
sample_modifiers:
  append:
    command_extra: "--flavor-flag"
```

This will add `--flavor-flag` the end of the command looper constructs. If you need to modulate the extras depending on another attribute value, you could use an imply modifier:

```yaml
sample_modifiers:
  imply:
    - if:
        protocol: "rrbs"
      then:
        command_extra: "-C flavor.yaml --epilog"
```

#### Adding sample command extras via the command line

You can also pass extra arguments using `--command-extra` like this:

```
looper run project_config.yaml --command-extra="--flavor-flag"
```

### 2. Project pipeline command extras

For *project pipelines*, you can specify command extras in the `looper` section of the PEP config:

```yaml
looper:
  output_dir: "/path/to/output_dir"
  cli:
    runp:
      command-extra: "--flavor"
```

or as an argument to the `looper runp` command:


```bash
looper runp project_config.yaml --command-extra="--flavor-flag"
```


### Overriding PEP-based command extras

By default, the CLI extras are *appended to the command_extra specified in your PEP*. If you instead want to *override* the command extras listed in the PEP, you can instead use `--command-extra-override`.

So, for example, make your looper call like this:

```bash
looper run --command-extra-override="-R"
```

That will remove any defined command extras and append `-R` to the end of any commands created by looper.

## Add CLI arguments to looper config

You can provide a `cli` keyword to specify any command line (CLI) options from within the **looper config file**. The subsections within this section direct the arguments to the respective `looper` subcommands. For example, to specify a sample submission limit for a `looper run` command, use:

```yaml
cli:
    run:
      limit: 2
```

Keys in the `cli.<subcommand>` section *must* match the long argument parser option strings, so `command-extra`, `limit`, `dry-run` and so on. For more CLI options refer to the subcommands [usage](../usage.md).




## Selecting or excluding samples

Looper provides several ways to select (filter) samples, so you only submit certain ones.

### Sample selection by inclusion

To submit only certain samples, specify the sample attribute with `--sel-attr` and the values the attribute can take `--sel-incl`. 
For example, to choose only samples where the `species` attribute is `human`, `mouse`, or `fly`:

```console
looper run \
  --sel-attr species \
  --sel-incl human mouse fly
```

Similarly, to submit only one sample, with `sample_name` as `sample`, you could use:

```console
looper run \
  --sel-attr sample_name \
  --sel-incl sample1
```

### Sample selection by exclusion

If it's more convenient to *exclude* samples by filter, you can use the analogous arguments `--sel-attr` with `--sel-excl`.
This will exclude any samples matching the specified values. For example, to run all samples *except* those where `species` is `rat`:

```console
looper run \
  --sel-attr species \
  --sel-excl rat
```

### Toggling sample jobs through the sample table

You can also set the `toggle` value of attributes (either in your sample table or via a sample modifier). If the value of this column is not 1, `looper` will not submit the pipeline for that sample.
This enables you to submit a subset of samples.


!!! tip "Summary"
    - You can use `--lump`, `--lump-n`, or `--lump-j` to group jobs into the same script.
    - Looper `run` has sample selection and exclusion arguments.
    - You can attach multiple pipeline interfaces to a looper project, resulting in multiple pipeline submissions.

