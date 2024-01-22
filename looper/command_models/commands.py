"""
`pydantic` models for `looper` commands and a wrapper class.
"""

from dataclasses import dataclass
from typing import List, Optional, Type

import pydantic

from ..const import MESSAGE_BY_SUBCOMMAND
from .arguments import Argument, ArgumentEnum


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
    arguments: List[Argument]

    def create_model(self) -> Type[pydantic.BaseModel]:
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
        ArgumentEnum.DIVVY.value,
    ],
)
RunParserModel = RunParser.create_model()

SUPPORTED_COMMANDS = [RunParser]


class TopLevelParser(pydantic.BaseModel):
    """
    Top level parser that takes
    - commands (run, runp, check...)
    - arguments that are required no matter the subcommand
    """

    # commands
    run: Optional[RunParserModel] = pydantic.Field(description=RunParser.description)

    # arguments
    settings: Optional[str] = ArgumentEnum.SETTINGS.value.with_reduced_default()
    pep_config: Optional[str] = ArgumentEnum.PEP_CONFIG.value.with_reduced_default()
    output_dir: Optional[str] = ArgumentEnum.OUTPUT_DIR.value.with_reduced_default()
    config_file: Optional[str] = ArgumentEnum.CONFIG_FILE.value.with_reduced_default()
    looper_config: Optional[
        str
    ] = ArgumentEnum.LOOPER_CONFIG.value.with_reduced_default()
    sample_pipeline_interfaces: Optional[
        List[str]
    ] = ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value.with_reduced_default()
    project_pipeline_interfaces: Optional[
        List[str]
    ] = ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value.with_reduced_default()
    amend: Optional[List[str]] = ArgumentEnum.AMEND.value.with_reduced_default()
    sel_flag: Optional[str] = ArgumentEnum.SEL_FLAG.value.with_reduced_default()
    exc_flag: Optional[str] = ArgumentEnum.EXC_FLAG.value.with_reduced_default()

    # arguments for logging
    silent: Optional[bool] = ArgumentEnum.SILENT.value.with_reduced_default()
    verbosity: Optional[int] = ArgumentEnum.VERBOSITY.value.with_reduced_default()
    logdev: Optional[bool] = ArgumentEnum.LOGDEV.value.with_reduced_default()
