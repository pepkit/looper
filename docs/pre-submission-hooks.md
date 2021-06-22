# Pre-submission hooks

## Purpose

Sometimes there is a need to perform some job/submission related tasks *before* the main pipeline submission. For example, we may need to generate a particular representation of the sample metadata to be consumed by a pipeline run. Some of these pre-submission tasks may depend on the information outside of the sample, such as the compute settings. For this purpose looper provides **pre-submission hooks**, which allows users to run arbitrary shell commands or Python functions before submitting the actual pipeline. These hooks have access to all of the job submission settings looper uses to populate the primary command template. They can be used in two ways: 1) to simply run required tasks, producing required output before the pipeline is run; and 2) to modify the job submission settings, which can then be used in the actual submission template.


## How to specify pre-submission tasks in the pipeline interface

The pre-submission tasks to be executed are listed in the [pipeline interface](pipeline-interface-specification.md) file under the top-level `pre_submit` key. The `pre_submit` section is divided into two subsections corresponding to two types of hooks: `python_functions` and `command_templates`. The `python_functions` key specifies a list of strings corresponding to Python functions to run. The `command_templates` key is more generic, specifying shell command templates to be executed in a subprocess. Here is an example:

```yaml
pre_submit:
  python_functions: 
    - "package_name.function_name"
    - "package_name1.function_name"
  command_templates: 
    - "tool.sh --param {sample.attribute}"
    - "tool1.sh --param {sample.attribute1}"
```

Because the looper variables are the input to each task, and are also potentially modified by each task, the order of execution is critical. Execution order follows two rules: First, `python_functions` are *always* executed before `command_templates`; and second, the user-specified order in the pipeline interface is preserved within each subsection.

## Built-in pre-submission functions

Looper ships with several included plugins that you can use as pre-submission functions without installing additional software. These plugins produce various representations of the sample metadata, which can be useful for different types of pipelines. The included plugins are described below:


### Included plugin: `looper.write_sample_yaml`

Saves all sample metadata as a YAML file. The output file path can be customized using `var_templates.sample_yaml_path`. If this parameter is not provided, the file will be saved as `{looper.output_dir}/submission/{sample.sample_name}_sample.yaml`.

**Parameters:**
  
  - `pipeline.var_templates.sample_yaml_path` (optional): absolute path to file where YAML is to be stored.

**Usage:**

```yaml
pipeline_type: sample
var_templates:
  main: "{looper.piface_dir}/pipelines/pipeline1.py"
  sample_yaml_path: "{looper.output_dir}/custom_sample_yamls"
pre_submit:
  python_functions:
    - looper.write_sample_yaml
command_template: >
  {pipeline.var_templates.main} ...
```

### Included plugin: `looper.write_sample_yaml_cwl`

This plugin writes a sample yaml file compatible as a job input file for a CWL pipeline. This plugin allows looper to be used as a scatterer to run an independent CWL workflow for each sample in your PEP sample table. You can parametrize the plugin with a custom output file name using `sample_yaml_cwl_path`. If the parameter is not provided, the file will be saved in `{looper.output_dir}/submission/{sample.sample_name}_sample_cwl.yaml`.

**Parameters:**

  - `pipeline.var_templates.sample_yaml_path` (optional): absolute path to file where YAML is to be stored.

**Usage:**

```yaml
pipeline_type: sample
var_templates:
  main: "{looper.piface_dir}/pipelines/pipeline1.py"
  sample_yaml_cwl_path: "{looper.output_dir}/custom_sample_yamls/custom_{sample.name}.yaml"
pre_submit:
  python_functions:
    - looper.write_sample_yaml_cwl
command_template: >
  {pipeline.var_templates.main} ...
```


### Included plugin: `looper.write_sample_yaml_prj`

Saves the sample to YAML file with project reference.  This plugin can be parametrized with a custom YAML directory (see "parameters" below). If the parameter is not provided, the file will be saved in `{looper.output_dir}/submission/{sample.sample_name}_sample_prj.yaml`.

**Parameters:**
  
  - `pipeline.var_templates.sample_yaml_prj_path` (optional): absolute path to file where YAML is to be stored.

**Usage:**

```yaml
pipeline_type: sample
var_templates:
  main: "{looper.piface_dir}/pipelines/pipeline1.py"
  sample_yaml_prj_path: "{looper.output_dir}/custom_sample_yamls"
pre_submit:
  python_functions:
    - looper.write_sample_yaml_prj
command_template: >
  {pipeline.var_templates.main} ...
```

### Included plugin: `looper.write_submission_yaml`

Saves all five namespaces of pre-submission to YAML file.  This plugin can be parametrized with a custom YAML directory (see "parameters" below). If the parameter is not provided, the file will be saved in `{looper.output_dir}/submission/{sample.sample_name}_submission.yaml`.

**Parameters:**
  
  - `pipeline.var_templates.submission_yaml_path` (optional): a complete and absolute path to the *directory* where submission YAML representation is to be stored.

**Example usage:**

```yaml
pipeline_type: sample
var_templates:
  main: "{looper.piface_dir}/pipelines/pipeline1.py"
  submission_yaml_path: "{looper.output_dir}/custom_path"
pre_submit:
  python_functions:
    - looper.write_submission_yaml
command_template: >
  {pipeline.var_templates.main} ...
```

### Included plugin: `looper.write_custom_template`

Populates an independent jinja template with values from all the available looper namespaces.

**Parameters:**
- `pipeline.var_templates.custom_template` (required): a jinja template to be populated for each job.
- `pipeline.var_templates.custom_template_output` (optional): path to which the populated template file will be saved. If not provided, the populated fill will be saved in `{looper.output_dir}/submission/{sample.sample_name}_config.yaml


## Writing your own pre-submission hooks

Pre-submission tasks can be written as a Python function or a shell commands. We will explain each type below:

### Python functions

Python plugin functions have access *all of the metadata variables looper has access to to construct the primary command template*. The Python function must obey the following rules:

1. The Python function *must* take as input a `namespaces` object, which is a Python [`dict`](https://docs.python.org/3/tutorial/datastructures.html#dictionaries) of [looper variable namespaces](variable-namespaces.md). 

2. The function *should* return any updated namespace variables; or can potentially return an empty `dict` (`{}`) if no changes are intended, which may the case if the function is only used for its side effect.

#### Custom function input parameters

How can you parameterize your plugin function? Since the function will have access to all the looper variable namespaces, this means that plugin authors may require users to specify any attributes within any namespace to parametrize them. For example, a plugin that increases the compute wall time by an arbitrary amount of time may require `extra_time` attribute in the `pipeline` namespace. Users would specify this parameter like this:

```{yaml}
pipeline_name: my_pipeline
pipeline_type: sample
extra_time: 3
```

This variable would be accessible in your python function as `namespaces["pipeline"]["extra_time"]`. This works, but we recommend keeping things clean by putting all required pipeline parameters into the [`pipeline.template_vars`](pipeline-interface-specification.md#var_templates) section. This not only keeps things tidy in a particular section, but also adds additional functionality of making these templates that can themselves refer to namespace variables, which can be very convenient. For example, a better approach would be:

```{yaml}
pipeline_name: my_pipeline
pipeline_type: sample
var_templates:
  extra_time: 3
  plugin_path: "{looper.piface_dir}/plugin_results"
```

In this example you'd use `namespaces["pipeline"]["var_templates"]["extra_time"]` to access the user-provided parameter. Notice we included another example, `plugin_path`, which can refer to the `{looper.piface_dir}` variable. Because this variable is included under `var_templates`, it will be populated with any namespace variables. 

The plugins need to handle incomplete parametrization, either by providing defaults or by raising exceptions. 

#### Function output: updating submission metadata via return value

One of the features of the pre-submission hooks is that they can be used to update the [looper variable namespaces](variable-namespaces.md) so that you can use modified variables in your primary command template. This is effectively a way for a plugin function to provide output that can be used by looper. The way this works is that after every successful pre-submission hook execution, the input namespaces are updated with the return value of the hook execution. Existing values are overwritten with the returned ones, whereas omitted values are not changed. Therefore, you must simply write your function to return any updated variables in the same format as in the input function. That is, your return value should be a Python [`dict`](https://docs.python.org/3/tutorial/datastructures.html#dictionaries) of [looper variable namespaces](variable-namespaces.md)


For example, given this input (which represents the looper variable namespaces):

Input:
```yaml
sample:
    name: test
    size: 30
    genome: hg38
looper:
    log_file: /home/michal/my_log.txt
    job_name: test_pepatac
compute:
    submission_template: /home/michal/divvy_templates/localhost_template.sub
    submission_command: sh
...
``` 

Say your function returned this data:
```yaml
sample:
    size: 1000
looper:
    log_file: /home/michal/Desktop/new_log.txt
```

Then looper would have this object available for populating the primary command template (input + returned data):
```yaml
sample:
    name: test
    size: 1000
    genome: hg38
looper:
    log_file: /home/michal/Desktop/new_log.txt
    job_name: test_pepatac
compute:
    submission_template: /home/michal/divvy_templates/localhost_template.sub
    submission_command: sh
...
```

### Shell command plugins

In case you need more flexibility than a Python function, you can also execute arbitrary commands as a pre-submission task. You define exactly what command you want to run, like this:

```yaml
var_templates:
  compute_script: "{looper.piface_dir}/hooks/script.py"
pre_submit:
  command_templates: 
    - "{pipeline.var_templates.compute_script} --genome {sample.genome} --log-file {looper.output_dir}/log.txt" 
```

This `command_templates` section specifies a list with one or more entries. Each entry specifies a command. The commands are themselves templates, just like the primary `command_template`, so you have access to the looper variable namespaces to put together the appropriate command. In fact, really, the other difference between these `pre_submit.command_templates` and the primary `command_template` is that the final one has access to the changes introduce in the variables by the `pre_submit` commands. The inputs to the script are completely user-defined -- you choose what information and how you want to pass it to your script.
 
**Output:** The output of your command should be a JSON-formatted string (`str`), that is processed with [json.loads](https://docs.python.org/3/library/json.html#json.loads) and [subprocess.check_output](https://docs.python.org/3/library/subprocess.html#subprocess.check_output) as follows: `json.loads(subprocess.check_output(str))`. This JSON object will be used to update the looper variable namespaces. 

#### Example: Dynamic compute parameters 

In the `compute` section of the pipeline interface, looper allows you to specify a `size_dependent_variables` section, which  lets you specify variables with values that are modulated based on the total input file size for the run. This is typically used to add variables for memory, CPU, and clock time to request, if they depend on the input file size. This a good example  of modulating computing variables based on file size, but it is not flexible enough to allow modulated compute variables on the basis of other sample attributes. For a more flexible version, you can use a pre-submission hook.

The `pre_submit.command_templates` specifies a list of Jinja2 templates to construct a system command run in a subprocess. This command template has available all of the namespaces in the primary command template. The command should return a JSON object, which is then used to populate the namespaces. This allows you to specify computing variables that depend on any attributes of a project, sample, or pipeline, which can be used for ultimate flexibility in computing.

**Usage**:

```yaml
pipeline_type: sample
var_templates:
  pipeline_path: "{looper.piface_dir}/pipelines/pepatac.py"
  compute_script: "{looper.piface_dir}/hooks/script.py"
pre_submit:
  command_templates: 
    - "{pipeline.var_templates.compute_script} --genome {sample.genome} --log-file {looper.output_dir}/log.txt"    
command_template: >
  {pipeline.var_templates.pipeline_path} ...
```

**Script example:**

```python
#!/usr/bin/env python3

import json
from argparse import ArgumentParser

parser = ArgumentParser(description="Test script")

parser.add_argument("-s", "--sample-size", help="Sample size", required=False)
parser.add_argument("-g", "--genome", type=str, help="Genome", required=True)
parser.add_argument("-m", "--log-file", type=str, help="Log file path", required=True)
parser.add_argument("-c", "--custom-cores", type=str, help="Force number of cores to use", required=False)
args = parser.parse_args()

y = json.dumps({
    "cores": args.custom_cores or "4",
    "mem": "10000" if args.genome == "hg38" else "20000",
    "time": "00-11:00:00",
    "logfile": args.log_file
})

print(y)
```
