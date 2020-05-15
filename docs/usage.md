# Usage reference

Looper doesn't just run pipelines; it can also check and summarize the progress of your jobs, as well as remove all files created by them.

Each task is controlled by one of the following commands: `run`, `rerun`, `runp` , `table`,`report`, `destroy`, `check`, `clean`, `inspect`, `init`

- `looper run`:  Runs pipelines for each sample, for each pipeline. This will use your `compute` settings to build and submit scripts to your specified compute environment, or run them sequentially on your local computer.

- `looper runp`:  Runs pipelines for each pipeline for project.

- `looper rerun`: Exactly the same as `looper run`, but only runs jobs with a failed flag.

- `looper report`: Summarize your project results in a form of browsable HTML pages.

- `looper table`: This command parses all key-value results reported in the each sample `stats.tsv` and collates them into a large summary matrix, which it saves in the project output directory. This creates such a matrix for each pipeline type run on the project, and a combined master summary table

- `looper check`: Checks the run progress of the current project. This will display a summary of job status; which pipelines are currently running on which samples, which have completed, which have failed, etc.

- `looper destroy`: Deletes all output results for this project.

- `looper inspect`: Display the Prioject or Sample information

- `looper init`: Initialize a looper dotfile (`.looper.yaml`) in the current directory


Here you can see the command-line usage instructions for the main looper command and for each subcommand:
## `looper --help`
```console
version: 1.2.0-dev
usage: looper [-h] [--version] [--logfile LOGFILE] [--verbosity {0,1,2,3,4}]
              [--dbg] [--env ENV]
              {run,rerun,runp,table,report,destroy,check,clean,inspect,init}
              ...

looper - A project job submission engine and project manager.

positional arguments:
  {run,rerun,runp,table,report,destroy,check,clean,inspect,init}
    run                 Run or submit sample jobs.
    rerun               Resubmit sample jobs with failed flags.
    runp                Run or submit a project job.
    table               Write summary stats table for project samples.
    report              Create browsable HTML report of project results.
    destroy             Remove output files of the project.
    check               Check flag status of current runs.
    clean               Run clean scripts of already processed jobs.
    inspect             Print information about a project.
    init                Initialize looper dotfile.

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
```console
usage: looper run [-h] [--ignore-flags] [-t S] [-p P] [-s S] [-m C] [-l N] [-x S] [-y S] [-u SIZE]
                  [-n N] [-o OUTPUT_DIR] [--submission-subdir SUBMISSION_SUBDIR]
                  [--results-subdir RESULTS_SUBDIR]
                  [--pipeline-interfaces-key PIPELINE_INTERFACES_KEY] [--toggle-key TOGGLE_KEY]
                  [--pipeline-interfaces P [P ...]] [--file-checks] [-d]
                  [--selector-attribute SELECTOR_ATTRIBUTE]
                  [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]] | --selector-include
                  [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]] [-a AMENDMENTS [AMENDMENTS ...]]
                  [config_file]

Run or submit sample jobs.

positional arguments:
  config_file               Project configuration file (YAML).

optional arguments:
  -h, --help                show this help message and exit
  --ignore-flags            Ignore run status flags? Default: False. By default, pipelines will not
                            be submitted if a pypiper flag file exists marking the run (e.g. as
                            'running' or 'failed'). Set this option to ignore flags and submit the
                            runs anyway. Default=False
  -t S, --time-delay S      Time delay in seconds between job submissions.
  -p P, --package P         Divvy: Name of computing resource package to use
  -s S, --settings S        Divvy: Path to a YAML settings file with compute settings
  -m C, --compute C         Divvy: Comma-separated list of computing resource key-value pairs, e.g.,
                            --compute k1=v1,k2=v2
  -l N, --limit N           Limit to n samples.
  -x S, --command-extra S   String to append to every command
  -y S, --command-extra-override S
                            String to append to every command, overriding values in PEP.
  -u SIZE, --lump SIZE      Total input file size in GB to batch into a single job
  -n N, --lumpn N           Number of individual commands to batch into a single job
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Path to the output directory
  --submission-subdir SUBMISSION_SUBDIR
                            Name of the submission subdirectory
  --results-subdir RESULTS_SUBDIR
                            Name of the results subdirectory
  --pipeline-interfaces-key PIPELINE_INTERFACES_KEY
                            Name of sample attribute to look for pipeline interface sources in
  --toggle-key TOGGLE_KEY   Name of sample attribute to look for toggle values in
  --pipeline-interfaces P [P ...]
                            Path to a pipeline interface files
  --file-checks             Perform input file checks. Default=True.
  -d, --dry-run             Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                            List of of amendments to activate

select samples:
  This group of arguments lets you specify samples to use by exclusion OR inclusion of the samples
  attribute values.

  --selector-attribute SELECTOR_ATTRIBUTE
                            Specify the attribute for samples exclusion OR inclusion
  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                            Operate only on samples that either lack this attribute value or for
                            which this value is not in this collection.
  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
                            Operate only on samples associated with these attribute values; if not
                            provided, all samples are used.
```

## `looper runp --help`
```console
usage: looper runp [-h] [--ignore-flags] [-t S] [-p P] [-s S] [-m C] [-l N] [-x S] [-y S]
                   [-o OUTPUT_DIR] [--submission-subdir SUBMISSION_SUBDIR]
                   [--results-subdir RESULTS_SUBDIR]
                   [--pipeline-interfaces-key PIPELINE_INTERFACES_KEY] [--toggle-key TOGGLE_KEY]
                   [--pipeline-interfaces P [P ...]] [--file-checks] [-d]
                   [--selector-attribute SELECTOR_ATTRIBUTE]
                   [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]] |
                   --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                   [-a AMENDMENTS [AMENDMENTS ...]]
                   [config_file]

Run or submit a project job.

positional arguments:
  config_file               Project configuration file (YAML).

optional arguments:
  -h, --help                show this help message and exit
  --ignore-flags            Ignore run status flags? Default: False. By default, pipelines will not
                            be submitted if a pypiper flag file exists marking the run (e.g. as
                            'running' or 'failed'). Set this option to ignore flags and submit the
                            runs anyway. Default=False
  -t S, --time-delay S      Time delay in seconds between job submissions.
  -p P, --package P         Divvy: Name of computing resource package to use
  -s S, --settings S        Divvy: Path to a YAML settings file with compute settings
  -m C, --compute C         Divvy: Comma-separated list of computing resource key-value pairs, e.g.,
                            --compute k1=v1,k2=v2
  -l N, --limit N           Limit to n samples.
  -x S, --command-extra S   String to append to every command
  -y S, --command-extra-override S
                            String to append to every command, overriding values in PEP.
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Path to the output directory
  --submission-subdir SUBMISSION_SUBDIR
                            Name of the submission subdirectory
  --results-subdir RESULTS_SUBDIR
                            Name of the results subdirectory
  --pipeline-interfaces-key PIPELINE_INTERFACES_KEY
                            Name of sample attribute to look for pipeline interface sources in
  --toggle-key TOGGLE_KEY   Name of sample attribute to look for toggle values in
  --pipeline-interfaces P [P ...]
                            Path to a pipeline interface files
  --file-checks             Perform input file checks. Default=True.
  -d, --dry-run             Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                            List of of amendments to activate

select samples:
  This group of arguments lets you specify samples to use by exclusion OR inclusion of the samples
  attribute values.

  --selector-attribute SELECTOR_ATTRIBUTE
                            Specify the attribute for samples exclusion OR inclusion
  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                            Operate only on samples that either lack this attribute value or for
                            which this value is not in this collection.
  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
                            Operate only on samples associated with these attribute values; if not
                            provided, all samples are used.
```

## `looper rerun --help`
```console
usage: looper rerun [-h] [--ignore-flags] [-t S] [-p P] [-s S] [-m C] [-l N] [-x S] [-y S] [-u SIZE]
                    [-n N] [-o OUTPUT_DIR] [--submission-subdir SUBMISSION_SUBDIR]
                    [--results-subdir RESULTS_SUBDIR]
                    [--pipeline-interfaces-key PIPELINE_INTERFACES_KEY] [--toggle-key TOGGLE_KEY]
                    [--pipeline-interfaces P [P ...]] [--file-checks] [-d]
                    [--selector-attribute SELECTOR_ATTRIBUTE]
                    [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]] |
                    --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                    [-a AMENDMENTS [AMENDMENTS ...]]
                    [config_file]

Resubmit sample jobs with failed flags.

positional arguments:
  config_file               Project configuration file (YAML).

optional arguments:
  -h, --help                show this help message and exit
  --ignore-flags            Ignore run status flags? Default: False. By default, pipelines will not
                            be submitted if a pypiper flag file exists marking the run (e.g. as
                            'running' or 'failed'). Set this option to ignore flags and submit the
                            runs anyway. Default=False
  -t S, --time-delay S      Time delay in seconds between job submissions.
  -p P, --package P         Divvy: Name of computing resource package to use
  -s S, --settings S        Divvy: Path to a YAML settings file with compute settings
  -m C, --compute C         Divvy: Comma-separated list of computing resource key-value pairs, e.g.,
                            --compute k1=v1,k2=v2
  -l N, --limit N           Limit to n samples.
  -x S, --command-extra S   String to append to every command
  -y S, --command-extra-override S
                            String to append to every command, overriding values in PEP.
  -u SIZE, --lump SIZE      Total input file size in GB to batch into a single job
  -n N, --lumpn N           Number of individual commands to batch into a single job
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Path to the output directory
  --submission-subdir SUBMISSION_SUBDIR
                            Name of the submission subdirectory
  --results-subdir RESULTS_SUBDIR
                            Name of the results subdirectory
  --pipeline-interfaces-key PIPELINE_INTERFACES_KEY
                            Name of sample attribute to look for pipeline interface sources in
  --toggle-key TOGGLE_KEY   Name of sample attribute to look for toggle values in
  --pipeline-interfaces P [P ...]
                            Path to a pipeline interface files
  --file-checks             Perform input file checks. Default=True.
  -d, --dry-run             Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                            List of of amendments to activate

select samples:
  This group of arguments lets you specify samples to use by exclusion OR inclusion of the samples
  attribute values.

  --selector-attribute SELECTOR_ATTRIBUTE
                            Specify the attribute for samples exclusion OR inclusion
  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                            Operate only on samples that either lack this attribute value or for
                            which this value is not in this collection.
  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
                            Operate only on samples associated with these attribute values; if not
                            provided, all samples are used.
```

## `looper report --help`
```console
usage: looper report [-h] [-o OUTPUT_DIR] [--submission-subdir SUBMISSION_SUBDIR]
                     [--results-subdir RESULTS_SUBDIR]
                     [--pipeline-interfaces-key PIPELINE_INTERFACES_KEY] [--toggle-key TOGGLE_KEY]
                     [--pipeline-interfaces P [P ...]] [--file-checks] [-d]
                     [--selector-attribute SELECTOR_ATTRIBUTE]
                     [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]] |
                     --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                     [-a AMENDMENTS [AMENDMENTS ...]]
                     [config_file]

Create browsable HTML report of project results.

positional arguments:
  config_file               Project configuration file (YAML).

optional arguments:
  -h, --help                show this help message and exit
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Path to the output directory
  --submission-subdir SUBMISSION_SUBDIR
                            Name of the submission subdirectory
  --results-subdir RESULTS_SUBDIR
                            Name of the results subdirectory
  --pipeline-interfaces-key PIPELINE_INTERFACES_KEY
                            Name of sample attribute to look for pipeline interface sources in
  --toggle-key TOGGLE_KEY   Name of sample attribute to look for toggle values in
  --pipeline-interfaces P [P ...]
                            Path to a pipeline interface files
  --file-checks             Perform input file checks. Default=True.
  -d, --dry-run             Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                            List of of amendments to activate

select samples:
  This group of arguments lets you specify samples to use by exclusion OR inclusion of the samples
  attribute values.

  --selector-attribute SELECTOR_ATTRIBUTE
                            Specify the attribute for samples exclusion OR inclusion
  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                            Operate only on samples that either lack this attribute value or for
                            which this value is not in this collection.
  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
                            Operate only on samples associated with these attribute values; if not
                            provided, all samples are used.
```

## `looper table --help`
```console
usage: looper table [-h] [-o OUTPUT_DIR] [--submission-subdir SUBMISSION_SUBDIR]
                    [--results-subdir RESULTS_SUBDIR]
                    [--pipeline-interfaces-key PIPELINE_INTERFACES_KEY] [--toggle-key TOGGLE_KEY]
                    [--pipeline-interfaces P [P ...]] [--file-checks] [-d]
                    [--selector-attribute SELECTOR_ATTRIBUTE]
                    [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]] |
                    --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                    [-a AMENDMENTS [AMENDMENTS ...]]
                    [config_file]

Write summary stats table for project samples.

positional arguments:
  config_file               Project configuration file (YAML).

optional arguments:
  -h, --help                show this help message and exit
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Path to the output directory
  --submission-subdir SUBMISSION_SUBDIR
                            Name of the submission subdirectory
  --results-subdir RESULTS_SUBDIR
                            Name of the results subdirectory
  --pipeline-interfaces-key PIPELINE_INTERFACES_KEY
                            Name of sample attribute to look for pipeline interface sources in
  --toggle-key TOGGLE_KEY   Name of sample attribute to look for toggle values in
  --pipeline-interfaces P [P ...]
                            Path to a pipeline interface files
  --file-checks             Perform input file checks. Default=True.
  -d, --dry-run             Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                            List of of amendments to activate

select samples:
  This group of arguments lets you specify samples to use by exclusion OR inclusion of the samples
  attribute values.

  --selector-attribute SELECTOR_ATTRIBUTE
                            Specify the attribute for samples exclusion OR inclusion
  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                            Operate only on samples that either lack this attribute value or for
                            which this value is not in this collection.
  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
                            Operate only on samples associated with these attribute values; if not
                            provided, all samples are used.
```

## `looper inspect --help`
```console
usage: looper inspect [-h] [-n SAMPLE_NAME [SAMPLE_NAME ...]] [-o OUTPUT_DIR]
                      [--submission-subdir SUBMISSION_SUBDIR] [--results-subdir RESULTS_SUBDIR]
                      [--pipeline-interfaces-key PIPELINE_INTERFACES_KEY] [--toggle-key TOGGLE_KEY]
                      [--pipeline-interfaces P [P ...]] [--file-checks] [-d]
                      [--selector-attribute SELECTOR_ATTRIBUTE]
                      [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]] |
                      --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                      [-a AMENDMENTS [AMENDMENTS ...]]
                      [config_file]

Print information about a project.

positional arguments:
  config_file               Project configuration file (YAML).

optional arguments:
  -h, --help                show this help message and exit
  -n SAMPLE_NAME [SAMPLE_NAME ...], --sample-name SAMPLE_NAME [SAMPLE_NAME ...]
                            Name of the samples to inspect.
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Path to the output directory
  --submission-subdir SUBMISSION_SUBDIR
                            Name of the submission subdirectory
  --results-subdir RESULTS_SUBDIR
                            Name of the results subdirectory
  --pipeline-interfaces-key PIPELINE_INTERFACES_KEY
                            Name of sample attribute to look for pipeline interface sources in
  --toggle-key TOGGLE_KEY   Name of sample attribute to look for toggle values in
  --pipeline-interfaces P [P ...]
                            Path to a pipeline interface files
  --file-checks             Perform input file checks. Default=True.
  -d, --dry-run             Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                            List of of amendments to activate

select samples:
  This group of arguments lets you specify samples to use by exclusion OR inclusion of the samples
  attribute values.

  --selector-attribute SELECTOR_ATTRIBUTE
                            Specify the attribute for samples exclusion OR inclusion
  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                            Operate only on samples that either lack this attribute value or for
                            which this value is not in this collection.
  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
                            Operate only on samples associated with these attribute values; if not
                            provided, all samples are used.
```

## `looper init --help`
```console
usage: looper init [-h] config_file

Initialize looper dotfile.

positional arguments:
  config_file  Project configuration file (YAML).

optional arguments:
  -h, --help   show this help message and exit
```

## `looper destroy --help`
```console
usage: looper destroy [-h] [--force-yes] [-o OUTPUT_DIR] [--submission-subdir SUBMISSION_SUBDIR]
                      [--results-subdir RESULTS_SUBDIR]
                      [--pipeline-interfaces-key PIPELINE_INTERFACES_KEY] [--toggle-key TOGGLE_KEY]
                      [--pipeline-interfaces P [P ...]] [--file-checks] [-d]
                      [--selector-attribute SELECTOR_ATTRIBUTE]
                      [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]] |
                      --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                      [-a AMENDMENTS [AMENDMENTS ...]]
                      [config_file]

Remove output files of the project.

positional arguments:
  config_file               Project configuration file (YAML).

optional arguments:
  -h, --help                show this help message and exit
  --force-yes               Provide upfront confirmation of destruction intent, to skip console
                            query. Default=False
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Path to the output directory
  --submission-subdir SUBMISSION_SUBDIR
                            Name of the submission subdirectory
  --results-subdir RESULTS_SUBDIR
                            Name of the results subdirectory
  --pipeline-interfaces-key PIPELINE_INTERFACES_KEY
                            Name of sample attribute to look for pipeline interface sources in
  --toggle-key TOGGLE_KEY   Name of sample attribute to look for toggle values in
  --pipeline-interfaces P [P ...]
                            Path to a pipeline interface files
  --file-checks             Perform input file checks. Default=True.
  -d, --dry-run             Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                            List of of amendments to activate

select samples:
  This group of arguments lets you specify samples to use by exclusion OR inclusion of the samples
  attribute values.

  --selector-attribute SELECTOR_ATTRIBUTE
                            Specify the attribute for samples exclusion OR inclusion
  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                            Operate only on samples that either lack this attribute value or for
                            which this value is not in this collection.
  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
                            Operate only on samples associated with these attribute values; if not
                            provided, all samples are used.
```

## `looper check --help`
```console
usage: looper check [-h] [-A] [-F [FLAGS [FLAGS ...]]] [-o OUTPUT_DIR]
                    [--submission-subdir SUBMISSION_SUBDIR] [--results-subdir RESULTS_SUBDIR]
                    [--pipeline-interfaces-key PIPELINE_INTERFACES_KEY] [--toggle-key TOGGLE_KEY]
                    [--pipeline-interfaces P [P ...]] [--file-checks] [-d]
                    [--selector-attribute SELECTOR_ATTRIBUTE]
                    [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]] |
                    --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                    [-a AMENDMENTS [AMENDMENTS ...]]
                    [config_file]

Check flag status of current runs.

positional arguments:
  config_file               Project configuration file (YAML).

optional arguments:
  -h, --help                show this help message and exit
  -A, --all-folders         Check status for all project's output folders, not just those for
                            samples specified in the config file used. Default=False
  -F [FLAGS [FLAGS ...]], --flags [FLAGS [FLAGS ...]]
                            Check on only these flags/status values.
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Path to the output directory
  --submission-subdir SUBMISSION_SUBDIR
                            Name of the submission subdirectory
  --results-subdir RESULTS_SUBDIR
                            Name of the results subdirectory
  --pipeline-interfaces-key PIPELINE_INTERFACES_KEY
                            Name of sample attribute to look for pipeline interface sources in
  --toggle-key TOGGLE_KEY   Name of sample attribute to look for toggle values in
  --pipeline-interfaces P [P ...]
                            Path to a pipeline interface files
  --file-checks             Perform input file checks. Default=True.
  -d, --dry-run             Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                            List of of amendments to activate

select samples:
  This group of arguments lets you specify samples to use by exclusion OR inclusion of the samples
  attribute values.

  --selector-attribute SELECTOR_ATTRIBUTE
                            Specify the attribute for samples exclusion OR inclusion
  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                            Operate only on samples that either lack this attribute value or for
                            which this value is not in this collection.
  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
                            Operate only on samples associated with these attribute values; if not
                            provided, all samples are used.
```

## `looper clean --help`
```console
usage: looper clean [-h] [--force-yes] [-o OUTPUT_DIR] [--submission-subdir SUBMISSION_SUBDIR]
                    [--results-subdir RESULTS_SUBDIR]
                    [--pipeline-interfaces-key PIPELINE_INTERFACES_KEY] [--toggle-key TOGGLE_KEY]
                    [--pipeline-interfaces P [P ...]] [--file-checks] [-d]
                    [--selector-attribute SELECTOR_ATTRIBUTE]
                    [--selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]] |
                    --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]]
                    [-a AMENDMENTS [AMENDMENTS ...]]
                    [config_file]

Run clean scripts of already processed jobs.

positional arguments:
  config_file               Project configuration file (YAML).

optional arguments:
  -h, --help                show this help message and exit
  --force-yes               Provide upfront confirmation of destruction intent, to skip console
                            query. Default=False
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            Path to the output directory
  --submission-subdir SUBMISSION_SUBDIR
                            Name of the submission subdirectory
  --results-subdir RESULTS_SUBDIR
                            Name of the results subdirectory
  --pipeline-interfaces-key PIPELINE_INTERFACES_KEY
                            Name of sample attribute to look for pipeline interface sources in
  --toggle-key TOGGLE_KEY   Name of sample attribute to look for toggle values in
  --pipeline-interfaces P [P ...]
                            Path to a pipeline interface files
  --file-checks             Perform input file checks. Default=True.
  -d, --dry-run             Don't actually submit the jobs. Default=False
  -a AMENDMENTS [AMENDMENTS ...], --amendments AMENDMENTS [AMENDMENTS ...]
                            List of of amendments to activate

select samples:
  This group of arguments lets you specify samples to use by exclusion OR inclusion of the samples
  attribute values.

  --selector-attribute SELECTOR_ATTRIBUTE
                            Specify the attribute for samples exclusion OR inclusion
  --selector-exclude [SELECTOR_EXCLUDE [SELECTOR_EXCLUDE ...]]
                            Operate only on samples that either lack this attribute value or for
                            which this value is not in this collection.
  --selector-include [SELECTOR_INCLUDE [SELECTOR_INCLUDE ...]]
                            Operate only on samples associated with these attribute values; if not
                            provided, all samples are used.
```

