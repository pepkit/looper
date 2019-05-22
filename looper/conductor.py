""" Pipeline job submission orchestration """

import logging
import os
import re
import subprocess
import time

from .const import *
from .exceptions import JobSubmissionException
from .utils import \
    create_looper_args_text, grab_project_data, fetch_sample_flags

from .sample import Sample
from peppy import VALID_READ_TYPES


__author__ = "Vince Reuter"
__email__ = "vreuter@virginia.edu"


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

    def __init__(self, pipeline_key, pipeline_interface, cmd_base, prj,
                 dry_run=False, delay=0, sample_subtype=None, extra_args=None,
                 ignore_flags=False, compute_variables=None,
                 max_cmds=None, max_size=None, automatic=True):
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
        :param str cmd_base: Base of each command for each job, e.g. the
            script path and command-line options/flags that are constant
            across samples.
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
        """

        super(SubmissionConductor, self).__init__()

        self.pl_key = pipeline_key
        self.pl_iface = pipeline_interface
        self.pl_name = pipeline_interface.get_pipeline_name(pipeline_key)
        self.cmd_base = cmd_base.rstrip(" ")

        self.dry_run = dry_run
        self.delay = float(delay)

        self.sample_subtype = sample_subtype or Sample
        self.compute_variables = compute_variables
        self.extra_pipe_args = extra_args or []
        #self.extra_args_text = (extra_args and " ".join(extra_args)) or ""
        self.uses_looper_args = \
                pipeline_interface.uses_looper_args(pipeline_key)
        self.ignore_flags = ignore_flags
        self.prj = prj
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

        self._failed_sample_names = []
        self._pool = []
        self._curr_size = 0
        self._reset_curr_skips()
        self._skipped_sample_pools = []
        self._num_good_job_submissions = 0
        self._num_total_job_submissions = 0
        self._num_cmds_submitted = 0

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

    def add_sample(self, sample, sample_subtype=Sample, rerun=False):
        """
        Add a sample for submission to this conductor.

        :param peppy.Sample sample: sample to be included with this conductor's
            currently growing collection of command submissions
        :param type sample_subtype: specific subtype associated
            with this new sample; this is used to tailor-make the sample
            instance as required by its protocol/pipeline and supported
            by the pipeline interface.
        :param bool rerun: whether the given sample is being rerun rather than
            run for the first time
        :return bool: Indication of whether the given sample was added to
            the current 'pool.'
        :raise TypeError: If sample subtype is provided but does not extend
            the base Sample class, raise a TypeError.
        """

        _LOGGER.debug("Adding {} to conductor for {}".format(sample.name, self.pl_name))
        
        if not issubclass(sample_subtype, Sample):
            raise TypeError("If provided, sample_subtype must extend {}".
                            format(Sample.__name__))

        flag_files = fetch_sample_flags(self.prj, sample, self.pl_name)

        use_this_sample = True

        if flag_files:
            if not self.ignore_flags:
                use_this_sample = False
            # But rescue the sample in case rerun/failed passes
            failed_flag = any("failed" in x for x in flag_files)
            if rerun and failed_flag:
                _LOGGER.info("> Re-running failed sample '%s' for pipeline '%s'.",
                     sample.name, self.pl_name)
                use_this_sample = True
            if not use_this_sample:
                _LOGGER.info("> Skipping sample '%s' for pipeline '%s', "
                             "%s found: %s", sample.name, self.pl_name,
                             "flags" if len(flag_files) > 1 else "flag",
                             ", ".join(['{}'.format(
                                 os.path.basename(fp)) for fp in flag_files]))
                _LOGGER.debug("NO SUBMISSION")

        if type(sample) != sample_subtype:
            _LOGGER.debug(
                "Building {} from {}".format(sample_subtype, type(sample)))
            sample = sample_subtype(sample.to_dict())
        else:
            _LOGGER.debug(
                "{} is already of type {}".format(sample.name, sample_subtype))
        _LOGGER.debug("Created %s instance: '%s'",
                      sample_subtype.__name__, sample.name)
        sample.prj = grab_project_data(self.prj)

        skip_reasons = []
        
        try:
            # Add pipeline-specific attributes.
            sample.set_pipeline_attributes(
                    self.pl_iface, pipeline_name=self.pl_key)
        except AttributeError:
            # TODO: inform about WHICH missing attributes?
            fail_message = "Pipeline required attribute missing"
            _LOGGER.warning("> Not submitted: %s", fail_message)
            use_this_sample and skip_reasons.append(fail_message)
            
        # Check for any missing requirements before submitting.
        _LOGGER.debug("Determining missing requirements")
        error_type, missing_reqs_general, missing_reqs_specific = \
            sample.determine_missing_requirements()
        if missing_reqs_general:
            missing_reqs_msg = "{}: {}".format(
                missing_reqs_general, missing_reqs_specific)
            if self.prj.permissive:
                _LOGGER.warning("> Not submitted: %s", missing_reqs_msg)
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

        # Append arguments for this pipeline
        # Sample-level arguments are handled by the pipeline interface.
        try:
            argstring = self.pl_iface.get_arg_string(
                pipeline_name=self.pl_key, sample=sample,
                submission_folder_path=self.prj.submission_folder)
        except AttributeError:
            argstring = None
            # TODO: inform about which missing attribute.
            fail_message = "Required attribute missing " \
                           "for pipeline arguments string"
            _LOGGER.warning("> Not submitted: %s", fail_message)
            use_this_sample and skip_reasons.append(fail_message)
            use_this_sample = False

        this_sample_size = float(sample.input_file_size)

        if use_this_sample and not skip_reasons:
            assert argstring is not None, \
                "Failed to create argstring for sample: {}".format(sample.name)
            self._pool.append((sample, argstring))
            self._curr_size += this_sample_size
            if self.automatic and self._is_full(self._pool, self._curr_size):
                self.submit()
        elif argstring is not None:
            self._curr_skip_size += this_sample_size
            self._curr_skip_pool.append((sample, argstring))
            if self._is_full(self._curr_skip_pool, self._curr_skip_size):
                self._skipped_sample_pools.append(
                    (self._curr_skip_pool, self._curr_skip_size))
                self._reset_curr_skips()

        return skip_reasons

    def _get_settings_looptext_prjtext(self, size):
        """
        Determine settings, looper argstring, and project argstring.

        :param int | float size: size of submission, used to select the proper
            resource package from the pipeline interface
        :return dict, str, str: collection of settings, looper argstring, and
            project argstring
        """
        settings = self.pl_iface.choose_resource_package(self.pl_key, size)
        settings.update(self.compute_variables or {})
        if self.uses_looper_args:
            settings.setdefault("cores", 1)
            looper_argtext = \
                create_looper_args_text(self.pl_key, settings, self.prj)
        else:
            looper_argtext = ""
        prj_argtext = self.prj.get_arg_string(
            self.pl_key, {x for x in self.extra_pipe_args if x.startswith("-")})
        return settings, looper_argtext, prj_argtext

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

        elif force or self._is_full(self._pool, self._curr_size):
            # Ensure that each sample is individually represented on disk,
            # specific to subtype as applicable (should just be a single
            # subtype for each submission conductor, but some may just be
            # the base Sample while others are the single valid subtype.)
            for s, _ in self._pool:
                if type(s) is Sample:
                    exp_fname = "{}.yaml".format(s.name)
                    exp_fpath = os.path.join(
                            self.prj.submission_folder, exp_fname)
                    if not os.path.isfile(exp_fpath):
                        _LOGGER.warning("Missing %s file will be created: '%s'",
                                     Sample.__name__, exp_fpath)
                else:
                    subtype_name = s.__class__.__name__
                    _LOGGER.debug("Writing %s representation to disk: '%s'",
                                  subtype_name, s.name)
                    s.to_yaml(subs_folder_path=self.prj.submission_folder)

            script = self.write_script(self._pool, self._curr_size)

            self._num_total_job_submissions += 1

            # Determine whether to actually do the submission.
            _LOGGER.info("Job script (n=%d; %.2f Gb): %s",
                         len(self._pool), self._curr_size, script)
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
                    self._failed_sample_names.extend(
                            [s.name for s in self._samples])
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
        return [s for s, _ in self._pool]

    def _jobname(self, pool):
        """ Create the name for a job submission. """
        if 1 == self.max_cmds:
            assert 1 == len(pool), \
                "If there's a single-command limit on job submission, jobname " \
                "must be determined with exactly one sample in the pool, but " \
                "there is/are {}.".format(len(pool))
            sample, _ = pool[0]
            name = sample.name
        else:
            # Note the order in which the increment of submission count and
            # the call to this function can influence naming. Make the jobname
            # generation call (this method) before incrementing the
            # submission counter, but add 1 to the index so that we get a
            # name concordant with 1-based, not 0-based indexing.
            name = "lump{}".format(self._num_total_job_submissions + 1)
        return "{}_{}".format(self.pl_key, name)

    def _cmd_text_extra(self, size):
        _LOGGER.debug("Determining submission settings for pool of size %.2f Gb", size)
        settings, ltext, ptext = self._get_settings_looptext_prjtext(size)
        from_cli = " ".join(self.extra_pipe_args) if self.extra_pipe_args else ""
        return settings, " ".join([t for t in [ptext, ltext, from_cli] if t])

    def write_script(self, pool, size):
        """
        Create the script for job submission.

        :param Iterable[(peppy.Sample, str)] pool: collection of pairs in which
            first component is a sample instance and second is command/argstring
        :param float size: cumulative size of the given pool
        :return str: Path to the job submission script created.
        """

        template_values, extra_parts_text = self._cmd_text_extra(size)

        def get_final_cmd(c):
            return "{} {}".format(c, extra_parts_text) if extra_parts_text else c

        def get_base_cmd(argstr):
            b = self.cmd_base
            return (argstr and "{} {}".format(b, argstr.strip(" "))) or b

        # Create the individual commands to lump into this job.
        commands = [get_final_cmd(get_base_cmd(argstring)) for _, argstring in pool]

        jobname = self._jobname(pool)
        submission_base = os.path.join(
                self.prj.submission_folder, jobname)
        logfile = submission_base + ".log"
        template_values["JOBNAME"] = jobname
        template_values["CODE"] = "\n".join(commands)
        template_values["LOGFILE"] = logfile
        submission_script = submission_base + ".sub"

        _LOGGER.debug("> Creating submission script; command count: %d", len(commands))
        return self.prj.dcc.write_script(submission_script, template_values)

    def write_skipped_sample_scripts(self):
        """ For any sample skipped during initial processing, write submission script. """
        return [self.write_script(pool, size) for pool, size in self._skipped_sample_pools]

    def _reset_pool(self):
        """ Reset the state of the pool of samples """
        self._pool = []
        self._curr_size = 0

    def _reset_curr_skips(self):
        self._curr_skip_pool = []
        self._curr_skip_size = 0
