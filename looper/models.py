#!/usr/bin/env python

"""
Models for NGS projects
=======================

Workflow explained:
	- Project is created
	- Add Sample sheet to project (spawns next)
		- Samples are created and added to project (automatically)

In the process, stuff is checked:
	- project structure (created if not existing)
	- existance of csv sample sheet with minimal fields
	- Constructing a path to a sample's input file and checking for its existance
	- read type/length of samples (optionally)

Example:

.. code-block:: python

	from looper.models import Project
	prj = Project("config.yaml")
	prj.add_sample_sheet()
	# that's it!

Explore!

.. code-block:: python

	# see all samples
	prj.samples
	prj.samples[0].fastq
	# get fastq file of first sample
	# get all bam files of WGBS samples
	[s.mapped for s in prj.samples if s.library == "WGBS"]

	prj.metadata.results  # results directory of project
	# export again the project's annotation
	prj.sheet.to_csv(os.path.join(prj.metadata.output_dir, "sample_annotation.csv"))

	# project options are read from the config file
	# but can be changed on the fly:
	prj = Project("test.yaml")
	# change options on the fly
	prj.config["merge_technical"] = False
	# annotation sheet not specified initially in config file
	prj.add_sample_sheet("sample_annotation.csv")

"""

import os as _os
import pandas as _pd
import yaml as _yaml
from collections import OrderedDict as _OrderedDict


def copy(obj):
	def copy(self):
		"""
		Copy self to a new object.
		"""
		from copy import deepcopy

		return deepcopy(self)
	obj.copy = copy
	return obj


@copy
class Paths(object):
	"""
	A class to hold paths as attributes.
	"""
	def __repr__(self):
		return "Paths object."

	def __getitem__(self, key):
		"""
		Provides dict-style access to attributes
		"""
		return getattr(self, key)


@copy
class AttributeDict(object):
	"""
	A class to convert a nested Dictionary into an object with key-values
	accessibly using attribute notation (AttributeDict.attribute) instead of
	key notation (Dict["key"]). This class recursively sets Dicts to objects,
	allowing you to recurse down nested dicts (like: AttributeDict.attr.attr)
	"""
	def __init__(self, entries):
		self.add_entries(entries)

	def add_entries(self, entries):
		for key, value in entries.items():
			if type(value) is dict:
				# key exists
				if hasattr(self, key):
					if type(self[key]) is AttributeDict:
						print ("Updating existing key: " + key)
						# Combine them
						self.__dict__[key].add_entries(value)
					else:
						# Create new AttributeDict, replace previous value
						self.__dict__[key] = AttributeDict(value)
				else:
					# Create new AttributeDict
					self.__dict__[key] = AttributeDict(value)
			else:
				if type(value) is not type(None):
					# Overwrite even if it's a dict; only if it's not None
					self.__dict__[key] = value

	def __getitem__(self, key):
		"""
		Provides dict-style access to attributes
		"""
		return getattr(self, key)

	def __repr__(self):
		return str(self.__dict__)


@copy
class Project(AttributeDict):
	"""
	A class to model a Project.

	:param config_file: Project config file (yaml).
	:type config_file: str
	:param dry: If dry mode is activated, no directories will be created upon project instantiation.
	:type dry: bool
	:param permissive: Whether a error should be thrown if a sample input file(s) do not exist or cannot be open.
	:type permissive: bool
	:param file_checks: Whether sample input files should be checked for their attributes (read type, read length) if this is not set in sample metadata.
	:type file_checks: bool
	:param looperenv_file: Looperenv YAML file specifying compute settings.
	:type looperenv_file: str

	:Example:

	.. code-block:: python

		from looper.models import Project
		prj = Project("config.yaml")
	"""
	def __init__(self, config_file, subproject=None, dry=False, permissive=True, file_checks=False, looperenv_file=None):
		# super(Project, self).__init__(**config_file)

		# Initialize local, serial compute as default (no cluster submission)
		from pkg_resources import resource_filename

		# Start with default looperenv
		default_looperenv = resource_filename("looper", 'submit_templates/default_looperenv.yaml')
		self.update_looperenv(default_looperenv)

		# Load settings from looper environment yaml for local compute infrastructure.
		if looperenv_file == '' or looperenv_file is None:
			print("Using default LOOPERENV. You may set environment variable 'LOOPERENV' to configure compute settings.")
		else:
			self.update_looperenv(looperenv_file)

		# Here, looperenv has been loaded (either custom or default). Initialize default compute settings.
		self.set_compute("default")

		print(self.compute)
		# optional configs
		self.permissive = permissive
		self.file_checks = file_checks

		# include the path to the config file
		self.config_file = _os.path.abspath(config_file)

		# Parse config file
		self.parse_config_file(subproject)

		# Get project name
		# deduce from output_dir variable in config file:

		self.name = _os.path.basename(self.metadata.output_dir)
		self.subproject = subproject

		# TODO:
		# or require config file to have it:
		# self.name = self.config["project"]["name"]

		# Set project's directory structure
		if not dry:
			self.make_project_dirs()
			# self.set_project_permissions()

		# samples
		self.samples = list()

	def __repr__(self):
		if hasattr(self, "name"):
			name = self.name
		else:
			name = "[no name]"

		return "Project '%s'" % name + "\nConfig: " + str(self.config)

	def parse_config_file(self, subproject=None):
		"""
		Parse provided yaml config file and check required fields exist.
		"""
		with open(self.config_file, 'r') as handle:
			self.config = _yaml.load(handle)

		# parse yaml into the project's attributes
		self.add_entries(self.config)

		# Overwrite any config entries with entries in the subproject
		if "subprojects" in self.config and subproject:
			self.add_entries(self.config['subprojects'][subproject])

		# In looper 0.4 we eliminated the paths section for simplicity.
		# For backwards compatibility, mirror the paths section into metadata
		if "paths" in self.config:
			print("Warning: paths section in project config is deprecated. Please move all paths attributes to metadata section.")
			print("This option will be removed in future versions.")
			self.metadata.add_entries(self.paths.__dict__)
			print(self.metadata)
			print(self.paths)
			self.paths = None

		# self.paths = self.metadata

		# These are required variables which have absolute paths
		mandatory = ["output_dir", "pipelines_dir"]
		for var in mandatory:
			if not hasattr(self.metadata, var):
				raise KeyError("Required field not in config file: %s" % var)
			setattr(self.metadata, var, _os.path.expandvars(getattr(self.metadata, var)))

		# These are optional because there are defaults
		config_vars = {  # variables with defaults = {"variable": "default"}, relative to output_dir
			"results_subdir": "results_pipeline",
			"submission_subdir": "submission"
		}
		for key, value in config_vars.items():
			if hasattr(self.metadata, key):
				if not _os.path.isabs(getattr(self.metadata, key)):
					setattr(self.metadata, key, _os.path.join(self.metadata.output_dir, getattr(self.metadata, key)))
			else:
				setattr(self.metadata, key, _os.path.join(self.metadata.output_dir, value))

		# Variables which are relative to the config file
		# All variables in these sections should be relative to the project config
		relative_sections = ["metadata", "pipeline_config"]

		for sect in relative_sections:
			if not hasattr(self, sect):
				continue
			relative_vars = getattr(self, sect)
			if not relative_vars:
				continue
			# print(relative_vars.__dict__)
			for var in relative_vars.__dict__:
				# print(type(relative_vars), var, getattr(relative_vars, var))
				if not hasattr(relative_vars, var):
					continue
				# It could have been 'null' in which case, don't do this.
				if getattr(relative_vars, var) is None:
					continue
				if not _os.path.isabs(getattr(relative_vars, var)):
					# Set the path to an absolute path, relative to project config
					setattr(relative_vars, var, _os.path.join(_os.path.dirname(self.config_file), getattr(relative_vars, var)))

		# compute.submission_template could have been reset by project config into a relative path;
		# make sure it stays absolute
		if not _os.path.isabs(self.compute.submission_template):
			# self.compute.submission_template = _os.path.join(self.metadata.pipelines_dir, self.compute.submission_template)
			# Relative to looper environment config file.
			self.compute.submission_template = _os.path.join(_os.path.dirname(self.looperenv_file), self.compute.submission_template)

		# Required variables check
		if not hasattr(self.metadata, "sample_annotation"):
			raise KeyError("Required field not in config file: %s" % "sample_annotation")

	def update_looperenv(self, looperenv_file):
		"""
		"""
		try:
			with open(looperenv_file, 'r') as handle:
				looperenv = _yaml.load(handle)
				print("Loading LOOPERENV: " + looperenv_file)
				print(looperenv)

				# Any compute.submission_template variables should be made absolute; relative
				# to current looperenv yaml file
				y = looperenv['compute']
				for key, value in y.items():
					if type(y[key]) is dict:
						for key2, value2 in y[key].items():
							if key2 == 'submission_template':
								if not _os.path.isabs(y[key][key2]):
									y[key][key2] = _os.path.join(_os.path.dirname(looperenv_file), y[key][key2])

				looperenv['compute'] = y
				if hasattr(self, "looperenv"):
					self.looperenv.add_entries(looperenv)
				else:
					self.looperenv = AttributeDict(looperenv)

			self.looperenv_file = looperenv_file

		except Exception as e:
			print("Can't load looperenv config file: " + looperenv_file)
			print(str(type(e).__name__) + str(e))

	def make_project_dirs(self):
		"""
		Creates project directory structure if it doesn't exist.
		"""
		for name, path in self.metadata.__dict__.items():
			if name not in ["pipelines_dir"]:   # this is a list just to support future variables
				if not _os.path.exists(path):
					try:
						_os.makedirs(path)
					except OSError:
						raise OSError("Cannot create directory %s" % path)

	def set_project_permissions(self):
		"""
		Makes the project's public_html folder executable.
		"""
		for d in [self.trackhubs.trackhub_dir]:
			try:
				_os.chmod(d, 0755)
			except OSError:
				# This currently does not fail now
				# ("cannot change folder's mode: %s" % d)
				continue

	def set_compute(self, setting):
		"""
		Sets the compute attributes according to the specified settings in the environment file
		:param: setting	An option for compute settings as specified in the environment file.
		"""

		if setting and hasattr(self, "looperenv") and hasattr(self.looperenv, "compute"):
			print("Loading compute settings: " + setting)
			if hasattr(self, "compute"):
				self.compute.add_entries(self.looperenv.compute[setting].__dict__)
			else:
				self.compute = AttributeDict(self.looperenv.compute[setting].__dict__)

			print(self.looperenv.compute[setting])
			print(self.looperenv.compute)
			if not _os.path.isabs(self.compute.submission_template):
				# self.compute.submission_template = _os.path.join(self.metadata.pipelines_dir, self.compute.submission_template)
				# Relative to looper environment config file.
				self.compute.submission_template = _os.path.join(_os.path.dirname(self.looperenv_file), self.compute.submission_template)
		else:
			print("Cannot load compute settings: " + setting)

	def get_arg_string(self, pipeline_name):
		"""
		For this project, given a pipeline, return an argument string
		specified in the project config file.
		"""
		argstring = ""  # Initialize to empty
		if hasattr(self, "pipeline_args"):
			# Add default args to every pipeline
			if hasattr(self.pipeline_args, "default"):
				for key, value in getattr(self.pipeline_args, "default").__dict__.items():
					argstring += " " + key
					# Arguments can have null values; then print nothing
					if value:
						argstring += " " + value
			# Now add pipeline-specific args
			if hasattr(self.pipeline_args, pipeline_name):
				for key, value in getattr(self.pipeline_args, pipeline_name).__dict__.items():
					argstring += " " + key
					# Arguments can have null values; then print nothing
					if value:
						argstring += " " + value

		return argstring

	def add_sample_sheet(self, csv=None, permissive=None, file_checks=None):
		"""
		Build a `SampleSheet` object from a csv file and
		add it and its samples to the project.

		:param csv: Path to csv file.
		:type csv: str
		:param permissive: Should it throw error if sample input is not found/readable? Defaults to what is set to the Project.
		:type permissive: bool
		:param file_checks: Should it check for properties of sample input files (e.g. read type, length)? Defaults to what is set to the Project.
		:type file_checks: bool
		"""
		# If options are not passed, used what has been set for project
		if permissive is None:
			permissive = self.permissive
		else:
			permissive = self.permissive

		if file_checks is None:
			file_checks = self.file_checks
		else:
			file_checks = self.file_checks

		# Make SampleSheet object
		# by default read sample_annotation, but allow csv argument to be passed here explicitely
		if csv is None:
			self.sheet = SampleSheet(self.metadata.sample_annotation)
		else:
			self.sheet = SampleSheet(csv)

		# pair project and sheet
		self.sheet.prj = self

		# Generate sample objects from annotation sheet
		self.sheet.make_samples()

		# Add samples to Project
		for sample in self.sheet.samples:
			sample.merged = False  # mark sample as not merged - will be overwritten later if indeed merged
			self.add_sample(sample)

		# Merge sample files (!) using merge table if provided:
		if hasattr(self.metadata, "merge_table"):
			if self.metadata.merge_table is not None:
				if _os.path.isfile(self.metadata.merge_table):
					# read in merge table
					merge_table = _pd.read_csv(self.metadata.merge_table)

					if 'sample_name' not in merge_table.columns:
						raise KeyError("Required merge table column named 'sample_name' is missing.")

					# for each sample:
					for sample in self.sheet.samples:
						merge_rows = merge_table[merge_table['sample_name'] == sample.name]

						# check if there are rows in the merge table for this sample:
						if len(merge_rows) > 0:
							# for each row in the merge table of this sample:
							# 1) update the sample values with the merge table
							# 2) get data source (file path) for each row (which represents a file to be added)
							# 3) append file path to sample.data_path (space delimited)
							data_paths = list()
							for row in merge_rows.index:
								sample.update(merge_rows.ix[row].to_dict())  # 1)
								data_paths.append(sample.locate_data_source())  # 2)
							sample.data_path = " ".join(data_paths)  # 3)
							sample.merged = True  # mark sample as merged

		# With all samples, prepare file paths and get read type (optionally make sample dirs)
		for sample in self.samples:
			if hasattr(sample, "organism"):
				sample.get_genome_transcriptome()
			sample.set_file_paths()
			if not sample.check_input_exists():
				continue

			# get read type and length if not provided
			if not hasattr(sample, "read_type") and self.file_checks:
				sample.get_read_type()

			# make sample directory structure
			# sample.make_sample_dirs()

	def add_sample(self, sample):
		"""
		Adds a sample to the project's `samples`.
		"""
		# Check sample is Sample object
		if not isinstance(sample, Sample):
			raise TypeError("Provided object is not a Sample object.")

		# Tie sample and project bilateraly
		sample.prj = self
		# Append
		self.samples.append(sample)


@copy
class SampleSheet(object):
	"""
	Class to model a sample annotation sheet.

	:param csv: Path to csv file.
	:type csv: str

	Kwargs (will overule specified in config):
	:param merge_technical: Should technical replicates be merged to create biological replicate samples?
	:type merge_technical: bool
	:param merge_biological: Should biological replicates be merged?
	:type merge_biological: bool
	:param dtype: Data type to read csv file as. Default=str.
	:type dtype: type

	:Example:

	.. code-block:: python

		from looper.models import Project, SampleSheet
		prj = Project("config.yaml")
		sheet = SampleSheet("sheet.csv")
	"""
	def __init__(self, csv, dtype=str, **kwargs):

		super(SampleSheet, self).__init__()

		self.csv = csv
		self.samples = list()
		self.check_sheet(dtype)

	def __repr__(self):
		if hasattr(self, "prj"):
			return "SampleSheet for project '%s' with %i samples." % (self.prj, len(self.df))
		else:
			return "SampleSheet with %i samples." % len(self.df)

	def check_sheet(self, dtype):
		"""
		Check if csv file exists and has all required columns.
		"""
		# Read in sheet
		try:
			self.df = _pd.read_csv(self.csv, dtype=dtype)
		except IOError("Given csv file couldn't be read.") as e:
			raise e

		# Check mandatory items are there
		req = ["sample_name"]
		missing = [col for col in req if col not in self.df.columns]

		if len(missing) != 0:
			raise ValueError("Annotation sheet is missing columns: %s" % " ".join(missing))

	def make_sample(self, series):
		"""
		Make a children of class Sample dependent on its "library" attribute if existing.

		:param series: Pandas `Series` object.
		:type series: pandas.Series
		:return: An object or class `Sample` or a child of that class.
		:rtype: looper.models.Sample
		"""
		import sys
		import inspect

		if not hasattr(series, "library"):
			return Sample(series)

		# If "library" attribute exists, try to get a matched Sample object for it from any "pipelines" repository.
		try:
			import pipelines  # try to use a pipelines package is installed
		except ImportError:
			try:
				sys.path.append(self.prj.metadata.pipelines_dir)  # try using the pipeline package from the config file
				import pipelines
			except ImportError:
				return Sample(series)  # if so, return generic Sample

		# get all class objects from modules of the pipelines package that have a __library__ attribute
		sample_types = list()
		for _, module in inspect.getmembers(sys.modules["pipelines"], lambda member: inspect.ismodule(member)):
			st = inspect.getmembers(module, lambda member: inspect.isclass(member) and hasattr(member, "__library__"))
			sample_types += st
			# print("Detected a pipeline module '{}' with sample types: {}".format(module.__name__, ", ".join([x[0] for x in st])))

		# get __library__ attribute from classes and make mapping of __library__: Class (a dict)
		pairing = {sample_class.__library__: sample_class for sample_type, sample_class in sample_types}

		# Match sample and sample_class
		try:
			return pairing[series.library](series)  # quite stringent matching, maybe improve
		except KeyError:
			return Sample(series)

	def make_samples(self):
		"""
		Creates samples from annotation sheet dependent on library and adds them to the project.
		"""
		for i in range(len(self.df)):
			self.samples.append(self.make_sample(self.df.ix[i].dropna()))

	def as_data_frame(self, all_attrs=True):
		"""
		Returns a `pandas.DataFrame` representation of self.
		"""
		df = _pd.DataFrame([s.as_series() for s in self.samples])

		# One might want to filter some attributes out

		return df

	def to_csv(self, path, all_attrs=False):
		"""
		Saves a csv annotation sheet from the samples.

		:param path: Path to csv file to be written.
		:type path: str
		:param all_attrs: If all sample attributes should be kept in the annotation sheet.
		:type all_attrs: bool

		:Example:

		.. code-block:: python

			from looper.models import SampleSheet
			sheet = SampleSheet("/projects/example/sheet.csv")
			sheet.to_csv("/projects/example/sheet2.csv")
		"""
		df = self.as_data_frame(all_attrs=all_attrs)
		df.to_csv(path, index=False)


@copy
class Sample(object):
	"""
	Class to model Samples basd on a pandas Series.

	:param series: Pandas `Series` object.
	:type series: pandas.Series
	:param permissive: Should throw error if sample file is not found/readable?.
	:type permissive: bool

	:Example:

	.. code-block:: python

		from looper.models import Project, SampleSheet, Sample
		prj = Project("ngs")
		sheet = SampleSheet("/projects/example/sheet.csv", prj)
		s1 = Sample(sheet.ix[0])
	"""
	# Originally, this object was inheriting from _pd.Series,
	# but complications with serializing and code maintenance
	# made me go back and implement it as a top-level object
	def __init__(self, series, permissive=True):
		# Passed series must either be a pd.Series or a daugther class
		if not isinstance(series, _pd.Series):
			raise TypeError("Provided object is not a pandas Series.")
		super(Sample, self).__init__()

		# Keep a list of attributes that came from the sample sheet, so we can provide a
		# minimal representation of the original sample as provided (in order!).
		# Useful to summarize the sample (appending new columns onto the original table)
		self.sheet_attributes = series.keys()

		# Set series attributes on self
		for key, value in series.to_dict().items():
			setattr(self, key, value)

		# Check if required attributes exist and are not empty
		self.check_valid()

		# Short hand for getting sample_name
		self.name = self.sample_name

		# Default to no required paths
		self.required_paths = None

		# Get name for sample:
		# this is a concatenation of all passed Series attributes except "unmappedBam"
		# self.generate_name()

		# Sample dirs
		self.paths = Paths()
		# Only when sample is added to project, can paths be added -
		# this is because sample-specific files will be created in a data root directory dependent on the project.
		# The SampleSheet object, after being added to a project, will
		# call Sample.set_file_paths(), creating the data_path of the sample (the bam file)
		# and other paths.

	def __repr__(self):
		return "Sample '%s'" % self.sample_name

	def __getitem__(self, item):
		"""
		Provides dict-style access to attributes
		"""
		return getattr(self, item)

	def update(self, newdata):
		"""
		Update Sample object with attributes from a dict.
		"""
		for key, value in newdata.items():
			setattr(self, key, value)

	def check_valid(self):
		"""
		Check provided sample annotation is valid.

		It requires the field `sample_name` is existent and non-empty.
		"""
		def check_attrs(req):
			for attr in req:
				if not hasattr(self, attr):
					raise ValueError("Missing value for " + attr + " (sample: " + str(self) + ")")
				if attr == "nan":
					raise ValueError("Empty value for " + attr + " (sample: " + str(self) + ")")

		# Check mandatory items are there.
		# We always require a sample_name
		check_attrs(["sample_name"])

	def generate_name(self):
		"""
		Generates a name for the sample by joining some of its attribute strings.
		"""
		raise NotImplementedError("Not implemented in new code base.")

	def as_series(self):
		"""
		Returns a `pandas.Series` object with all the sample's attributes.
		"""
		return _pd.Series(self.__dict__)

	def to_yaml(self, path=None):
		"""
		Serializes itself in YAML format.

		:param path: A file path to write yaml to.
		:type path: str
		"""
		def obj2dict(obj, to_skip=["samples", "sheet", "sheet_attributes"]):
			"""
			Build representation of object as a dict, recursively
			for all objects that might be attributes of self.

			:param obj: skips including attributes named in provided list.
			:param to_skip: List of strings to ignore.
			:type to_skip: list.
			"""
			if type(obj) is list:  # recursive serialization (lists)
				return [obj2dict(i) for i in obj]
			elif type(obj) is dict:  # recursive serialization (dict)
				return {k: obj2dict(v) for k, v in obj.items() if (k not in to_skip)}
			elif any([isinstance(obj, t) for t in [AttributeDict, Project, Paths, Sample]]):  # recursive serialization (AttributeDict and children)
				return {k: obj2dict(v) for k, v in obj.__dict__.items() if (k not in to_skip)}
			elif hasattr(obj, 'dtype'):  # numpy data types
				return obj.item()
			elif _pd.isnull(obj):  # Missing values as evaluated by pd.isnull() <- this gets correctly written into yaml
				return "NaN"
			else:
				return obj

		# if path is not specified, use default:
		# prj.metadata.submission_dir + sample_name + yaml
		if path is None:
			self.yaml_file = _os.path.join(self.prj.metadata.submission_subdir, self.sample_name + ".yaml")
		else:
			self.yaml_file = path

		# transform into dict
		serial = obj2dict(self)

		# write
		with open(self.yaml_file, 'w') as outfile:
			outfile.write(_yaml.safe_dump(serial, default_flow_style=False))

	def locate_data_source(self, column_name="data_source"):
		"""
		Locates the path of input file `data_path` based on a regex.

		:param column_name: Name of sample attribute to get input data.
		:type column_name: str
		"""
		# default_regex = "/scratch/lab_bsf/samples/{flowcell}/{flowcell}_{lane}_samples/{flowcell}_{lane}#{BSF_name}.bam"

		if hasattr(self, column_name):
			try:
				regex = self.prj["data_sources"][getattr(self, column_name)]
			except:
				print("Config lacks location for data_source: " + getattr(self, column_name))
				return ""

			# This will populate any environment variables like $VAR with os.environ["VAR"]
			regex = _os.path.expandvars(regex)

			try:
				val = regex.format(**self.__dict__)
			except Exception as e:
				print("Can't format data source correctly:" + regex)
				print(str(type(e).__name__) + str(e))
				return ""

			return val

	def get_genome_transcriptome(self):
		"""
		Get genome and transcriptome, based on project config file.
		If not available (matching config), genome and transcriptome will be set to sample.organism.
		"""
		try:
			self.genome = getattr(self.prj.genomes, self.organism)
		except AttributeError:
			print(Warning("Config lacks genome mapping for organism: " + self.organism))
		# get transcriptome
		try:
			self.transcriptome = getattr(self.prj.transcriptomes, self.organism)
		except AttributeError:
			print(Warning("Config lacks transcriptome mapping for organism: " + self.organism))

	def set_file_paths(self, overide=False):
		"""
		Sets the paths of all files for this sample.
		"""
		# If sample has data_path and is merged, then skip this because the paths are already built
		if self.merged and hasattr(self, "data_path") and not overide:
			pass

		# If sample does not have data_path, then build the file path to the input file.
		# this is built on a regex specified in the config file or the custom one (see `Project`).
		if hasattr(self, "data_path"):
			if (self.data_path == "nan") or (self.data_path == ""):
				self.data_path = self.locate_data_source()
		else:
			self.data_path = self.locate_data_source()

		# any columns specified as "derived" will be constructed based on regex
		# in the "data_sources" section (should be renamed?)

		if hasattr(self.prj, "derived_columns"):
			for col in self.prj["derived_columns"]:

				# Only proceed if the specified column exists.
				if hasattr(self, col):
					# should we set a variable called col_source, so that the original
					# data source value can also be retrieved?
					setattr(self, col + "_source", getattr(self, col))
					setattr(self, col, self.locate_data_source(col))
		# 			if not self.required_paths:
		# 				self.required_paths = ""
		# 			self.required_paths += " " + getattr(self, col)

		# # Construct required_inputs
		# if hasattr(self.prj, "required_inputs"):
		# 	for col in self.prj["required_inputs"]:

		# 		# Only proceed if the specified column exists.
		# 		if hasattr(self, col):
		# 			self.required_paths += " " + getattr(self, col)

		# parent
		self.results_subdir = self.prj.metadata.results_subdir
		self.paths.sample_root = _os.path.join(self.prj.metadata.results_subdir, self.sample_name)

		# Track url
		try:
			# Project's public_html folder
			self.bigwig = _os.path.join(self.prj.trackhubs.trackhub_dir, self.sample_name + ".bigWig")
			self.track_url = "/".join([self.prj.trackhubs.url, self.sample_name + ".bigWig"])
		except:
			pass

	def make_sample_dirs(self):
		"""
		Creates sample directory structure if it doesn't exist.
		"""
		for path in self.paths.__dict__.values():
			if not _os.path.exists(path):
				_os.makedirs(path)

	def get_sheet_dict(self):
		"""
		Returns a dict of values but only those that were originally passed in via the sample
		sheet. This is useful for summarizing; it gives you a representation of the sample that
		excludes things like config files or other derived entries. Could probably be made
		more robust but this works for now.
		"""

		return _OrderedDict([[k, getattr(self, k)] for k in self.sheet_attributes])

	def check_input_exists(self, permissive=True):
		"""
		Creates sample directory structure if it doesn't exist.

		:param permissive: Whether error should be ignored if input file does not exist.
		:type permissive: bool
		"""
		#hack!
		#return True

		l = list()
		# Sanity check:
		if not self.data_path:
			self.data_path = ""

		# There can be multiple, space-separated values here.
		for path in self.data_path.split(" "):
			if not _os.path.exists(path):
				l.append(path)

		# Only one of the inputs needs exist.
		# If any of them exists, length will be > 0
		if len(l) > 0:
			if not permissive:
				raise IOError("Input file does not exist or cannot be read: %s" % path)
			else:
				print("Input file does not exist or cannot be read: %s" % ", ".join(l))
				return False
		return True

	def get_read_type(self, n=10, permissive=True):
		"""
		Gets the read type (single, paired) and read length of an input file.

		:param n: Number of reads to read to determine read type. Default=10.
		:type n: int
		:param permissive: Should throw error if sample file is not found/readable?.
		:type permissive: bool
		"""
		import subprocess as sp
		from collections import Counter

		def bam_or_fastq(input_file):
			"""
			Checks if string endswith `bam` or `fastq`.
			Returns string. Raises TypeError if neither.

			:param input_file: String to check.
			:type input_file: str
			"""
			if input_file.endswith(".bam"):
				return "bam"
			elif input_file.endswith(".fastq"):
				return "fastq"
			else:
				raise TypeError("Type of input file does not end in either '.bam' or '.fastq'")

		def check_bam(bam, o):
			"""
			Check reads in BAM file for read type and lengths.

			:param bam: BAM file path.
			:type bam: str
			:param o: Number of reads to look at for estimation.
			:type o: int
			"""
			# view reads
			p = sp.Popen(['samtools', 'view', bam], stdout=sp.PIPE)

			# Count paired alignments
			paired = 0
			read_length = Counter()
			while o > 0:
				line = p.stdout.next().split("\t")
				flag = int(line[1])
				read_length[len(line[9])] += 1
				if 1 & flag:  # check decimal flag contains 1 (paired)
					paired += 1
				o -= 1
			p.kill()
			return (read_length, paired)

		def check_fastq(fastq, o):
			"""
			"""
			raise NotImplementedError("Detection of read type/length for fastq input is not yet implemented.")

		# Initialize the parameters in case there is no input_file,
		# so these attributes at least exist
		self.read_length = None
		self.read_type = None
		self.paired = None

		# for samples with multiple original bams, check all
		files = list()
		for input_file in self.data_path.split(" "):
			try:
				# Guess the file type, parse accordingly
				file_type = bam_or_fastq(input_file)
				if file_type == "bam":
					read_length, paired = check_bam(input_file, n)
				elif file_type == "fastq":
					read_length, paired = check_fastq(input_file, n)
				else:
					if not permissive:
						raise TypeError("Type of input file does not end in either '.bam' or '.fastq'")
					else:
						print(Warning("Type of input file does not end in either '.bam' or '.fastq'"))
					return
			except NotImplementedError as e:
				if not permissive:
					raise e
				else:
					print(e)
					return
			except IOError as e:
				if not permissive:
					raise e
				else:
					print(Warning("Input file does not exist or cannot be read: {}".format(input_file)))
					self.read_length = None
					self.read_type = None
					self.paired = None
					return

			# Get most abundant read length
			read_length = sorted(read_length)[-1]

			# If at least half is paired, consider paired end reads
			if paired > (n / 2):
				read_type = "paired"
				paired = True
			else:
				read_type = "single"
				paired = False

			files.append([read_length, read_type, paired])

		# Check agreement between different files
		# if all values are equal, set to that value;
		# if not, set to None and warn the user about the inconsistency
		for i, feature in enumerate(["read_length", "read_type", "paired"]):
			setattr(self, feature, files[0][i] if len(set(f[i] for f in files)) == 1 else None)

			if getattr(self, feature) is None:
				print(Warning("Not all input files agree on read type/length for sample : %s" % self.name))


@copy
class PipelineInterface(object):
	"""
	This class parses, holds, and returns information for a yaml file that
	specifies tells the looper how to interact with each individual pipeline. This
	includes both resources to request for cluster job submission, as well as
	arguments to be passed from the sample annotation metadata to the pipeline
	"""
	def __init__(self, yaml_config_file):
		import yaml
		self.looper_config_file = yaml_config_file
		self.looper_config = yaml.load(open(yaml_config_file, 'r'))

		# A variable to control the verbosity level of output
		self.verbose = 0

	def select_pipeline(self, pipeline_name):
		"""
		Check to make sure that pipeline has an entry and if so, return it.

		:param pipeline_name: Name of pipeline.
		:type pipeline_name: str
		"""
		if pipeline_name not in self.looper_config:
			print(
				"Missing pipeline description: '" + pipeline_name + "' not found in '" +
				self.looper_config_file + "'")
			# Should I just use defaults or force you to define this?
			raise Exception("You need to teach the looper about that pipeline")

		return(self.looper_config[pipeline_name])

	def get_pipeline_name(self, pipeline_name):
		"""
		:param pipeline_name: Name of pipeline.
		:type pipeline_name: str
		"""
		config = self.select_pipeline(pipeline_name)

		if "name" not in config:
			# Discard extensions for the name
			name = _os.path.splitext(pipeline_name)[0]
		else:
			name = config["name"]

		return name

	def choose_resource_package(self, pipeline_name, file_size):
		"""
		Given a pipeline name (pipeline_name) and a file size (size), return the
		resource configuratio specified by the config file.

		:param pipeline_name: Name of pipeline.
		:type pipeline_name: str
		:param file_size: Size of input data.
		:type file_size: float
		"""
		config = self.select_pipeline(pipeline_name)

		if "resources" not in config:
			msg = "No resources found for '" + pipeline_name + "' in '" + self.looper_config_file + "'"
			# Should I just use defaults or force you to define this?
			raise IOError(msg)

		table = config['resources']
		current_pick = "default"

		for option in table:
			if table[option]['file_size'] == "0":
				continue
			if file_size < float(table[option]['file_size']):
				continue
			elif float(table[option]['file_size']) > float(table[current_pick]['file_size']):
				current_pick = option

		# print("choose:" + str(current_pick))

		return(table[current_pick])

	def confirm_required_inputs(self, pipeline_name, sample, permissive = True):
		config = self.select_pipeline(pipeline_name)

		# Pipeline interface file may specify required input files;
		if config.has_key('required_input_files'):
			required_input_attributes = config['required_input_files']
		else:
			required_input_attributes = None
			return True

		print("required_input_attributes" + str(required_input_attributes))

		# Identify and accumulate a list of any missing required inputs for this sample
		missing_files = []
		for file_attribute in required_input_attributes:
			if not hasattr(sample, file_attribute):
				raise IOError("Sample missing required input attribute: " + file_attribute)

			paths = getattr(sample, file_attribute)
			# There can be multiple, space-separated values here.
			for path in paths.split(" "):
				if not _os.path.exists(path):
					missing_files.append(path)

		if len(missing_files) > 0:
			if not permissive:
				raise IOError("Input file does not exist or cannot be read: %s" % str(missing_files))
			else:
				print("Input file does not exist or cannot be read: %s" % str(missing_files))
				return False

		return True

	def get_total_input_size(self, pipeline_name, sample):
		# Make this pipeline-specific, since different pipelines may have different inputs.
		config = self.select_pipeline(pipeline_name)
		if config.has_key('all_input_files'):
			files_paths = [getattr(sample, file_attribute) for file_attribute in config['all_input_files']]
			input_file_size = self.get_file_size(files_paths)
		elif config.has_key('required_input_files'):
			files_paths = [getattr(sample, file_attribute) for file_attribute in config['required_input_files']]
			input_file_size = self.get_file_size(files_paths)
		else:
			input_file_size = 0

		return(input_file_size)

	def get_file_size(self, filename):
		"""
		Get size of all files in string (space-separated) in gigabytes (Gb).
		"""
		try:
			return sum([float(_os.stat(f).st_size) for f in filename.split(" ") if f is not '']) / (1024 ** 3)
		except OSError:
			# File not found
			return 0


	def get_arg_string(self, pipeline_name, sample):
		"""
		For a given pipeline and sample, return the argument string

		:param pipeline_name: Name of pipeline.
		:type pipeline_name: str
		:param sample: Sample object.
		:type sample: Sample
		"""
		config = self.select_pipeline(pipeline_name)

		if "arguments" not in config:
			print(
				"No arguments found for '" + pipeline_name + "' in '" +
				self.looper_config_file + "'")
			return("")  # empty argstring

		argstring = ""
		args = config['arguments']

		for key, value in args.iteritems():
			if self.verbose:
				print(key, value)
			if value is None:
				arg = ""
			else:
				try:
					arg = getattr(sample, value)
				except AttributeError as e:
					print(
						"Pipeline '" + pipeline_name + "' requests for argument '" +
						key + "' a sample attribute named '" + value + "'" +
						" but no such attribute exists for sample '" +
						sample.sample_name + "'")
					raise e

				argstring += " " + str(key) + " " + str(arg)

		# Add optional arguments
		if 'optional_arguments' in config:
			args = config['optional_arguments']
			for key, value in args.iteritems():
				if self.verbose:
					print(key, value, "(optional)")
				if value is None:
					arg = ""
				else:
					try:
						arg = getattr(sample, value)
					except AttributeError as e:
						print(
							"Pipeline '" + pipeline_name + "' requests for OPTIONAL argument '" +
							key + "' a sample attribute named '" + value + "'" +
							" but no such attribute exists for sample '" +
							sample.sample_name + "'")
						continue
						# raise e

					argstring += " " + str(key) + " " + str(arg)

		return(argstring)


@copy
class ProtocolMapper(object):
	"""
	This class maps protocols (the library column) to pipelines. For example,
	WGBS is mapped to wgbs.py
	"""
	def __init__(self, mappings_file):
		import yaml
		# mapping libraries to pipelines
		self.mappings_file = mappings_file
		self.mappings = yaml.load(open(mappings_file, 'r'))
		self.mappings = {k.upper(): v for k, v in self.mappings.items()}

	def build_pipeline(self, protocol):
		"""
		:param protocol: Name of protocol.
		:type protocol: str
		"""
		# print("Building pipeline for protocol '" + protocol + "'")

		if protocol not in self.mappings:
			print("  Missing Protocol Mapping: '" + protocol + "' is not found in '" + self.mappings_file + "'")
			return([])  # empty list

		# print(self.mappings[protocol]) # The raw string with mappings
		# First list level
		split_jobs = [x.strip() for x in self.mappings[protocol].split(';')]
		# print(split_jobs) # Split into a list
		return(split_jobs)  # hack works if no parallelism

		for i in range(0, len(split_jobs)):
			if i == 0:
				self.parse_parallel_jobs(split_jobs[i], None)
			else:
				self.parse_parallel_jobs(split_jobs[i], split_jobs[i - 1])

	def parse_parallel_jobs(self, job, dep):
		# Eliminate any parenthesis
		job = job.replace("(", "")
		job = job.replace(")", "")
		# Split csv entry
		split_jobs = [x.strip() for x in job.split(',')]
		if len(split_jobs) > 1:
			for s in split_jobs:
				self.register_job(s, dep)
		else:
			self.register_job(job, dep)

	def register_job(self, job, dep):
		print("Register Job Name:" + job + "\tDep:" + str(dep))

	def __repr__(self):
		return str(self.__dict__)


class CommandChecker(object):
	"""
	This class checks if programs specified in a
	pipeline config file (under "tools") exist and are callable.
	"""
	def __init__(self, config):
		import yaml

		self.config = yaml.load(open(config, 'r'))

		# Check if ALL returned elements are True
		if not all(map(self.check_command, self.config["tools"].items())):
			raise BaseException("Config file contains non-callable tools.")

	@staticmethod
	def check_command(name, command):
		"""
		Check if command can be called.

		:param command: Name of command to be called.
		:type command: str
		"""
		import os

		# Use `command` to see if command is callable, store exit code
		code = os.system("command -v {0} >/dev/null 2>&1 || {{ exit 1; }}".format(command))

		# If exit code is not 0, report which command failed and return False, else return True
		if code != 0:
			print("Command '{0}' is not callable: {1}".format(name, command))
			return False
		else:
			return True
