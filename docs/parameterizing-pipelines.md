# How to pass extra command-line arguments

Occasionally, a particular project needs to run a particular flavor of a pipeline. We'd like to just adjust the arguments passed for just this project. 
We may be passing a completely separate config file to the pipeline, or just tweaking a command-line argument. Either way, we treat things the same way.

Looper provides a feature called *command extras* to solve this problem. Command extras provide a way to pass arbitrary commands through looper on to the pipeline. This *extra* information can be specified on the command line, or at the sample or project level, depending on the pipeline.

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

## Sample-level command extras

For sample pipelines, there are two possibilies: 1) command line argument, modulated the same way as shown above, but for `run` subcommand and 2) setting sample attribute using general PEP sample modifiers to add a `command_extra` attribute to any samples, however you wish. For example, if your extras are the same for all samples you could just use an `append` modifier:


Or, if you need to modulate on the basis of some other attribute value, you could use an imply modifer:

```yaml
sample_modifiers:
  append:
    command_extra: "--flavor-flag"
```


```yaml
sample_modifiers:
  imply:
    - if:
        protocol: "rrbs"
      then:
        command_extra: "-C flavor.yaml --epilog"
```

## CLI command extras

By default, the CLI extras are *appended to the command_extra specified in your PEP*. If you instead want to *override* the command extras listed in the PEP, you can instead use `--command-extra-override`.

So, for example, make your looper call like this:

```bash
looper run --command-extra-override="-R"
```

That will remove any defined command extras and append `-R` to the end of any commands created by looper.

## Implementation

Under the hood, all looper is doing is automatically adding this template to the end of the `command_template` in the pipeline interface:

For sample pipelines,

```bash
{% if sample.command_extra is defined %} {sample.command_extra}{% endif %}
```

For project pipelines,

```bash
{% if project.looper.command_extra is defined %} {project.looper.command_extra}{% endif %}
```

In either case, after this, the CLI `command-extra` value is appended.