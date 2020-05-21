# How to pass extra command-line arguments

Occasionally, a particular project needs to run a particular flavor of a pipeline. We'd like to just adjust the arguments passed for just this project. 
We may be passing a completely separate config file to the pipeline, or just tweaking a command-line argument. Either way, we treat things the same way.

Looper provides a feature called *command extras* to solve this problem. Command extras provide a way to pass arbitrary commands through looper on to the pipeline. This *extra* information can be specified on the command line, or at the sample or project level, depending on the pipeline.

## Sample-level command extras

For sample pipelines, there are two possibilities: 1) command line argument  for `run` subcommand and 2) setting sample attribute using general PEP sample modifiers to add a `command_extra` attribute to any samples, however you wish. 

You can pass extra arguments using `--command-extra` like this:

```
looper run project_config.yaml --command-extra="--flavor-flag"
```

For the PEP-based approach, for example, if your extras are the same for all samples you could just use an `append` modifier:


```yaml
sample_modifiers:
  append:
    command_extra: "--flavor-flag"
```

Or, if you need to modulate on the basis of some other attribute value, you could use an imply modifier:


```yaml
sample_modifiers:
  imply:
    - if:
        protocol: "rrbs"
      then:
        command_extra: "-C flavor.yaml --epilog"
```

## Project-level command extras

For *project pipelines*, you can specify command extras in the `looper` section of the PEP config:

```yaml
looper:
  output_dir: "/path/to/output_dir"
  cli:
    runp:
      command-extra: "--flavor"
```

or as an argument to the `looper runp` command:


```bash
looper runp project_config.yaml --command-extra="--flavor-flag"
```


## Overriding PEP-based command extras

By default, the CLI extras are *appended to the command_extra specified in your PEP*. If you instead want to *override* the command extras listed in the PEP, you can instead use `--command-extra-override`.

So, for example, make your looper call like this:

```bash
looper run --command-extra-override="-R"
```

That will remove any defined command extras and append `-R` to the end of any commands created by looper.
