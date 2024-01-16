from dataclasses import dataclass
from typing import Optional

import pydantic

from .arguments import Argument, ArgumentEnum
from ..const import MESSAGE_BY_SUBCOMMAND

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

    # arguments
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
    amend: Optional[bool] = pydantic.Field(description="Amend stuff?")
    sel_flag: Optional[bool] = pydantic.Field(description="Selection flag")
    exc_flag: Optional[bool] = pydantic.Field(description="Exclusion flag")
