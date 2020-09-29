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
 
 
 
## Example uses

Below we provide couple of use examples of the pre-submission hooks system

### Sample namespace serialization

A built-in plugin, that saves the sample to YAML file.

**Required parameters:** None

```yaml
pipeline_type: sample
var_templates:
  main: "{looper.piface_dir}/pipelines/pipeline1.py"
pre_submit:
  python_functions:
    - looper.write_sample_yaml
command_template: >
  {pipeline.var_templates.main} ...
```

### Entire submission serialization

A built-in plugin, that saves the submission namespace to YAML file.

**Required parameters:**
- input1
- input2
- input3

```yaml
pipeline_type: sample
var_templates:
  main: "{looper.piface_dir}/pipelines/pipeline1.py"
pre_submit:
  python_functions:
    - looper.write_submission_yaml
command_template: >
  {pipeline.var_templates.main} ...
```

### Dynamic compute parameters 

The size-dependent variables is a convenient system to modulate computing variables based on file size, but it is not flexible enough to allow modulated compute variables on the basis of other sample attributes. For a more flexible version, you can use the pre submission hooks system. The `pre_submit.command_templates` specifies a list of Jinja2 templates to construct a system command run in a subprocess. This command template has available all of the namespaces in the primary command template. The command should return a JSON object, which is then used to populate the namespaces. This allows you to specify computing variables that depend on any attributes of a project, sample, or pipeline, which can be used for ultimate flexibility in computing.

Example:

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