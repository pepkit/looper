import enum
from dataclasses import dataclass
from typing import Optional

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
    :param dict kwargs: additional keyword arguments supported by
        `FieldInfo`, such as description, default value, etc.
    """

    def __init__(self, name, **kwargs) -> None:
        self._name = name
        super().__init__(**kwargs)
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
                pydantic.Field(arg_default_value, description=arg.description),
            )
        return pydantic.create_model(self.name, **arguments)


class ArgumentEnum(enum.Enum):
    """
    Lists all available arguments

    TODO: not sure whether an enum is the ideal data structure for that
    """

    IGNORE_FLAGS = Argument(
        name="ignore-flags",
        default=(bool, False),
        description="Ignore run status flags",
    )
    TIME_DELAY = Argument(
        name="time-delay",
        default=(int, 0),
        description="Time delay in seconds between job submissions (min: 0, max: 30)",
    )
    DRY_RUN = Argument(
        name="dry-run", default=(bool, False), description="Don't actually submit jobs"
    )
    COMMAND_EXTRA = Argument(
        name="command-extra",
        default=(str, ""),
        description="String to append to every command",
    )
    COMMAND_EXTRA_OVERRIDE = Argument(
        name="command-extra-override",
        default=(str, ""),
        description="Same as command-extra, but overrides values in PEP",
    )
    LUMP = Argument(
        name="lump",
        default=(int, None),
        description="Total input file size (GB) to batch into one job",
    )
    LUMPN = Argument(
        name="lumpn",
        default=(int, None),
        description="Number of commands to batch into one job",
    )
    LIMIT = Argument(
        name="limit", default=(int, None), description="Limit to n samples"
    )
    SKIP = Argument(
        name="skip", default=(int, None), description="Skip samples by numerical index"
    )


RunParser = Command(
    "run",
    MESSAGE_BY_SUBCOMMAND["run"],
    [
        ArgumentEnum.IGNORE_FLAGS.value,
        ArgumentEnum.TIME_DELAY.value,
        ArgumentEnum.DRY_RUN.value,
        ArgumentEnum.COMMAND_EXTRA.value,
        ArgumentEnum.COMMAND_EXTRA_OVERRIDE.value,
        ArgumentEnum.LUMP.value,
        ArgumentEnum.LUMPN.value,
        ArgumentEnum.LIMIT.value,
        ArgumentEnum.SKIP.value,
    ],
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
