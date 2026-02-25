# pydantic-based definitions of looper commands and their arguments

This module defines looper commands as pydantic models for use with:
- `pydantic-settings` for CLI parsing (see `../cli_pydantic.py`)
- HTTP API for validating POST data (see `../api/`)

## Key files

- `commands.py` - Command definitions and `TopLevelParser` (pydantic-settings entry point)
- `arguments.py` - Argument definitions (`ArgumentEnum`)
- `messages.py` - Subcommand help text

## Adding a new command

1. Add arguments to `ArgumentEnum` in `arguments.py`:
   ```python
   NEW_ARGUMENT = Argument(
       name="new_argument",
       default=(str, "default_value"),
       description="Description",
   )
   ```

2. Create the command in `commands.py`:
   ```python
   NewCommandParser = Command("new_command", MESSAGE_BY_SUBCOMMAND["new_command"], [...])
   NewCommandParserModel = NewCommandParser.create_model()
   SUPPORTED_COMMANDS.append(NewCommandParser)
   ```

3. Add to `TopLevelParser`:
   ```python
   new_command: CliSubCommand[NewCommandParserModel] = Field(description=...)
   ```

4. Handle the command in `../cli_pydantic.py` `run_looper()`.
