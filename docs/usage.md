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

- `looper inspect`: Display the Project or Sample information

- `looper init`: Initialize a looper dotfile (`.looper.yaml`) in the current directory


Here you can see the command-line usage instructions for the main looper command and for each subcommand:
## `looper --help`
```console
version: 1.5.2-dev
usage: looper [-h] [--version] [--logfile LOGFILE] [--dbg] [--silent]
              [--verbosity V] [--logdev]
              {run,rerun,runp,table,report,destroy,check,clean,inspect,init,init-piface,link}
              ...

looper - A project job submission engine and project manager.

positional arguments:
  {run,rerun,runp,table,report,destroy,check,clean,inspect,init,init-piface,link}
    run                 Run or submit sample jobs.
    rerun               Resubmit sample jobs with failed flags.
    runp                Run or submit project jobs.
    table               Write summary stats table for project samples.
    report              Create browsable HTML report of project results.
    destroy             Remove output files of the project.
    check               Check flag status of current runs.
    clean               Run clean scripts of already processed jobs.
    inspect             Print information about a project.
    init                Initialize looper config file.
    init-piface         Initialize generic pipeline interface.
    link                Create directory of symlinks for reported results.

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --logfile LOGFILE     Optional output file for looper logs (default: None)
  --dbg                 Turn on debug mode (default: False)
  --silent              Silence logging. Overrides verbosity.
  --verbosity V         Set logging level (1-5 or logging module level name)
  --logdev              Expand content of logging message format.

For subcommand-specific options, type: 'looper <subcommand> -h'
https://github.com/pepkit/looper
```

## `looper run --help`
```console
usage: looper run [-h] [-i] [-d] [-t S] [-x S] [-y S] [-f] [--divvy DIVCFG] [-p P] [-s S]
                  [-c K [K ...]] [-u X] [-n N] [--looper-config LOOPER_CONFIG]
                  [-S YAML [YAML ...]] [-P YAML [YAML ...]] [-l N] [-k N]
                  [--sel-attr ATTR] [--sel-excl [E ...] | --sel-incl [I ...]]
                  [-a A [A ...]]
                  [config_file]

Run or submit sample jobs.

positional arguments:
  config_file                        Project configuration file (YAML) or pephub registry
                                     path.

options:
  -h, --help                         show this help message and exit
  -i, --ignore-flags                 Ignore run status flags? Default=False
  -d, --dry-run                      Don't actually submit the jobs. Default=False
  -t S, --time-delay S               Time delay in seconds between job submissions
  -x S, --command-extra S            String to append to every command
  -y S, --command-extra-override S   Same as command-extra, but overrides values in PEP
  -f, --skip-file-checks             Do not perform input file checks
  -u X, --lump X                     Total input file size (GB) to batch into one job
  -n N, --lumpn N                    Number of commands to batch into one job
  --looper-config LOOPER_CONFIG      Looper configuration file (YAML)
  -S YAML [YAML ...], --sample-pipeline-interfaces YAML [YAML ...]
                                     Path to looper sample config file
  -P YAML [YAML ...], --project-pipeline-interfaces YAML [YAML ...]
                                     Path to looper project config file
  -a A [A ...], --amend A [A ...]    List of amendments to activate

divvy arguments:
  Configure divvy to change computing settings

  --divvy DIVCFG                     Path to divvy configuration file. Default=$DIVCFG env
                                     variable. Currently: not set
  -p P, --package P                  Name of computing resource package to use
  -s S, --settings S                 Path to a YAML settings file with compute settings
  -c K [K ...], --compute K [K ...]  List of key-value pairs (k1=v1)

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -l N, --limit N                    Limit to n samples
  -k N, --skip N                     Skip samples by numerical index
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E ...]                 Exclude samples with these values
  --sel-incl [I ...]                 Include only samples with these values
```

## `looper runp --help`
```console
usage: looper runp [-h] [-i] [-d] [-t S] [-x S] [-y S] [-f] [--divvy DIVCFG] [-p P] [-s S]
                   [-c K [K ...]] [--looper-config LOOPER_CONFIG] [-S YAML [YAML ...]]
                   [-P YAML [YAML ...]] [-l N] [-k N] [--sel-attr ATTR]
                   [--sel-excl [E ...] | --sel-incl [I ...]] [-a A [A ...]]
                   [config_file]

Run or submit project jobs.

positional arguments:
  config_file                        Project configuration file (YAML) or pephub registry
                                     path.

options:
  -h, --help                         show this help message and exit
  -i, --ignore-flags                 Ignore run status flags? Default=False
  -d, --dry-run                      Don't actually submit the jobs. Default=False
  -t S, --time-delay S               Time delay in seconds between job submissions
  -x S, --command-extra S            String to append to every command
  -y S, --command-extra-override S   Same as command-extra, but overrides values in PEP
  -f, --skip-file-checks             Do not perform input file checks
  --looper-config LOOPER_CONFIG      Looper configuration file (YAML)
  -S YAML [YAML ...], --sample-pipeline-interfaces YAML [YAML ...]
                                     Path to looper sample config file
  -P YAML [YAML ...], --project-pipeline-interfaces YAML [YAML ...]
                                     Path to looper project config file
  -a A [A ...], --amend A [A ...]    List of amendments to activate

divvy arguments:
  Configure divvy to change computing settings

  --divvy DIVCFG                     Path to divvy configuration file. Default=$DIVCFG env
                                     variable. Currently: not set
  -p P, --package P                  Name of computing resource package to use
  -s S, --settings S                 Path to a YAML settings file with compute settings
  -c K [K ...], --compute K [K ...]  List of key-value pairs (k1=v1)

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -l N, --limit N                    Limit to n samples
  -k N, --skip N                     Skip samples by numerical index
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E ...]                 Exclude samples with these values
  --sel-incl [I ...]                 Include only samples with these values
```

## `looper rerun --help`
```console
usage: looper rerun [-h] [-i] [-d] [-t S] [-x S] [-y S] [-f] [--divvy DIVCFG] [-p P]
                    [-s S] [-c K [K ...]] [-u X] [-n N] [--looper-config LOOPER_CONFIG]
                    [-S YAML [YAML ...]] [-P YAML [YAML ...]] [-l N] [-k N]
                    [--sel-attr ATTR] [--sel-excl [E ...] | --sel-incl [I ...]]
                    [-a A [A ...]]
                    [config_file]

Resubmit sample jobs with failed flags.

positional arguments:
  config_file                        Project configuration file (YAML) or pephub registry
                                     path.

options:
  -h, --help                         show this help message and exit
  -i, --ignore-flags                 Ignore run status flags? Default=False
  -d, --dry-run                      Don't actually submit the jobs. Default=False
  -t S, --time-delay S               Time delay in seconds between job submissions
  -x S, --command-extra S            String to append to every command
  -y S, --command-extra-override S   Same as command-extra, but overrides values in PEP
  -f, --skip-file-checks             Do not perform input file checks
  -u X, --lump X                     Total input file size (GB) to batch into one job
  -n N, --lumpn N                    Number of commands to batch into one job
  --looper-config LOOPER_CONFIG      Looper configuration file (YAML)
  -S YAML [YAML ...], --sample-pipeline-interfaces YAML [YAML ...]
                                     Path to looper sample config file
  -P YAML [YAML ...], --project-pipeline-interfaces YAML [YAML ...]
                                     Path to looper project config file
  -a A [A ...], --amend A [A ...]    List of amendments to activate

divvy arguments:
  Configure divvy to change computing settings

  --divvy DIVCFG                     Path to divvy configuration file. Default=$DIVCFG env
                                     variable. Currently: not set
  -p P, --package P                  Name of computing resource package to use
  -s S, --settings S                 Path to a YAML settings file with compute settings
  -c K [K ...], --compute K [K ...]  List of key-value pairs (k1=v1)

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -l N, --limit N                    Limit to n samples
  -k N, --skip N                     Skip samples by numerical index
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E ...]                 Exclude samples with these values
  --sel-incl [I ...]                 Include only samples with these values
```

## `looper report --help`
```console
usage: looper report [-h] [--looper-config LOOPER_CONFIG] [-S YAML [YAML ...]]
                     [-P YAML [YAML ...]] [-l N] [-k N] [--sel-attr ATTR]
                     [--sel-excl [E ...] | --sel-incl [I ...]] [-a A [A ...]] [--project]
                     [config_file]

Create browsable HTML report of project results.

positional arguments:
  config_file                        Project configuration file (YAML) or pephub registry
                                     path.

options:
  -h, --help                         show this help message and exit
  --looper-config LOOPER_CONFIG      Looper configuration file (YAML)
  -S YAML [YAML ...], --sample-pipeline-interfaces YAML [YAML ...]
                                     Path to looper sample config file
  -P YAML [YAML ...], --project-pipeline-interfaces YAML [YAML ...]
                                     Path to looper project config file
  -a A [A ...], --amend A [A ...]    List of amendments to activate
  --project                          Process project-level pipelines

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -l N, --limit N                    Limit to n samples
  -k N, --skip N                     Skip samples by numerical index
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E ...]                 Exclude samples with these values
  --sel-incl [I ...]                 Include only samples with these values
```

## `looper table --help`
```console
usage: looper table [-h] [--looper-config LOOPER_CONFIG] [-S YAML [YAML ...]]
                    [-P YAML [YAML ...]] [-l N] [-k N] [--sel-attr ATTR]
                    [--sel-excl [E ...] | --sel-incl [I ...]] [-a A [A ...]] [--project]
                    [config_file]

Write summary stats table for project samples.

positional arguments:
  config_file                        Project configuration file (YAML) or pephub registry
                                     path.

options:
  -h, --help                         show this help message and exit
  --looper-config LOOPER_CONFIG      Looper configuration file (YAML)
  -S YAML [YAML ...], --sample-pipeline-interfaces YAML [YAML ...]
                                     Path to looper sample config file
  -P YAML [YAML ...], --project-pipeline-interfaces YAML [YAML ...]
                                     Path to looper project config file
  -a A [A ...], --amend A [A ...]    List of amendments to activate
  --project                          Process project-level pipelines

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -l N, --limit N                    Limit to n samples
  -k N, --skip N                     Skip samples by numerical index
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E ...]                 Exclude samples with these values
  --sel-incl [I ...]                 Include only samples with these values
```

## `looper inspect --help`
```console
usage: looper inspect [-h] [--looper-config LOOPER_CONFIG] [-S YAML [YAML ...]]
                      [-P YAML [YAML ...]] [-l N] [-k N] [--sel-attr ATTR]
                      [--sel-excl [E ...] | --sel-incl [I ...]] [-a A [A ...]]
                      [--sample-names [SAMPLE_NAMES ...]] [--attr-limit ATTR_LIMIT]
                      [config_file]

Print information about a project.

positional arguments:
  config_file                        Project configuration file (YAML) or pephub registry
                                     path.

options:
  -h, --help                         show this help message and exit
  --looper-config LOOPER_CONFIG      Looper configuration file (YAML)
  -S YAML [YAML ...], --sample-pipeline-interfaces YAML [YAML ...]
                                     Path to looper sample config file
  -P YAML [YAML ...], --project-pipeline-interfaces YAML [YAML ...]
                                     Path to looper project config file
  -a A [A ...], --amend A [A ...]    List of amendments to activate
  --sample-names [SAMPLE_NAMES ...]  Names of the samples to inspect
  --attr-limit ATTR_LIMIT            Number of attributes to display

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -l N, --limit N                    Limit to n samples
  -k N, --skip N                     Skip samples by numerical index
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E ...]                 Exclude samples with these values
  --sel-incl [I ...]                 Include only samples with these values
```

## `looper init --help`
```console
usage: looper init [-h] [-f] [-o DIR] [-S YAML [YAML ...]] [-P YAML [YAML ...]] [-p]
                   pep_config

Initialize looper config file.

positional arguments:
  pep_config                         Project configuration file (PEP)

options:
  -h, --help                         show this help message and exit
  -f, --force                        Force overwrite
  -o DIR, --output-dir DIR
  -S YAML [YAML ...], --sample-pipeline-interfaces YAML [YAML ...]
                                     Path to looper sample config file
  -P YAML [YAML ...], --project-pipeline-interfaces YAML [YAML ...]
                                     Path to looper project config file
  -p, --piface                       Generates generic pipeline interface
```

## `looper destroy --help`
```console
usage: looper destroy [-h] [-d] [--force-yes] [--looper-config LOOPER_CONFIG]
                      [-S YAML [YAML ...]] [-P YAML [YAML ...]] [-l N] [-k N]
                      [--sel-attr ATTR] [--sel-excl [E ...] | --sel-incl [I ...]]
                      [-a A [A ...]] [--project]
                      [config_file]

Remove output files of the project.

positional arguments:
  config_file                        Project configuration file (YAML) or pephub registry
                                     path.

options:
  -h, --help                         show this help message and exit
  -d, --dry-run                      Don't actually submit the jobs. Default=False
  --force-yes                        Provide upfront confirmation of destruction intent,
                                     to skip console query. Default=False
  --looper-config LOOPER_CONFIG      Looper configuration file (YAML)
  -S YAML [YAML ...], --sample-pipeline-interfaces YAML [YAML ...]
                                     Path to looper sample config file
  -P YAML [YAML ...], --project-pipeline-interfaces YAML [YAML ...]
                                     Path to looper project config file
  -a A [A ...], --amend A [A ...]    List of amendments to activate
  --project                          Process project-level pipelines

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -l N, --limit N                    Limit to n samples
  -k N, --skip N                     Skip samples by numerical index
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E ...]                 Exclude samples with these values
  --sel-incl [I ...]                 Include only samples with these values
```

## `looper check --help`
```console
usage: looper check [-h] [--describe-codes] [--itemized] [-f [F ...]]
                    [--looper-config LOOPER_CONFIG] [-S YAML [YAML ...]]
                    [-P YAML [YAML ...]] [-l N] [-k N] [--sel-attr ATTR]
                    [--sel-excl [E ...] | --sel-incl [I ...]] [-a A [A ...]] [--project]
                    [config_file]

Check flag status of current runs.

positional arguments:
  config_file                        Project configuration file (YAML) or pephub registry
                                     path.

options:
  -h, --help                         show this help message and exit
  --describe-codes                   Show status codes description
  --itemized                         Show a detailed, by sample statuses
  -f [F ...], --flags [F ...]        Check on only these flags/status values
  --looper-config LOOPER_CONFIG      Looper configuration file (YAML)
  -S YAML [YAML ...], --sample-pipeline-interfaces YAML [YAML ...]
                                     Path to looper sample config file
  -P YAML [YAML ...], --project-pipeline-interfaces YAML [YAML ...]
                                     Path to looper project config file
  -a A [A ...], --amend A [A ...]    List of amendments to activate
  --project                          Process project-level pipelines

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -l N, --limit N                    Limit to n samples
  -k N, --skip N                     Skip samples by numerical index
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E ...]                 Exclude samples with these values
  --sel-incl [I ...]                 Include only samples with these values
```

## `looper clean --help`
```console
usage: looper clean [-h] [-d] [--force-yes] [--looper-config LOOPER_CONFIG]
                    [-S YAML [YAML ...]] [-P YAML [YAML ...]] [-l N] [-k N]
                    [--sel-attr ATTR] [--sel-excl [E ...] | --sel-incl [I ...]]
                    [-a A [A ...]]
                    [config_file]

Run clean scripts of already processed jobs.

positional arguments:
  config_file                        Project configuration file (YAML) or pephub registry
                                     path.

options:
  -h, --help                         show this help message and exit
  -d, --dry-run                      Don't actually submit the jobs. Default=False
  --force-yes                        Provide upfront confirmation of destruction intent,
                                     to skip console query. Default=False
  --looper-config LOOPER_CONFIG      Looper configuration file (YAML)
  -S YAML [YAML ...], --sample-pipeline-interfaces YAML [YAML ...]
                                     Path to looper sample config file
  -P YAML [YAML ...], --project-pipeline-interfaces YAML [YAML ...]
                                     Path to looper project config file
  -a A [A ...], --amend A [A ...]    List of amendments to activate

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -l N, --limit N                    Limit to n samples
  -k N, --skip N                     Skip samples by numerical index
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E ...]                 Exclude samples with these values
  --sel-incl [I ...]                 Include only samples with these values
```

