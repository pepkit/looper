from dataclasses import dataclass
import enum
import os
from typing import Optional, TypeAlias

import pydantic
import pydantic_argparse

from const import MESSAGE_BY_SUBCOMMAND

AllowedArgumentType: TypeAlias = str | int | bool | list

class Command(enum.Enum):
    """
    Lists all supported commands
    """
    RUN = enum.auto()

@dataclass
class Argument:
    """
    CLI argument / flag definition
    """
    # argument name, e.g. "ignore-args"
    name: str
    # argument type, e.g. `bool`
    type: type[AllowedArgumentType]
    # argument description (will be the CLI help text)
    description: str
    # default value for argument (needs to be an instance of `type`)
    # TODO: how can we constrain the type of this to be an instance of
    # the value of the `type` field?
    default: None | AllowedArgumentType
    # set of commands this argument is used by
    used_by: set[Command]

    def __post_init__(self):
        if self.default is not None and not isinstance(self.default, self.type):
            raise TypeError(
                "Value for `default` needs to be of the type given in "
                f"the `type` field ({self.type})"
                )

arguments = [
    Argument(
        "ignore-flags",
        bool,
        "Ignore run status flags",
        False,
        {Command.RUN}
    ),
    Argument(
        "time-delay",
        int,
        "Time delay in seconds between job submissions (min: 0, max: 30)",
        0,
        {Command.RUN}
    ),
    Argument(
        "dry-run",
        bool,
        "Don't actually submit jobs",
        False,
        {Command.RUN}
    ),
    Argument(
        "command-extra",
        str,
        "String to append to every command",
        "",
        {Command.RUN}
    ),
    Argument(
        "command-extra-override",
        str,
        "Same as command-extra, but overrides values in PEP",
        "",
        {Command.RUN}
    ),
    Argument(
        "lump",
        int,
        "Total input file size (GB) to batch into one job",
        None,
        {Command.RUN}
    ),
    Argument(
        "lumpn",
        int,
        "Number of commands to batch into one job",
        None,
        {Command.RUN}
    ),
    Argument(
        "limit",
        int,
        "Limit to n samples",
        None,
        {Command.RUN}
    ),
    Argument(
        "skip",
        int,
        "Skip samples by numerical index",
        None,
        {Command.RUN}
    )
]

def create_model_from_arguments(name: str, command: Command, arguments: list[Argument]) -> type[pydantic.BaseModel]:
    """
    Creates a `pydantic` model for a command from a list of arguments
    """
    return pydantic.create_model(
    name, **{
        arg.name: (arg.type, pydantic.Field(description=arg.description, default=arg.default))
        for arg in arguments if command in arg.used_by
    }
)

RunParser = create_model_from_arguments("RunParser", Command.RUN, arguments)

class TopLevelParser(pydantic.BaseModel):
    """
    Top level parser that takes
    - commands (run, runp, check...)
    - arguments that are required no matter the subcommand
    """
    # commands
    run: Optional[RunParser] = pydantic.Field(description=MESSAGE_BY_SUBCOMMAND["run"])

    # top-level arguments
    config_file: Optional[str] = pydantic.Field(
        description="Project configuration file"
    )
    pep_config: Optional[str] = pydantic.Field(description="PEP configuration file")
    output_dir: Optional[str] = pydantic.Field(description="Output directory")
    sample_pipeline_interfaces: Optional[str] = pydantic.Field(
        description="Sample pipeline interfaces definition"
    )
    project_pipeline_interfaces: Optional[str] = pydantic.Field(
        description="Project pipeline interfaces definition"
    )
    amend: Optional[bool] = pydantic.Field(description="List of amendments to activate")
    sel_flag: Optional[bool] = pydantic.Field(description="Selection flag")
    exc_flag: Optional[bool] = pydantic.Field(description="Exclusion flag")
    divvy: Optional[str] = pydantic.Field(
        description=(
            "Path to divvy configuration file. Default=$DIVCFG env "
            "variable. Currently: {}".format(os.getenv("DIVCFG", None) or "not set")
        )
    )




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
