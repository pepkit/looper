"""
`pydantic` models for `looper` commands and a wrapper class.

Uses native pydantic v2 for model definitions. The CLI is built from
these models using argparse in cli_pydantic.py.
"""

import json
from dataclasses import dataclass
from typing import Annotated

import pydantic
from pydantic import AliasChoices, BeforeValidator, Field
from pydantic_settings import BaseSettings, CliSubCommand, SettingsConfigDict

from .arguments import Argument, ArgumentEnum
from .messages import MESSAGE_BY_SUBCOMMAND  # Local import, no looper/__init__.py


def deserialize_cli_list(v):
    """Deserialize list values from pydantic-settings CLI parsing.

    pydantic-settings internally serializes all list values as JSON strings
    (e.g., ["a"] becomes '["a"]') before passing to CliSubCommand models.
    Since subcommands are instantiated directly (not through settings sources),
    the automatic JSON deserialization doesn't happen.

    This is a pydantic-settings limitation, not a bug in our code.
    See: https://github.com/pydantic/pydantic-settings/issues/335
    """
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return [x.strip() for x in v.split(",") if x.strip()]
    return v


CliList = Annotated[list, BeforeValidator(deserialize_cli_list)]


@dataclass
class Command:
    """Representation of a command.

    Args:
        name (str): Command name.
        description (str): Command description.
        arguments (list[Argument]): List of arguments supported by this command.
    """

    name: str
    description: str
    arguments: list[Argument]

    def create_model(self) -> type[pydantic.BaseModel]:
        """
        Creates a `pydantic` model for this command.

        Uses AliasChoices to support kebab-case CLI flags (--dry-run) while
        keeping underscore field names in Python (dry_run).
        """
        arguments = {}
        for arg in self.arguments:
            arg_type, arg_default_value = arg.default
            if arg_type is list:
                arg_type = CliList
            # kebab-case version of the name for --dry-run style
            long_name = arg.name.replace("_", "-")
            if arg.alias:
                field = pydantic.Field(
                    arg_default_value,
                    description=arg.description,
                    validation_alias=AliasChoices(arg.alias, long_name),
                )
            else:
                # Even without alias, include kebab-case for CLI compatibility
                field = pydantic.Field(
                    arg_default_value,
                    description=arg.description,
                    validation_alias=AliasChoices(long_name),
                )
            arguments[arg.name] = (arg_type, field)
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

# Create all Models (for use with FastAPI)
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


class TopLevelParser(BaseSettings):
    """A pipeline submission engine for PEP-formatted projects."""

    model_config = SettingsConfigDict(
        cli_parse_args=True,
        cli_prog_name="looper",
        cli_kebab_case=True,  # Use --dry-run not --dry_run
        cli_implicit_flags=True,  # Allow --dry-run without value (instead of --dry-run true)
        cli_hide_none_type=True,  # Hide {bool,null} type hints in help
    )

    # commands (CliSubCommand creates argparse subparsers - only one is used at a time)
    run: CliSubCommand[RunParserModel] = Field(description=MESSAGE_BY_SUBCOMMAND["run"])
    rerun: CliSubCommand[RerunParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["rerun"]
    )
    runp: CliSubCommand[RunProjectParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["runp"]
    )
    table: CliSubCommand[TableParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["table"]
    )
    report: CliSubCommand[ReportParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["report"]
    )
    destroy: CliSubCommand[DestroyParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["destroy"]
    )
    check: CliSubCommand[CheckParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["check"]
    )
    clean: CliSubCommand[CleanParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["clean"]
    )
    init: CliSubCommand[InitParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["init"]
    )
    init_piface: CliSubCommand[InitPifaceParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["init-piface"]
    )
    link: CliSubCommand[LinkParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["link"]
    )
    inspect: CliSubCommand[InspectParserModel] = Field(
        description=MESSAGE_BY_SUBCOMMAND["inspect"]
    )

    # Additional arguments for logging
    silent: bool | None = ArgumentEnum.SILENT.value.with_reduced_default()
    verbosity: int | None = ArgumentEnum.VERBOSITY.value.with_reduced_default()
    logdev: bool | None = ArgumentEnum.LOGDEV.value.with_reduced_default()
