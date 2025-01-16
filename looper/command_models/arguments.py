"""
Argument definitions via a thin wrapper around `pydantic.fields.FieldInfo`
"""

import enum
import os
from copy import copy
from typing import Any, List

import pydantic.v1 as pydantic


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

    def __init__(
        self, name: str, default: Any, description: str, alias: str = None, **kwargs
    ) -> None:
        self._name = name
        super().__init__(
            default=default, description=description, alias=alias, **kwargs
        )
        self._validate()

    @property
    def name(self):
        """
        Argument name as used in the CLI, e.g. "ignore-args"
        """
        return self._name

    def with_reduced_default(self) -> pydantic.fields.FieldInfo:
        """
        Convert to a `FieldInfo` instance with reduced default value

        Returns a copy of an instance, but with the `default` attribute
        replaced by only the default value, without the type information.
        This is required when using an instance in a direct `pydantic`
        model definition, instead of creating a model dynamically using
        `pydantic.create_model`.

        TODO: this is due to this issue:
        https://github.com/pydantic/pydantic/issues/2248#issuecomment-757448447
        and it's a bit tedious.

        """
        c = copy(self)
        _, default_value = self.default
        c.default = default_value
        return c


class ArgumentEnum(enum.Enum):
    """
    Lists all available arguments

    Having a single "repository" of arguments allows us to re-use them easily across different commands.

    TODO: not sure whether an enum is the ideal data structure for that
    """

    IGNORE_FLAGS = Argument(
        name="ignore_flags",
        alias="-i",
        default=(bool, False),
        description="Ignore run status flags",
    )
    FORCE_YES = Argument(
        name="force_yes",
        alias="-f",
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
        alias="-f",
        default=(List, []),
        description="Only check samples based on these status flags.",
    )

    TIME_DELAY = Argument(
        name="time_delay",
        alias="-t",
        default=(int, 0),
        description="Time delay in seconds between job submissions (min: 0, max: 30)",
    )
    DRY_RUN = Argument(
        name="dry_run",
        alias="-d",
        default=(bool, False),
        description="Don't actually submit jobs",
    )
    COMMAND_EXTRA = Argument(
        name="command_extra",
        alias="-x",
        default=(str, ""),
        description="String to append to every command",
    )
    COMMAND_EXTRA_OVERRIDE = Argument(
        name="command_extra_override",
        alias="-y",
        default=(str, ""),
        description="Same as command-extra, but overrides values in PEP",
    )
    LUMP = Argument(
        name="lump",
        alias="-u",
        default=(float, None),
        description="Total input file size (GB) to batch into one job",
    )
    LUMPN = Argument(
        name="lump_n",
        alias="-n",
        default=(int, None),
        description="Number of commands to batch into one job",
    )
    LUMPJ = Argument(
        name="lump_j",
        alias="-j",
        default=(int, None),
        description="Lump samples into number of jobs.",
    )
    LIMIT = Argument(
        name="limit", alias="-l", default=(int, None), description="Limit to n samples"
    )
    SKIP = Argument(
        name="skip",
        alias="-k",
        default=(int, None),
        description="Skip samples by numerical index",
    )
    CONFIG = Argument(
        name="config",
        alias="-c",
        default=(str, None),
        description="Looper configuration file (YAML)",
    )
    SETTINGS = Argument(
        name="settings",
        default=(str, ""),
        description="Path to a YAML settings file with compute settings",
    )
    PEP_CONFIG = Argument(
        name="pep_config",
        default=(str, None),
        description="PEP configuration file",
    )
    OUTPUT_DIR = Argument(
        name="output_dir",
        alias="-o",
        default=(str, None),
        description="Output directory",
    )
    REPORT_OUTPUT_DIR = Argument(
        name="report_dir",
        alias="-r",
        default=(str, None),
        description="Set location for looper report and looper table outputs",
    )

    GENERIC = Argument(
        name="generic",
        alias="-g",
        default=(bool, False),
        description="Use generic looper config?",
    )

    SAMPLE_PIPELINE_INTERFACES = Argument(
        name="sample_pipeline_interfaces",
        alias="-S",
        default=(List, []),
        description="Paths to looper sample pipeline interfaces",
    )
    PROJECT_PIPELINE_INTERFACES = Argument(
        name="project_pipeline_interfaces",
        alias="-P",
        default=(List, []),
        description="Paths to looper project pipeline interfaces",
    )
    AMEND = Argument(
        name="amend", default=(List, []), description="List of amendments to activate"
    )
    SEL_ATTR = Argument(
        name="sel_attr",
        default=(str, "toggle"),
        description="Attribute for sample exclusion OR inclusion",
    )
    SEL_INCL = Argument(
        name="sel_incl",
        default=(List, []),
        description="Include only samples with these values",
    )
    SEL_EXCL = Argument(
        name="sel_excl",
        default=(str, ""),
        description="Exclude samples with these values",
    )
    SEL_FLAG = Argument(
        name="sel_flag", default=(List, []), description="Sample selection flag"
    )
    EXC_FLAG = Argument(
        name="exc_flag", default=(List, []), description="Sample exclusion flag"
    )
    SKIP_FILE_CHECKS = Argument(
        name="skip_file_checks",
        alias="-f",
        default=(bool, False),
        description="Do not perform input file checks",
    )
    PACKAGE = Argument(
        name="package",
        alias="-p",
        default=(str, None),
        description="Name of computing resource package to use",
    )
    COMPUTE = Argument(
        name="compute",
        default=(List, []),
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
        default=(int, None),
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
        default=(str, None),
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
