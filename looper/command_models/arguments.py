import enum
from typing import Any

import pydantic


class Argument(pydantic.fields.FieldInfo):
    """
    CLI argument / flag definition

    This class is designed to define CLI arguments or flags. It leverages
    Pydantic for data validation and serves as a source of truth for multiple
    interfaces, including a CLI.

    Naively, one would think one could just subclass `pydantic.Field`,
    but actually `pydantic.Field` is a function, and not a class.
    `pydantic.Field()` returns a validated `FieldInfo` instance,
    so we instead subclass `FieldInfo` directly and validate it in the
    constructor.

    :param str name: argument name, e.g. "ignore-args"
    :param Any default: a tuple of the form (type, default_value). If the
        default value is `...` (Ellipsis), then the argument is required.
    :param str description: argument description, which will appear as the
        help text for this argument
    :param dict kwargs: additional keyword arguments supported by
        `FieldInfo`. These are passed along as they are.
    """

    def __init__(self, name: str, default: Any, description: str, **kwargs) -> None:
        self._name = name
        super().__init__(default=default, description=description, **kwargs)
        self._validate()

    @property
    def name(self):
        """
        Argument name as used in the CLI, e.g. "ignore-args"
        """
        return self._name


class ArgumentEnum(enum.Enum):
    """
    Lists all available arguments

    Having a single "repository" of arguments allows us to re-use them easily across different commands.

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
