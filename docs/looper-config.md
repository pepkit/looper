# How to use the looper config file

Starting with `looper` version `>=1.5.0`, you should specify a pipeline interface in the looper config file, rather than in the PEP.

Example looper config file using local PEP:

```yaml
pep_config: $HOME/hello_looper-master/project/project_config.yaml
output_dir: "$HOME/hello_looper-master/output"
pipeline_interfaces:
  sample: ["$HOME/hello_looper-master/pipeline/pipeline_interface"]
  project: "some/project/pipeline"
```

In addition, looper>=1.5.0 supports projects from [PEPhub](https://pephub.databio.org/). 
Using a PEP from PEPhub allows a user to run a pipeline without downloading the PEP. This allows you to keep the sample table in a centralized, shared location. You need only specify all necessary
environment variables used by the PEP.

Example looper config file using PEPhub project:

```yaml
pep_config: pephub::databio/looper:default
output_dir: "$HOME/hello_looper-master/output"
pipeline_interfaces:
  sample: ["$HOME/hello_looper-master/pipeline/pipeline_interface"]
  project: "$HOME/hello_looper-master/project/pipeline"
```

Where:
- `output_dir` is pipeline output directory, where results will be saved.
- `pep_config` is a local config file or PEPhub registry path. (registry path should be specified in one
one of supported ways: `namespace/name`, `pephub::namespace/name`, `namespace/name:tag`, or `pephub::namespace/name:tag`)
- `pipeline interfaces` is a local path to project or sample pipelines.

To run pipeline, go to the directory of .looper.config and execute command in your terminal:
`looper run --looper-config {looper_config_path}` or `looper runp --looper-config {looper_config_path}`.
