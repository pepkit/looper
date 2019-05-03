# Package looper Documentation

## Class Project
Looper-specific NGS Project.

**Parameters:**

- `config_file` -- `str`:  path to configuration file with data fromwhich Project is to be built
- `subproject` -- `str`:  name indicating subproject to use, optional


### build\_submission\_bundles
Create pipelines to submit for each sample of a particular protocol.

With the argument (flag) to the priority parameter, there's control
over whether to submit pipeline(s) from only one of the project's
known pipeline locations with a match for the protocol, or whether to
submit pipelines created from all locations with a match for the
protocol.
```python
def build_submission_bundles(self, protocol, priority=True)
```

**Parameters:**

- `protocol` -- `str`:  name of the protocol/library for which tocreate pipeline(s)
- `priority` -- `bool`:  to only submit pipeline(s) from the first of thepipelines location(s) (indicated in the project config file) that has a match for the given protocol; optional, default True


**Returns:**

`Iterable[(PipelineInterface, type, str, str)]`: 


**Raises:**

- `AssertionError`:  if there's a failure in the attempt topartition an interface's pipeline scripts into disjoint subsets of those already mapped and those not yet mapped




### constants
Return key-value pairs of pan-Sample constants for this Project.
```python
def constants(self)
```

**Returns:**

`Mapping`:  collection of KV pairs, each representing a pairingof attribute name and attribute value




### derived\_columns
Collection of sample attributes for which value of each is derived from elsewhere
```python
def derived_columns(self)
```

**Returns:**

`list[str]`:  sample attribute names for which value is derived




### implied\_columns
Collection of sample attributes for which value of each is implied by other(s)
```python
def implied_columns(self)
```

**Returns:**

`list[str]`:  sample attribute names for which value is implied by other(s)




### num\_samples
Count the number of samples available in this Project.
```python
def num_samples(self)
```

**Returns:**

`int`:  number of samples available in this Project.




### output\_dir
Directory in which to place results and submissions folders.

By default, assume that the project's configuration file specifies
an output directory, and that this is therefore available within
the project metadata. If that assumption does not hold, though,
consider the folder in which the project configuration file lives
to be the project's output directory.
```python
def output_dir(self)
```

**Returns:**

`str`:  path to the project's output directory, either asspecified in the configuration file or the folder that contains the project's configuration file.




### project\_folders
Keys for paths to folders to ensure exist.
```python
def project_folders(self)
```




### protocols
Determine this Project's unique protocol names.
```python
def protocols(self)
```

**Returns:**

`Set[str]`:  collection of this Project's unique protocol names




### required\_metadata
Which metadata attributes are required.
```python
def required_metadata(self)
```




### sample\_annotation
Get the path to the project's sample annotations sheet.
```python
def sample_annotation(self)
```

**Returns:**

`str`:  path to the project's sample annotations sheet




### sample\_names
Names of samples of which this Project is aware.
```python
def sample_names(self)
```




### sample\_subannotation
Return the data table that stores metadata for subsamples/units.
```python
def sample_subannotation(self)
```

**Returns:**

`pandas.core.frame.DataFrame | NoneType`:  table ofsubsamples/units metadata




### sample\_table
Return (possibly first parsing/building) the table of samples.
```python
def sample_table(self)
```

**Returns:**

`pandas.core.frame.DataFrame | NoneType`:  table of samples'metadata, if one is defined




### samples
Generic/base Sample instance for each of this Project's samples.
```python
def samples(self)
```

**Returns:**

`Iterable[Sample]`:  Sample instance for eachof this Project's samples




### sheet
Annotations/metadata sheet describing this Project's samples.
```python
def sheet(self)
```

**Returns:**

`pandas.core.frame.DataFrame`:  table of samples in this Project




### subproject
Return currently active subproject or None if none was activated
```python
def subproject(self)
```

**Returns:**

`str`:  name of currently active subproject




### subsample\_table
Return (possibly first parsing/building) the table of subsamples.
```python
def subsample_table(self)
```

**Returns:**

`pandas.core.frame.DataFrame | NoneType`:  table of subsamples'metadata, if the project defines such a table




### templates\_folder
Path to folder with default submission templates.
```python
def templates_folder(self)
```

**Returns:**

`str`:  path to folder with default submission templates




### Class MissingMetadataException
Project needs certain metadata.


### Class MissingSampleSheetError
Represent case in which sample sheet is specified but nonexistent.


## Class SubmissionConductor
Collects and then submits pipeline jobs.

This class holds a 'pool' of commands to submit as a single cluster job.
Eager to submit a job, each instance's collection of commands expands until
it reaches the 'pool' has been filled, and it's therefore time to submit the
job. The pool fills as soon as a fill criteria has been reached, which can
be either total input file size or the number of individual commands.


### add\_sample
Add a sample for submission to this conductor.
```python
def add_sample(self, sample, sample_subtype=<class 'peppy.sample.Sample'>, rerun=False)
```

**Parameters:**

- `sample` -- `Sample`:  sample to be included with this conductor'scurrently growing collection of command submissions
- `sample_subtype` -- `type`:  specific subtype associatedwith this new sample; this is used to tailor-make the sample instance as required by its protocol/pipeline and supported by the pipeline interface.
- `rerun` -- `bool`:  whether the given sample is being rerun rather thanrun for the first time


**Returns:**

`bool`:  Indication of whether the given sample was added tothe current 'pool.'


**Raises:**

- `TypeError`:  If sample subtype is provided but does not extendthe base Sample class, raise a TypeError.




### failed\_samples
```python
def failed_samples(self)
```



### num\_cmd\_submissions
Return the number of commands that this conductor has submitted.
```python
def num_cmd_submissions(self)
```

**Returns:**

`int`:  Number of commands submitted so far.




### num\_job\_submissions
Return the number of jobs that this conductor has submitted.
```python
def num_job_submissions(self)
```

**Returns:**

`int`:  Number of jobs submitted so far.




### submit
Submit command(s) as a job.

This call will submit the commands corresponding to the current pool 
of samples if and only if the argument to 'force' evaluates to a 
true value, or the pool of samples is full.
```python
def submit(self, force=False)
```

**Parameters:**

- `force` -- `bool`:  Whether submission should be done/simulated evenif this conductor's pool isn't full.


**Returns:**

`bool`:  Whether a job was submitted (or would've been ifnot for dry run)




### write\_script
Create the script for job submission.
```python
def write_script(self, pool, template_values, prj_argtext, looper_argtext)
```

**Parameters:**

- `template_values` -- `Mapping`:  Collection of template placeholderkeys and the values with which to replace them.
- `prj_argtext` -- `str`:  Command text related to Project data.
- `looper_argtext` -- `str`:  Command text related to looper arguments.


**Returns:**

`str`:  Path to the job submission script created.




### write\_skipped\_sample\_scripts
For any sample skipped during initial processing, write submission script.
```python
def write_skipped_sample_scripts(self)
```




## Class PipelineInterface
This class parses, holds, and returns information for a yaml file that specifies how to interact with each individual pipeline. This includes both resources to request for cluster job submission, as well as arguments to be passed from the sample annotation metadata to the pipeline

**Parameters:**

- `config` -- `str | Mapping`:  path to file from which to parseconfiguration data, or pre-parsed configuration data.


### choose\_resource\_package
Select resource bundle for given input file size to given pipeline.
```python
def choose_resource_package(self, pipeline_name, file_size)
```

**Parameters:**

- `pipeline_name` -- `str`:  Name of pipeline.
- `file_size` -- `float`:  Size of input data (in gigabytes).


**Returns:**

`MutableMapping`:  resource bundle appropriate for given pipeline,for given input file size


**Raises:**

- `ValueError`:  if indicated file size is negative, or if thefile size value specified for any resource package is negative
- `_InvalidResourceSpecificationException`:  if no defaultresource package specification is provided




### copy
Copy self to a new object.
```python
def copy(self)
```




### fetch\_pipelines
Fetch the mapping for a particular protocol, null if unmapped.
```python
def fetch_pipelines(self, protocol)
```

**Parameters:**

- `protocol` -- `str`:  name/key for the protocol for which to fetch thepipeline(s)


**Returns:**

`str | Iterable[str] | NoneType`:  pipeline(s) to which the givenprotocol is mapped, otherwise null




### fetch\_sample\_subtype
Determine the interface and Sample subtype for a protocol and pipeline.
```python
def fetch_sample_subtype(self, protocol, strict_pipe_key, full_pipe_path)
```

**Parameters:**

- `protocol` -- `str`:  name of the relevant protocol
- `strict_pipe_key` -- `str`:  key for specific pipeline in a pipelineinterface mapping declaration; this must exactly match a key in the PipelineInterface (or the Mapping that represent it)
- `full_pipe_path` -- `str`:  (absolute, expanded) path to thepipeline script


**Returns:**

`type`:  Sample subtype to use for jobs for the given protocol,that use the pipeline indicated


**Raises:**

- `KeyError`:  if given a pipeline key that's not mapped in thepipelines section of this PipelineInterface




### finalize\_pipeline\_key\_and\_paths
Determine pipeline's full path, arguments, and strict key.

This handles multiple ways in which to refer to a pipeline (by key)
within the mapping that contains the data that defines a
PipelineInterface. It also ensures proper handling of the path to the
pipeline (i.e., ensuring that it's absolute), and that the text for
the arguments are appropriately dealt parsed and passed.
```python
def finalize_pipeline_key_and_paths(self, pipeline_key)
```

**Parameters:**

- `pipeline_key` -- `str`:  the key in the pipeline interface file usedfor the protocol_mappings section. Previously was the script name.


**Returns:**

`(str, str, str)`:  more precise version of input key, along withabsolute path for pipeline script, and full script path + options




### get\_arg\_string
For a given pipeline and sample, return the argument string.
```python
def get_arg_string(self, pipeline_name, sample, submission_folder_path='', **null_replacements)
```

**Parameters:**

- `pipeline_name` -- `str`:  Name of pipeline.
- `sample` -- `Sample`:  current sample for which job is being built
- `submission_folder_path` -- `str`:  path to folder in which filesrelated to submission of this sample will be placed.
- `null_replacements` -- `dict`:  mapping from name of Sample attributename to value to use in arg string if Sample attribute's value is null


**Returns:**

`str`:  command-line argument string for pipeline




### get\_attribute
Return the value of the named attribute for the pipeline indicated.
```python
def get_attribute(self, pipeline_name, attribute_key, path_as_list=True)
```

**Parameters:**

- `pipeline_name` -- `str`:  name of the pipeline of interest
- `attribute_key` -- `str`:  name of the pipeline attribute of interest
- `path_as_list` -- `bool`:  whether to ensure that a string attributeis returned as a list; this is useful for safe iteration over the returned value.




### get\_pipeline\_name
Translate a pipeline name (e.g., stripping file extension).
```python
def get_pipeline_name(self, pipeline)
```

**Parameters:**

- `pipeline` -- `str`:  Pipeline name or script (top-level key inpipeline interface mapping).


**Returns:**

`str`:  translated pipeline name, as specified in config or bystripping the pipeline's file extension




### iterpipes
Iterate over pairs of pipeline key and interface data.
```python
def iterpipes(self)
```

**Returns:**

`iterator of (str, Mapping)`:  Iterator over pairs of pipelinekey and interface data




### pipe\_iface
Old-way access to pipeline key-to-interface mapping
```python
def pipe_iface(self)
```

**Returns:**

`Mapping`:  Binding between pipeline key and interface data




### pipeline\_names
Names of pipelines about which this interface is aware.
```python
def pipeline_names(self)
```

**Returns:**

`Iterable[str]`:  names of pipelines about which thisinterface is aware




### pipelines\_path
Path to pipelines folder.
```python
def pipelines_path(self)
```

**Returns:**

`str | None`:  Path to pipelines folder, if configured withfile rather than with raw mapping.




### protomap
Access protocol mapping portion of this composite interface.
```python
def protomap(self)
```

**Returns:**

`Mapping`:  binding between protocol name and pipeline key.




### select\_pipeline
Check to make sure that pipeline has an entry and if so, return it.
```python
def select_pipeline(self, pipeline_name)
```

**Parameters:**

- `pipeline_name` -- `str`:  Name of pipeline.


**Returns:**

`Mapping`:  configuration data for pipeline indicated


**Raises:**

- `MissingPipelineConfigurationException`:  if there's noconfiguration data for the indicated pipeline




### uses\_looper\_args
Determine whether indicated pipeline accepts looper arguments.
```python
def uses_looper_args(self, pipeline_name)
```

**Parameters:**

- `pipeline_name` -- `str`:  Name of pipeline to check for looperargument acceptance.


**Returns:**

`bool`:  Whether indicated pipeline accepts looper arguments.





**Version Information**: `looper` v0.11.0, generated by `lucidoc` v0.3