from argparse import Namespace

from fastapi import FastAPI
from looper.cli_pydantic import run_looper
from looper.command_models.commands import SUPPORTED_COMMANDS, TopLevelParser

app = FastAPI(validate_model=True)


def create_argparse_namespace(top_level_model: TopLevelParser) -> Namespace:
    """
    Converts a TopLevelParser instance into an argparse.Namespace object.

    This function takes a TopLevelParser instance, and converts it into an
    argparse.Namespace object. It includes handling for supported commands
    specified in SUPPORTED_COMMANDS.

    :param TopLevelParser top_level_model: An instance of the TopLevelParser
        model
    :return argparse.Namespace: An argparse.Namespace object representing
        the parsed command-line arguments.
    """
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


@app.post("/run")
async def run_endpoint(top_level_model: TopLevelParser):
    argparse_namespace = create_argparse_namespace(top_level_model)
    run_looper(argparse_namespace, None, True)
    return top_level_model
