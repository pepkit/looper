Usage reference
******************************

Looper doesn't just run pipelines; it can also check and summarize the progress of your jobs, as well as remove all files created by them.

Each task is controlled by one of the five main commands ``run``, ``summarize``, ``destroy``, ``check``, ``clean``.

- ``looper run``:  Runs pipelines for each sample, for each pipeline. This will use your ``compute`` settings to build and submit scripts to your specified compute environment, or run them sequentially on your local computer.

- ``looper summarize``: Summarize your project results. This command parses all key-value results reported in the each sample `stats.tsv` and collates them into a large summary matrix, which it saves in the project output directory. This creates such a matrix for each pipeline type run on the project, and a combined master summary table.

- ``looper check``: Checks the run progress of the current project. This will display a summary of job status; which pipelines are currently running on which samples, which have completed, which have failed, etc.

- ``looper destroy``: Deletes all output results for this project.


Here you can see the command-line usage instructions for the main looper command and for each subcommand:


``looper --help``
----------------------------------

.. code-block:: none

	version: 0.11.0
	usage: looper [-h] [-V] [--logfile LOGFILE] [--verbosity {0,1,2,3,4}] [--dbg]
	              [--env ENV]
	              {run,rerun,summarize,destroy,check,clean} ...
	
	looper - Loop through samples and submit pipelines.
	
	positional arguments:
	  {run,rerun,summarize,destroy,check,clean}
	    run                 Main Looper function: Submit jobs for samples.
	    rerun               Resubmit jobs with failed flags.
	    summarize           Summarize statistics of project samples.
	    destroy             Remove all files of the project.
	    check               Checks flag status of current runs.
	    clean               Runs clean scripts to remove intermediate files of
	                        already processed jobs.
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -V, --version         show program's version number and exit
	  --logfile LOGFILE     Optional output file for looper logs (default: None)
	  --verbosity {0,1,2,3,4}
	                        Choose level of verbosity (default: None)
	  --dbg                 Turn on debug mode (default: False)
	  --env ENV             Environment variable that points to the DIVCFG file.
	                        (default: DIVCFG)
	
	For subcommand-specific options, type: 'looper <subcommand> -h'
	https://github.com/pepkit/looper

``looper run --help``
----------------------------------

.. code-block:: none

	version: 0.11.0
	usage: looper run [-h] [--ignore-flags] [-t TIME_DELAY]
	                  [--allow-duplicate-names] [--compute COMPUTE]
	                  [--resources RESOURCES] [--limit LIMIT] [--lump LUMP]
	                  [--lumpn LUMPN] [--file-checks] [-d]
	                  [--selector-attribute SELECTOR_ATTRIBUTE]
	                  [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                  | --selector-include
	                  [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]] [--sp SUBPROJECT]
	                  config_file
	
	Main Looper function: Submit jobs for samples.
	
	positional arguments:
	  config_file           Project configuration file (YAML).
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --ignore-flags        Ignore run status flags? Default: False. By default,
	                        pipelines will not be submitted if a pypiper flag file
	                        exists marking the run (e.g. as 'running' or
	                        'failed'). Set this option to ignore flags and submit
	                        the runs anyway. Default=False
	  -t TIME_DELAY, --time-delay TIME_DELAY
	                        Time delay in seconds between job submissions.
	  --allow-duplicate-names
	                        Allow duplicate names? Default: False. By default,
	                        pipelines will not be submitted if a sample name is
	                        duplicated, since samples names should be unique. Set
	                        this option to override this setting. Default=False
	  --compute COMPUTE     YAML file with looper environment compute settings.
	  --resources RESOURCES
	                        Specification of individual computing resource
	                        settings; separate setting name/key from value with
	                        equals sign, and separate key-value pairs from each
	                        other by comma; e.g., --resources k1=v1,k2=v2
	  --limit LIMIT         Limit to n samples.
	  --lump LUMP           Maximum total input file size for a lump/batch of
	                        commands in a single job (in GB)
	  --lumpn LUMPN         Number of individual scripts grouped into single
	                        submission
	  --file-checks         Perform input file checks. Default=True.
	  -d, --dry-run         Don't actually submit the project/subproject.
	                        Default=False
	  --sp SUBPROJECT       Name of subproject to use, as designated in the
	                        project's configuration file
	
	select samples:
	  This group of arguments lets you specify samples to use by exclusion OR
	  inclusion of the samples attribute values.
	
	  --selector-attribute SELECTOR_ATTRIBUTE
	                        Specify the attribute for samples exclusion OR
	                        inclusion
	  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                        Operate only on samples that either lack this
	                        attribute value or for which this value is not in this
	                        collection.
	  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
	                        Operate only on samples associated with these
	                        attribute values; if not provided, all samples are
	                        used.

``looper summarize --help``
----------------------------------

.. code-block:: none

	version: 0.11.0
	usage: looper summarize [-h] [--file-checks] [-d]
	                        [--selector-attribute SELECTOR_ATTRIBUTE]
	                        [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                        | --selector-include
	                        [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
	                        [--sp SUBPROJECT]
	                        config_file
	
	Summarize statistics of project samples.
	
	positional arguments:
	  config_file           Project configuration file (YAML).
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --file-checks         Perform input file checks. Default=True.
	  -d, --dry-run         Don't actually submit the project/subproject.
	                        Default=False
	  --sp SUBPROJECT       Name of subproject to use, as designated in the
	                        project's configuration file
	
	select samples:
	  This group of arguments lets you specify samples to use by exclusion OR
	  inclusion of the samples attribute values.
	
	  --selector-attribute SELECTOR_ATTRIBUTE
	                        Specify the attribute for samples exclusion OR
	                        inclusion
	  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                        Operate only on samples that either lack this
	                        attribute value or for which this value is not in this
	                        collection.
	  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
	                        Operate only on samples associated with these
	                        attribute values; if not provided, all samples are
	                        used.

``looper destroy --help``
----------------------------------

.. code-block:: none

	version: 0.11.0
	usage: looper destroy [-h] [--force-yes] [--file-checks] [-d]
	                      [--selector-attribute SELECTOR_ATTRIBUTE]
	                      [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                      | --selector-include
	                      [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
	                      [--sp SUBPROJECT]
	                      config_file
	
	Remove all files of the project.
	
	positional arguments:
	  config_file           Project configuration file (YAML).
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --force-yes           Provide upfront confirmation of destruction intent, to
	                        skip console query. Default=False
	  --file-checks         Perform input file checks. Default=True.
	  -d, --dry-run         Don't actually submit the project/subproject.
	                        Default=False
	  --sp SUBPROJECT       Name of subproject to use, as designated in the
	                        project's configuration file
	
	select samples:
	  This group of arguments lets you specify samples to use by exclusion OR
	  inclusion of the samples attribute values.
	
	  --selector-attribute SELECTOR_ATTRIBUTE
	                        Specify the attribute for samples exclusion OR
	                        inclusion
	  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                        Operate only on samples that either lack this
	                        attribute value or for which this value is not in this
	                        collection.
	  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
	                        Operate only on samples associated with these
	                        attribute values; if not provided, all samples are
	                        used.

``looper check --help``
----------------------------------

.. code-block:: none

	version: 0.11.0
	usage: looper check [-h] [-A] [-F [FLAGS [FLAGS ...]]] [--file-checks] [-d]
	                    [--selector-attribute SELECTOR_ATTRIBUTE]
	                    [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                    | --selector-include
	                    [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
	                    [--sp SUBPROJECT]
	                    config_file
	
	Checks flag status of current runs.
	
	positional arguments:
	  config_file           Project configuration file (YAML).
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -A, --all-folders     Check status for all project's output folders, not
	                        just those for samples specified in the config file
	                        used. Default=False
	  -F [FLAGS [FLAGS ...]], --flags [FLAGS [FLAGS ...]]
	                        Check on only these flags/status values.
	  --file-checks         Perform input file checks. Default=True.
	  -d, --dry-run         Don't actually submit the project/subproject.
	                        Default=False
	  --sp SUBPROJECT       Name of subproject to use, as designated in the
	                        project's configuration file
	
	select samples:
	  This group of arguments lets you specify samples to use by exclusion OR
	  inclusion of the samples attribute values.
	
	  --selector-attribute SELECTOR_ATTRIBUTE
	                        Specify the attribute for samples exclusion OR
	                        inclusion
	  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                        Operate only on samples that either lack this
	                        attribute value or for which this value is not in this
	                        collection.
	  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
	                        Operate only on samples associated with these
	                        attribute values; if not provided, all samples are
	                        used.

``looper clean --help``
----------------------------------

.. code-block:: none

	version: 0.11.0
	usage: looper clean [-h] [--force-yes] [--file-checks] [-d]
	                    [--selector-attribute SELECTOR_ATTRIBUTE]
	                    [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                    | --selector-include
	                    [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
	                    [--sp SUBPROJECT]
	                    config_file
	
	Runs clean scripts to remove intermediate files of already processed jobs.
	
	positional arguments:
	  config_file           Project configuration file (YAML).
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --force-yes           Provide upfront confirmation of cleaning intent, to
	                        skip console query. Default=False
	  --file-checks         Perform input file checks. Default=True.
	  -d, --dry-run         Don't actually submit the project/subproject.
	                        Default=False
	  --sp SUBPROJECT       Name of subproject to use, as designated in the
	                        project's configuration file
	
	select samples:
	  This group of arguments lets you specify samples to use by exclusion OR
	  inclusion of the samples attribute values.
	
	  --selector-attribute SELECTOR_ATTRIBUTE
	                        Specify the attribute for samples exclusion OR
	                        inclusion
	  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                        Operate only on samples that either lack this
	                        attribute value or for which this value is not in this
	                        collection.
	  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
	                        Operate only on samples associated with these
	                        attribute values; if not provided, all samples are
	                        used.

``looper rerun --help``
----------------------------------

.. code-block:: none

	version: 0.11.0
	usage: looper rerun [-h] [--ignore-flags] [-t TIME_DELAY]
	                    [--allow-duplicate-names] [--compute COMPUTE]
	                    [--resources RESOURCES] [--limit LIMIT] [--lump LUMP]
	                    [--lumpn LUMPN] [--file-checks] [-d]
	                    [--selector-attribute SELECTOR_ATTRIBUTE]
	                    [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                    | --selector-include
	                    [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
	                    [--sp SUBPROJECT]
	                    config_file
	
	Resubmit jobs with failed flags.
	
	positional arguments:
	  config_file           Project configuration file (YAML).
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --ignore-flags        Ignore run status flags? Default: False. By default,
	                        pipelines will not be submitted if a pypiper flag file
	                        exists marking the run (e.g. as 'running' or
	                        'failed'). Set this option to ignore flags and submit
	                        the runs anyway. Default=False
	  -t TIME_DELAY, --time-delay TIME_DELAY
	                        Time delay in seconds between job submissions.
	  --allow-duplicate-names
	                        Allow duplicate names? Default: False. By default,
	                        pipelines will not be submitted if a sample name is
	                        duplicated, since samples names should be unique. Set
	                        this option to override this setting. Default=False
	  --compute COMPUTE     YAML file with looper environment compute settings.
	  --resources RESOURCES
	                        Specification of individual computing resource
	                        settings; separate setting name/key from value with
	                        equals sign, and separate key-value pairs from each
	                        other by comma; e.g., --resources k1=v1,k2=v2
	  --limit LIMIT         Limit to n samples.
	  --lump LUMP           Maximum total input file size for a lump/batch of
	                        commands in a single job (in GB)
	  --lumpn LUMPN         Number of individual scripts grouped into single
	                        submission
	  --file-checks         Perform input file checks. Default=True.
	  -d, --dry-run         Don't actually submit the project/subproject.
	                        Default=False
	  --sp SUBPROJECT       Name of subproject to use, as designated in the
	                        project's configuration file
	
	select samples:
	  This group of arguments lets you specify samples to use by exclusion OR
	  inclusion of the samples attribute values.
	
	  --selector-attribute SELECTOR_ATTRIBUTE
	                        Specify the attribute for samples exclusion OR
	                        inclusion
	  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
	                        Operate only on samples that either lack this
	                        attribute value or for which this value is not in this
	                        collection.
	  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
	                        Operate only on samples associated with these
	                        attribute values; if not provided, all samples are
	                        used.
