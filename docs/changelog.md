# Changelog

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

## [1.5.1] -- 2023-08-14

### Fixed
- fix `looper table` failing without `sample.protocol`

### Changed
- correct `--looper_conifg` to `--looper-config`

## [1.5.0] -- 2023-08-09

### Added 

- ability to use PEPs from PEPhub without downloading project [#341](https://github.com/pepkit/looper/issues/341)
- ability to specify pipeline interfaces inside looper config [Looper Config](https://looper.databio.org/en/dev/how_to_define_looper_config/)
- divvy re-integrated in looper
- divvy inspect -p package
- Looper will now check that the command path provided in the pipeline interface is callable before submitting.


### Changed
- initialization of generic pipeline interface available using subcommand `init-piface`
- `looper report` will now use pipestat to generate browsable HTML reports if pipestat is configured.
- looper now works with pipestat v0.5.0.
- Removed --toggle-key functionality. 
- Allow for user to input single integer value for --sel-incl or --sel-excl

## [1.4.3] -- 2023-08-01

### Fixed
- Fix regression for var_templates expansion.

## [1.4.2] -- 2023-07-31

### Fixed
- Fix for expanding paths properly.

## [1.4.1] -- 2023-06-22


## [1.4.0] -- 2023-04-24

### Added

- preliminary support for [pipestat](http://pipestat.databio.org).
- ability to skip samples using  `-k` or `--skip` [#367](https://github.com/pepkit/looper/pull/367)
- ability to input a range into `limit` and `skip`[#367](https://github.com/pepkit/looper/pull/367)
- `limit` and `skip` are now both usable with Destroy and Run. [#367](https://github.com/pepkit/looper/pull/367)
- ability to generate generic pipeline interface using `init -p` or `init --piface` [#368](https://github.com/pepkit/looper/pull/368)
- Fixed ability to use custom sample index
- Added `write_custom_template`, a built-in pre-submit plugin for writing templates

### Changed
- looper now returns nonzero if any samples fail submission
- various other developer changes

### Deprecated
- `path` variable will be deprecated in favor of `var_templates` [#322](https://github.com/pepkit/looper/issues/322)

## [1.3.2] -- 2022-02-09

### Changed
- Fixed bug with use_2to3 for setuptools compatibility.

## [1.3.1] -- 2021-06-18

### Changed
- If remote schemas are not accessbile, the job submission doesn't fail anymore
- Fixed a bug where looper stated "No failed flag found" when a failed flag was found

### Deprecated
- Fixed and deprecated `looper inspect`. Use `eido inspect` from now on.


## [1.3.0] -- 2020-10-07

### Added
- New plugin system for pre-submission hooks
- Included plugin functions: `write_sample_yaml`, `write_sample_yaml_prj`, `write_sample_yaml_cwl` and `write_submission_yaml`
- New `var_templates` section for defining variables in the pipeline interface

### Changed
- Pipeline interface specification was updated to accommodate new `var_templates` section and pre-submission hooks

### Deprecated
- pipeline interface sections:
    - `dynamic_variables_command_template`, which can now be more simply accomplished with a pre-submission hook
    - `path`, which is replaced by a more generic `var_templates` section

## [1.2.1] - 2020-08-26

### Added
- Environment variables expansion in custom sample YAML paths; [Issue 273](https://github.com/pepkit/looper/issues/273)
- `dynamic_variables_script_path` key in the pipeline interface. Path, absolute or relative to the pipeline interface file; [Issue 276](https://github.com/pepkit/looper/issues/276)
### Changed
- Resolve project pipeline interface path by making it relative to the config not current directory; [Issue 268](https://github.com/pepkit/looper/issues/268)
### Fixed
- Unclear error when `output_dir` was not provided in a config `looper` section; [Issue 286](https://github.com/pepkit/looper/issues/286)

## [1.2.0] - 2020-05-26

**This version introduced backwards-incompatible changes.**

### Added
- Commands:
    - `init`; initializes `.looper.yaml` file
    - `inspect`; inspects `Project` or `Sample` objects
    - `table`; writes summary stats table
    - `runp`; runs project level pipelines
- Input schemas and output schemas
- `--settings` argument to specify compute resources as a YAML file
- Option to preset CLI options in a dotfile
- `--command-extra` and `--command-extra-override` arguments that append specified string to pipeline commands. These functions supercede the previous `pipeline_config` and `pipeline_args` sections, which are now deprecated. The new method is more universal, and can accomplish the same functionality but more simply, using the built-in PEP machinery to selectively apply commands to samples.
- Option to specify destination of sample YAML in pipeline interface
- `--pipeline_interfaces` argument that allows pipeline interface specification via CLI

### Changed
- `looper summarize` to `looper report`
- Pipeline interface format changed drastically
- The PyPi name changed from 'loopercli' to 'looper'
- resources section in pipeline interface replaced with `size_dependent_attributes` or `dynamic_variables_command_template`.
- `--compute` can be used to specify arguments other than resources
- `all_input_files` and `required_input_files` keys in pipeline interface moved to the input schema and renamed to `files` and `required_files`
- pipeline interface specification

## [0.12.6] -- 2020-02-21

### Added
- possibility to execute library module as a script: `python -m looper ...`

### Changed
- in the summary page account for missing values when plotting; the value is disregarded in such a case and plot is still created
- show 50 rows in the summary table
- make links to the summary page relative
- long entries in the sample stats table are truncated with an option to see original value in a popover

### Fixed
- inactive jQuery dependent components in the status page
- project objects layout in the summary index page
- inactivation of popovers after Bootstrap Table events
- non-homogeneous status flags appearance

## [0.12.5] -- 2019-12-13
### Changed
- reduce verbosity of missing options; [Issue 174](https://github.com/pepkit/looper/issues/174)
- switch to [Bootstrap Table](https://bootstrap-table.com/) in the summary index page table and sample status tables

## [0.12.4] -- 2019-07-18
### Added
- Ability to declare `required_executables` in a `PipelineInterface`, to trigger a naive "runnability" check for a sample submission
- A possibility to opt out of status page inclusion in the navbar

### Changed
- The status tables now use DataTables jQuery plugin to make them interactive

### Fixed
- Navbar links creation

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
