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
usage: looper [-h] [-v] [--silent] [--verbosity VERBOSITY] [--logdev]
              {run,rerun,runp,table,report,destroy,check,clean,init,init_piface,link,inspect}
              ...

Looper Pydantic Argument Parser

commands:
  {run,rerun,runp,table,report,destroy,check,clean,init,init_piface,link,inspect}
    run                 Run or submit sample jobs.
    rerun               Resubmit sample jobs with failed flags.
    runp                Run or submit project jobs.
    table               Write summary stats table for project samples.
    report              Create browsable HTML report of project results.
    destroy             Remove output files of the project.
    check               Check flag status of current runs.
    clean               Run clean scripts of already processed jobs.
    init                Initialize looper config file.
    init_piface         Initialize generic pipeline interface.
    link                Create directory of symlinks for reported results.
    inspect             Print information about a project.

optional arguments:
  --silent              Whether to silence logging (default: False)
  --verbosity VERBOSITY
                        Alternate mode of expression for logging level that
                        better accords with intuition about how to convey
                        this. (default: None)
  --logdev              Whether to log in development mode; possibly among
                        other behavioral changes to logs handling, use a more
                        information-rich message format template. (default:
                        False)

help:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
```

## `looper run --help`
```console
usage: looper run [-h] [-i] [-t TIME_DELAY] [-d] [-x COMMAND_EXTRA]
                  [-y COMMAND_EXTRA_OVERRIDE] [-u LUMP] [-n LUMP_N]
                  [-j LUMP_J] [--divvy DIVVY] [-f] [-c COMPUTE [COMPUTE ...]]
                  [--package PACKAGE] [--settings SETTINGS]
                  [--exc-flag EXC_FLAG [EXC_FLAG ...]]
                  [--sel-flag SEL_FLAG [SEL_FLAG ...]] [--sel-attr SEL_ATTR]
                  [--sel-incl SEL_INCL [SEL_INCL ...]] [--sel-excl SEL_EXCL]
                  [-l LIMIT] [-k SKIP] [--pep-config PEP_CONFIG]
                  [-o OUTPUT_DIR] [--config-file CONFIG_FILE]
                  [--looper-config LOOPER_CONFIG]
                  [-S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]]
                  [-P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]]
                  [--pipestat PIPESTAT] [--amend AMEND [AMEND ...]]
                  [--project]

optional arguments:
  -i, --ignore-flags    Ignore run status flags (default: False)
  -t TIME_DELAY, --time-delay TIME_DELAY
                        Time delay in seconds between job submissions (min: 0,
                        max: 30) (default: 0)
  -d, --dry-run         Don't actually submit jobs (default: False)
  -x COMMAND_EXTRA, --command-extra COMMAND_EXTRA
                        String to append to every command (default: )
  -y COMMAND_EXTRA_OVERRIDE, --command-extra-override COMMAND_EXTRA_OVERRIDE
                        Same as command-extra, but overrides values in PEP
                        (default: )
  -u LUMP, --lump LUMP  Total input file size (GB) to batch into one job
                        (default: None)
  -n LUMP_N, --lump-n LUMP_N
                        Number of commands to batch into one job (default:
                        None)
  -j LUMP_J, --lump-j LUMP_J
                        Lump samples into number of jobs. (default: None)
  --divvy DIVVY         Path to divvy configuration file. Default=$DIVCFG env
                        variable. Currently: not set (default: None)
  -f, --skip-file-checks
                        Do not perform input file checks (default: False)
  -c COMPUTE [COMPUTE ...], --compute COMPUTE [COMPUTE ...]
                        List of key-value pairs (k1=v1) (default: [])
  --package PACKAGE     Name of computing resource package to use (default:
                        None)
  --settings SETTINGS   Path to a YAML settings file with compute settings
                        (default: )
  --exc-flag EXC_FLAG [EXC_FLAG ...]
                        Sample exclusion flag (default: [])
  --sel-flag SEL_FLAG [SEL_FLAG ...]
                        Sample selection flag (default: [])
  --sel-attr SEL_ATTR   Attribute for sample exclusion OR inclusion (default:
                        toggle)
  --sel-incl SEL_INCL [SEL_INCL ...]
                        Include only samples with these values (default: [])
  --sel-excl SEL_EXCL   Exclude samples with these values (default: )
  -l LIMIT, --limit LIMIT
                        Limit to n samples (default: None)
  -k SKIP, --skip SKIP  Skip samples by numerical index (default: None)
  --pep-config PEP_CONFIG
                        PEP configuration file (default: None)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: None)
  --config-file CONFIG_FILE
                        Project configuration file (default: None)
  --looper-config LOOPER_CONFIG
                        Looper configuration file (YAML) (default: None)
  -S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...], --sample-pipeline-interfaces SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]
                        Paths to looper sample pipeline interfaces (default:
                        [])
  -P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...], --project-pipeline-interfaces PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]
                        Paths to looper project pipeline interfaces (default:
                        [])
  --pipestat PIPESTAT   Path to pipestat files. (default: None)
  --amend AMEND [AMEND ...]
                        List of amendments to activate (default: [])
  --project             Is this command executed for project-level? (default:
                        False)

help:
  -h, --help            show this help message and exit
```

## `looper runp --help`
```console
usage: looper runp [-h] [-i] [-t TIME_DELAY] [-d] [-x COMMAND_EXTRA]
                   [-y COMMAND_EXTRA_OVERRIDE] [-u LUMP] [-n LUMP_N]
                   [--divvy DIVVY] [-f] [-c COMPUTE [COMPUTE ...]]
                   [--package PACKAGE] [--settings SETTINGS]
                   [--exc-flag EXC_FLAG [EXC_FLAG ...]]
                   [--sel-flag SEL_FLAG [SEL_FLAG ...]] [--sel-attr SEL_ATTR]
                   [--sel-incl SEL_INCL [SEL_INCL ...]] [--sel-excl SEL_EXCL]
                   [-l LIMIT] [-k SKIP] [--pep-config PEP_CONFIG]
                   [-o OUTPUT_DIR] [--config-file CONFIG_FILE]
                   [--looper-config LOOPER_CONFIG]
                   [-S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]]
                   [-P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]]
                   [--pipestat PIPESTAT] [--amend AMEND [AMEND ...]]
                   [--project]

optional arguments:
  -i, --ignore-flags    Ignore run status flags (default: False)
  -t TIME_DELAY, --time-delay TIME_DELAY
                        Time delay in seconds between job submissions (min: 0,
                        max: 30) (default: 0)
  -d, --dry-run         Don't actually submit jobs (default: False)
  -x COMMAND_EXTRA, --command-extra COMMAND_EXTRA
                        String to append to every command (default: )
  -y COMMAND_EXTRA_OVERRIDE, --command-extra-override COMMAND_EXTRA_OVERRIDE
                        Same as command-extra, but overrides values in PEP
                        (default: )
  -u LUMP, --lump LUMP  Total input file size (GB) to batch into one job
                        (default: None)
  -n LUMP_N, --lump-n LUMP_N
                        Number of commands to batch into one job (default:
                        None)
  --divvy DIVVY         Path to divvy configuration file. Default=$DIVCFG env
                        variable. Currently: not set (default: None)
  -f, --skip-file-checks
                        Do not perform input file checks (default: False)
  -c COMPUTE [COMPUTE ...], --compute COMPUTE [COMPUTE ...]
                        List of key-value pairs (k1=v1) (default: [])
  --package PACKAGE     Name of computing resource package to use (default:
                        None)
  --settings SETTINGS   Path to a YAML settings file with compute settings
                        (default: )
  --exc-flag EXC_FLAG [EXC_FLAG ...]
                        Sample exclusion flag (default: [])
  --sel-flag SEL_FLAG [SEL_FLAG ...]
                        Sample selection flag (default: [])
  --sel-attr SEL_ATTR   Attribute for sample exclusion OR inclusion (default:
                        toggle)
  --sel-incl SEL_INCL [SEL_INCL ...]
                        Include only samples with these values (default: [])
  --sel-excl SEL_EXCL   Exclude samples with these values (default: )
  -l LIMIT, --limit LIMIT
                        Limit to n samples (default: None)
  -k SKIP, --skip SKIP  Skip samples by numerical index (default: None)
  --pep-config PEP_CONFIG
                        PEP configuration file (default: None)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: None)
  --config-file CONFIG_FILE
                        Project configuration file (default: None)
  --looper-config LOOPER_CONFIG
                        Looper configuration file (YAML) (default: None)
  -S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...], --sample-pipeline-interfaces SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]
                        Paths to looper sample pipeline interfaces (default:
                        [])
  -P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...], --project-pipeline-interfaces PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]
                        Paths to looper project pipeline interfaces (default:
                        [])
  --pipestat PIPESTAT   Path to pipestat files. (default: None)
  --amend AMEND [AMEND ...]
                        List of amendments to activate (default: [])
  --project             Is this command executed for project-level? (default:
                        False)

help:
  -h, --help            show this help message and exit
```

## `looper rerun --help`
```console
usage: looper rerun [-h] [-i] [-t TIME_DELAY] [-d] [-x COMMAND_EXTRA]
                    [-y COMMAND_EXTRA_OVERRIDE] [-u LUMP] [-n LUMP_N]
                    [-j LUMP_J] [--divvy DIVVY] [-f]
                    [-c COMPUTE [COMPUTE ...]] [--package PACKAGE]
                    [--settings SETTINGS] [--exc-flag EXC_FLAG [EXC_FLAG ...]]
                    [--sel-flag SEL_FLAG [SEL_FLAG ...]] [--sel-attr SEL_ATTR]
                    [--sel-incl SEL_INCL [SEL_INCL ...]] [--sel-excl SEL_EXCL]
                    [-l LIMIT] [-k SKIP] [--pep-config PEP_CONFIG]
                    [-o OUTPUT_DIR] [--config-file CONFIG_FILE]
                    [--looper-config LOOPER_CONFIG]
                    [-S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]]
                    [-P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]]
                    [--pipestat PIPESTAT] [--amend AMEND [AMEND ...]]
                    [--project]

optional arguments:
  -i, --ignore-flags    Ignore run status flags (default: False)
  -t TIME_DELAY, --time-delay TIME_DELAY
                        Time delay in seconds between job submissions (min: 0,
                        max: 30) (default: 0)
  -d, --dry-run         Don't actually submit jobs (default: False)
  -x COMMAND_EXTRA, --command-extra COMMAND_EXTRA
                        String to append to every command (default: )
  -y COMMAND_EXTRA_OVERRIDE, --command-extra-override COMMAND_EXTRA_OVERRIDE
                        Same as command-extra, but overrides values in PEP
                        (default: )
  -u LUMP, --lump LUMP  Total input file size (GB) to batch into one job
                        (default: None)
  -n LUMP_N, --lump-n LUMP_N
                        Number of commands to batch into one job (default:
                        None)
  -j LUMP_J, --lump-j LUMP_J
                        Lump samples into number of jobs. (default: None)
  --divvy DIVVY         Path to divvy configuration file. Default=$DIVCFG env
                        variable. Currently: not set (default: None)
  -f, --skip-file-checks
                        Do not perform input file checks (default: False)
  -c COMPUTE [COMPUTE ...], --compute COMPUTE [COMPUTE ...]
                        List of key-value pairs (k1=v1) (default: [])
  --package PACKAGE     Name of computing resource package to use (default:
                        None)
  --settings SETTINGS   Path to a YAML settings file with compute settings
                        (default: )
  --exc-flag EXC_FLAG [EXC_FLAG ...]
                        Sample exclusion flag (default: [])
  --sel-flag SEL_FLAG [SEL_FLAG ...]
                        Sample selection flag (default: [])
  --sel-attr SEL_ATTR   Attribute for sample exclusion OR inclusion (default:
                        toggle)
  --sel-incl SEL_INCL [SEL_INCL ...]
                        Include only samples with these values (default: [])
  --sel-excl SEL_EXCL   Exclude samples with these values (default: )
  -l LIMIT, --limit LIMIT
                        Limit to n samples (default: None)
  -k SKIP, --skip SKIP  Skip samples by numerical index (default: None)
  --pep-config PEP_CONFIG
                        PEP configuration file (default: None)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: None)
  --config-file CONFIG_FILE
                        Project configuration file (default: None)
  --looper-config LOOPER_CONFIG
                        Looper configuration file (YAML) (default: None)
  -S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...], --sample-pipeline-interfaces SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]
                        Paths to looper sample pipeline interfaces (default:
                        [])
  -P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...], --project-pipeline-interfaces PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]
                        Paths to looper project pipeline interfaces (default:
                        [])
  --pipestat PIPESTAT   Path to pipestat files. (default: None)
  --amend AMEND [AMEND ...]
                        List of amendments to activate (default: [])
  --project             Is this command executed for project-level? (default:
                        False)

help:
  -h, --help            show this help message and exit
```

## `looper report --help`
```console
usage: looper report [-h] [--portable] [--settings SETTINGS]
                     [--exc-flag EXC_FLAG [EXC_FLAG ...]]
                     [--sel-flag SEL_FLAG [SEL_FLAG ...]]
                     [--sel-attr SEL_ATTR]
                     [--sel-incl SEL_INCL [SEL_INCL ...]]
                     [--sel-excl SEL_EXCL] [-l LIMIT] [-k SKIP]
                     [--pep-config PEP_CONFIG] [-o OUTPUT_DIR]
                     [--config-file CONFIG_FILE]
                     [--looper-config LOOPER_CONFIG]
                     [-S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]]
                     [-P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]]
                     [--pipestat PIPESTAT] [--amend AMEND [AMEND ...]]
                     [--project]

optional arguments:
  --portable            Makes html report portable. (default: False)
  --settings SETTINGS   Path to a YAML settings file with compute settings
                        (default: )
  --exc-flag EXC_FLAG [EXC_FLAG ...]
                        Sample exclusion flag (default: [])
  --sel-flag SEL_FLAG [SEL_FLAG ...]
                        Sample selection flag (default: [])
  --sel-attr SEL_ATTR   Attribute for sample exclusion OR inclusion (default:
                        toggle)
  --sel-incl SEL_INCL [SEL_INCL ...]
                        Include only samples with these values (default: [])
  --sel-excl SEL_EXCL   Exclude samples with these values (default: )
  -l LIMIT, --limit LIMIT
                        Limit to n samples (default: None)
  -k SKIP, --skip SKIP  Skip samples by numerical index (default: None)
  --pep-config PEP_CONFIG
                        PEP configuration file (default: None)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: None)
  --config-file CONFIG_FILE
                        Project configuration file (default: None)
  --looper-config LOOPER_CONFIG
                        Looper configuration file (YAML) (default: None)
  -S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...], --sample-pipeline-interfaces SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]
                        Paths to looper sample pipeline interfaces (default:
                        [])
  -P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...], --project-pipeline-interfaces PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]
                        Paths to looper project pipeline interfaces (default:
                        [])
  --pipestat PIPESTAT   Path to pipestat files. (default: None)
  --amend AMEND [AMEND ...]
                        List of amendments to activate (default: [])
  --project             Is this command executed for project-level? (default:
                        False)

help:
  -h, --help            show this help message and exit
```

## `looper table --help`
```console
usage: looper table [-h] [--settings SETTINGS]
                    [--exc-flag EXC_FLAG [EXC_FLAG ...]]
                    [--sel-flag SEL_FLAG [SEL_FLAG ...]] [--sel-attr SEL_ATTR]
                    [--sel-incl SEL_INCL [SEL_INCL ...]] [--sel-excl SEL_EXCL]
                    [-l LIMIT] [-k SKIP] [--pep-config PEP_CONFIG]
                    [-o OUTPUT_DIR] [--config-file CONFIG_FILE]
                    [--looper-config LOOPER_CONFIG]
                    [-S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]]
                    [-P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]]
                    [--pipestat PIPESTAT] [--amend AMEND [AMEND ...]]
                    [--project]

optional arguments:
  --settings SETTINGS   Path to a YAML settings file with compute settings
                        (default: )
  --exc-flag EXC_FLAG [EXC_FLAG ...]
                        Sample exclusion flag (default: [])
  --sel-flag SEL_FLAG [SEL_FLAG ...]
                        Sample selection flag (default: [])
  --sel-attr SEL_ATTR   Attribute for sample exclusion OR inclusion (default:
                        toggle)
  --sel-incl SEL_INCL [SEL_INCL ...]
                        Include only samples with these values (default: [])
  --sel-excl SEL_EXCL   Exclude samples with these values (default: )
  -l LIMIT, --limit LIMIT
                        Limit to n samples (default: None)
  -k SKIP, --skip SKIP  Skip samples by numerical index (default: None)
  --pep-config PEP_CONFIG
                        PEP configuration file (default: None)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: None)
  --config-file CONFIG_FILE
                        Project configuration file (default: None)
  --looper-config LOOPER_CONFIG
                        Looper configuration file (YAML) (default: None)
  -S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...], --sample-pipeline-interfaces SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]
                        Paths to looper sample pipeline interfaces (default:
                        [])
  -P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...], --project-pipeline-interfaces PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]
                        Paths to looper project pipeline interfaces (default:
                        [])
  --pipestat PIPESTAT   Path to pipestat files. (default: None)
  --amend AMEND [AMEND ...]
                        List of amendments to activate (default: [])
  --project             Is this command executed for project-level? (default:
                        False)

help:
  -h, --help            show this help message and exit
```

## `looper inspect --help`
```console
usage: looper inspect [-h] [--settings SETTINGS]
                      [--exc-flag EXC_FLAG [EXC_FLAG ...]]
                      [--sel-flag SEL_FLAG [SEL_FLAG ...]]
                      [--sel-attr SEL_ATTR]
                      [--sel-incl SEL_INCL [SEL_INCL ...]]
                      [--sel-excl SEL_EXCL] [-l LIMIT] [-k SKIP]
                      [--pep-config PEP_CONFIG] [-o OUTPUT_DIR]
                      [--config-file CONFIG_FILE]
                      [--looper-config LOOPER_CONFIG]
                      [-S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]]
                      [-P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]]
                      [--pipestat PIPESTAT] [--amend AMEND [AMEND ...]]
                      [--project]

optional arguments:
  --settings SETTINGS   Path to a YAML settings file with compute settings
                        (default: )
  --exc-flag EXC_FLAG [EXC_FLAG ...]
                        Sample exclusion flag (default: [])
  --sel-flag SEL_FLAG [SEL_FLAG ...]
                        Sample selection flag (default: [])
  --sel-attr SEL_ATTR   Attribute for sample exclusion OR inclusion (default:
                        toggle)
  --sel-incl SEL_INCL [SEL_INCL ...]
                        Include only samples with these values (default: [])
  --sel-excl SEL_EXCL   Exclude samples with these values (default: )
  -l LIMIT, --limit LIMIT
                        Limit to n samples (default: None)
  -k SKIP, --skip SKIP  Skip samples by numerical index (default: None)
  --pep-config PEP_CONFIG
                        PEP configuration file (default: None)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: None)
  --config-file CONFIG_FILE
                        Project configuration file (default: None)
  --looper-config LOOPER_CONFIG
                        Looper configuration file (YAML) (default: None)
  -S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...], --sample-pipeline-interfaces SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]
                        Paths to looper sample pipeline interfaces (default:
                        [])
  -P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...], --project-pipeline-interfaces PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]
                        Paths to looper project pipeline interfaces (default:
                        [])
  --pipestat PIPESTAT   Path to pipestat files. (default: None)
  --amend AMEND [AMEND ...]
                        List of amendments to activate (default: [])
  --project             Is this command executed for project-level? (default:
                        False)

help:
  -h, --help            show this help message and exit
```

## `looper init --help`
```console
usage: looper init [-h] [-f] [-o OUTPUT_DIR] [--pep-config PEP_CONFIG]
                   [-S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]]
                   [-P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]]

optional arguments:
  -f, --force-yes       Provide upfront confirmation of destruction intent, to
                        skip console query. Default=False (default: False)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: None)
  --pep-config PEP_CONFIG
                        PEP configuration file (default: None)
  -S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...], --sample-pipeline-interfaces SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]
                        Paths to looper sample pipeline interfaces (default:
                        [])
  -P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...], --project-pipeline-interfaces PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]
                        Paths to looper project pipeline interfaces (default:
                        [])

help:
  -h, --help            show this help message and exit
```

## `looper destroy --help`
```console
usage: looper destroy [-h] [-d] [-f] [--settings SETTINGS]
                      [--exc-flag EXC_FLAG [EXC_FLAG ...]]
                      [--sel-flag SEL_FLAG [SEL_FLAG ...]]
                      [--sel-attr SEL_ATTR]
                      [--sel-incl SEL_INCL [SEL_INCL ...]]
                      [--sel-excl SEL_EXCL] [-l LIMIT] [-k SKIP]
                      [--pep-config PEP_CONFIG] [-o OUTPUT_DIR]
                      [--config-file CONFIG_FILE]
                      [--looper-config LOOPER_CONFIG]
                      [-S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]]
                      [-P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]]
                      [--pipestat PIPESTAT] [--amend AMEND [AMEND ...]]
                      [--project]

optional arguments:
  -d, --dry-run         Don't actually submit jobs (default: False)
  -f, --force-yes       Provide upfront confirmation of destruction intent, to
                        skip console query. Default=False (default: False)
  --settings SETTINGS   Path to a YAML settings file with compute settings
                        (default: )
  --exc-flag EXC_FLAG [EXC_FLAG ...]
                        Sample exclusion flag (default: [])
  --sel-flag SEL_FLAG [SEL_FLAG ...]
                        Sample selection flag (default: [])
  --sel-attr SEL_ATTR   Attribute for sample exclusion OR inclusion (default:
                        toggle)
  --sel-incl SEL_INCL [SEL_INCL ...]
                        Include only samples with these values (default: [])
  --sel-excl SEL_EXCL   Exclude samples with these values (default: )
  -l LIMIT, --limit LIMIT
                        Limit to n samples (default: None)
  -k SKIP, --skip SKIP  Skip samples by numerical index (default: None)
  --pep-config PEP_CONFIG
                        PEP configuration file (default: None)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: None)
  --config-file CONFIG_FILE
                        Project configuration file (default: None)
  --looper-config LOOPER_CONFIG
                        Looper configuration file (YAML) (default: None)
  -S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...], --sample-pipeline-interfaces SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]
                        Paths to looper sample pipeline interfaces (default:
                        [])
  -P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...], --project-pipeline-interfaces PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]
                        Paths to looper project pipeline interfaces (default:
                        [])
  --pipestat PIPESTAT   Path to pipestat files. (default: None)
  --amend AMEND [AMEND ...]
                        List of amendments to activate (default: [])
  --project             Is this command executed for project-level? (default:
                        False)

help:
  -h, --help            show this help message and exit
```

## `looper check --help`
```console
usage: looper check [-h] [--describe-codes] [--itemized]
                    [-f FLAGS [FLAGS ...]] [--settings SETTINGS]
                    [--exc-flag EXC_FLAG [EXC_FLAG ...]]
                    [--sel-flag SEL_FLAG [SEL_FLAG ...]] [--sel-attr SEL_ATTR]
                    [--sel-incl SEL_INCL [SEL_INCL ...]] [--sel-excl SEL_EXCL]
                    [-l LIMIT] [-k SKIP] [--pep-config PEP_CONFIG]
                    [-o OUTPUT_DIR] [--config-file CONFIG_FILE]
                    [--looper-config LOOPER_CONFIG]
                    [-S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]]
                    [-P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]]
                    [--pipestat PIPESTAT] [--amend AMEND [AMEND ...]]
                    [--project]

optional arguments:
  --describe-codes      Show status codes description. Default=False (default:
                        False)
  --itemized            Show detailed overview of sample statuses.
                        Default=False (default: False)
  -f FLAGS [FLAGS ...], --flags FLAGS [FLAGS ...]
                        Only check samples based on these status flags.
                        (default: [])
  --settings SETTINGS   Path to a YAML settings file with compute settings
                        (default: )
  --exc-flag EXC_FLAG [EXC_FLAG ...]
                        Sample exclusion flag (default: [])
  --sel-flag SEL_FLAG [SEL_FLAG ...]
                        Sample selection flag (default: [])
  --sel-attr SEL_ATTR   Attribute for sample exclusion OR inclusion (default:
                        toggle)
  --sel-incl SEL_INCL [SEL_INCL ...]
                        Include only samples with these values (default: [])
  --sel-excl SEL_EXCL   Exclude samples with these values (default: )
  -l LIMIT, --limit LIMIT
                        Limit to n samples (default: None)
  -k SKIP, --skip SKIP  Skip samples by numerical index (default: None)
  --pep-config PEP_CONFIG
                        PEP configuration file (default: None)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: None)
  --config-file CONFIG_FILE
                        Project configuration file (default: None)
  --looper-config LOOPER_CONFIG
                        Looper configuration file (YAML) (default: None)
  -S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...], --sample-pipeline-interfaces SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]
                        Paths to looper sample pipeline interfaces (default:
                        [])
  -P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...], --project-pipeline-interfaces PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]
                        Paths to looper project pipeline interfaces (default:
                        [])
  --pipestat PIPESTAT   Path to pipestat files. (default: None)
  --amend AMEND [AMEND ...]
                        List of amendments to activate (default: [])
  --project             Is this command executed for project-level? (default:
                        False)

help:
  -h, --help            show this help message and exit
```

## `looper clean --help`
```console
usage: looper clean [-h] [-d] [-f] [--settings SETTINGS]
                    [--exc-flag EXC_FLAG [EXC_FLAG ...]]
                    [--sel-flag SEL_FLAG [SEL_FLAG ...]] [--sel-attr SEL_ATTR]
                    [--sel-incl SEL_INCL [SEL_INCL ...]] [--sel-excl SEL_EXCL]
                    [-l LIMIT] [-k SKIP] [--pep-config PEP_CONFIG]
                    [-o OUTPUT_DIR] [--config-file CONFIG_FILE]
                    [--looper-config LOOPER_CONFIG]
                    [-S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]]
                    [-P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]]
                    [--pipestat PIPESTAT] [--amend AMEND [AMEND ...]]
                    [--project]

optional arguments:
  -d, --dry-run         Don't actually submit jobs (default: False)
  -f, --force-yes       Provide upfront confirmation of destruction intent, to
                        skip console query. Default=False (default: False)
  --settings SETTINGS   Path to a YAML settings file with compute settings
                        (default: )
  --exc-flag EXC_FLAG [EXC_FLAG ...]
                        Sample exclusion flag (default: [])
  --sel-flag SEL_FLAG [SEL_FLAG ...]
                        Sample selection flag (default: [])
  --sel-attr SEL_ATTR   Attribute for sample exclusion OR inclusion (default:
                        toggle)
  --sel-incl SEL_INCL [SEL_INCL ...]
                        Include only samples with these values (default: [])
  --sel-excl SEL_EXCL   Exclude samples with these values (default: )
  -l LIMIT, --limit LIMIT
                        Limit to n samples (default: None)
  -k SKIP, --skip SKIP  Skip samples by numerical index (default: None)
  --pep-config PEP_CONFIG
                        PEP configuration file (default: None)
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Output directory (default: None)
  --config-file CONFIG_FILE
                        Project configuration file (default: None)
  --looper-config LOOPER_CONFIG
                        Looper configuration file (YAML) (default: None)
  -S SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...], --sample-pipeline-interfaces SAMPLE_PIPELINE_INTERFACES [SAMPLE_PIPELINE_INTERFACES ...]
                        Paths to looper sample pipeline interfaces (default:
                        [])
  -P PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...], --project-pipeline-interfaces PROJECT_PIPELINE_INTERFACES [PROJECT_PIPELINE_INTERFACES ...]
                        Paths to looper project pipeline interfaces (default:
                        [])
  --pipestat PIPESTAT   Path to pipestat files. (default: None)
  --amend AMEND [AMEND ...]
                        List of amendments to activate (default: [])
  --project             Is this command executed for project-level? (default:
                        False)

help:
  -h, --help            show this help message and exit
```

