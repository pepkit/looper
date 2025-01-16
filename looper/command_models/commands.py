"""
`pydantic` models for `looper` commands and a wrapper class.
"""

from dataclasses import dataclass
from typing import List, Optional, Type, Union

import pydantic.v1 as pydantic

from ..const import MESSAGE_BY_SUBCOMMAND
from .arguments import Argument, ArgumentEnum
from pydantic_argparse import ArgumentParser


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


SHARED_ARGUMENTS = [
    ArgumentEnum.SETTINGS.value,
    ArgumentEnum.EXC_FLAG.value,
    ArgumentEnum.SEL_FLAG.value,
    ArgumentEnum.SEL_ATTR.value,
    ArgumentEnum.SEL_INCL.value,
    ArgumentEnum.SEL_EXCL.value,
    ArgumentEnum.LIMIT.value,
    ArgumentEnum.SKIP.value,
    ArgumentEnum.PEP_CONFIG.value,
    ArgumentEnum.OUTPUT_DIR.value,
    ArgumentEnum.CONFIG.value,
    ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value,
    ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value,
    ArgumentEnum.PIPESTAT.value,
    ArgumentEnum.SETTINGS.value,
    ArgumentEnum.AMEND.value,
    ArgumentEnum.PROJECT_LEVEL.value,
]

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
        ArgumentEnum.LUMPJ.value,
        ArgumentEnum.DIVVY.value,
        ArgumentEnum.SKIP_FILE_CHECKS.value,
        ArgumentEnum.COMPUTE.value,
        ArgumentEnum.PACKAGE.value,
    ],
)

# RERUN
RerunParser = Command(
    "rerun",
    MESSAGE_BY_SUBCOMMAND["rerun"],
    [
        ArgumentEnum.IGNORE_FLAGS.value,
        ArgumentEnum.TIME_DELAY.value,
        ArgumentEnum.DRY_RUN.value,
        ArgumentEnum.COMMAND_EXTRA.value,
        ArgumentEnum.COMMAND_EXTRA_OVERRIDE.value,
        ArgumentEnum.LUMP.value,
        ArgumentEnum.LUMPN.value,
        ArgumentEnum.LUMPJ.value,
        ArgumentEnum.DIVVY.value,
        ArgumentEnum.SKIP_FILE_CHECKS.value,
        ArgumentEnum.COMPUTE.value,
        ArgumentEnum.PACKAGE.value,
    ],
)

# RUNP
RunProjectParser = Command(
    "runp",
    MESSAGE_BY_SUBCOMMAND["runp"],
    [
        ArgumentEnum.IGNORE_FLAGS.value,
        ArgumentEnum.TIME_DELAY.value,
        ArgumentEnum.DRY_RUN.value,
        ArgumentEnum.COMMAND_EXTRA.value,
        ArgumentEnum.COMMAND_EXTRA_OVERRIDE.value,
        ArgumentEnum.LUMP.value,
        ArgumentEnum.LUMPN.value,
        ArgumentEnum.DIVVY.value,
        ArgumentEnum.SKIP_FILE_CHECKS.value,
        ArgumentEnum.COMPUTE.value,
        ArgumentEnum.PACKAGE.value,
    ],
)

# TABLE
TableParser = Command(
    "table",
    MESSAGE_BY_SUBCOMMAND["table"],
    [
        ArgumentEnum.REPORT_OUTPUT_DIR.value,
    ],
)


# REPORT
ReportParser = Command(
    "report",
    MESSAGE_BY_SUBCOMMAND["report"],
    [
        ArgumentEnum.PORTABLE.value,
        ArgumentEnum.REPORT_OUTPUT_DIR.value,
    ],
)

# DESTROY
DestroyParser = Command(
    "destroy",
    MESSAGE_BY_SUBCOMMAND["destroy"],
    [
        ArgumentEnum.DRY_RUN.value,
        ArgumentEnum.FORCE_YES.value,
    ],
)

# CHECK
CheckParser = Command(
    "check",
    MESSAGE_BY_SUBCOMMAND["check"],
    [
        ArgumentEnum.DESCRIBE_CODES.value,
        ArgumentEnum.ITEMIZED.value,
        ArgumentEnum.FLAGS.value,
    ],
)

# CLEAN
CleanParser = Command(
    "clean",
    MESSAGE_BY_SUBCOMMAND["clean"],
    [
        ArgumentEnum.DRY_RUN.value,
        ArgumentEnum.FORCE_YES.value,
    ],
)

# INSPECT
InspectParser = Command(
    "inspect",
    MESSAGE_BY_SUBCOMMAND["inspect"],
    [],
)


# INIT
InitParser = Command(
    "init",
    MESSAGE_BY_SUBCOMMAND["init"],
    [
        # Original command has force flag which is technically a different flag, but we should just use FORCE_YES
        ArgumentEnum.FORCE_YES.value,
        ArgumentEnum.OUTPUT_DIR.value,
        ArgumentEnum.PEP_CONFIG.value,
        ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value,
        ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value,
        ArgumentEnum.GENERIC.value,
    ],
)


# INIT-PIFACE
InitPifaceParser = Command(
    "init_piface",
    MESSAGE_BY_SUBCOMMAND["init-piface"],
    [],
)


# LINK
LinkParser = Command(
    "link",
    MESSAGE_BY_SUBCOMMAND["link"],
    [],
)


# Add shared arguments for all commands that use them
for arg in SHARED_ARGUMENTS:
    RunParser.arguments.append(arg)
    RerunParser.arguments.append(arg)
    RunProjectParser.arguments.append(arg)
    ReportParser.arguments.append(arg)
    DestroyParser.arguments.append(arg)
    CheckParser.arguments.append(arg)
    CleanParser.arguments.append(arg)
    TableParser.arguments.append(arg)
    LinkParser.arguments.append(arg)
    InspectParser.arguments.append(arg)

# Create all Models
RunParserModel = RunParser.create_model()
RerunParserModel = RerunParser.create_model()
RunProjectParserModel = RunProjectParser.create_model()
ReportParserModel = ReportParser.create_model()
DestroyParserModel = DestroyParser.create_model()
CheckParserModel = CheckParser.create_model()
CleanParserModel = CleanParser.create_model()
TableParserModel = TableParser.create_model()
LinkParserModel = LinkParser.create_model()
InspectParserModel = InspectParser.create_model()
InitParserModel = InitParser.create_model()
InitPifaceParserModel = InitPifaceParser.create_model()


def add_short_arguments(
    parser: ArgumentParser, argument_enums: Type[ArgumentEnum]
) -> ArgumentParser:
    """
    This function takes a parser object created under pydantic argparse and adds the short arguments AFTER the initial creation.
    This is a workaround as pydantic-argparse does not currently support this during initial parser creation.

    :param ArgumentParser parser: parser before adding short arguments
    :param Type[ArgumentEnum] argument_enums:  enumeration of arguments that contain names and aliases
    :return ArgumentParser parser: parser after short arguments have been added
    """

    for cmd in parser._subcommands.choices.keys():

        for argument_enum in list(argument_enums):
            # First check there is an alias for the argument otherwise skip
            if argument_enum.value.alias:
                short_key = argument_enum.value.alias
                long_key = "--" + argument_enum.value.name.replace(
                    "_", "-"
                )  # We must do this because the ArgumentEnum names are transformed during parser creation
                if long_key in parser._subcommands.choices[cmd]._option_string_actions:
                    argument = parser._subcommands.choices[cmd]._option_string_actions[
                        long_key
                    ]
                    argument.option_strings = (short_key, long_key)
                    parser._subcommands.choices[cmd]._option_string_actions[
                        short_key
                    ] = argument

    return parser


SUPPORTED_COMMANDS = [
    RunParser,
    RerunParser,
    RunProjectParser,
    TableParser,
    ReportParser,
    DestroyParser,
    CheckParser,
    CleanParser,
    InitParser,
    InitPifaceParser,
    LinkParser,
    InspectParser,
]


class TopLevelParser(pydantic.BaseModel):
    """
    Top level parser that takes
    - commands (run, runp, check...)
    - arguments that are required no matter the subcommand
    """

    # commands
    run: Optional[RunParserModel] = pydantic.Field(description=RunParser.description)
    rerun: Optional[RerunParserModel] = pydantic.Field(
        description=RerunParser.description
    )
    runp: Optional[RunProjectParserModel] = pydantic.Field(
        description=RunProjectParser.description
    )
    table: Optional[TableParserModel] = pydantic.Field(
        description=TableParser.description
    )
    report: Optional[ReportParserModel] = pydantic.Field(
        description=ReportParser.description
    )
    destroy: Optional[DestroyParserModel] = pydantic.Field(
        description=DestroyParser.description
    )
    check: Optional[CheckParserModel] = pydantic.Field(
        description=CheckParser.description
    )
    clean: Optional[CleanParserModel] = pydantic.Field(
        description=CleanParser.description
    )
    init: Optional[InitParserModel] = pydantic.Field(description=InitParser.description)
    init_piface: Optional[InitPifaceParserModel] = pydantic.Field(
        description=InitPifaceParser.description
    )
    link: Optional[LinkParserModel] = pydantic.Field(description=LinkParser.description)

    inspect: Optional[InspectParserModel] = pydantic.Field(
        description=InspectParser.description
    )

    # Additional arguments for logging, added to ALL commands
    # These must be used before the command
    silent: Optional[bool] = ArgumentEnum.SILENT.value.with_reduced_default()
    verbosity: Optional[int] = ArgumentEnum.VERBOSITY.value.with_reduced_default()
    logdev: Optional[bool] = ArgumentEnum.LOGDEV.value.with_reduced_default()
