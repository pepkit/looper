# How to run pipeline using looper config file

In looper>=1.5.0 was added new functionality that supports usage of projects from [PEPhub](https://pephub.databio.org/) and
decouples PEP from pipeline interfaces.
By using project from PEPhub, user can run pipeline without downloading PEP. User should only specify all necessary
environment variables that are in PEP, to point directory of actual files and pipeline interfaces.

Example looper config file using local PEP:
```yaml
pep_config: $HOME/hello_looper-master/project/project_config.yaml
output_dir: "$HOME/hello_looper-master/output"
pipeline_interfaces:
  sample: ["$HOME/hello_looper-master/pipeline/pipeline_interface"]
  project: "some/project/pipeline"
```

Example looper config file using PEPhub project:
```yaml
pep_config: pephub::databio/looper:default
output_dir: "$HOME/hello_looper-master/output"
pipeline_interfaces:
  sample: ["$HOME/hello_looper-master/pipeline/pipeline_interface"]
  project: "some[requirements-all.txt](..%2Frequirements%2Frequirements-all.txt)/project/pipeline"
```

Where:
- `output_dir` is pipeline output directory, where results will be saved.
- `pep_config` is a local config file or PEPhub registry path. (registry path should be specified in one
one of supported ways: `namespace/name`, `pephub::namespace/name`, `namespace/name:tag`, or `pephub::namespace/name:tag`)
- `pipeline interfaces` is a local path to project or sample pipelines.

To run pipeline, go to the directory of .looper.config and execute command in your terminal:
`looper run` or `looper runp`.
