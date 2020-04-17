# Usage reference

Looper doesn't just run pipelines; it can also check and summarize the progress of your jobs, as well as remove all files created by them.

Each task is controlled by one of the five main commands `run`, `summarize`, `destroy`, `check`, `clean`, `rerun`.

- `looper run`:  Runs pipelines for each sample, for each pipeline. This will use your `compute` settings to build and submit scripts to your specified compute environment, or run them sequentially on your local computer.

- `looper summarize`: Summarize your project results. This command parses all key-value results reported in the each sample `stats.tsv` and collates them into a large summary matrix, which it saves in the project output directory. This creates such a matrix for each pipeline type run on the project, and a combined master summary table.

- `looper check`: Checks the run progress of the current project. This will display a summary of job status; which pipelines are currently running on which samples, which have completed, which have failed, etc.

- `looper destroy`: Deletes all output results for this project.

- `looper rerun`: Exactly the same as `looper run`, but only runs jobs with a failed flag.


Here you can see the command-line usage instructions for the main looper command and for each subcommand:
## `looper --help`
version: 0.12.6-dev
usage: looper [-h] [--version] [--logfile LOGFILE] [--verbosity {0,1,2,3,4}]
              [--dbg] [--env ENV]
              {run,rerun,runp,summarize,destroy,check,clean} ...

looper - Loop through samples and submit pipelines.

positional arguments:
  {run,rerun,runp,summarize,destroy,check,clean}
    run                 Main Looper function: Submit jobs for samples.
    rerun               Resubmit jobs with failed flags.
    runp                Submit jobs for a project.
    summarize           Summarize statistics of project samples.
    destroy             Remove all files of the project.
    check               Checks flag status of current runs.
    clean               Runs clean scripts to remove intermediate files of
                        already processed jobs.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --logfile LOGFILE     Optional output file for looper logs (default: None)
  --verbosity {0,1,2,3,4}
                        Choose level of verbosity (default: None)
  --dbg                 Turn on debug mode (default: False)
  --env ENV             Environment variable that points to the DIVCFG file.
                        (default: DIVCFG)

For subcommand-specific options, type: 'looper <subcommand> -h'
https://github.com/pepkit/looper
```

## `looper run --help`
usage: looper run [-h] [--ignore-flags] [-t TIME_DELAY]
                  [--allow-duplicate-names] [--package PACKAGE]
                  [--compute COMPUTE] [--limit LIMIT] [--lump LUMP]
                  [--lumpn LUMPN]
                  [--pipeline-interfaces PIFACES [PIFACES ...]]
                  [--file-checks] [-d]
                  [--selector-attribute SELECTOR_ATTRIBUTE]
                  [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                  | --selector-include
                  [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                  [-a AMENDMENTS [AMENDMENTS ...]]
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
  --package PACKAGE     Name of computing resource package to use
  --compute COMPUTE     Specification of individual computing resource
                        settings; separate setting name/key from value with
                        equals sign, and separate key-value pairs from each
                        other by comma; e.g., --compute k1=v1,k2=v2
  --limit LIMIT         Limit to n samples.
  --lump LUMP           Maximum total input file size for a lump/batch of
                        commands in a single job (in GB)
  --lumpn LUMPN         Number of individual scripts grouped into single
                        submission
  --pipeline-interfaces PIFACES [PIFACES ...]
                        Path to a pipeline interface file
  --file-checks         Perform input file checks. Default=True.
  -d, --dry-run         Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                        Name of amendment(s) to use, as designated in the
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
```

## `looper summarize --help`
usage: looper summarize [-h] [--pipeline-interfaces PIFACES [PIFACES ...]]
                        [--file-checks] [-d]
                        [--selector-attribute SELECTOR_ATTRIBUTE]
                        [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                        | --selector-include
                        [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                        [-a AMENDMENTS [AMENDMENTS ...]]
                        config_file

Summarize statistics of project samples.

positional arguments:
  config_file           Project configuration file (YAML).

optional arguments:
  -h, --help            show this help message and exit
  --pipeline-interfaces PIFACES [PIFACES ...]
                        Path to a pipeline interface file
  --file-checks         Perform input file checks. Default=True.
  -d, --dry-run         Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                        Name of amendment(s) to use, as designated in the
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
```

## `looper destroy --help`
usage: looper destroy [-h] [--force-yes]
                      [--pipeline-interfaces PIFACES [PIFACES ...]]
                      [--file-checks] [-d]
                      [--selector-attribute SELECTOR_ATTRIBUTE]
                      [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                      | --selector-include
                      [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                      [-a AMENDMENTS [AMENDMENTS ...]]
                      config_file

Remove all files of the project.

positional arguments:
  config_file           Project configuration file (YAML).

optional arguments:
  -h, --help            show this help message and exit
  --force-yes           Provide upfront confirmation of destruction intent, to
                        skip console query. Default=False
  --pipeline-interfaces PIFACES [PIFACES ...]
                        Path to a pipeline interface file
  --file-checks         Perform input file checks. Default=True.
  -d, --dry-run         Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                        Name of amendment(s) to use, as designated in the
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
```

## `looper check --help`
usage: looper check [-h] [-A] [-F [FLAGS [FLAGS ...]]]
                    [--pipeline-interfaces PIFACES [PIFACES ...]]
                    [--file-checks] [-d]
                    [--selector-attribute SELECTOR_ATTRIBUTE]
                    [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                    | --selector-include
                    [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                    [-a AMENDMENTS [AMENDMENTS ...]]
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
  --pipeline-interfaces PIFACES [PIFACES ...]
                        Path to a pipeline interface file
  --file-checks         Perform input file checks. Default=True.
  -d, --dry-run         Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                        Name of amendment(s) to use, as designated in the
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
```

## `looper clean --help`
usage: looper clean [-h] [--force-yes]
                    [--pipeline-interfaces PIFACES [PIFACES ...]]
                    [--file-checks] [-d]
                    [--selector-attribute SELECTOR_ATTRIBUTE]
                    [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                    | --selector-include
                    [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                    [-a AMENDMENTS [AMENDMENTS ...]]
                    config_file

Runs clean scripts to remove intermediate files of already processed jobs.

positional arguments:
  config_file           Project configuration file (YAML).

optional arguments:
  -h, --help            show this help message and exit
  --force-yes           Provide upfront confirmation of cleaning intent, to
                        skip console query. Default=False
  --pipeline-interfaces PIFACES [PIFACES ...]
                        Path to a pipeline interface file
  --file-checks         Perform input file checks. Default=True.
  -d, --dry-run         Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                        Name of amendment(s) to use, as designated in the
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
```

## `looper rerun --help`
usage: looper rerun [-h] [--ignore-flags] [-t TIME_DELAY]
                    [--allow-duplicate-names] [--package PACKAGE]
                    [--compute COMPUTE] [--limit LIMIT] [--lump LUMP]
                    [--lumpn LUMPN]
                    [--pipeline-interfaces PIFACES [PIFACES ...]]
                    [--file-checks] [-d]
                    [--selector-attribute SELECTOR_ATTRIBUTE]
                    [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                    | --selector-include
                    [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                    [-a AMENDMENTS [AMENDMENTS ...]]
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
  --package PACKAGE     Name of computing resource package to use
  --compute COMPUTE     Specification of individual computing resource
                        settings; separate setting name/key from value with
                        equals sign, and separate key-value pairs from each
                        other by comma; e.g., --compute k1=v1,k2=v2
  --limit LIMIT         Limit to n samples.
  --lump LUMP           Maximum total input file size for a lump/batch of
                        commands in a single job (in GB)
  --lumpn LUMPN         Number of individual scripts grouped into single
                        submission
  --pipeline-interfaces PIFACES [PIFACES ...]
                        Path to a pipeline interface file
  --file-checks         Perform input file checks. Default=True.
  -d, --dry-run         Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                        Name of amendment(s) to use, as designated in the
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
```

