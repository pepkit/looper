# Package looper Documentation

## Class Project
Looper-specific NGS Project.

**Parameters:**

- `config_file` -- `str`:  path to configuration file with data fromwhich Project is to be built
- `subproject` -- `str`:  name indicating subproject to use, optional


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




### sample\_names
Names of samples of which this Project is aware.
```python
def sample_names(self)
```




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

`str`:  currently active subproject




### templates\_folder
Path to folder with default submission templates.
```python
def templates_folder(self)
```

**Returns:**

`str`:  path to folder with default submission templates




## Class MissingMetadataException
Project needs certain metadata.


## Class MissingSampleSheetError
Represent case in which sample sheet is specified but nonexistent.


## Class PipelineInterface
This class parses, holds, and returns information for a yaml file that specifies how to interact with each individual pipeline. This includes both resources to request for cluster job submission, as well as arguments to be passed from the sample annotation metadata to the pipeline

**Parameters:**

- `config` -- `str | Mapping`:  path to file from which to parseconfiguration data, or pre-parsed configuration data.


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




## Class SubmissionConductor
Collects and then submits pipeline jobs.

This class holds a 'pool' of commands to submit as a single cluster job.
Eager to submit a job, each instance's collection of commands expands until
it reaches the 'pool' has been filled, and it's therefore time to submit the
job. The pool fills as soon as a fill criteria has been reached, which can
be either total input file size or the number of individual commands.


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



