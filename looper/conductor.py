"""Pipeline job submission orchestration"""

import importlib
import logging
import os
import subprocess
import signal
import psutil
import sys
import time
import yaml
from math import ceil
from json import loads
from subprocess import check_output
from typing import *

from eido import read_schema, get_input_files_size
from eido.const import INPUT_FILE_SIZE_KEY, MISSING_KEY
from jinja2.exceptions import UndefinedError

from peppy.const import CONFIG_KEY, SAMPLE_YAML_EXT
from peppy.exceptions import RemoteYAMLError
from pipestat import PipestatError
from ubiquerg import expandpath
from yaml import dump
from yacman import FutureYAMLConfigManager as YAMLConfigManager

from .const import *
from .exceptions import JobSubmissionException
from .processed_project import populate_sample_paths
from .utils import (
    fetch_sample_flags,
    jinja_render_template_strictly,
    expand_nested_var_templates,
)
from .const import PipelineLevel


_LOGGER = logging.getLogger(__name__)


def _get_yaml_path(namespaces, template_key, default_name_appendix="", filename=None):
    """
    Get a path to a YAML file for the sample.

    :param dict[dict]] namespaces: namespaces mapping
    :param str template_key: the name of the key in 'var_templates' piface
        section that points to a template to render to get the
        user-provided target YAML path
    :param str default_name_appendix: a string to append to insert in target
        YAML file name: '{sample.sample_name}<>.yaml'
    :param str filename: A filename without folders. If not provided, a
        default name of sample_name.yaml will be used.
    :return str: sample YAML file path
    """
    if (
        VAR_TEMPL_KEY in namespaces["pipeline"]
        and template_key in namespaces["pipeline"][VAR_TEMPL_KEY]
    ):
        _LOGGER.debug(f"Sample namespace: {namespaces['sample']}")
        x = jinja_render_template_strictly("{sample.sample_name}", namespaces)
        _LOGGER.debug(f"x: {x}")
        cpy = namespaces["pipeline"][VAR_TEMPL_KEY][template_key]
        _LOGGER.debug(f"cpy: {cpy}")
        path = expandpath(jinja_render_template_strictly(cpy, namespaces))
        _LOGGER.debug(f"path: {path}")

        if not path.endswith(SAMPLE_YAML_EXT) and not filename:
            raise ValueError(
                f"{template_key} is not a valid target YAML file path. "
                f"It needs to end with: {' or '.join(SAMPLE_YAML_EXT)}"
            )
        final_path = os.path.join(path, filename) if filename else path
        if not os.path.exists(os.path.dirname(final_path)):
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
    else:
        # default YAML location
        f = (
            filename
            or f"{namespaces['sample'][namespaces['sample']['_project'].sample_table_index]}"
            f"{default_name_appendix}"
            f"{SAMPLE_YAML_EXT[0]}"
        )
        default = os.path.join(namespaces["looper"][OUTDIR_KEY], "submission")
        final_path = os.path.join(default, f)
        if not os.path.exists(default):
            os.makedirs(default, exist_ok=True)

    _LOGGER.debug(f"Writing sample yaml: {final_path}")
    return final_path


def write_pipestat_config(looper_pipestat_config_path, pipestat_config_dict):
    """
    This writes a combined configuration file to be passed to a PipestatManager.
    :param str looper_pipestat_config_path: path to the created pipestat configuration file
    :param dict pipestat_config_dict: the dict containing key value pairs to be written to the pipestat configutation
    return bool
    """

    if not os.path.exists(os.path.dirname(looper_pipestat_config_path)):
        try:
            os.makedirs(os.path.dirname(looper_pipestat_config_path))
        except FileExistsError:
            pass

    with open(looper_pipestat_config_path, "w") as f:
        yaml.dump(pipestat_config_dict, f)
    _LOGGER.debug(
        msg=f"Initialized pipestat config file: {looper_pipestat_config_path}"
    )

    return True


def write_submission_yaml(namespaces):
    """
    Save all namespaces to YAML.

    :param dict namespaces: variable namespaces dict
    :return dict: sample namespace dict
    """
    path = _get_yaml_path(namespaces, SAMPLE_CWL_YAML_PATH_KEY, "_submission")
    my_namespaces = {}
    for namespace, values in namespaces.items():
        my_namespaces.update({str(namespace): dict(values)})
    with open(path, "w") as yamlfile:
        dump(my_namespaces, yamlfile)
    return my_namespaces


class SubmissionConductor(object):
    """
    Collects and then submits pipeline jobs.

    This class holds a 'pool' of commands to submit as a single cluster job.
    Eager to submit a job, each instance's collection of commands expands until
    it reaches the 'pool' has been filled, and it's therefore time to submit the
    job. The pool fills as soon as a fill criteria has been reached, which can
    be either total input file size or the number of individual commands.

    """

    def __init__(
        self,
        pipeline_interface,
        prj,
        delay=0,
        extra_args=None,
        extra_args_override=None,
        ignore_flags=False,
        compute_variables=None,
        max_cmds=None,
        max_size=None,
        max_jobs=None,
        automatic=True,
        collate=False,
    ):
        """
        Create a job submission manager.

        The most critical inputs are the pipeline interface and the pipeline
        key, which together determine which provide critical pipeline
        information like resource allocation packages and which pipeline will
        be overseen by this instance, respectively.

        :param PipelineInterface pipeline_interface: Collection of important
            data for one or more pipelines, like resource allocation packages
            and option/argument specifications
        :param prj: Project with which each sample being considered is
            associated (what generated each sample)
        :param float delay: Time (in seconds) to wait before submitting a job
            once it's ready
        :param str extra_args: string to pass to each job generated,
            for example additional pipeline arguments
        :param str extra_args_override: string to pass to each job generated,
            for example additional pipeline arguments. This deactivates the
            'extra' functionality that appends strings defined in
            Sample.command_extra and Project.looper.command_extra to the
            command template.
        :param bool ignore_flags: Whether to ignore flag files present in
            the sample folder for each sample considered for submission
        :param dict[str] compute_variables: A dict with variables that will be made
            available to the compute package. For example, this should include
            the name of the cluster partition to which job or jobs will be submitted
        :param int | NoneType max_cmds: Upper bound on number of commands to
            include in a single job script.
        :param int | float | NoneType max_size: Upper bound on total file
            size of inputs used by the commands lumped into single job script.
        :param int | float | NoneType max_jobs: Upper bound on total number of jobs to
            group samples for submission.
        :param bool automatic: Whether the submission should be automatic once
            the pool reaches capacity.
        :param bool collate: Whether a collate job is to be submitted (runs on
            the project level, rather that on the sample level)
        """
        super(SubmissionConductor, self).__init__()

        self.collate = collate
        self.section_key = PROJECT_PL_KEY if self.collate else SAMPLE_PL_KEY
        self.pipeline_interface_type = (
            "project_interface" if self.collate else "sample_interface"
        )
        self.pl_iface = pipeline_interface
        self.pl_name = self.pl_iface.pipeline_name
        self.prj = prj
        self.compute_variables = compute_variables
        self.extra_pipe_args = extra_args
        self.override_extra = False
        if extra_args_override:
            self.extra_pipe_args = extra_args_override
            self.override_extra = True
        self.ignore_flags = ignore_flags

        self.dry_run = self.prj.dry_run
        self.delay = float(delay)
        self._num_good_job_submissions = 0
        self._num_total_job_submissions = 0
        self._num_cmds_submitted = 0
        self._curr_size = 0
        self._failed_sample_names = []
        self._curr_skip_pool = []
        self.process_id = None  # this is used for currently submitted subprocess

        if self.extra_pipe_args:
            _LOGGER.debug(
                "String appended to every pipeline command: "
                "{}".format(self.extra_pipe_args)
            )

        if max_jobs:
            if max_jobs == 0 or max_jobs < 0:
                raise ValueError(
                    "If specified, max job command count must be a positive integer, greater than zero."
                )

            num_samples = len(self.prj.samples)
            samples_per_job = num_samples / max_jobs
            max_cmds = ceil(samples_per_job)

        if not self.collate:
            self.automatic = automatic
            if max_cmds is None and max_size is None:
                self.max_cmds = 1
            elif (max_cmds is not None and max_cmds < 1) or (
                max_size is not None and max_size < 0
            ):
                raise ValueError(
                    "If specified, max per-job command count must positive, "
                    "and max per-job total file size must be nonnegative"
                )
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

    def is_project_submittable(self, force=False):
        """
        Check whether the current project has been already submitted

        :param bool frorce: whether to force the project submission (ignore status/flags)
        """
        psms = {}
        if self.prj.pipestat_configured_project:
            for piface in self.prj.project_pipeline_interfaces:
                if piface.psm.pipeline_type == PipelineLevel.PROJECT.value:
                    psms[piface.psm.pipeline_name] = piface.psm
            psm = psms[self.pl_name]
            status = psm.get_status()
            if not force and status is not None:
                _LOGGER.info(f"> Skipping project. Determined status: {status}")
                return False
        return True

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
        _LOGGER.debug(
            "Adding {} to conductor for {} to {}run".format(
                sample.sample_name, self.pl_name, "re" if rerun else ""
            )
        )
        if self.prj.pipestat_configured:
            sample_statuses = self.pl_iface.psm.get_status(
                record_identifier=sample.sample_name
            )
            if sample_statuses == "failed" and rerun is True:
                self.pl_iface.psm.set_status(
                    record_identifier=sample.sample_name, status_identifier="waiting"
                )
                sample_statuses = "waiting"
            sample_statuses = [sample_statuses] if sample_statuses else []
        else:
            sample_statuses = fetch_sample_flags(self.prj, sample, self.pl_name)

        use_this_sample = True  # default to running this sample
        msg = None
        if rerun and sample_statuses == []:
            msg = f"> Skipping sample because rerun requested, but no failed or waiting flag found."
            use_this_sample = False
        if sample_statuses:
            status_str = ", ".join(sample_statuses)
            failed_flag = any("failed" in x for x in sample_statuses)
            waiting_flag = any("waiting" in x for x in sample_statuses)
            if self.ignore_flags:
                msg = f"> Found existing status: {status_str}. Ignoring."
            else:  # this pipeline already has a status
                msg = f"> Found existing status: {status_str}. Skipping sample."
                if failed_flag and not rerun:
                    msg += " Use rerun to ignore failed status."  # help guidance
                use_this_sample = False
            if rerun:
                # Rescue the sample if rerun requested, and failed flag is found
                if failed_flag or waiting_flag:
                    msg = f"> Re-running sample. Status: {status_str}"
                    use_this_sample = True
                else:
                    msg = f"> Skipping sample because rerun requested, but no failed or waiting flag found. Status: {status_str}"
                    use_this_sample = False
        if msg:
            _LOGGER.info(msg)

        skip_reasons = []
        validation = {}
        validation.setdefault(INPUT_FILE_SIZE_KEY, 0)
        # Check for any missing requirements before submitting.
        _LOGGER.debug("Determining missing requirements")
        schema_source = self.pl_iface.get_pipeline_schemas()
        if schema_source and self.prj.file_checks:
            try:
                validation = get_input_files_size(sample, read_schema(schema_source))
            except RemoteYAMLError:
                _LOGGER.warn(
                    "Could not read remote schema. Skipping inputs validation."
                )
            else:
                if validation[MISSING_KEY]:
                    missing_reqs_msg = (
                        f"Missing files: {', '.join(validation[MISSING_KEY])}"
                    )
                    _LOGGER.warning(NOT_SUB_MSG.format(missing_reqs_msg))
                    use_this_sample and skip_reasons.append("Missing files")

        if _use_sample(use_this_sample, skip_reasons):
            self._pool.append(sample)
            self._curr_size += float(validation[INPUT_FILE_SIZE_KEY])
            if self.automatic and self._is_full(self._pool, self._curr_size):
                self.submit()
        else:
            self._curr_skip_size += float(validation[INPUT_FILE_SIZE_KEY])
            self._curr_skip_pool.append(sample)
            self.write_script(self._curr_skip_pool, self._curr_skip_size)
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
        submitted = False

        # Override signal handler so that Ctrl+C can be used to gracefully terminate child process
        signal.signal(signal.SIGINT, self._signal_int_handler)

        if not self._pool:
            _LOGGER.debug("No submission (no pooled samples): %s", self.pl_name)
            # submitted = False
        elif self.collate or force or self._is_full(self._pool, self._curr_size):
            if not self.collate:
                for s in self._pool:
                    schemas = self.prj.get_schemas(
                        self.prj.get_sample_piface(s[self.prj.sample_table_index]),
                        OUTPUT_SCHEMA_KEY,
                    )

                    for schema in schemas:
                        populate_sample_paths(s, read_schema(schema)[0])

            script = self.write_script(self._pool, self._curr_size)
            # Determine whether to actually do the submission.
            _LOGGER.info(
                "Job script (n={0}; {1:.2f}Gb): {2}".format(
                    len(self._pool), self._curr_size, script
                )
            )
            if self.dry_run:
                _LOGGER.info("Dry run, not submitted")
            elif self._rendered_ok:
                sub_cmd = self.prj.dcc.compute["submission_command"]
                submission_command = "{} {}".format(sub_cmd, script)
                # Capture submission command return value so that we can
                # intercept and report basic submission failures; #167
                process = subprocess.Popen(submission_command, shell=True)
                self.process_id = process.pid
                process.wait()
                if process.returncode != 0:
                    fails = (
                        "" if self.collate else [s.sample_name for s in self._samples]
                    )
                    self._failed_sample_names.extend(fails)
                    self._reset_pool()
                    raise JobSubmissionException(sub_cmd, script)
                time.sleep(self.delay)

            # Update the job and command submission tallies.
            _LOGGER.debug("SUBMITTED")
            if self._rendered_ok:
                submitted = True
                self._num_cmds_submitted += len(self._pool)
            self._reset_pool()

        else:
            _LOGGER.debug(
                f"No submission (pool is not full and submission was not forced): {self.pl_name}"
            )
            # submitted = False

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
        """Determine how to refer to the 'sample' for this submission."""
        if self.collate:
            return self.prj.name
        if 1 == self.max_cmds:
            assert 1 == len(pool), (
                "If there's a single-command limit on job submission, jobname"
                " must be determined with exactly one sample in the pool,"
                " but there is/are {}.".format(len(pool))
            )
            sample = pool[0]
            return sample.sample_name
        else:
            # Note the order in which the increment of submission count and
            # the call to this function can influence naming. Make the jobname
            # generation call (this method) before incrementing the
            # submission counter, but add 1 to the index so that we get a
            # name concordant with 1-based, not 0-based indexing.
            return "lump{}".format(self._num_total_job_submissions + 1)

    def _signal_int_handler(self, signal, frame):
        """
        For catching interrupt (Ctrl +C) signals. Fails gracefully.
        """
        signal_type = "SIGINT"
        self._generic_signal_handler(signal_type)

    def _generic_signal_handler(self, signal_type):
        """
        Function for handling both SIGTERM and SIGINT
        """
        message = "Received " + signal_type + ". Failing gracefully..."
        _LOGGER.warning(msg=message)

        self._terminate_current_subprocess()

        sys.exit(1)

    def _terminate_current_subprocess(self):
        """This terminates the current sub process associated with self.process_id"""

        def pskill(proc_pid, sig=signal.SIGINT):
            parent_process = psutil.Process(proc_pid)
            for child_proc in parent_process.children(recursive=True):
                child_proc.send_signal(sig)
            parent_process.send_signal(sig)

        if self.process_id is None:
            return

        # Gently wait for the subprocess before attempting to kill it
        sys.stdout.flush()
        still_running = self._attend_process(psutil.Process(self.process_id), 0)
        sleeptime = 0.25
        time_waiting = 0

        while still_running and time_waiting < 3:
            try:
                if time_waiting > 2:
                    pskill(self.process_id, signal.SIGKILL)
                elif time_waiting > 1:
                    pskill(self.process_id, signal.SIGTERM)
                else:
                    pskill(self.process_id, signal.SIGINT)

            except OSError:
                # This would happen if the child process ended between the check
                # and the next kill step
                still_running = False
                time_waiting = time_waiting + sleeptime

            # Now see if it's still running
            time_waiting = time_waiting + sleeptime
            if not self._attend_process(psutil.Process(self.process_id), sleeptime):
                still_running = False

        if still_running:
            _LOGGER.warning(f"Unable to halt child process: {self.process_id}")
        else:
            if time_waiting > 0:
                note = f"terminated after {time_waiting} sec"
            else:
                note = "was already terminated"
            _LOGGER.warning(msg=f"Child process {self.process_id} {note}.")

    def _attend_process(self, proc, sleeptime):
        """
        Waits on a process for a given time to see if it finishes, returns True
        if it's still running after the given time or False as soon as it
        returns.

        :param psutil.Process proc: Process object opened by psutil.Popen()
        :param float sleeptime: Time to wait
        :return bool: True if process is still running; otherwise false
        """
        try:
            proc.wait(timeout=int(sleeptime))
        except psutil.TimeoutExpired:
            return True
        return False

    def _jobname(self, pool):
        """Create the name for a job submission."""
        return "{}_{}".format(self.pl_iface.pipeline_name, self._sample_lump_name(pool))

    def _build_looper_namespace(self, pool, size):
        """
        Compile a mapping of looper/submission related settings for use in
        the command templates and in submission script creation
        in divvy (via adapters).

        :param Iterable[peppy.Sample] pool: collection of sample instances
        :param float size: cumulative size of the given pool
        :return yacman.YAMLConfigManager: looper/submission related settings
        """
        settings = YAMLConfigManager()
        settings["config_file"] = self.prj.config_file
        settings["pep_config"] = self.prj.pep_config

        settings[RESULTS_SUBDIR_KEY] = self.prj.results_folder
        settings[SUBMISSION_SUBDIR_KEY] = self.prj.submission_folder
        settings[OUTDIR_KEY] = self.prj.output_dir
        # TODO: explore pulling additional constants from peppy and/or divvy.
        settings["sample_output_folder"] = os.path.join(
            self.prj.results_folder, self._sample_lump_name(pool)
        )
        settings[JOB_NAME_KEY] = self._jobname(pool)
        settings["total_input_size"] = size
        settings["log_file"] = (
            os.path.join(self.prj.submission_folder, settings[JOB_NAME_KEY]) + ".log"
        )
        settings["piface_dir"] = os.path.dirname(self.pl_iface.pipe_iface_file)
        if hasattr(self.prj, "pipeline_config"):
            # Make sure it's a file (it could be provided as null.)
            pl_config_file = self.prj.pipeline_config
            if pl_config_file:
                if not os.path.isfile(pl_config_file):
                    _LOGGER.error(
                        "Pipeline config file specified " "but not found: %s",
                        pl_config_file,
                    )
                    raise IOError(pl_config_file)
                _LOGGER.info("Found config file: %s", pl_config_file)
                # Append arg for config file if found
                settings["pipeline_config"] = pl_config_file
        return settings

    def _set_pipestat_namespace(
        self, sample_name: Optional[str] = None
    ) -> YAMLConfigManager:
        """
        Compile a mapping of pipestat-related settings for use in
        the command templates. Accessible via: {pipestat.attrname}

        :param str sample_name: name of the sample to get the pipestat
            namespace for. If not provided the pipestat namespace will
            be determined based on the Project
        :return yacman.YAMLConfigManager: pipestat namespace
        """
        try:
            psm = self.pl_iface.psm
        except (PipestatError, AttributeError) as e:
            # pipestat section faulty or not found in project.looper or sample
            # or project is missing required pipestat attributes
            _LOGGER.debug(
                f"Could not determine pipestat namespace. Caught exception: "
                f"{getattr(e, 'message', repr(e))}"
            )
            # return an empty mapping
            return YAMLConfigManager()
        else:
            full_namespace = {
                "results_file": psm.file,
                "record_identifier": psm.record_identifier,
                "config_file": psm.config_path,
                "output_schema": psm.cfg["_schema_path"],
                "pephub_path": psm.cfg["pephub_path"],
                "flag_file_dir": psm.cfg["_config"].data.get("flag_file_dir"),
            }
            filtered_namespace = {k: v for k, v in full_namespace.items() if v}
            return YAMLConfigManager(filtered_namespace)

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
        looper = self._build_looper_namespace(pool, size)
        commands = []
        namespaces = dict(
            project=self.prj[CONFIG_KEY],
            looper=looper,
            pipeline=self.pl_iface,
            compute=self.prj.dcc.compute,
        )

        if self.pipeline_interface_type is None:
            templ = self.pl_iface["command_template"]
        else:
            templ = self.pl_iface[self.pipeline_interface_type]["command_template"]
        if not self.override_extra:
            extras_template = (
                EXTRA_PROJECT_CMD_TEMPLATE
                if self.collate
                else EXTRA_SAMPLE_CMD_TEMPLATE
            )
            templ += extras_template
        for sample in pool:
            # cascading compute settings determination:
            # divcfg < pipeline interface < config <  CLI
            cli = self.compute_variables or {}  # CLI
            if sample:
                namespaces.update({"sample": sample})
            else:
                namespaces.update({"samples": self.prj.samples})
            if self.prj.pipestat_configured:
                pipestat_namespace = self._set_pipestat_namespace(
                    sample_name=sample.sample_name if sample else None
                )
                namespaces.update({"pipestat": pipestat_namespace})
            else:
                # Pipestat isn't configured, simply place empty YAMLConfigManager object instead.
                pipestat_namespace = YAMLConfigManager()
                namespaces.update({"pipestat": pipestat_namespace})
            res_pkg = self.pl_iface.choose_resource_package(
                namespaces, size or 0
            )  # config
            res_pkg.update(cli)
            self.prj.dcc.compute.update(res_pkg)  # divcfg
            namespaces["compute"].update(res_pkg)
            # Here we make a copy of this so that each iteration gets its own template values
            pl_iface = {}
            pl_iface.update(self.pl_iface)
            pl_iface[VAR_TEMPL_KEY] = self.pl_iface.render_var_templates(
                namespaces=namespaces
            )
            _LOGGER.debug(f"namespace pipelines: { pl_iface }")

            namespaces["pipeline"]["var_templates"] = pl_iface[VAR_TEMPL_KEY] or {}

            namespaces["pipeline"]["var_templates"] = expand_nested_var_templates(
                namespaces["pipeline"]["var_templates"], namespaces
            )

            # pre_submit hook namespace updates
            namespaces = _exec_pre_submit(pl_iface, namespaces)
            self._rendered_ok = False
            try:
                argstring = jinja_render_template_strictly(
                    template=templ, namespaces=namespaces
                )
            except UndefinedError as jinja_exception:
                _LOGGER.warning(NOT_SUB_MSG.format(str(jinja_exception)))
            except KeyError as e:
                exc = "pipeline interface is missing {} section".format(str(e))
                _LOGGER.warning(NOT_SUB_MSG.format(exc))
            else:
                commands.append("{} {}".format(argstring, self.extra_pipe_args))
                self._rendered_ok = True
                if sample not in self._curr_skip_pool:
                    self._num_good_job_submissions += 1
                    self._num_total_job_submissions += 1

        looper["command"] = "\n".join(commands)
        if self.collate:
            _LOGGER.debug("samples namespace:\n{}".format(self.prj.samples))
        else:
            _LOGGER.debug(
                "sample namespace:\n{}".format(
                    sample.__str__(max_attr=len(list(sample.keys())))
                )
            )
        _LOGGER.debug("project namespace:\n{}".format(self.prj[CONFIG_KEY]))
        _LOGGER.debug("pipeline namespace:\n{}".format(self.pl_iface))
        _LOGGER.debug("compute namespace:\n{}".format(self.prj.dcc.compute))
        _LOGGER.debug("looper namespace:\n{}".format(looper))
        _LOGGER.debug("pipestat namespace:\n{}".format(pipestat_namespace))
        subm_base = os.path.join(
            expandpath(self.prj.submission_folder), looper[JOB_NAME_KEY]
        )
        return self.prj.dcc.write_script(
            output_path=subm_base + ".sub", extra_vars=[{"looper": looper}]
        )

    def _reset_pool(self):
        """Reset the state of the pool of samples"""
        self._pool = []
        self._curr_size = 0

    def _reset_curr_skips(self):
        self._curr_skip_pool = []
        self._curr_skip_size = 0


def _use_sample(flag, skips):
    return flag and not skips


def _exec_pre_submit(piface, namespaces):
    """
    Execute pre submission hooks defined in the pipeline interface

    :param PipelineInterface piface: piface, a source of pre_submit hooks to execute
    :param dict[dict[]] namespaces: namspaces mapping
    :return dict[dict[]]: updated namspaces mapping
    """

    def _update_namespaces(x, y, cmd=False):
        """
        Update namespaces mapping with a dictionary of the same structure,
        that includes just the values that need to be updated.

        :param dict[dict] x: namespaces mapping
        :param dict[dict] y: mapping to update namespaces with
        :param bool cmd: whether the mapping to update with comes from the
            command template, used for messaging
        """
        if not y:
            return
        if not isinstance(y, dict):
            if cmd:
                raise TypeError(
                    f"Object returned by {PRE_SUBMIT_HOOK_KEY}."
                    f"{PRE_SUBMIT_CMD_KEY} must return a dictionary when "
                    f"processed with json.loads(), not {y.__class__.__name__}"
                )
            raise TypeError(
                f"Object returned by {PRE_SUBMIT_HOOK_KEY}."
                f"{PRE_SUBMIT_PY_FUN_KEY} must return a dictionary,"
                f" not {y.__class__.__name__}"
            )
        _LOGGER.debug("Updating namespaces with:\n{}".format(y))
        for namespace, mapping in y.items():
            for key, val in mapping.items():
                x[namespace][key] = val

    if PRE_SUBMIT_HOOK_KEY in piface:
        pre_submit = piface[PRE_SUBMIT_HOOK_KEY]
        if PRE_SUBMIT_PY_FUN_KEY in pre_submit:
            for py_fun in pre_submit[PRE_SUBMIT_PY_FUN_KEY]:
                pkgstr, funcstr = os.path.splitext(py_fun)
                pkg = importlib.import_module(pkgstr)
                func = getattr(pkg, funcstr[1:])
                _LOGGER.info(
                    "Calling pre-submit function: {}.{}".format(pkgstr, func.__name__)
                )
                _update_namespaces(namespaces, func(namespaces))
        if PRE_SUBMIT_CMD_KEY in pre_submit:
            for cmd_template in pre_submit[PRE_SUBMIT_CMD_KEY]:
                _LOGGER.debug(
                    "Rendering pre-submit command template: {}".format(cmd_template)
                )
                try:
                    cmd = jinja_render_template_strictly(
                        template=cmd_template, namespaces=namespaces
                    )
                    _LOGGER.info("Executing pre-submit command: {}".format(cmd))
                    json = loads(check_output(cmd, shell=True))
                except Exception as e:
                    if hasattr(e, "output"):
                        print(e.output)
                    _LOGGER.error(
                        "Could not retrieve JSON via command: '{}'".format(cmd)
                    )
                    raise
                else:
                    _update_namespaces(namespaces, json, cmd=True)
    return namespaces
