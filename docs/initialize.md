# How to initialize a looper repository

*This is considered a beta feature and may change in future releases*.

Looper provides a command `looper init` that allows you to initialize folders as looper repositories. This enables you to use `looper` without passing your PEP every time.

```bash
looper init pep.yaml
```

Now, as long as you are operating from within this directory or any of the subdirectories, you can run any looper command without passing `pep.yaml`:

```bash
looper run
```

The `looper init` command creates a dotfile called `.looper.yaml` in the current directory. This file simply points looper to the to the config file passed as positional argument to `looper init`:

```yaml
config_file_path: relative/path/to/pep.yaml
```
