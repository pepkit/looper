# Developer Documentation

## Adding New Models

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
