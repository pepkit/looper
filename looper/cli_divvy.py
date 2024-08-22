import logmuse
import os
import sys
import yaml
from yaml import SafeLoader
from ubiquerg import is_writable, VersionInHelpParser
from .const import (
    DEFAULT_COMPUTE_RESOURCES_NAME,
    DEFAULT_CONFIG_FILEPATH,
)
from .divvy import select_divvy_config, ComputingConfiguration, divvy_init


def build_argparser():
    """
    Builds argument parser.

    :return argparse.ArgumentParser
    """

    banner = (
        "%(prog)s - write compute job scripts that can be submitted to "
        "any computing resource"
    )
    additional_description = "\nhttps://divvy.databio.org"

    parser = VersionInHelpParser(
        prog="divvy",
        description=banner,
        epilog=additional_description,
        # version=__version__,
    )

    subparsers = parser.add_subparsers(dest="command")

    def add_subparser(cmd, description):
        return subparsers.add_parser(cmd, description=description, help=description)

    subparser_messages = {
        "init": "Initialize a new divvy config file",
        "list": "List available compute packages",
        "write": "Write a job script",
        "submit": "Write and then submit a job script",
        "inspect": "Inspect compute package",
    }

    sps = {}
    for cmd, desc in subparser_messages.items():
        sps[cmd] = add_subparser(cmd, desc)
        # sps[cmd].add_argument(
        #     "config", nargs="?", default=None,
        #     help="Divvy configuration file.")

    for sp in [sps["list"], sps["write"], sps["submit"], sps["inspect"]]:
        sp.add_argument(
            "--config", nargs="?", default=None, help="Divvy configuration file."
        )

    sps["init"].add_argument("--config", default=None, help="Divvy configuration file.")

    for sp in [sps["inspect"]]:
        sp.add_argument(
            "-p",
            "--package",
            default=DEFAULT_COMPUTE_RESOURCES_NAME,
            help="Select from available compute packages",
        )

    for sp in [sps["write"], sps["submit"]]:
        sp.add_argument(
            "-s",
            "--settings",
            help="YAML file with job settings to populate the template",
        )

        sp.add_argument(
            "-p",
            "--package",
            default=DEFAULT_COMPUTE_RESOURCES_NAME,
            help="Select from available compute packages",
        )

        sp.add_argument(
            "-c",
            "--compute",
            nargs="+",
            default=None,
            help="Extra key=value variable pairs",
        )

        # sp.add_argument(
        #         "-t", "--template",
        #         help="Provide a template file (not yet implemented).")

        sp.add_argument(
            "-o", "--outfile", required=False, default=None, help="Output filepath"
        )

    return parser


def main():
    """Primary workflow for divvy CLI"""

    parser = logmuse.add_logging_options(build_argparser())
    # args, remaining_args = parser.parse_known_args()
    args = parser.parse_args()

    logger_kwargs = {"level": args.verbosity, "devmode": args.logdev}
    logmuse.init_logger("yacman", **logger_kwargs)
    global _LOGGER
    _LOGGER = logmuse.logger_via_cli(args)

    if not args.command:
        parser.print_help()
        _LOGGER.error("No command given")
        sys.exit(1)

    if args.command == "init":
        divcfg = args.config
        _LOGGER.debug("Initializing divvy configuration")
        is_writable(os.path.dirname(divcfg), check_exist=False)
        divvy_init(divcfg, DEFAULT_CONFIG_FILEPATH)
        sys.exit(0)

    _LOGGER.debug("Divvy config: {}".format(args.config))

    divcfg = select_divvy_config(args.config)

    _LOGGER.info("Using divvy config: {}".format(divcfg))
    dcc = ComputingConfiguration.from_yaml_file(filepath=divcfg)

    if args.command == "list":
        # Output header via logger and content via print so the user can
        # redirect the list from stdout if desired without the header as clutter
        _LOGGER.info("Available compute packages:\n")
        print("{}".format("\n".join(dcc.list_compute_packages())))
        sys.exit(1)

    if args.command == "inspect":
        # Output contents of selected compute package
        _LOGGER.info("Your compute package template for: " + args.package + "\n")
        found = False
        for pkg_name, pkg in dcc.compute_packages.items():
            if pkg_name == args.package:
                found = True
                with open(pkg["submission_template"], "r") as f:
                    print(f.read())
                _LOGGER.info(
                    "Submission command is: " + pkg["submission_command"] + "\n"
                )
                if pkg_name == "docker":
                    print("Docker args are: " + pkg["docker_args"])

        if not found:
            _LOGGER.info("Package not found. Use 'divvy list' to see list of packages.")
        sys.exit(1)

    # Any non-divvy arguments will be passed along as key-value pairs
    # that can be used to populate the template.
    # keys = [str.replace(x, "--", "") for x in remaining_args[::2]]
    # cli_vars = dict(zip(keys, remaining_args[1::2]))
    if args.compute:
        cli_vars = {y[0]: y[1] for y in [x.split("=") for x in args.compute]}
    else:
        cli_vars = {}

    if args.command == "write" or args.command == "submit":
        try:
            dcc.activate_package(args.package)
        except AttributeError:
            parser.print_help(sys.stderr)
            sys.exit(1)

        if args.settings:
            _LOGGER.info("Loading settings file: %s", args.settings)
            with open(args.settings, "r") as f:
                vars_groups = [cli_vars, yaml.load(f, SafeLoader)]
        else:
            vars_groups = [cli_vars]

        _LOGGER.debug(vars_groups)
        if args.command == "write":
            dcc.write_script(args.outfile, vars_groups)
        elif args.command == "submit":
            dcc.submit(args.outfile, vars_groups)
