# How to pass extra command-line arguments

Occasionally, a particular project needs to run a particular flavor of a pipeline. How can you  adjust pipeline arguments for just this project? You can use looper *command extras* to solve this problem. Command extras let you pass any string on to the pipeline, which will be appended to the command. 

There are 2 ways to use command extras: for sample pipelines, or for project pipelines:

## 1. Sample pipeline command extras

### Adding sample command extras via sample attributes

Looper uses a reserved sample attribute called `command_extras`, which you can set using general PEP sample modifiers however you wish. For example, if your extras are the same for all samples you could use an `append` modifier:


```yaml
sample_modifiers:
  append:
    command_extra: "--flavor-flag"
```

This will add `--flavor-flag` the end of the command looper constructs. If you need to modulate the extras depending on another attribute value, you could use an imply modifier:

```yaml
sample_modifiers:
  imply:
    - if:
        protocol: "rrbs"
      then:
        command_extra: "-C flavor.yaml --epilog"
```

### Adding sample command extras via the command line

You can also pass extra arguments using `--command-extra` like this:

```
looper run project_config.yaml --command-extra="--flavor-flag"
```

## 2. Project pipeline command extras

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
