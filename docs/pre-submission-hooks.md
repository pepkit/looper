# Pre-submission hooks

## Purpose

Sometimes there is a need to perform some job/submission related tasks *before* the main pipeline submission. FOr example, we may need to generate a particular representation of the sample metadata to be consumed by a pipeline run. Some of these pre-submission tasks may depend on the information outside of the sample, such as the compute settings. For this purpose looper provides **pre-submission hooks**, which allows users to run arbitrary commands or Python functions before submitting the actual pipeline. These hooks have access to all of the job submission settings. They can be used in two ways: 1) to simply run required tasks, producing required output before the pipeline is run; and 2) to modify the job submission settings, which can then be used in the actual submission template.

## Syntax

The pre-submission tasks to be executed are listed in the [pipeline interface](pipeline-interface-specification.md) file under `pre_submit` top-level key. The `pre_submit` section is divided into two subsections corresponding to there  two types of hooks: `python_functions` and `command_templates`. The `python_functions` key specifies a list of strings corresponding to python functions to run. The `command_templates` key is more generic, specifying shell commands to be executed in a subprocess. Here is an example:

```yaml
pre_submit:
  python_functions: 
    - "package_name.function_name"
    - "package_name1.function_name"
  command_templates: 
    - "tool.sh --param {sample.attribute}"
    - "tool1.sh --param {sample.attribute1}"
```










 (for their composition please refer to [looper variable namespaces](variable-namespaces.md) section).

## Execution order

The state of variable namespaces used as an input for any of the hooks depends on the resulting state of the previous one (output). Therefore, the execution order is crucial for complex system designs. There are two rules to remember:

 - the execution order is preserved within the subsections of `pre_submit` block (YAML lists order)
 - plugins listed under `python_functions` are *always* executed before `command_templates`

## Input and output specification

### Namespaces updates strategy

After every successful pre-submission hook execution the input namespaces are updated with the result of the hook execution. The values within particular namespace are overwritten with the returned ones. Therefore if the user's desire is to preserve a value, it can be absent in the resulting data structure. Please see the following example of input and output namespaces object for the illustration of the described bahavior:

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

Returned data:
```yaml
sample:
    size: 1000
looper:
    log_file: /home/michal/Desktop/new_log.txt
```

Result (input + returned data):
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

### Input and output formats

Plugin authors may require users to specify any attributes within any namespace to parametrize them. For example, a plugin that increases the compute wall time by an arbitrary amount of time may require `extra_time` attribute in the `pipeline` namespace. The plugins need to handle incomplete parametrization, either by providing defaults or by raising exceptions.

[`pipeline.template_vars`](pipeline-interface-specification.md#var_templates) section is particularly useful and recommended to parametrize plugin functions.
 
#### `python_functions`

**Input:**
 - Python [`dict`](https://docs.python.org/3/tutorial/datastructures.html#dictionaries) of [looper variable namespaces](variable-namespaces.md)
 
**Output:**
 - Python [`dict`](https://docs.python.org/3/tutorial/datastructures.html#dictionaries) of [looper variable namespaces](variable-namespaces.md)

#### `command_templates`

**Input:**
 - NA (since it is a template, the command can be supplied with choice of [looper variable namespaces](variable-namespaces.md))
 
**Output:**
 - JSON-formatted string (`str`), that is processed with [json.loads](https://docs.python.org/3/library/json.html#json.loads) and [subprocess.check_output](https://docs.python.org/3/library/subprocess.html#subprocess.check_output) as follows: `json.loads(subprocess.check_output(str))` 
 

## Built-in `pre_submit.python_functions`

Looper ships with several included plugins that you can use as pre-submission functions without installing additional software. These plugins produce various representations of the sample metadata, which can be useful for different types of pipelines. The included plugins are described blow


### `looper.write_sample_yaml`

Saves the sample to YAML file. This plugin can be parametrized with a custom output directory using `sample_yaml_path`. If the parameter is not provided, the file will be saved in `{looper.output_dir}/submission`.

**Parameters:**
   - (optional) `pipeline.var_templates.sample_yaml_path`: a complete and absolute path to the *directory* where sample YAML representation is to be stored.

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

### `looper.write_sample_yaml_prj`

Saves the sample to YAML file with project reference.  This plugin can be parametrized with a custom YAML directory (see "parameters" below). If the parameter is not provided, the file will be saved in `{looper.output_dir}/submission`.

**Parameters:**
   - (optional) `pipeline.var_templates.sample_yaml_path`: a complete and absolute path to the *directory* where sample YAML representation is to be stored.

**Usage:**

```yaml
pipeline_type: sample
var_templates:
  main: "{looper.piface_dir}/pipelines/pipeline1.py"
  sample_yaml_path: "{looper.output_dir}/custom_sample_yamls"
pre_submit:
  python_functions:
    - looper.write_sample_yaml_prj
command_template: >
  {pipeline.var_templates.main} ...
```

### `looper.write_submission_yaml`

Saves all five namespaces of pre-submission to YAML file.  This plugin can be parametrized with a custom YAML directory (see "parameters" below). If the parameter is not provided, the file will be saved in `{looper.output_dir}/submission`.

**Parameters:**
   - (optional) `pipeline.var_templates.submission_yaml_path`: a complete and absolute path to the *directory* where submission YAML representation is to be stored.

**Usage:**

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

## Example uses of `pre_submit.command_templates`

### Dynamic compute parameters 

The size-dependent variables is a convenient system to modulate computing variables based on file size, but it is not flexible enough to allow modulated compute variables on the basis of other sample attributes. For a more flexible version, you can use the pre submission hooks system. The `pre_submit.command_templates` specifies a list of Jinja2 templates to construct a system command run in a subprocess. This command template has available all of the namespaces in the primary command template. The command should return a JSON object, which is then used to populate the namespaces. This allows you to specify computing variables that depend on any attributes of a project, sample, or pipeline, which can be used for ultimate flexibility in computing.

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
