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
              [--dbg]
              {run,rerun,runp,table,report,destroy,check,clean,inspect,init}
              ...

looper - A project job submission engine and project manager.

positional arguments:
  {run,rerun,runp,table,report,destroy,check,clean,inspect,init}
    run                 Run or submit sample jobs.
    rerun               Resubmit sample jobs with failed flags.
    runp                Run or submit project jobs.
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

For subcommand-specific options, type: 'looper <subcommand> -h'
https://github.com/pepkit/looper
```

## `looper run --help`
```console
usage: looper run [-h] [-i] [-d] [-t S] [-l N] [-x S] [-y S] [-f] [--divvy DIVCFG] [-p P]
                  [-s S] [-c K [K ...]] [-u X] [-n N] [-g K] [--sel-attr ATTR]
                  [--sel-excl [E [E ...]] | --sel-incl [I [I ...]]] [-a A [A ...]]
                  [config_file]

Run or submit sample jobs.

positional arguments:
  config_file                        Project configuration file (YAML)

optional arguments:
  -h, --help                         show this help message and exit
  -i, --ignore-flags                 Ignore run status flags? Default=False
  -d, --dry-run                      Don't actually submit the jobs. Default=False
  -t S, --time-delay S               Time delay in seconds between job submissions
  -l N, --limit N                    Limit to n samples
  -x S, --command-extra S            String to append to every command
  -y S, --command-extra-override S   Same as command-extra, but overrides values in PEP
  -f, --skip-file-checks             Do not perform input file checks
  -u X, --lump X                     Total input file size (GB) to batch into one job
  -n N, --lumpn N                    Number of commands to batch into one job
  -a A [A ...], --amend A [A ...]    List of amendments to activate

divvy arguments:
  Configure divvy to change computing settings

  --divvy DIVCFG                     Path to divvy configuration file. Default=$DIVCFG env
                                     variable. Currently: /Users/mstolarczyk/Uczelnia/UVA/
                                     code//divcfg/uva_rivanna.yaml
  -p P, --package P                  Name of computing resource package to use
  -s S, --settings S                 Path to a YAML settings file with compute settings
  -c K [K ...], --compute K [K ...]  List of key-value pairs (k1=v1)

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -g K, --toggle-key K               Sample attribute specifying toggle. Default: toggle
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E [E ...]]             Exclude samples with these values
  --sel-incl [I [I ...]]             Include only samples with these values
```

## `looper runp --help`
```console
usage: looper runp [-h] [-i] [-d] [-t S] [-l N] [-x S] [-y S] [-f] [--divvy DIVCFG] [-p P]
                   [-s S] [-c K [K ...]] [-g K] [--sel-attr ATTR] [--sel-excl [E [E ...]]
                   | --sel-incl [I [I ...]]] [-a A [A ...]]
                   [config_file]

Run or submit project jobs.

positional arguments:
  config_file                        Project configuration file (YAML)

optional arguments:
  -h, --help                         show this help message and exit
  -i, --ignore-flags                 Ignore run status flags? Default=False
  -d, --dry-run                      Don't actually submit the jobs. Default=False
  -t S, --time-delay S               Time delay in seconds between job submissions
  -l N, --limit N                    Limit to n samples
  -x S, --command-extra S            String to append to every command
  -y S, --command-extra-override S   Same as command-extra, but overrides values in PEP
  -f, --skip-file-checks             Do not perform input file checks
  -a A [A ...], --amend A [A ...]    List of amendments to activate

divvy arguments:
  Configure divvy to change computing settings

  --divvy DIVCFG                     Path to divvy configuration file. Default=$DIVCFG env
                                     variable. Currently: /Users/mstolarczyk/Uczelnia/UVA/
                                     code//divcfg/uva_rivanna.yaml
  -p P, --package P                  Name of computing resource package to use
  -s S, --settings S                 Path to a YAML settings file with compute settings
  -c K [K ...], --compute K [K ...]  List of key-value pairs (k1=v1)

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -g K, --toggle-key K               Sample attribute specifying toggle. Default: toggle
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E [E ...]]             Exclude samples with these values
  --sel-incl [I [I ...]]             Include only samples with these values
```

## `looper rerun --help`
```console
usage: looper rerun [-h] [-i] [-d] [-t S] [-l N] [-x S] [-y S] [-f] [--divvy DIVCFG]
                    [-p P] [-s S] [-c K [K ...]] [-u X] [-n N] [-g K] [--sel-attr ATTR]
                    [--sel-excl [E [E ...]] | --sel-incl [I [I ...]]] [-a A [A ...]]
                    [config_file]

Resubmit sample jobs with failed flags.

positional arguments:
  config_file                        Project configuration file (YAML)

optional arguments:
  -h, --help                         show this help message and exit
  -i, --ignore-flags                 Ignore run status flags? Default=False
  -d, --dry-run                      Don't actually submit the jobs. Default=False
  -t S, --time-delay S               Time delay in seconds between job submissions
  -l N, --limit N                    Limit to n samples
  -x S, --command-extra S            String to append to every command
  -y S, --command-extra-override S   Same as command-extra, but overrides values in PEP
  -f, --skip-file-checks             Do not perform input file checks
  -u X, --lump X                     Total input file size (GB) to batch into one job
  -n N, --lumpn N                    Number of commands to batch into one job
  -a A [A ...], --amend A [A ...]    List of amendments to activate

divvy arguments:
  Configure divvy to change computing settings

  --divvy DIVCFG                     Path to divvy configuration file. Default=$DIVCFG env
                                     variable. Currently: /Users/mstolarczyk/Uczelnia/UVA/
                                     code//divcfg/uva_rivanna.yaml
  -p P, --package P                  Name of computing resource package to use
  -s S, --settings S                 Path to a YAML settings file with compute settings
  -c K [K ...], --compute K [K ...]  List of key-value pairs (k1=v1)

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -g K, --toggle-key K               Sample attribute specifying toggle. Default: toggle
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E [E ...]]             Exclude samples with these values
  --sel-incl [I [I ...]]             Include only samples with these values
```

## `looper report --help`
```console
usage: looper report [-h] [-g K] [--sel-attr ATTR] [--sel-excl [E [E ...]] | --sel-incl
                     [I [I ...]]] [-a A [A ...]]
                     [config_file]

Create browsable HTML report of project results.

positional arguments:
  config_file                      Project configuration file (YAML)

optional arguments:
  -h, --help                       show this help message and exit
  -a A [A ...], --amend A [A ...]  List of amendments to activate

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -g K, --toggle-key K             Sample attribute specifying toggle. Default: toggle
  --sel-attr ATTR                  Attribute for sample exclusion OR inclusion
  --sel-excl [E [E ...]]           Exclude samples with these values
  --sel-incl [I [I ...]]           Include only samples with these values
```

## `looper table --help`
```console
usage: looper table [-h] [-g K] [--sel-attr ATTR] [--sel-excl [E [E ...]] | --sel-incl
                    [I [I ...]]] [-a A [A ...]]
                    [config_file]

Write summary stats table for project samples.

positional arguments:
  config_file                      Project configuration file (YAML)

optional arguments:
  -h, --help                       show this help message and exit
  -a A [A ...], --amend A [A ...]  List of amendments to activate

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -g K, --toggle-key K             Sample attribute specifying toggle. Default: toggle
  --sel-attr ATTR                  Attribute for sample exclusion OR inclusion
  --sel-excl [E [E ...]]           Exclude samples with these values
  --sel-incl [I [I ...]]           Include only samples with these values
```

## `looper inspect --help`
```console
usage: looper inspect [-h] [-n S [S ...]] [-l L] [-g K] [--sel-attr ATTR]
                      [--sel-excl [E [E ...]] | --sel-incl [I [I ...]]] [-a A [A ...]]
                      [config_file]

Print information about a project.

positional arguments:
  config_file                       Project configuration file (YAML)

optional arguments:
  -h, --help                        show this help message and exit
  -n S [S ...], --snames S [S ...]  Name of the samples to inspect
  -l L, --attr-limit L              Number of sample attributes to display
  -a A [A ...], --amend A [A ...]   List of amendments to activate

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -g K, --toggle-key K              Sample attribute specifying toggle. Default: toggle
  --sel-attr ATTR                   Attribute for sample exclusion OR inclusion
  --sel-excl [E [E ...]]            Exclude samples with these values
  --sel-incl [I [I ...]]            Include only samples with these values
```

## `looper init --help`
```console
usage: looper init [-h] [-f] config_file

Initialize looper dotfile.

positional arguments:
  config_file  Project configuration file (YAML)

optional arguments:
  -h, --help   show this help message and exit
  -f, --force  Force overwrite
```

## `looper destroy --help`
```console
usage: looper destroy [-h] [-d] [--force-yes] [-g K] [--sel-attr ATTR]
                      [--sel-excl [E [E ...]] | --sel-incl [I [I ...]]] [-a A [A ...]]
                      [config_file]

Remove output files of the project.

positional arguments:
  config_file                      Project configuration file (YAML)

optional arguments:
  -h, --help                       show this help message and exit
  -d, --dry-run                    Don't actually submit the jobs. Default=False
  --force-yes                      Provide upfront confirmation of destruction intent, to
                                   skip console query. Default=False
  -a A [A ...], --amend A [A ...]  List of amendments to activate

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -g K, --toggle-key K             Sample attribute specifying toggle. Default: toggle
  --sel-attr ATTR                  Attribute for sample exclusion OR inclusion
  --sel-excl [E [E ...]]           Exclude samples with these values
  --sel-incl [I [I ...]]           Include only samples with these values
```

## `looper check --help`
```console
usage: looper check [-h] [-A] [-f [F [F ...]]] [-g K] [--sel-attr ATTR]
                    [--sel-excl [E [E ...]] | --sel-incl [I [I ...]]] [-a A [A ...]]
                    [config_file]

Check flag status of current runs.

positional arguments:
  config_file                        Project configuration file (YAML)

optional arguments:
  -h, --help                         show this help message and exit
  -A, --all-folders                  Check status for all output folders, not just for
                                     samples specified in the config. Default=False
  -f [F [F ...]], --flags [F [F ...]]
                                     Check on only these flags/status values
  -a A [A ...], --amend A [A ...]    List of amendments to activate

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -g K, --toggle-key K               Sample attribute specifying toggle. Default: toggle
  --sel-attr ATTR                    Attribute for sample exclusion OR inclusion
  --sel-excl [E [E ...]]             Exclude samples with these values
  --sel-incl [I [I ...]]             Include only samples with these values
```

## `looper clean --help`
```console
usage: looper clean [-h] [-d] [--force-yes] [-g K] [--sel-attr ATTR]
                    [--sel-excl [E [E ...]] | --sel-incl [I [I ...]]] [-a A [A ...]]
                    [config_file]

Run clean scripts of already processed jobs.

positional arguments:
  config_file                      Project configuration file (YAML)

optional arguments:
  -h, --help                       show this help message and exit
  -d, --dry-run                    Don't actually submit the jobs. Default=False
  --force-yes                      Provide upfront confirmation of destruction intent, to
                                   skip console query. Default=False
  -a A [A ...], --amend A [A ...]  List of amendments to activate

sample selection arguments:
  Specify samples to include or exclude based on sample attribute values

  -g K, --toggle-key K             Sample attribute specifying toggle. Default: toggle
  --sel-attr ATTR                  Attribute for sample exclusion OR inclusion
  --sel-excl [E [E ...]]           Exclude samples with these values
  --sel-incl [I [I ...]]           Include only samples with these values
```

