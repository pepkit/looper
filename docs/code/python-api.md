# Looper Python API

The looper Python API provides classes for managing pipeline submissions and compute configurations.

## Project

The main class for working with looper projects. Extends peppy's Project with pipeline submission capabilities.

::: looper.project.Project
    options:
      members:
        - __init__
        - cli_pifaces
        - get_sample_piface
        - get_schemas
        - make_project_dirs
        - output_dir
        - pipeline_interfaces
        - populate_pipeline_outputs
        - results_folder
        - selected_compute_package
        - set_sample_piface
        - submission_folder
      heading_level: 3

## PipelineInterface

Parses and holds information from a pipeline interface YAML file, including resource specifications and command templates.

::: looper.pipeline_interface.PipelineInterface
    options:
      members:
        - __init__
        - choose_resource_package
        - get_pipeline_schemas
        - pipeline_name
        - render_var_templates
      heading_level: 3

## SubmissionConductor

Collects and submits pipeline jobs. Manages job pooling based on file size or command count limits.

::: looper.conductor.SubmissionConductor
    options:
      members:
        - __init__
        - add_sample
        - failed_samples
        - is_project_submittable
        - num_cmd_submissions
        - num_job_submissions
        - submit
        - write_script
      heading_level: 3

## ComputingConfiguration

Manages compute environment settings from divvy configuration files. Handles resource packages and submission templates.

::: looper.divvy.ComputingConfiguration
    options:
      members:
        - __init__
        - activate_package
        - clean_start
        - default_config_file
        - get_active_package
        - get_adapters
        - list_compute_packages
        - reset_active_settings
        - template
        - templates_folder
        - update_packages
        - write_script
      heading_level: 3

## Utility Functions

### select_divvy_config

::: looper.divvy.select_divvy_config
    options:
      heading_level: 3
