# How to initialize a looper repository

*This is considered a beta feature and may change in future releases*.

Looper provides a command `looper init` that allows you to initialize folders as looper repositories. This enables you to use `looper` without passing your PEP every time. 

```
looper init pep.yaml
```

Now, as long as you are operating from within this folder, you can run any looper command without passing `pep.yaml`:

```
looper run
```

The `init` command creates a dotfile called `.looper.yaml` in the current directory. This file points to the config file, and you can also edit it to add in any other arguments that you want automatically passed to looper for this project.

