# How to pass extra command-line arguments

Occasionally, a particular project needs to run a particular flavor of a pipeline. We'd like to just adjust the arguments passed for just this project. 
We may be passing a completely separate config file to the pipeline, or just tweaking a command-line argument. Either way, we treat things the same way.

Looper provides a feature called *command extras* to solve this problem. Command extras provide a way to pass arbitrary commands through looper on to the pipeline. This *extra* information can be specified on the command line, or at the sample or project level, depending on the pipeline.

## Project-level command extras

For *project pipelines*, you can specify command extras in the `looper` section of the PEP config, like this:

```
looper:
  command_extra: "--flavor"
```

Remember, these command extras are used for project pipelines, not for sample pipelines. If you want to add extras to sample pipelines, you need to modulate the sample objects.

## Sample-level command extras

For sample pipelines, you can use general PEP sample modifiers to add a `command_extras` attribute to any samples, however you wish. For example, if your extras are the same for all samples you could just use an `append` modifier:


```
sample_modifiers:
  append:
    command_extra: "--flavor-flag"
```

Or, if you need to modulate on the basis of some other attribute value, you could use an imply modifer:

```
sample_modifiers:
  imply:
    - if:
        protocol: "rrbs"
      then:
        command_extra: "-C flavor.yaml --epilog"
```

## CLI command extras

Both project and sample pipelines calls can be tweaked from the command line. You use `--command-extra` to pass any arguments you want. Looper will pass these append these to your command, whether it be a sample or a project pipeline.

By default, the CLI extras are *appended to the command_extras specified in you PEP*. If you instead want to *override* the command extras listed in the PEP, you can instead use `--command-extra-override`.

So, for example, make your looper call like this:

```
looper run --command-extra "-R"
```

That will append `-R` to the end of any commands created by looper.

## Implementation

Under the hood, all looper is doing is automatically adding this template to the end of the `command_template` in the pipeline interface:

For sample pipelines,

```
{% if sample.command_extra is defined %} {sample.command_extra}{% endif %}
```

For project pipelines,

```
{% if project.looper.command_extra is defined %} {project.looper.command_extra}{% endif %}
```

In either case, after this, the CLI `command-extras` value is appended.