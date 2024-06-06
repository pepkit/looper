# Developer documentation

## Adding new command models

To add a new model (command) to the project, follow these steps:

1. Add new arguments in `looper/command_models/arguments.py` if necessary.

- Add a new entry for the `ArgumentEnum` class.
- For example:

```python
# arguments.py

class ArgumentEnum(enum.Enum):
    ...

    NEW_ARGUMENT = Argument(
        name="new_argument",
        default=(new_argument_type, "default_value"),
        description="Description of the new argument",
    )

```

2. Create a new command in the existing command creation logic in `looper/command_models/commands.py`.

- Create a new `Command` instance.
- Create a `pydantic` model for this new command.
- Add the new `Command` instance to `SUPPORTED_COMMANDS`.
- For example:

```python
NewCommandParser = Command(
    "new_command",
    MESSAGE_BY_SUBCOMMAND["new_command"],
    [
        ...
        ArgumentEnum.NEW_ARGUMENT.value,
        # Add more arguments as needed for the new command
    ],
)
NewCommandParserModel = NewCommandParser.create_model()

SUPPORTED_COMMANDS = [..., NewCommandParser]
```

3. Update the new argument(s) and command in `TopLevelParser` from `looper/command_models/commands.py`.

- Add a new field for the new command.
- Add a new field for the new argument(s).
- For example:

```python
class TopLevelParser(pydantic.BaseModel):

    # commands
    ...
    new_command: Optional[NewCommandParserModel] = pydantic.Field(description=NewCommandParser.description)

    # arguments
    ...
    new_argument: Optional[new_argument_type] = ArgumentEnum.NEW_ARGUMENT.value.with_reduced_default()
```

## Special treatment for the `run` command

The `run` command in our project requires special treatment to accommodate hierarchical namespaces
and properly handle its unique characteristics. Several functions have been adapted to ensure the
correct behavior of the run command, and similar adaptations may be necessary for other commands.

For developers looking to understand the details of the special treatment given to the `run`
command and its associated changes, we recommend to inspect the following functions / part of the
code:
- `looper/cli_looper.py`:
  - `make_hierarchical_if_needed()`
  - assignment of the `divcfg` variable
  - assignment of the `project_args` variable
  - `_proc_resources_spec()`
  - `validate_post_parse()`
- `looper/utils.py`:
  - `enrich_args_via_cfg()`

If you are adding new commands to the project / migrate existing commands to a `pydantic` model-based definition, adapt these parts of the codes with equivalent behavior for your new command.
Likewise, adapt argument accessions in the corresponding executor in `looper/looper.py` to take into account the hierarchical organization of the command's arguments.
