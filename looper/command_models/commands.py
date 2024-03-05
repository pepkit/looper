"""
`pydantic` models for `looper` commands and a wrapper class.
"""

from dataclasses import dataclass
from typing import List, Optional, Type, Union

import pydantic.v1 as pydantic

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
        ArgumentEnum.LUMPJ.value,
        ArgumentEnum.DIVVY.value,
        ArgumentEnum.SKIP_FILE_CHECKS.value,
        ArgumentEnum.COMPUTE.value,
        ArgumentEnum.PACKAGE.value,
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
        ArgumentEnum.CONFIG_FILE.value,
        ArgumentEnum.LOOPER_CONFIG.value,
        ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value,
        ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value,
        ArgumentEnum.PIPESTAT.value,
        ArgumentEnum.SETTINGS.value,
        ArgumentEnum.AMEND.value,
    ],
)
RunParserModel = RunParser.create_model()

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
        ArgumentEnum.CONFIG_FILE.value,
        ArgumentEnum.LOOPER_CONFIG.value,
        ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value,
        ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value,
        ArgumentEnum.PIPESTAT.value,
        ArgumentEnum.SETTINGS.value,
        ArgumentEnum.AMEND.value,
    ],
)
RerunParserModel = RerunParser.create_model()

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
        ArgumentEnum.CONFIG_FILE.value,
        ArgumentEnum.LOOPER_CONFIG.value,
        ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value,
        ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value,
        ArgumentEnum.PIPESTAT.value,
        ArgumentEnum.SETTINGS.value,
        ArgumentEnum.AMEND.value,
    ],
)
RunProjectParserModel = RunProjectParser.create_model()

# TABLE
TableParser = Command(
    "table",
    MESSAGE_BY_SUBCOMMAND["table"],
    [
        ArgumentEnum.EXC_FLAG.value,
        ArgumentEnum.SEL_FLAG.value,
        ArgumentEnum.SEL_ATTR.value,
        ArgumentEnum.SEL_INCL.value,
        ArgumentEnum.SEL_EXCL.value,
        ArgumentEnum.LIMIT.value,
        ArgumentEnum.SKIP.value,
        ArgumentEnum.PEP_CONFIG.value,
        ArgumentEnum.OUTPUT_DIR.value,
        ArgumentEnum.CONFIG_FILE.value,
        ArgumentEnum.LOOPER_CONFIG.value,
        ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value,
        ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value,
        ArgumentEnum.PIPESTAT.value,
        ArgumentEnum.AMEND.value,
    ],
)
TableParserModel = TableParser.create_model()


# REPORT
ReportParser = Command(
    "report",
    MESSAGE_BY_SUBCOMMAND["report"],
    [
        ArgumentEnum.PORTABLE.value,
        ArgumentEnum.EXC_FLAG.value,
        ArgumentEnum.SEL_FLAG.value,
        ArgumentEnum.SEL_ATTR.value,
        ArgumentEnum.SEL_INCL.value,
        ArgumentEnum.SEL_EXCL.value,
        ArgumentEnum.LIMIT.value,
        ArgumentEnum.SKIP.value,
        ArgumentEnum.PEP_CONFIG.value,
        ArgumentEnum.OUTPUT_DIR.value,
        ArgumentEnum.CONFIG_FILE.value,
        ArgumentEnum.LOOPER_CONFIG.value,
        ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value,
        ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value,
        ArgumentEnum.PIPESTAT.value,
        ArgumentEnum.AMEND.value,
    ],
)
ReportParserModel = ReportParser.create_model()

# DESTROY
DestroyParser = Command(
    "destroy",
    MESSAGE_BY_SUBCOMMAND["destroy"],
    [
        ArgumentEnum.DRY_RUN.value,
        ArgumentEnum.FORCE_YES.value,
        ArgumentEnum.EXC_FLAG.value,
        ArgumentEnum.SEL_FLAG.value,
        ArgumentEnum.SEL_ATTR.value,
        ArgumentEnum.SEL_INCL.value,
        ArgumentEnum.SEL_EXCL.value,
        ArgumentEnum.LIMIT.value,
        ArgumentEnum.SKIP.value,
        ArgumentEnum.PEP_CONFIG.value,
        ArgumentEnum.OUTPUT_DIR.value,
        ArgumentEnum.CONFIG_FILE.value,
        ArgumentEnum.LOOPER_CONFIG.value,
        ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value,
        ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value,
        ArgumentEnum.PIPESTAT.value,
        ArgumentEnum.AMEND.value,
    ],
)
DestroyParserModel = DestroyParser.create_model()

# CHECK
CheckParser = Command(
    "check",
    MESSAGE_BY_SUBCOMMAND["check"],
    [
        ArgumentEnum.DESCRIBE_CODES.value,
        ArgumentEnum.ITEMIZED.value,
        ArgumentEnum.FLAGS.value,
        ArgumentEnum.EXC_FLAG.value,
        ArgumentEnum.SEL_FLAG.value,
        ArgumentEnum.SEL_ATTR.value,
        ArgumentEnum.SEL_INCL.value,
        ArgumentEnum.SEL_EXCL.value,
        ArgumentEnum.LIMIT.value,
        ArgumentEnum.SKIP.value,
        ArgumentEnum.PEP_CONFIG.value,
        ArgumentEnum.OUTPUT_DIR.value,
        ArgumentEnum.CONFIG_FILE.value,
        ArgumentEnum.LOOPER_CONFIG.value,
        ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value,
        ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value,
        ArgumentEnum.PIPESTAT.value,
        ArgumentEnum.AMEND.value,
    ],
)
CheckParserModel = CheckParser.create_model()

# CLEAN
CleanParser = Command(
    "clean",
    MESSAGE_BY_SUBCOMMAND["clean"],
    [
        ArgumentEnum.DRY_RUN.value,
        ArgumentEnum.FORCE_YES.value,
        ArgumentEnum.EXC_FLAG.value,
        ArgumentEnum.SEL_FLAG.value,
        ArgumentEnum.SEL_ATTR.value,
        ArgumentEnum.SEL_INCL.value,
        ArgumentEnum.SEL_EXCL.value,
        ArgumentEnum.LIMIT.value,
        ArgumentEnum.SKIP.value,
        ArgumentEnum.PEP_CONFIG.value,
        ArgumentEnum.OUTPUT_DIR.value,
        ArgumentEnum.CONFIG_FILE.value,
        ArgumentEnum.LOOPER_CONFIG.value,
        ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value,
        ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value,
        ArgumentEnum.PIPESTAT.value,
        ArgumentEnum.SETTINGS.value,
        ArgumentEnum.AMEND.value,
    ],
)
CleanParserModel = CleanParser.create_model()

# INSPECT
# TODO Did this move to Eido?
InspectParser = Command(
    "inspect",
    MESSAGE_BY_SUBCOMMAND["inspect"],
    [],
)
InspectParserModel = InspectParser.create_model()

# INIT
# TODO rename to `init-config` ?
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
    ],
)
InitParserModel = InitParser.create_model()

# INIT-PIFACE
InitPifaceParser = Command(
    "init_piface",
    MESSAGE_BY_SUBCOMMAND["init-piface"],
    [],
)
InitPifaceParserModel = InitPifaceParser.create_model()

# LINK
LinkParser = Command(
    "link",
    MESSAGE_BY_SUBCOMMAND["link"],
    [
        ArgumentEnum.EXC_FLAG.value,
        ArgumentEnum.SEL_FLAG.value,
        ArgumentEnum.SEL_ATTR.value,
        ArgumentEnum.SEL_INCL.value,
        ArgumentEnum.SEL_EXCL.value,
        ArgumentEnum.LIMIT.value,
        ArgumentEnum.SKIP.value,
        ArgumentEnum.PEP_CONFIG.value,
        ArgumentEnum.OUTPUT_DIR.value,
        ArgumentEnum.CONFIG_FILE.value,
        ArgumentEnum.LOOPER_CONFIG.value,
    ],
)
LinkParserModel = LinkParser.create_model()

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

    # arguments
    # settings: Optional[str] = ArgumentEnum.SETTINGS.value.with_reduced_default()
    # pep_config: Optional[str] = ArgumentEnum.PEP_CONFIG.value.with_reduced_default()
    # output_dir: Optional[str] = ArgumentEnum.OUTPUT_DIR.value.with_reduced_default()
    # config_file: Optional[str] = ArgumentEnum.CONFIG_FILE.value.with_reduced_default()
    # looper_config: Optional[str] = (
    #     ArgumentEnum.LOOPER_CONFIG.value.with_reduced_default()
    # )
    # sample_pipeline_interfaces: Optional[List[str]] = (
    #     ArgumentEnum.SAMPLE_PIPELINE_INTERFACES.value.with_reduced_default()
    # )
    # project_pipeline_interfaces: Optional[List[str]] = (
    #     ArgumentEnum.PROJECT_PIPELINE_INTERFACES.value.with_reduced_default()
    # )
    # amend: Optional[List[str]] = ArgumentEnum.AMEND.value.with_reduced_default()
    # sel_attr: Optional[str] = ArgumentEnum.SEL_ATTR.value.with_reduced_default()
    # sel_incl: Optional[str] = ArgumentEnum.SEL_INCL.value.with_reduced_default()
    # sel_excl: Optional[str] = ArgumentEnum.SEL_EXCL.value.with_reduced_default()
    # sel_flag: Optional[str] = ArgumentEnum.SEL_FLAG.value.with_reduced_default()
    # exc_flag: Optional[Union[str, List[str]]] = (
    #     ArgumentEnum.EXC_FLAG.value.with_reduced_default()
    # )

    # arguments for logging
    silent: Optional[bool] = ArgumentEnum.SILENT.value.with_reduced_default()
    verbosity: Optional[int] = ArgumentEnum.VERBOSITY.value.with_reduced_default()
    logdev: Optional[bool] = ArgumentEnum.LOGDEV.value.with_reduced_default()
    # pipestat: Optional[str] = ArgumentEnum.PIPESTAT.value.with_reduced_default()
    # limit: Optional[int] = ArgumentEnum.LIMIT.value.with_reduced_default()
    # skip: Optional[int] = ArgumentEnum.SKIP.value.with_reduced_default()
