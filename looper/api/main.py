import os
import sys
from argparse import Namespace

import yaml
from divvy import select_divvy_config
from fastapi import FastAPI
from looper.cli_looper import _proc_resources_spec
from looper.command_models.commands import (  # RunParserModel,
    SUPPORTED_COMMANDS,
    TopLevelParser,
)
from looper.const import *
from looper.divvy import DEFAULT_COMPUTE_RESOURCES_NAME, select_divvy_config
from looper.exceptions import *
from looper.looper import *
from looper.parser_types import *
from looper.project import Project, ProjectContext
from looper.utils import (
    dotfile_path,
    enrich_args_via_cfg,
    is_registry_path,
    read_looper_dotfile,
)
from pephubclient import PEPHubClient

app = FastAPI(validate_model=True)


def create_argparse_namespace(top_level_model: TopLevelParser) -> Namespace:
    # Create an argparse namespace from the submitted top level model
    namespace = Namespace()
    for arg in vars(top_level_model):
        if arg not in [cmd.name for cmd in SUPPORTED_COMMANDS]:
            setattr(namespace, arg, getattr(top_level_model, arg))
        else:
            command_namespace = Namespace()
            command_namespace_args = getattr(top_level_model, arg)
            for argname in vars(command_namespace_args):
                setattr(
                    command_namespace,
                    argname,
                    getattr(command_namespace_args, argname),
                )
            setattr(namespace, arg, command_namespace)
    return namespace


def run_cmd(args: Namespace):
    # here comes adapted `cli_looper.py` code
    looper_cfg_path = os.path.relpath(dotfile_path(), start=os.curdir)
    try:
        looper_config_dict = read_looper_dotfile()

        for looper_config_key, looper_config_item in looper_config_dict.items():
            print(looper_config_key, looper_config_item)
            setattr(args, looper_config_key, looper_config_item)

    except OSError:
        # parser.print_help(sys.stderr)
        raise ValueError(
            f"Looper config file does not exist. Use looper init to create one at {looper_cfg_path}."
        )

    print("#####################################")
    print(args)

    args = enrich_args_via_cfg(args, None, False, True)
    divcfg = (
        select_divvy_config(filepath=args.run.divvy)
        if hasattr(args.run, "divvy")
        else None
    )
    # Ignore flags if user is selecting or excluding on flags:
    if args.sel_flag or args.exc_flag:
        args.ignore_flags = True

    # Initialize project
    if is_registry_path(args.config_file):
        if vars(args)[SAMPLE_PL_ARG]:
            p = Project(
                amendments=args.amend,
                divcfg_path=divcfg,
                runp=args.command == "runp",
                project_dict=PEPHubClient()._load_raw_pep(
                    registry_path=args.config_file
                ),
                **{
                    attr: getattr(args, attr) for attr in CLI_PROJ_ATTRS if attr in args
                },
            )
        else:
            raise MisconfigurationException(
                f"`sample_pipeline_interface` is missing. Provide it in the parameters."
            )
    else:
        try:
            p = Project(
                cfg=args.config_file,
                amendments=args.amend,
                divcfg_path=divcfg,
                runp=False,
                **{
                    attr: getattr(args, attr) for attr in CLI_PROJ_ATTRS if attr in args
                },
            )
        except yaml.parser.ParserError as e:
            _LOGGER.error(f"Project config parse failed -- {e}")
            sys.exit(1)

    selected_compute_pkg = p.selected_compute_package or DEFAULT_COMPUTE_RESOURCES_NAME
    if p.dcc is not None and not p.dcc.activate_package(selected_compute_pkg):
        _LOGGER.info(
            "Failed to activate '{}' computing package. "
            "Using the default one".format(selected_compute_pkg)
        )

    with ProjectContext(
        prj=p,
        selector_attribute="toggle",
        selector_include=None,
        selector_exclude=None,
        selector_flag=None,
        exclusion_flag=None,
    ) as prj:
        command = "run"
        if command == "run":
            run = Runner(prj)
            try:
                compute_kwargs = _proc_resources_spec(args)
                return run(args, rerun=False, **compute_kwargs)
            except SampleFailedException:
                sys.exit(1)
            except IOError:
                _LOGGER.error(
                    "{} pipeline_interfaces: '{}'".format(
                        prj.__class__.__name__, prj.pipeline_interface_sources
                    )
                )
                raise


@app.post("/run")
async def run_endpoint(top_level_model: TopLevelParser):
    print(top_level_model)
    argparse_namespace = create_argparse_namespace(top_level_model)
    run_cmd(argparse_namespace)
    return top_level_model
