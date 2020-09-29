# Pre-submission hooks

## Purpose

Sometimes there is a need to perform some job/submission related tasks *before* the main pipeline submission, particularly ones that depend on the submission settings as a whole. For this purpose we've designed the **pre-submission hooks** system, which allows to run arbitrary commands or Python plugin functions before submitting the actual pipeline. These hooks can use and modify the job submission settings (for their composition please refer to [looper variable namespaces](variable-namespaces.md) section).

## Syntax

The pre-submission tasks to be executed are listed in the [pipeline interface](pipeline-interface-specification.md) file under `pre_submit` top-level key. Since there are two classes of hooks that can be executed the section is divided into `python_functions` and `command_templates`, which both are YAML lists of strings that specify source of the plugin functions and commands to be executed in a subprocess, respectively.

```yaml
pre_submit:
  python_functions: 
    - package_name.function_name
    - package_name1.function_name
  command_templates: 
    - tool.sh --param {sample.attribute}
    - tool1.sh --param {sample.attribute1}
```

## Execution order

The state of variable namespaces used as and input for any of the hooks depends on the resulting state (output) of the previous one. Therefore, the execution order is crucial for complex system designs. There are two rules to rememer:

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

Result:
```yaml
sample:
    size: 1000
looper:
    log_file: /home/michal/Desktop/new_log.txt
```

Output:
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
 - NA (the command can be supplied with choice of [looper variable namespaces](variable-namespaces.md))
 
**Output:**
 - JSON-formatted string (`str`), that is processed with [json.loads](https://docs.python.org/3/library/json.html#json.loads) and [subprocess.check_output](https://docs.python.org/3/library/subprocess.html#subprocess.check_output) as follows: `json.loads(subprocess.check_output(str))` 
 
## Built-in `pre_submit.python_functions`

### `looper.write_sample_yaml`

Saves the sample to YAML file. This plugin can be parametrized with a custom YAML directory (see "parameters" below). If the parameter is not provided, the file will be saved in `{looper.output_dir}/submission`.

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

...

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
    - "{pipeline.var_templates.compute_script} --sample-size {sample.input_size} --genome {sample.genome}"    
command_template: >
  {pipeline.var_templates.pipeline_path} ...
```

**Script example:**

```python
#!/usr/bin/env python3

import json
from argparse import ArgumentParser

parser = ArgumentParser(description="Test script")

parser.add_argument("-s", "--size", help="max size", required=True)
parser.add_argument("-g", "--genome", type=str, help="genome", required=True)
parser.add_argument("-m", "--log-file", type=str, help="log_file", required=True)
parser.add_argument("-c", "--custom-cores", type=str, help="Force number of cores to use", required=False)
args = parser.parse_args()

y = json.dumps({
    "cores": args.custom_cores or "4",
    "mem": "10000",
    "time": "00-11:00:00",
    "logfile": args.log_file
})

print(y)
```
