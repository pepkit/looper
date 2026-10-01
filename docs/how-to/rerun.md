# How to rerun samples

## Introduction

It is recommended that you have read and completed the basic [pipestat tutorial](../user-tutorial/user-pipestat.md) as well as [configuring pipestat backends](configure-pipestat-backends.md). 

This document will briefly cover details about how to configure pipestat in looper:

!!! note "What you'll accomplish"
    Configure looper to rerun failed samples using pipestat status flags.

There may be a time when you need to re-submit samples. Looper's `rerun` command can be used to achieve this. By default, the `rerun` command will gather any samples with a `failed` status and submit again.

However, Looper does not create flags for samples. It only reads them. Creating flags is the job of the pipeline via either the pipeline manager (e.g. [pypiper](/pypiper/)) or pipestat.

Therefore, to create submission flags, you must:

1. Configure looper to use pipestat
2. Add the `flag_file_dir` key and a flag directory path under the pipestat key within the looper config:
```yaml title=".looper.yaml" hl_lines="6"
pep_config: project_config_pipestat.yaml
output_dir: results
pipeline_interfaces:
  - ./pipeline_interface1_sample_pipestat.yaml
pipestat:
  flag_file_dir: output/results_pipeline
  results_file_path: tmp_pipestat_results.yaml
```
3. Ensure your pipeline is using pipestat to set the [status](/pipestat/code/python-tutorial/#pipeline-status-management) upon sample processing.

```python
currentPipestatManager.set_status(record_identifier="sample1", status_identifier="running")
currentPipestatManager.set_status(record_identifier="sample2", status_identifier="failed")
```
More info on setting status can be found [here](../developer-tutorial/developer-pipestat.md#setting-and-checking-status).

Now that your pipeline is setting statuses, you can check the status of all samples using:
```shell
looper check
```
This command will show you a list of samples and their associated status,e.g:

```
     'count_lines' pipeline status summary     
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃    Status     ┃    Jobs count/total jobs    ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│   completed   │             1/3             │
│    failed     │             2/3             │
└───────────────┴─────────────────────────────┘
```

You can resubmit all failed jobs with:
```shell
looper rerun
```

By default, this command will _only_ submit failed jobs. However, you can use the `--ignore-flags` flag to resubmit all jobs.
```shell
looper rerun --ignore-flags
```
 