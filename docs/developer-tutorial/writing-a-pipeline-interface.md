---
title: Pipeline interface specification
---

# Writing a pipeline interface

## Introduction

In the [User Tutorial](../user-tutorial/initialize.md) we walked you through creating a Looper workspace to run a pipeline on a dataset.
That tutorial assumed you already want to run an existing looper-compatible pipeline.
For pipelines that are already looper-compatible, you just point your looper configuration file at pipeline's interface file, as described in the User Tutorial.

This Developer Tutorial goes into more detail on how to *create* a looper-compatible pipeline.
If you're interested in building a looper-compatible pipeline, or taking an existing pipeline and making it work with looper, the critical point of contact is the pipeline interface.
A pipeline interface *describes how to run a pipeline*.

This tutorial will show you how to write a pipeline interface.
Once you've been through this, you can consult the formal [pipeline interface format specification](pipeline-interface-specification.md) for further details and reference.

!!! success "Learning objectives"
    - What is a looper pipeline interface?
    - How do I write a looper pipeline interface for my custom pipeline?
    - Do I have to write a pipeline interface to have looper just run some command that isn't really a pipeline?


## An example pipeline interface

Each Looper project requires one or more pipeline interfaces that points to sample and/or project pipelines.
The looper config file points to the pipeline interface, and the pipeline interface tells looper how to run the pipeline.

![pipeline interface](../img/pipeline_interface.svg)


Let's revisit the simple pipeline interface the `count_lines` pipeline example:

```yaml title="pipeline_interface.yaml"
pipeline_name: count_lines
sample_interface:
  command_template: >
    pipeline/count_lines.sh {sample.file_path}
```

There are 2 required keys.
First, the `pipeline_name` can be anything, as long as it is unique to the pipeline.
It will be used for communication and keeping track of which results belong to which pipeline.
Think of it as a unique identifier label you assign to the pipeline.

Second, the `sample_interface` tells looper (and pipestat) that this is a **sample-level pipeline.**
Under `sample_interface` is the `command_template`, which holds our command string with variables that will be populated.
In this example, looper will run `pipeline/count_lines.sh`.
Looper will pass a single argument to the script, `{sample.file_path}`, which is a variable that will be populated with the `file_path` attribute on the sample.
This `file_path` field which corresponds to a column header in the sample table.
As the pipeline author, your command template can use any attributes with `{sample.<attribute>}` syntax.
You can make the command template much more complicated and refer to any sample or project attributes, as well as a bunch of [other variables made available by looper](../advanced-guide/advanced-computing.md#divvy-config-variable-adapters-and-built-in-looper-variables).

That's all you need for a basic pipeline interface!
But there's also a lot more you can do, such as providing a schema to specify inputs or outputs, making input-size-dependent compute settings, and more.
Let's walk through some of these more advanced options.

## Initializing a generic pipeline interface

So you don't have to remember the general syntax, you can run a command that will create a generic pipeline interface, a generic `output_schema.yaml` (for pipestat-compatible pipelines) and a generic pipeline to get you started:

```shell
looper init_piface
```


<!-- 

The `output_schema` is used if you are using pipestat to report results.
If you are not using pipestat, you can remove this line. -->


## Making pipeline interface portable with `{looper.piface_dir}`

One of the problems with the above pipeline interface is that it is hard-coding a relative path to the pipeline, `pipeline/count_lines.sh`:


```yaml title="pipeline_interface.yaml" hl_lines="4"
pipeline_name: count_lines
sample_interface:
  command_template: >
    pipeline/count_lines.sh {sample.file_path}
```

Looper will literally run `pipeline/count_lines.sh`, which will only work if the working directory contains the `pipeline/` subfolder holding `count_lines.sh`.
This may work, since we typically call `looper run` from our looper workspace folder, where the `.looper.yaml` config file lives. 

For example, it would work if you invoke `looper run` from this working directory:

```
.
├── pipeline
│   └── count_lines.sh
├── pipeline_interface.yaml
└── .looper.yaml
```

But what if we want to run the jobs from a different directory? It would be better if the jobs could run correctly from any working directory.

One way we could do that is to hard-code the absolute path to the script.
Then, the resulting commands could run from anywhere on that system.

```yaml title="pipeline_interface.yaml" hl_lines="4"
pipeline_name: count_lines
sample_interface:
  command_template: >
    /absolute/path/to/pipeline/count_lines.sh {sample.file_path}
```

But then this pipeline interface this would not be portable.
It could not be shared with another user on a different system.

Another solution is that we could just put the pipeline command into our shell `PATH`, so it can be run globally, like this:


```yaml title="pipeline_interface.yaml" hl_lines="4"
pipeline_name: count_lines
sample_interface:
  command_template: >
    count_lines {sample.file_path}
```


This way, it would run correctly from any folder, and would work on any system.
But then users of our pipeline would have to adjust their `PATH` to make the pipeline globally runnable.
This is fine for an installed pipeline intended to be in the `PATH`, but it is not ideal for basic scripts or other non-global pipelines.

Luckily, looper offers a better solution. 
It is convenient to specify a path relative to the pipeline interface file, which looper can populate as needed.
For this purpose, looper provides the `{looper.piface_dir}` variable.
The pipeline interface author can make any paths portable by simply prepending `{looper.piface_dir}` to the script in a `command_template`.

Our improved pipeline interface looks like this:

```yaml title="pipeline_interface.yaml" hl_lines="4"
pipeline_name: count_lines
sample_interface:
  command_template: >
    {looper.piface_dir}/pipeline/count_lines.sh {sample.file_path}
```

Looper will automatically populate `{looper.piface_dir}` on the system with the absolute path, giving us the best of both worlds.
The pipeline script can be distributed alongside the pipeline interface, and this will automatically work from any working directory, on any system.

Therefore, we recommend pipeline authors always use `{looper.piface_dir}` to make sure their pipeline interfaces are portable.
This is also true for pre-submit command templates.


## Validating sample input attributes

Right now, looper will create and submit jobs for every row in the table.
What if we want to prevent jobs from being submitted if the row lacks all the information required by the pipeline?
This could help us fail early and save submitting jobs that won't succeed.
For example, what if we want to make sure a particular required attribute is set before we submit a job?

To demonstrate, let's make a simple modification to the pipeline.
We'll adjust it to report the area type.

```sh title="pipeline/count_lines.sh" hl_lines="3 4"
#!/bin/bash
linecount=`wc -l $1 | sed -E 's/^[[:space:]]+//' | cut -f1 -d' '`
export area_type=$2
echo "Number of ${area_type}s: $linecount"
```

Then, we'll adjust the pipeline interface to pass the `area_type` as the second argument to the pipeline.

```yaml title="pipeline_interface.yaml" hl_lines="3 4" 
# stuff before
sample_interface:
  command_template: >
    pipeline/count_lines.sh {sample.file_path} {sample.area_type}
```

Now, let's add a new sample to the sample table that lacks the `area_type`.

```csv title="metadata/sample_table.csv" hl_lines="5"
sample_name,area_type
mexico,state
switzerland,canton
canada,province
usa,
```

Right now, if you invoke `looper run`, you will create a job for all 4 samples.
But what we want to do is tell looper that the last sample is incomplete, and should give an error instead of creating and running the job.
We will do that through the `input_schema`.

### Create an input schema

The input schema formally specifies the *input processed by this pipeline*.
It serves several purposes, like sample validation, specifying which attributes should be used to determine sample size, and specifying which attributes are files.
We'll get into those details later.
First, let's make an input schema.
Paste this text into `pipeline/input_schema.yaml`

```yaml title="input_schema.yaml"
description: An input schema for count_lines pipeline pipeline.
properties:
  samples:
    type: array
    items:
      type: object
      properties:
        sample_name: 
          type: string
          description: "Name of the sample"
          minLength: 1 # set a minimum length required for this required attribute
        file_path: 
          type: string
          description: "Path to the input file to count"
          minLength: 1 # set a minimum length required for this required attribute
        area_type:
          type: string
          description: "Name of the components of the country"
          minLength: 1 # set a minimum length required for this required attribute
      required:
        - sample_name
        - file_path
        - area_type
required:
  - samples
```

This file specifies what inputs the pipeline uses, and what type they are.
It is a [JSON Schema](https://json-schema.org/), which allows us to use this file to validate the inputs, which we'll cover later.
For now, it defines that our input samples have 3 properties: `sample_name`, `file_path`, and `area_type`. 
We also specify a minimum length required for these inputs with `minLength: 1`.

### Adapt the pipeline interface to use the input schema

Next, we need to tell looper to use this as the input schema for the pipeline.
Do this by adding the `input_schema` in the pipeline interface.

```yaml title="pipeline_interface.yaml" hl_lines="2"
pipeline_name: count_lines
input_schema: input_schema.yaml
sample_interface:
  command_template: >
    {looper.piface_dir}/pipeline/count_lines.sh {sample.file_path}
```

Now, the input schema is created and linked to the pipeline.
If you invoke `looper run`, looper will read the schema, and first validate the sample before running the job.
In this example, the first 3 samples will validate and run as before, but the final sample will not pass the validation stage.

To solve the problem, we need to specify the `area_type` for country `usa`.
Let's add that back in.

```csv title="metadata/sample_table.csv" hl_lines="5"
sample_name,area_type
mexico,state
switzerland,canton
canada,province
usa,state
```

Now, all 4 samples will validate and `looper run` will run all jobs.

## Validating that input files exist

Another thing we may want to validate is that a file actually exists.
But how does looper know which attributes point to files that must exist?
It is not enough to state that the `file_path` attribute is `required`; this simply means the sample specifies something for that attribute.
It *also* must actually point to a file that exists.
Looper does this through the `tangible` key.

```yaml title="input_schema.yaml" hl_lines="14 15"
description: An input schema for count_lines pipeline pipeline.
properties:
  samples:
    type: array
    items:
      type: object
      properties:
        sample_name: 
          type: string
          description: "Name of the sample"
        file_path: 
          type: string
          description: "Path to the input file to count"
      tangible:
        - file_path
      sizing:
        - file_path
      required:
        - sample_name
        - file_path
required:
  - samples
```

By specifying `file_path` under `required`, we are telling looper to make sure that attribute is defined on the sample.
Then, by adding `file_path` under `tangible`, we are telling looper that the file it points to must actually exist.

To test, the `usa` sample should be missing its data file, so it should not run.
Try it by running `looper run`.

You will see:

```console hl_lines="12"
...
## [3 of 4] sample: canada; pipeline: count_lines
Writing script to /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_canada.sub
Job script (n=1; 0.05Gb): /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_canada.sub
Compute node: zither
Start time: 2024-09-19 16:27:32
Number of lines: 4091500
## [4 of 4] sample: usa; pipeline: count_lines
1 input files missing, job input size was not calculated accurately
> Not submitted: Missing files: data/usa.txt
Writing script to /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_usa.sub

Looper finished
```

Looper will not submit this job because it recognizes that there is no file in `data/usa.txt`.
Let's make one.
This command will make new data file for usa with 100 million lines in it and a file size of around 1 Gb.

```sh
shuf -r -n 100000000 data/mexico.txt > data/usa.txt
```

Now if you run this it will work. 
But this also leads to another thought.
The `usa.txt` text file is way larger than the other files.
What if we need to modulate the job parameters by the size of the input file?

## Parameterizing job templates by sample through size-dependent variables

In the `count_lines` tutorials, we showed how to parameterize a job submission template via the `compute` section in the pipeline interface file, like this:

```yaml  title="pipeline/pipeline_interface.yaml" hl_lines="5 6 7 8 9"
pipeline_name: count_lines
sample_interface:
  command_template: >
    {looper.piface_dir}/pipeline/count_lines.sh {sample.file_path}
compute:
  partition: standard
  time: '01-00:00:00'
  cores: '32'
  mem: '32000'
```

This allows a job submission template to use computing variables like `{CORES}` and `{MEM}`, so you can control cluster resources.
This provides the same compute parameters for every sample.
What if we have a huge file and we want to use different parameters?
It's common to need to increase memory usage for a larger sample.
Looper provides a simple but powerful way to configure pipelines depending on the input size of the samples.

Replace the `compute` variables with a single variable, `size_dependent_variables`, which points to a `.tsv` file:

```yaml title="pipeline_interface.yaml" hl_lines="3"
compute:
  partition: standard
  size_dependent_variables: resources-sample.tsv
```

(Here, we leave the `partition` variable there, since it won't change by sample input size).

Then, create `resources-sample.tsv` with these contents:

```tsv title="resources-sample.tsv"
max_file_size	cores	mem	time
0.05	1	1000	00-01:00:00
0.5	2	2000	00-03:00:00
NaN	4	4000	00-05:00:00
```

In this example, the `partition` will remain constant for all samples, but the `cores`, `mem`, and `time` variables will be modulated by sample file size.
For each sample, looper will select the first row for which the sample's input file size does not exceed the row's `max_file_size` value in gigabytes. In this example: 

Files up to 0.05 Gb (50 Mb) will use 1 core, 1000 mb of RAM, and 1 hour of clock time.
Files up to 0.5 Gb (500 Mb) will use 2 cores, 2000 mb of RAM, and 3 hours of clock time.
Anything larger will use 4 cores, 4000 mb of RAM, and 5 hours of clock time.

You can think of it like a coin sorter machine, going through a priority list of parameter sets with increasing file size allowed, and the sample falls into first bin in which it fits.
This allows a pipeline author to specify different computing requirements depending on the size of the input sample. 

To see this in action, we will need to use a compute template that uses these parameters.
The `slurm` template should do the trick.
We'll use `-d` to specify a dry run, so the jobs are created, but not run.

```
looper run -p slurm -d
```


You should see output like this:

```sh hl_lines="16"
Activating compute package 'slurm'
## [1 of 4] sample: mexico; pipeline: count_lines
Writing script to /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_mexico.sub
Job script (n=1; 0.00Gb): /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_mexico.sub
Dry run, not submitted
## [2 of 4] sample: switzerland; pipeline: count_lines
Writing script to /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_switzerland.sub
Job script (n=1; 0.00Gb): /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_switzerland.sub
Dry run, not submitted
## [3 of 4] sample: canada; pipeline: count_lines
Writing script to /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_canada.sub
Job script (n=1; 0.00Gb): /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_canada.sub
Dry run, not submitted
## [4 of 4] sample: usa; pipeline: count_lines
Writing script to /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_usa.sub
Job script (n=1; 0.00Gb): /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_usa.sub
Dry run, not submitted
```

But wait! The usa sample file size is listed as 0Gb.
Why is it not recognizing the true size of the input file?
There is one more thing we need to do.

### Configuring how looper determines sample size

You can use the input_schema `sizing` keyword to tell looper which attributes determine file size.
In most cases, `sizing` should be the same as `tangible,` because any file that is listed and must exist on disk would probably be the files that you want to use to determine the input file size.
But there is a possibility that you might have some required input files that you don't want to use to modulate how you think of the size of the sample.
For this reason, we have the ability to define them separately.
So, all we have to do is add `file_path` to the `sizing` section in the input schema, like this.

```yaml title="input_schema.yaml" hl_lines="21 22"
description: An input schema for count_lines pipeline pipeline.
properties:
  samples:
    type: array
    items:
      type: object
      properties:
        sample_name: 
          type: string
          description: "Name of the sample"
        file_path: 
          type: string
          description: "Path to the input file to count"
        area_type:
          type: string
          description: "Name of the components of the country"
      required:
        - sample_name
        - file_path
        - area_type
      sizing:
        - file_path
required:
  - samples
```


Under `sizing`, it lists `file_path`, which tells looper that this variable should be used for determining the size of the sample.

Now, if we try again, we will see that it works

```sh
looper run -p slurm -d --skip 3
```

```sh hl_lines="2"
## [1 of 4] sample: usa; pipeline: count_lines
Writing script to /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_usa.sub
Job script (n=1; 0.99Gb): /home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_usa.sub
Dry run, not submitted
```

Looper is computing this size based on the size of file listed in `file_path`.
Now, look at the job script that was created, which contains the parameters for large files:

```sh
cat results/submission/count_lines_usa.sub
```

```sh hl_lines="4 5 6"
#!/bin/bash
#SBATCH --job-name='count_lines_usa'
#SBATCH --output='/home/nsheff/code/hello_looper/input_schema_example/results/submission/count_lines_usa.log'
#SBATCH --mem='4000'
#SBATCH --cpus-per-task='4'
#SBATCH --time='00-05:00:00'
#SBATCH --partition='{PARTITION}'
#SBATCH -m block
#SBATCH --ntasks=1

echo 'Compute node:' `hostname`
echo 'Start time:' `date +'%Y-%m-%d %T'`



pipeline/count_lines.sh data/usa.txt

```

We recommend pipeline authors configure their pipeline interfaces with appropriate `size_dependent_variables` file, which should be distributed alongside the pipeline interface.

## Adding pre-submission commands to your pipeline run

Sometimes we need to run a set-up task *before* submitting the main pipeline.
Looper handles this through a [pre-submission hook system](pre-submission-hooks.md).

Looper provides several built-in hooks that do things like write out the sample information in different ways, which can be useful for different types of pipeline.
If your pipeline would benefit from one of these representations, all you need to do is add a reference to the plugin into the pipeline interface, like this:

```yaml title="pipeline_interface.yaml"
pre_submit:
  python_functions:
    - looper.write_sample_yaml
```

This will instruct looper to engage this plugin.
You can also parameterize the plugin by adding other variables into the pipeline interface.
Consult the plugin documentation for more details about how to parameterize the  plugins.

You can also write your own custom plugins, which can be as simple as a shell script, or they could be Python functions.
Here's an example of a Python script that will be executed through the command-line:


```yaml title="pipeline_interface.yaml"
pre_submit:
  command_templates:
    - "{looper.piface_dir}/hooks/script.py --genome {sample.genome} --log-file {looper.output_dir}/log.txt"
```

Looper will run this command before running each job, allowing you to create little set-up scripts to prepare things before a full job is run.

## Project-level pipeline interfaces

Remember, looper distinguishes sample-level from project-level pipelines.
This is explained in detail in [Advanced run options](../advanced-guide/advanced-run-options.md) and in [How to run a project-level pipeline](../user-tutorial/project-level-pipelines.md).
Basically, sample-level pipelines run *once per sample*, whereas project-level pipelines run *once per project*.
If this interface were describing a project-level pipeline, we would change out `sample_interface` to `project_interface`.

```yaml title="pipeline_interface.yaml" hl_lines="2"
pipeline_name: count_lines
project_interface:
  command_template: '{looper.piface_dir}/count_lines.sh
```

You can also write an interface with both a `sample_interface` and a `project_interface`.
This would make sense to do for a pipeline that had two parts, one that you run independently for each sample, and a second one that aggregates all those sample results at the project level.

The differences between using `sample_interface` vs `project_interface` are pretty simple, actually. When a user invokes `looper run`, looper reads data under `sample_interface` and will create one job template per sample. In contrast, when a user invokes `looper runp`, looper reads data under `project_interface` and  creates one job per project (one job total). 

The only other difference is that the sample-level command template has access to the `{sample.<attribute>}` namespace, whereas the project-level command template has access to the `{samples}` array.

!!! tip "Summary"
    - You can initialize and modify a generic pipeline interface using `looper init_piface`.
    - You should make your pipeline interfaces portable by using `{looper.piface_dir}`.
    - Pipeline-specific and sample-specific compute variables can be added to the pipeline interface to set items such as memory and number of cpus during the pipeline run.
    - You can specify pre-submission hooks for job setup in the pipeline interface.



