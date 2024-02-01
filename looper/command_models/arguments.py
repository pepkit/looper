"""
Argument definitions via a thin wrapper around `pydantic.fields.FieldInfo`
"""

import enum
import os
from copy import copy
from typing import Any, List

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
        default=(bool, False),
        description="Ignore run status flags",
    )
    TIME_DELAY = Argument(
        name="time_delay",
        default=(int, 0),
        description="Time delay in seconds between job submissions (min: 0, max: 30)",
    )
    DRY_RUN = Argument(
        name="dry_run", default=(bool, False), description="Don't actually submit jobs"
    )
    COMMAND_EXTRA = Argument(
        name="command_extra",
        default=(str, ""),
        description="String to append to every command",
    )
    COMMAND_EXTRA_OVERRIDE = Argument(
        name="command_extra_override",
        default=(str, ""),
        description="Same as command-extra, but overrides values in PEP",
    )
    LUMP = Argument(
        name="lump",
        default=(float, None),
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
    CONFIG_FILE = Argument(
        name="config_file",
        default=(str, None),
        description="Project configuration file",
    )
    LOOPER_CONFIG = Argument(
        name="looper_config",
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
        default=(str, None),
        description="Output directory",
    )
    SAMPLE_PIPELINE_INTERFACES = Argument(
        name="sample_pipeline_interfaces",
        default=(List, []),
        description="Paths to looper sample config files",
    )
    PROJECT_PIPELINE_INTERFACES = Argument(
        name="project_pipeline_interfaces",
        default=(List, []),
        description="Paths to looper project config files",
    )
    AMEND = Argument(
        name="amend", default=(List, []), description="List of amendments to activate"
    )
    SEL_FLAG = Argument(
        name="sel_flag", default=(str, ""), description="Sample selection flag"
    )
    EXC_FLAG = Argument(
        name="exc_flag", default=(str, ""), description="Sample exclusion flag"
    )
    SKIP_FILE_CHECKS = Argument(
        name="skip_file_checks",
        default=(bool, False),
        description="Do not perform input file checks",
    )
    PACKAGE = Argument(
        name="package",
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
