""" Pipeline job submission orchestration """

import logging
import os
import re
import subprocess
import time
from jinja2.exceptions import UndefinedError

from attmap import AttMap
from eido import read_schema
from peppy.const import CONFIG_KEY

from .processed_project import populate_sample_paths
from .const import *
from .exceptions import JobSubmissionException
from .pipeline_interface import PL_KEY
from .utils import grab_project_data, fetch_sample_flags, \
    jinja_render_cmd_strictly
from .sample import Sample

_LOGGER = logging.getLogger(__name__)


class SubmissionConductor(object):
    """
    Collects and then submits pipeline jobs.

    This class holds a 'pool' of commands to submit as a single cluster job.
    Eager to submit a job, each instance's collection of commands expands until
    it reaches the 'pool' has been filled, and it's therefore time to submit the
    job. The pool fills as soon as a fill criteria has been reached, which can
    be either total input file size or the number of individual commands.

    """

    def __init__(self, pipeline_key, pipeline_interface, prj, dry_run=False,
                 delay=0, sample_subtype=None, extra_args=None,
                 ignore_flags=False, compute_variables=None, max_cmds=None,
                 max_size=None, automatic=True, collate=False):
        """
        Create a job submission manager.

        The most critical inputs are the pipeline interface and the pipeline
        key, which together determine which provide critical pipeline
        information like resource allocation packages and which pipeline will
        be overseen by this instance, respectively.

        :param str pipeline_key: 'Hook' into the pipeline interface, and the
            datum that determines which pipeline this manager will oversee.
        :param PipelineInterface pipeline_interface: Collection of important
            data for one or more pipelines, like resource allocation packages
            and option/argument specifications
        :param prj: Project with which each sample being considered is
            associated (what generated each sample)
        :param bool dry_run: Whether this is a dry run and thus everything
            but the actual job submission should be done.
        :param float delay: Time (in seconds) to wait before submitting a job
            once it's ready
        :param type sample_subtype: Extension of base Sample, for particular
            pipeline for which submissions will be managed by this instance
        :param list extra_args: Additional arguments to add (positionally) to
            each command within each job generated
        :param bool ignore_flags: Whether to ignore flag files present in
            the sample folder for each sample considered for submission
        :param str compute_variables: A dict with variables that will be made
            available to the compute package. For example, this should include
            the name of the cluster partition to which job or jobs will be submitted
        :param int | NoneType max_cmds: Upper bound on number of commands to
            include in a single job script.
        :param int | float | NoneType max_size: Upper bound on total file
            size of inputs used by the commands lumped into single job script.
        :param bool automatic: Whether the submission should be automatic once
            the pool reaches capacity.
        :param bool collate: Whether a collate job is to be submitted (runs on
            the project level, rather that on the sample level)
        """

        super(SubmissionConductor, self).__init__()
        self.collate = collate
        self.pl_key = pipeline_key
        self.pl_iface = pipeline_interface
        self.pl_name = \
            pipeline_interface.get_pipeline_name(self.pl_key, self.collate)
        self.prj = prj
        self.compute_variables = compute_variables
        self.extra_pipe_args = extra_args or []
        self.ignore_flags = ignore_flags

        self.dry_run = dry_run
        self.delay = float(delay)
        self._num_good_job_submissions = 0
        self._num_total_job_submissions = 0
        self._num_cmds_submitted = 0
        self._curr_size = 0
        self._failed_sample_names = []

        if not self.collate:
            self.sample_subtype = sample_subtype or Sample
            if not issubclass(self.sample_subtype, Sample):
                raise TypeError("Sample type must extend {}; got {}".format(
                    Sample.__name__, type(self.sample_subtype).__name__))

            self.automatic = automatic
            if max_cmds is None and max_size is None:
                self.max_cmds = 1
            elif (max_cmds is not None and max_cmds < 1) or \
                    (max_size is not None and max_size < 0):
                raise ValueError(
                        "If specified, max per-job command count must positive, "
                        "and max per-job total file size must be nonnegative")
            else:
                self.max_cmds = max_cmds
            self.max_size = max_size or float("inf")

            self._pool = []
            self._reset_curr_skips()
            self._skipped_sample_pools = []

    @property
    def failed_samples(self):
        return self._failed_sample_names

    @property
    def num_cmd_submissions(self):
        """
        Return the number of commands that this conductor has submitted.
        
        :return int: Number of commands submitted so far.
        """
        return self._num_cmds_submitted

    @property
    def num_job_submissions(self):
        """
        Return the number of jobs that this conductor has submitted.
        
        :return int: Number of jobs submitted so far.
        """
        return self._num_good_job_submissions

    def add_sample(self, sample, rerun=False):
        """
        Add a sample for submission to this conductor.

        :param peppy.Sample sample: sample to be included with this conductor's
            currently growing collection of command submissions
        :param bool rerun: whether the given sample is being rerun rather than
            run for the first time
        :return bool: Indication of whether the given sample was added to
            the current 'pool.'
        :raise TypeError: If sample subtype is provided but does not extend
            the base Sample class, raise a TypeError.
        """
        _LOGGER.debug("Adding {} to conductor for {}".
                      format(sample.sample_name, self.pl_name))
        flag_files = fetch_sample_flags(self.prj, sample, self.pl_name)
        use_this_sample = True

        if flag_files:
            if not self.ignore_flags:
                use_this_sample = False
            # But rescue the sample in case rerun/failed passes
            failed_flag = any("failed" in x for x in flag_files)
            if rerun and failed_flag:
                _LOGGER.info(
                    "> Re-running failed sample '%s' for pipeline '%s'.",
                    sample.sample_name, self.pl_name)
                use_this_sample = True
            if not use_this_sample:
                _LOGGER.info("> Skipping sample '%s' for pipeline '%s', "
                             "%s found: %s", sample.sample_name, self.pl_name,
                             "flags" if len(flag_files) > 1 else "flag",
                             ", ".join(['{}'.format(
                                 os.path.basename(fp)) for fp in flag_files]))
                _LOGGER.debug("NO SUBMISSION")

        if type(sample) != self.sample_subtype:
            _LOGGER.debug(
                "Building {} from {}".format(self.sample_subtype, type(sample)))
            sample = self.sample_subtype(sample.to_dict())
        else:
            _LOGGER.debug(
                "{} is already of type {}".format(sample.sample_name,
                                                  self.sample_subtype))
        _LOGGER.debug("Created %s instance: '%s'",
                      self.sample_subtype.__name__, sample.sample_name)
        sample.prj = grab_project_data(self.prj)

        skip_reasons = []
        sample.setdefault("input_file_size", 0)
        # Check for any missing requirements before submitting.
        _LOGGER.debug("Determining missing requirements")
        schema_source = self.pl_iface.get_pipeline_schema(self.pl_key)
        if schema_source:
            error_type, missing_reqs_general, missing_reqs_specific = \
                sample.validate_inputs(schema=read_schema(schema_source))
            if missing_reqs_general:
                missing_reqs_msg = "{}: {}".format(
                    missing_reqs_general, missing_reqs_specific)
                if self.prj.permissive:
                    _LOGGER.warning(NOT_SUB_MSG.format(missing_reqs_msg))
                else:
                    raise error_type(missing_reqs_msg)
                use_this_sample and skip_reasons.append(missing_reqs_general)

        # Check if single_or_paired value is recognized.
        if hasattr(sample, "read_type"):
            # Drop "-end", "_end", or "end" from end of the column value.
            rtype = re.sub('[_\\-]?end$', '',
                           str(sample.read_type))
            sample.read_type = rtype.lower()
            if sample.read_type not in VALID_READ_TYPES:
                _LOGGER.debug(
                    "Invalid read type: '{}'".format(sample.read_type))
                use_this_sample and skip_reasons.append(
                    "read_type must be in {}".format(VALID_READ_TYPES))
        this_sample_size = float(sample.input_file_size)

        if _use_sample(use_this_sample, skip_reasons):
            self._pool.append(sample)
            self._curr_size += this_sample_size
            if self.automatic and self._is_full(self._pool, self._curr_size):
                self.submit()
        else:
            self._curr_skip_size += this_sample_size
            self._curr_skip_pool.append(sample)
            if self._is_full(self._curr_skip_pool, self._curr_skip_size):
                self._skipped_sample_pools.append((self._curr_skip_pool,
                                                   self._curr_skip_size))
                self._reset_curr_skips()

        return skip_reasons

    def submit(self, force=False):
        """
        Submit one or more commands as a job.
        
        This call will submit the commands corresponding to the current pool 
        of samples if and only if the argument to 'force' evaluates to a 
        true value, or the pool of samples is full.
        
        :param bool force: Whether submission should be done/simulated even
            if this conductor's pool isn't full.
        :return bool: Whether a job was submitted (or would've been if
            not for dry run)
        """
        if not self._pool:
            _LOGGER.debug("No submission (no pooled samples): %s", self.pl_name)
            submitted = False
        elif self.collate or force or self._is_full(self._pool, self._curr_size):
            if not self.collate:
                for s in self._pool:
                    if not _is_base_sample(s):
                        subtype_name = s.__class__.__name__
                        _LOGGER.debug("Writing %s representation to disk: '%s'",
                                      subtype_name, s.sample_name)
                    schemas = self.prj.get_schemas(s.protocol, OUTPUT_SCHEMA_KEY)
                    [populate_sample_paths(s, read_schema(schema))
                     for schema in schemas]
                    yaml_path = \
                        s.to_yaml(subs_folder_path=self.prj.submission_folder)
                    _LOGGER.debug("Wrote sample YAML: {}".format(yaml_path))

            script = self.write_script(self._pool, self._curr_size)

            self._num_total_job_submissions += 1

            # Determine whether to actually do the submission.
            _LOGGER.info("Job script (n={0}; {1:.2f}Gb): {2}".
                         format(len(self._pool), self._curr_size, script))
            if self.dry_run:
                _LOGGER.info("Dry run, not submitted")
            else:
                sub_cmd = self.prj.dcc.compute.submission_command
                submission_command = "{} {}".format(sub_cmd, script)
                # Capture submission command return value so that we can
                # intercept and report basic submission failures; #167
                try:
                    subprocess.check_call(submission_command, shell=True)
                except subprocess.CalledProcessError:
                    fails = "" if self.collate \
                        else [s.sample_name for s in self._samples]
                    self._failed_sample_names.extend(fails)
                    self._reset_pool()
                    raise JobSubmissionException(sub_cmd, script)
                time.sleep(self.delay)

            # Update the job and command submission tallies.
            _LOGGER.debug("SUBMITTED")
            submitted = True
            self._num_good_job_submissions += 1
            self._num_cmds_submitted += len(self._pool)
            self._reset_pool()

        else:
            _LOGGER.debug("No submission (pool is not full and submission "
                          "was not forced): %s", self.pl_name)
            submitted = False

        return submitted

    def _is_full(self, pool, size):
        """
        Determine whether it's time to submit a job for the pool of commands.

        Instances of this class maintain a sort of 'pool' of commands that
        expands as each new command is added, until a time that it's deemed
        'full' and th

        :return bool: Whether this conductor's pool of commands is 'full' and
            ready for submission, as determined by its parameterization
        """
        return self.max_cmds == len(pool) or size >= self.max_size

    @property
    def _samples(self):
        """
        Return a collection of pooled samples.

        :return Iterable[str]: collection of samples currently in the active
            pool for this submission conductor
        """
        return [s for s in self._pool]

    def _sample_lump_name(self, pool):
        """ Determine how to refer to the 'sample' for this submission. """
        if self.collate:
            return "collate"
        if 1 == self.max_cmds:
            assert 1 == len(pool), \
                "If there's a single-command limit on job submission, jobname" \
                " must be determined with exactly one sample in the pool," \
                " but there is/are {}.".format(len(pool))
            sample = pool[0]
            return sample.sample_name
        else:
            # Note the order in which the increment of submission count and
            # the call to this function can influence naming. Make the jobname
            # generation call (this method) before incrementing the
            # submission counter, but add 1 to the index so that we get a
            # name concordant with 1-based, not 0-based indexing.
            return "lump{}".format(self._num_total_job_submissions + 1)

    def _jobname(self, pool):
        """ Create the name for a job submission. """
        return "{}_{}".format(self.pl_key, self._sample_lump_name(pool))

    def _set_looper_namespace(self, pool, size):
        """
        Compile a dictionary of looper/submission related settings for use in
        the command templates and in submission script creation
        in divvy (via adapters). Accessible via: {looper.attrname}

        :param Iterable[peppy.Sample] pool: collection of sample instances
        :param float size: cumulative size of the given pool
        :return dict: looper/submission related settings
        """
        settings = AttMap()
        settings.pep_config = self.prj.config_file
        settings.output_folder = self.prj.results_folder
        settings.sample_output_folder = \
            os.path.join(self.prj.results_folder, self._sample_lump_name(pool))
        settings.job_name = self._jobname(pool)
        settings.total_input_size = size
        settings.log_file = \
            os.path.join(self.prj.submission_folder, settings.job_name) + ".log"
        if hasattr(self.prj, "pipeline_config"):
            # Index with 'pl_key' instead of 'pipeline'
            # because we don't care about parameters here.
            if hasattr(self.prj.pipeline_config, self.pl_key):
                # First priority: pipeline config in project config
                pl_config_file = getattr(self.prj.pipeline_config, self.pl_key)
                # Make sure it's a file (it could be provided as null.)
                if pl_config_file:
                    if not os.path.isfile(pl_config_file):
                        _LOGGER.error("Pipeline config file specified "
                                      "but not found: %s", pl_config_file)
                        raise IOError(pl_config_file)
                    _LOGGER.info("Found config file: %s", pl_config_file)
                    # Append arg for config file if found
                    settings.pipeline_config = pl_config_file
        return settings

    def write_script(self, pool, size):
        """
        Create the script for job submission.

        :param Iterable[peppy.Sample] pool: collection of sample instances
        :param float size: cumulative size of the given pool
        :return str: Path to the job submission script created.
        """
        # looper settings determination
        if self.collate:
            pool = [None]
        looper = self._set_looper_namespace(pool, size)
        extra_parts_text = " ".join(self.extra_pipe_args) \
            if self.extra_pipe_args else ""
        commands = []
        pkey = COLLATORS_KEY if self.collate else PL_KEY
        namespaces = dict(project=self.prj[CONFIG_KEY],
                          looper=looper,
                          pipeline=self.pl_iface[pkey][self.pl_key])

        templ = self.pl_iface[pkey][self.pl_key]["command_template"]
        for sample in pool:
            # cascading compute settings determination:
            # divcfg < pipeline interface < config < CLI
            cli = self.compute_variables or {}  # CLI
            if sample:
                namespaces.update({"sample": sample})
            res_pkg = self.pl_iface.choose_resource_package(
                self.pl_key, namespaces, size or 0, self.collate)  # piface < config
            res_pkg.update(cli)
            self.prj.dcc.compute.update(res_pkg)  # divcfg
            namespaces.update({"compute": self.prj.dcc.compute})
            try:
                argstring = jinja_render_cmd_strictly(cmd_template=templ,
                                                      namespaces=namespaces)
            except UndefinedError as jinja_exception:
                _LOGGER.warning(NOT_SUB_MSG.format(str(jinja_exception)))
            except KeyError as e:
                exc = "pipeline interface is missing {} section".format(str(e))
                _LOGGER.warning(NOT_SUB_MSG.format(exc))
            else:
                commands.append("{} {}".format(argstring, extra_parts_text))
        looper.command = "\n".join(commands)
        _LOGGER.debug("sample namespace:\n{}".format(sample))
        _LOGGER.debug("project namespace:\n{}".format(self.prj[CONFIG_KEY]))
        _LOGGER.debug("pipeline namespace:\n{}".
                      format(self.pl_iface[pkey][self.pl_key]))
        _LOGGER.debug("compute namespace:\n{}".format(self.prj.dcc.compute))
        _LOGGER.debug("looper namespace:\n{}".format(looper))
        subm_base = os.path.join(self.prj.submission_folder, looper.job_name)
        return self.prj.dcc.write_script(output_path=subm_base + ".sub",
                                         extra_vars=[{"looper": looper}])

    def write_skipped_sample_scripts(self):
        """
        For any sample skipped during initial processingwrite submission script
        """
        if self._curr_skip_pool:
            # move any hanging samples from current skip pool to the main pool
            self._skipped_sample_pools.append(
                (self._curr_skip_pool, self._curr_skip_size)
            )
        if self._skipped_sample_pools:
            _LOGGER.info("Writing submission scripts for {} skipped samples".
                          format(len(self._skipped_sample_pools)))
            [self.write_script(pool, size)
             for pool, size in self._skipped_sample_pools]

    def _reset_pool(self):
        """ Reset the state of the pool of samples """
        self._pool = []
        self._curr_size = 0

    def _reset_curr_skips(self):
        self._curr_skip_pool = []
        self._curr_skip_size = 0


def _check_argstring(argstring, sample_name):
    assert argstring is not None, \
        "Failed to create argstring for sample: {}".format(sample_name)


def _is_base_sample(s):
    return type(s) is Sample


def _use_sample(flag, skips):
    return flag and not skips
