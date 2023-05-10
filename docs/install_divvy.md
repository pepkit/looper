# Installing divvy

Install from [GitHub releases](https://github.com/databio/divvy/releases) or from PyPI using `pip`:

- `pip install --user divvy`: install into user space.
- `pip install --user --upgrade divvy`: update in user space.
- `pip install divvy`: install into an active virtual environment.
- `pip install --upgrade divvy`: update in virtual environment.

See if your install worked by calling `divvy -h` on the command line. If the `divvy` executable in not in your `$PATH`, append this to your `.bashrc` or `.profile` (or `.bash_profile` on macOS):

```{console}
export PATH=~/.local/bin:$PATH
```

# Initial configuration

On a fresh install, `divvy` comes pre-loaded with some built-in compute packages, which you can explore by typing `divvy list`. If you need to tweak these or create your own packages, you will need to configure divvy manually. Start by initializing an empty `divvy` config file:

```{console}
export DIVCFG="divvy_config.yaml"
divvy init $DIVCFG
```

This `init` command will create a default config file, along with a folder of templates. 


The `divvy write` and `list` commands require knowing where this genome config file is. You can pass it on the command line all the time (using the -c parameter), but this gets old. An alternative is to set up the $DIVCFG environment variable. Divvy will automatically use the config file in this environmental variable if it exists. Add this line to your `.bashrc` or `.profile` if you want it to persist for future command-line sessions. You can always specify -c if you want to override the value in the $DIVCFG variable on an ad-hoc basis:

```{console}
export DIVCFG=/path/to/divvy_config.yaml
```

More details can be found in the [configuring divvy how-to guide](configuration.md).