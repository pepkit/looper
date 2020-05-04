# How to pass extra command-line arguments

Occasionally, a particular project needs to run a particular flavor of a pipeline. We'd like to just adjust the arguments passed for just this project. 
We may be passing a completely separate config file to the pipeline, or just tweaking a command-line argument. Either way, we treat things the same way.

Looper provides a feature called *command extras* to solve this problem. Command extras provide a way to pass arbitrary commands through looper on to the pipeline. This *extra* information can be specified either on the command line, at the sample level, or at the project level.

## Project-level command extras

```
looper:
  command_extras: "--flavor"
```

These command extras are used for project pipelines, not for sample pipelines. If you want to add extras to sample pipelines, you need to modulate the sample.

## Sample-level command extras

You can use general PEP sample modifiers to add a `command_extras` attribute to any samples, however you wish. For example, if your extras are the same for all samples you could just use an `append` modifier:


```
sample_modifiers:
  append:
    command_extras: "--flavor-flag"
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

You can use `--command-extra` to pass any arguments. By default, these will be appended to whatever is listed in you PEP for sample- or project-level command extras. If you want to *override* the command extras listed in the PEP, you can instead use `--command-extra-override`.

So, for example, make your looper call like this:

```
looper run --command-extra "-R"
```

That will append `-R` to the end of all commands created by looper.

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
