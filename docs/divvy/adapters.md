# Adapters make template variables flexible

Starting with `divvy v0.5.0` the configuration file can include an `adapters` section, which is used to provide a set of variable mappings that `divvy` uses to populate the submission templates.

This makes the connection with `divvy` and client software more flexible and more elegant, since the source of the data does not need to follow any particular naming scheme, any mapping can be used and adapted to work with any `divvy` templates.

## Example

```yaml
adapters:
  CODE: namespace.command
  LOGFILE: namespace1.log_file
  JOBNAME: user_settings.program.job_name
  CORES: processors_number
...
```

As you can see in the example `adapters` section above, each adapter is a key-value pair that maps a `divvy` template variable to a target value. The target values can use namespaces (nested mapping).
