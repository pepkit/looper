# Changelog

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format. 

## [0.12.3] -- 2019-06-20
### Fixed
- Bug in `Sample` YAML naming, whereby a base `Sample` was being suffixed as a subtype would be, leading to a pipeline argument based on `yaml_file` that did not exist on disk.

## [0.12.2] -- 2019-06-06

### Fixed
- Fixed various bugs related to populating derived attributes, including using attributes like `sample_name` as keys.
- Fixed a bug related to singularity attributes not being passed from a pipeline interface file.
- Fixed several bugs with incorrect version requirements.

## [0.12.1] -- 2019-05-20

### Added
- Made `looper.Sample` include more specific functionality from `peppy`

### Changed
- Status table creation is possible outside of `looper`.
- In the summary index page the plottable columns list is now scrollable
- Status page relies on the `profile.tsv` file rather than `*.log`; [Issue 159](https://github.com/pepkit/looper/issues/159)

### Fixed
- In HTML reporting module, do not ignore objects which are neither HTMLs nor images in the summary, e.g. CSVs
- Restore parsing and application of pipeline-level computing resource specification from a pipeline interface file; [Issue 184](https://github.com/pepkit/looper/issues/184)
- Allow `ignore_flags` to properly modulate submission messaging; [Issue 179](https://github.com/pepkit/looper/issues/179)
- Do not display time-like summary columns as the plottable ones; [Issue 182](https://github.com/pepkit/looper/issues/182)

## [0.12.0] -- 2019-05-03

### Added
- First implementation of pipeline interface 'outputs', so pipeline authors can specify items of interest produced by the pipeline.
- Functions and attributes on `Project` to support "outputs" (`interfaces`, `get_interfaces`, `get_outputs`)

### Changed
- Start "compute" --> "compute_packages" transition 
- `get_logger` moved to `peppy`

### Fixed
- Prevent CLI option duplication in pipeline commands generated
- Make functional CLI spec of particular attribute on which to base selection of a subset of a project's samples ([`peppy` 298](https://github.com/pepkit/peppy/issues/298))

## [0.11.1] -- 2019-04-17

### Changed
- Improved documentation
- Improved interaction with `peppy` and `divvy` dependencies

## [0.11] -- 2019-04-17

### Added
- Implemented `looper rerun` command.
- Support use of custom `resources` in pipeline's `compute` section
- Listen for itemized compute resource specification on command-line with `--resources`
- Support pointing to `Project` config file with folder path rather than full filepath
- Add `selector-attribute` parameter for more generic sample selection.

### Changed
- Switched to a Jinja-style templating system for summary output
- Made various UI changes to adapt to `caravel` use.
- Using `attmap` for "attribute-style key-vale store" implementation
- Removed Python 3.4 support.
- UI: change parameter names `in/exclude-samples` to `selector-in/exclude`.
  
## [0.10.0] -- 2018-12-20

### Changed
- `PipelineInterface` now derives from `peppy.AttributeDict`.
- On `PipelineInterface`, iteration over pipelines now is with `iterpipes`.
- Rename `parse_arguments` to `build_parser`, which returns `argparse.ArgumentParser` object
- Integers in HTML reports are made more human-readable by including commas.
- Column headers in HTML reports are now stricly for sorting; there's a separate list for plottable columns.
- More informative error messages
- HTML samples list is fully populated.
- Existence of an object lacking an anchor image is no longer problematic for `summarize`.
- Basic package test in Python 3 now succeeds: `python3 setup.py test`.

## [v0.9.2] -- 2018-11-12

### Changed
- Fixed bugs with `looper summarize` when no summarizers were present
- Added CLI flag to force `looper destroy` for programmatic access
- Fixed a bug for samples with duplicate names
- Added new display features (graphs, table display) for HTML summary output.


## [0.9.1] -- 2018-06-30

### Changed
- Fixed several bugs with `looper summarize` that caused failure on edge cases.

## [0.9.0] -- 2018-06-25

### Added
- Support for custom summarizers
- Add `allow-duplicate-names` command-line options
- Allow any variables in environment config files or other `compute` sections to be used in submission templates. This allows looper to be used with containers.
- Add nice universal project-level HTML reporting

## [0.8.1] -- 2018-04-02

### Changed
- Minor documentation and packaging updates for first Pypi release.
- Fix a bug that incorrectly mapped protocols due to case sensitive issues
- Fix a bug with `report_figure` that made it output pandas code


## [0.8.0] -- 2018-01-19

### Changed
- Use independent `peppy` package, replacing `models` module for core data types.
- Integrate `ProtocolInterface` functionality into `PipelineInterface`.

## [0.7.2] -- 2017-11-16
### Changed
- Correctly count successful command submissions when not using `--dry-run`.

## [0.7.1] -- 2017-11-15

### Changed
- No longer falsely display that there's a submission failure.
- Allow non-string values to be unquoted in the `pipeline_args` section.

## [0.7] -- 2017-11-15
### Added
- Add `--lump` and `--lumpn` options
- Catch submission errors from cluster resource managers
- Implied columns can now be derived
- Now protocols can be specified on the command-line `--include-protocols`
- Add rudimentary figure summaries
- Simplifies command-line help display
- Allow wildcard protocol_mapping for catch-all pipeline assignment
- Improve user messages
- New sample_subtypes section in pipeline_interface
    
### Changed
- Sample child classes are now defined explicitly in the pipeline interface. Previously, they were guessed based on presence of a class extending Sample in a pipeline script.
- Changed 'library' key sample attribute to 'protocol'

## [0.6] -- 2017-07-21
### Added
  - Add support for implied_column section of the project config file
  - Add support for Python 3
  - Merges pipeline interface and protocol mappings. This means we now allow direct pointers to `pipeline_interface.yaml` files, increasing flexibility, so this relaxes the specified folder structure that was previously used for `pipelines_dir` (with `config` subfolder).
  - Allow URLs as paths to sample sheets.
  - Allow tsv format for sample sheets.
  - Checks that the path to a pipeline actually exists before writing the submission script. 

### Changed
- Changed LOOPERENV environment variable to PEPENV, generalizing it to generic models
- Changed name of `pipelines_dir` to `pipeline_interfaces` (but maintained backwards compatibility for now).
- Changed name of `run` column to `toggle`, since `run` can also refer to a sequencing run.
- Relaxes many constraints (like resources sections, pipelines_dir columns), making project configuration files useful outside looper. This moves us closer to dividing models from looper, and improves flexibility.
- Various small bug fixes and dev improvements.
- Require `setuptools` for installation, and `pandas 0.20.2`. If `numexpr` is installed, version `2.6.2` is required.
- Allows tilde in `pipeline_interfaces`

## [0.5] -- 2017-03-01
### Added
- Add new looper version tracking, with `--version` and `-V` options and printing version at runtime
- Add support for asterisks in file paths
- Add support for multiple pipeline directories in priority order
- Revamp of messages make more intuitive output
- Colorize output
- Complete rehaul of logging and test infrastructure, using logging and pytest packages

### Changed
- Removes pipelines_dir requirement for models, making it useful outside looper
- Small bug fixes related to `all_input_files` and `required_input_files` attributes
- More robust installation and more explicit requirement of Python 2.7


## [0.4] -- 2017-01-12
###  Added
- New command-line interface (CLI) based on sub-commands
- New subcommand (`looper summarize`) replacing the `summarizePipelineStats.R` script
- New subcommand (`looper check`) replacing the `flagCheck.sh` script
- New command (`looper destroy`) to remove all output of a project
- New command (`looper clean`) to remove intermediate files of a project flagged for deletion
- Support for portable and pipeline-independent allocation of computing resources with Looperenv.

### Changed
- Removed requirement to have `pipelines` repository installed in order to extend base Sample objects
- Maintenance of sample attributes as provided by user by means of reading them in as strings (to be improved further)
- Improved serialization of Sample objects
