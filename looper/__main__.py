import argparse
import sys

from .cli_pydantic import main


def divvy_main(argv=None):
    """Entry point for the divvy CLI.

    Args:
        argv: List of arguments (defaults to sys.argv[1:]).

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    from .const import DEFAULT_CONFIG_FILEPATH
    from .divvy import ComputingConfiguration, divvy_init, select_divvy_config

    parser = argparse.ArgumentParser(
        prog="divvy",
        description="Write and submit compute job scripts.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # -- list --
    sp_list = subparsers.add_parser("list", help="List available compute packages")
    sp_list.add_argument("--config", help="Path to divvy configuration file")

    # -- init --
    sp_init = subparsers.add_parser("init", help="Initialize a new divvy config file")
    sp_init.add_argument("--config", required=True, help="Path for new config file")

    # -- inspect --
    sp_inspect = subparsers.add_parser(
        "inspect", help="Display the template for a compute package"
    )
    sp_inspect.add_argument(
        "-p", "--package", default="default", help="Compute package to inspect"
    )
    sp_inspect.add_argument("--config", help="Path to divvy configuration file")

    # -- write --
    sp_write = subparsers.add_parser(
        "write", help="Write a job submission script from a template"
    )
    sp_write.add_argument(
        "-p", "--package", default="default", help="Compute package to use"
    )
    sp_write.add_argument("-s", "--settings", help="YAML file with job settings")
    sp_write.add_argument(
        "-c", "--compute", nargs="+", help="Extra key=value variable pairs"
    )
    sp_write.add_argument("-o", "--outfile", help="Output file path")
    sp_write.add_argument("--config", help="Path to divvy configuration file")

    # -- submit --
    sp_submit = subparsers.add_parser(
        "submit", help="Write and submit a job submission script"
    )
    sp_submit.add_argument(
        "-p", "--package", default="default", help="Compute package to use"
    )
    sp_submit.add_argument("-s", "--settings", help="YAML file with job settings")
    sp_submit.add_argument(
        "-c", "--compute", nargs="+", help="Extra key=value variable pairs"
    )
    sp_submit.add_argument("-o", "--outfile", help="Output file path")
    sp_submit.add_argument("--config", help="Path to divvy configuration file")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    # Load divvy config
    config_path = getattr(args, "config", None)

    if args.command == "init":
        divvy_init(config_path, DEFAULT_CONFIG_FILEPATH)
        return 0

    dcc = ComputingConfiguration.from_yaml_file(
        filepath=select_divvy_config(config_path)
    )

    if args.command == "list":
        print("Available compute packages:\n")
        for pkg_name in sorted(dcc.list_compute_packages()):
            print(pkg_name)
        return 0

    if args.command == "inspect":
        dcc.activate_package(args.package)
        print(dcc.template())
        return 0

    # Parse --compute key=value pairs into a dict
    extra_vars = None
    if args.compute:
        extra_vars = {}
        for item in args.compute:
            if "=" in item:
                k, v = item.split("=", 1)
                extra_vars[k] = v
            else:
                print(
                    f"Invalid compute spec (expected key=value): {item}",
                    file=sys.stderr,
                )
                return 1

    # Load --settings YAML if provided
    if args.settings:
        from yacman import load_yaml

        settings_data = load_yaml(args.settings)
        if extra_vars:
            settings_data.update(extra_vars)
        extra_vars = settings_data

    dcc.activate_package(args.package)

    if args.command == "write":
        dcc.write_script(args.outfile, extra_vars)
        return 0

    if args.command == "submit":
        dcc.submit(args.outfile, extra_vars)
        return 0

    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Program canceled by user!")
        sys.exit(1)
