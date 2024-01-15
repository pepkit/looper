from dataclasses import dataclass
import enum
from typing import Any, Optional

import pydantic
import pydantic_argparse

from .const import MESSAGE_BY_SUBCOMMAND


class Argument(pydantic.fields.FieldInfo):
    """
    CLI argument / flag definition

    Naively, one would think one could just subclass `pydantic.Field`,
    but actually `pydantic.Field` is a function, and not a class.
    `pydantic.Field()` returns a validated `FieldInfo` instance,
    so we instead subclass `FieldInfo` directly and validate it in the
    constructor.

    :param str name: argument name, e.g. "ignore-args"
    :param str description: argument description, which will appear as the
        help text for this argument
    :param Any default: a tuple of the form (type, default_value). If the
        default value is `...` (Ellipsis), then the argument is required.
    """

    def __init__(self, name: str, default: Any, description: str) -> None:
        self._name = name
        super().__init__(default=default, description=description)
        self._validate()

    @property
    def name(self):
        """
        Argument name as used in the CLI, e.g. "ignore-args"
        """
        return self._name

@dataclass
class Command:
    """
    Representation of a command

    :param str name: command name
    :param str description: command description
    :param list[Argument] arguments: list of arguments supported by this command
    """
    name: str
    description: str
    arguments: list[Argument]

    def create_model(self) -> type[pydantic.BaseModel]:
        """
        Creates a `pydantic` model for this command
        """
        arguments = dict()
        for arg in self.arguments:
            # These gymnastics are necessary because of
            # https://github.com/pydantic/pydantic/issues/2248#issuecomment-757448447
            arg_type, arg_default_value = arg.default
            arguments[arg.name] = (
                arg_type,
                pydantic.Field(arg_default_value, description=arg.description)
            )
        return pydantic.create_model(
            self.name, **arguments
        )

class ArgumentEnum(enum.Enum):
    """
    Lists all available arguments

    TODO: not sure whether an enum is the ideal data structure for that
    """
    IGNORE_FLAGS = Argument(
        "ignore-flags",
        (bool, False),
        "Ignore run status flags",
    )
    TIME_DELAY = Argument(
        "time-delay",
        (int, 0),
        "Time delay in seconds between job submissions (min: 0, max: 30)",
    )
    DRY_RUN = Argument(
        "dry-run",
        (bool, False),
        "Don't actually submit jobs"
    )
    COMMAND_EXTRA = Argument(
        "command-extra",
        (str, ""),
        "String to append to every command"
    )
    COMMAND_EXTRA_OVERRIDE = Argument(
        "command-extra-override",
        (str, ""),
        "Same as command-extra, but overrides values in PEP"
    )
    LUMP = Argument(
        "lump",
        (int, None),
        "Total input file size (GB) to batch into one job"
    )
    LUMPN = Argument(
        "lumpn",
        (int, None),
        "Number of commands to batch into one job"
    )
    LIMIT = Argument(
        "limit",
        (int, None),
        "Limit to n samples"
    )
    SKIP = Argument(
        "skip",
        (int, None),
        "Skip samples by numerical index"
    )

RunParser = Command(
    "run", MESSAGE_BY_SUBCOMMAND["run"],
    [
        ArgumentEnum.IGNORE_FLAGS.value,
        ArgumentEnum.TIME_DELAY.value,
        ArgumentEnum.DRY_RUN.value,
        ArgumentEnum.COMMAND_EXTRA.value,
        ArgumentEnum.COMMAND_EXTRA_OVERRIDE.value,
        ArgumentEnum.LUMP.value,
        ArgumentEnum.LUMPN.value,
        ArgumentEnum.LIMIT.value,
        ArgumentEnum.SKIP.value
    ]
)
RunParserModel = RunParser.create_model()

class TopLevelParser(pydantic.BaseModel):
    """
    Top level parser that takes
    - commands (run, runp, check...)
    - arguments that are required no matter the subcommand
    """
    # commands
    run: Optional[RunParserModel] = pydantic.Field(description=RunParser.description)


def main() -> None:
    parser = pydantic_argparse.ArgumentParser(
        model=TopLevelParser,
        prog="looper",
        description="pydantic-argparse demo",
        add_help=True,
    )
    args = parser.parse_typed_args()
    print(args)

if __name__ == "__main__":
    main()
