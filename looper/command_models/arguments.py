"""
Argument definitions for CLI arguments/flags.

Stores CLI argument metadata (name, type, default, description, alias)
for use in both pydantic-settings CLI and FastAPI interfaces.
"""

import enum
import os
from typing import Any

import pydantic
from pydantic import AliasChoices


class Argument:
    """CLI argument / flag definition.

    This class stores CLI argument metadata for use in multiple interfaces:
    - pydantic-settings CLI (via CliSubCommand)
    - FastAPI HTTP API (via pydantic models)

    Args:
        name (str): Argument name, e.g. "ignore-args".
        default (Any): A tuple of the form (type, default_value). If the
            default value is `...` (Ellipsis), then the argument is required.
        description (str): Argument description, which will appear as the
            help text for this argument.
        alias (str | None): Short argument alias, e.g. "-i".
    """

    def __init__(
        self,
        name: str,
        default: Any,
        description: str,
        alias: str | None = None,
    ) -> None:
        self._name = name
        self._default = default  # tuple: (type, default_value)
        self._description = description
        self._alias = alias

    @property
    def name(self) -> str:
        """Argument name as used in the CLI, e.g. "ignore-args"."""
        return self._name

    @property
    def default(self) -> Any:
        """Default value tuple (type, default_value)."""
        return self._default

    @property
    def description(self) -> str:
        """Argument description / help text."""
        return self._description

    @property
    def alias(self) -> str | None:
        """Short argument alias, e.g. "-i"."""
        return self._alias

    def with_reduced_default(self) -> pydantic.fields.FieldInfo:
        """
        Create a FieldInfo instance with the default value (not the type tuple).

        This is used when defining pydantic model fields directly,
        where only the default value (not the type) is needed.

        Uses AliasChoices to support kebab-case CLI flags (--dry-run) while
        keeping underscore field names in Python (dry_run).
        """
        _, default_value = self._default
        # kebab-case version of the name for --dry-run style
        long_name = self._name.replace("_", "-")
        if self._alias:
            return pydantic.Field(
                default=default_value,
                description=self._description,
                validation_alias=AliasChoices(self._alias, long_name),
            )
        # Even without alias, include kebab-case for CLI compatibility
        return pydantic.Field(
            default=default_value,
            description=self._description,
            validation_alias=AliasChoices(long_name),
        )


class ArgumentEnum(enum.Enum):
    """
    Lists all available arguments

    Having a single "repository" of arguments allows us to re-use them easily across different commands.

    TODO: not sure whether an enum is the ideal data structure for that
    """

    IGNORE_FLAGS = Argument(
        name="ignore_flags",
        alias="i",
        default=(bool, False),
        description="Ignore run status flags",
    )
    FORCE_YES = Argument(
        name="force_yes",
        alias="f",
        default=(bool, False),
        description="Provide upfront confirmation of destruction intent, to skip console query. Default=False",
    )

    DESCRIBE_CODES = Argument(
        name="describe_codes",
        default=(bool, False),
        description="Show status codes description. Default=False",
    )

    ITEMIZED = Argument(
        name="itemized",
        default=(bool, False),
        description="Show detailed overview of sample statuses. Default=False",
    )

    FLAGS = Argument(
        name="flags",
        alias="f",
        default=(list, []),
        description="Only check samples based on these status flags.",
    )

    TIME_DELAY = Argument(
        name="time_delay",
        alias="t",
        default=(int, 0),
        description="Time delay in seconds between job submissions (min: 0, max: 30)",
    )
    DRY_RUN = Argument(
        name="dry_run",
        alias="d",
        default=(bool, False),
        description="Don't actually submit jobs",
    )
    COMMAND_EXTRA = Argument(
        name="command_extra",
        alias="x",
        default=(str, ""),
        description="String to append to every command",
    )
    COMMAND_EXTRA_OVERRIDE = Argument(
        name="command_extra_override",
        alias="y",
        default=(str, ""),
        description="Same as command-extra, but overrides values in PEP",
    )
    LUMP = Argument(
        name="lump",
        alias="u",
        default=(float | None, None),
        description="Total input file size (GB) to batch into one job",
    )
    LUMPN = Argument(
        name="lump_n",
        alias="n",
        default=(int | None, None),
        description="Number of commands to batch into one job",
    )
    LUMPJ = Argument(
        name="lump_j",
        alias="j",
        default=(int | None, None),
        description="Lump samples into number of jobs.",
    )
    LIMIT = Argument(
        name="limit", alias="l", default=(int | None, None), description="Limit to n samples"
    )
    SKIP = Argument(
        name="skip",
        alias="k",
        default=(int | None, None),
        description="Skip samples by numerical index",
    )
    CONFIG = Argument(
        name="config",
        alias="c",
        default=(str | None, None),
        description="Looper configuration file (YAML)",
    )
    SETTINGS = Argument(
        name="settings",
        default=(str, ""),
        description="Path to a YAML settings file with compute settings",
    )
    PEP_CONFIG = Argument(
        name="pep_config",
        default=(str | None, None),
        description="PEP configuration file",
    )
    OUTPUT_DIR = Argument(
        name="output_dir",
        alias="o",
        default=(str | None, None),
        description="Output directory",
    )
    REPORT_OUTPUT_DIR = Argument(
        name="report_dir",
        alias="r",
        default=(str | None, None),
        description="Set location for looper report and looper table outputs",
    )

    GENERIC = Argument(
        name="generic",
        alias="g",
        default=(bool, False),
        description="Use generic looper config?",
    )

    SAMPLE_PIPELINE_INTERFACES = Argument(
        name="sample_pipeline_interfaces",
        # Backwards compatibility note: Changed from -S to spi with pydantic-settings
        # migration. Single-letter aliases are case-insensitive in pydantic-settings,
        # causing conflicts with other arguments.
        alias="spi",
        default=(list, []),
        description="Paths to looper sample pipeline interfaces",
    )
    PROJECT_PIPELINE_INTERFACES = Argument(
        name="project_pipeline_interfaces",
        # Backwards compatibility note: Changed from -P to ppi with pydantic-settings
        # migration. Single-letter aliases are case-insensitive in pydantic-settings,
        # causing conflicts with other arguments.
        alias="ppi",
        default=(list, []),
        description="Paths to looper project pipeline interfaces",
    )
    AMEND = Argument(
        name="amend", default=(list, []), description="List of amendments to activate"
    )
    SEL_ATTR = Argument(
        name="sel_attr",
        default=(str, "toggle"),
        description="Attribute for sample exclusion OR inclusion",
    )
    SEL_INCL = Argument(
        name="sel_incl",
        default=(list, []),
        description="Include only samples with these values",
    )
    SEL_EXCL = Argument(
        name="sel_excl",
        default=(str, ""),
        description="Exclude samples with these values",
    )
    SEL_FLAG = Argument(
        name="sel_flag", default=(list, []), description="Sample selection flag"
    )
    EXC_FLAG = Argument(
        name="exc_flag", default=(list, []), description="Sample exclusion flag"
    )
    SKIP_FILE_CHECKS = Argument(
        name="skip_file_checks",
        alias="f",  # Restored: no conflict since run/rerun/runp don't use FORCE_YES
        default=(bool, False),
        description="Do not perform input file checks",
    )
    PACKAGE = Argument(
        name="package",
        alias="p",
        default=(str | None, None),
        description="Name of computing resource package to use",
    )
    COMPUTE = Argument(
        name="compute",
        default=(list, []),
        description="List of key-value pairs (k1=v1)",
    )
    DIVVY = Argument(
        name="divvy",
        default=(str, os.getenv("DIVCFG", None)),
        description=(
            "Path to divvy configuration file. Default=$DIVCFG env "
            "variable. Currently: {}".format(os.getenv("DIVCFG") or "not set")
        ),
    )
    # Arguments for logger compatible with logmuse
    SILENT = Argument(
        name="silent", default=(bool, False), description="Whether to silence logging"
    )
    VERBOSITY = Argument(
        name="verbosity",
        default=(int | None, None),
        description="Alternate mode of expression for logging level that better "
        "accords with intuition about how to convey this.",
    )
    LOGDEV = Argument(
        name="logdev",
        default=(bool, False),
        description="Whether to log in development mode; possibly among other "
        "behavioral changes to logs handling, use a more information-rich "
        "message format template.",
    )
    PIPESTAT = Argument(
        name="pipestat",
        default=(str | None, None),
        description="Path to pipestat files.",
    )
    PORTABLE = Argument(
        name="portable",
        default=(bool, False),
        description="Makes html report portable.",
    )
    PROJECT_LEVEL = Argument(
        name="project",
        default=(bool, False),
        description="Is this command executed for project-level?",
    )
