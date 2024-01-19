from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
import io

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

    for argname, value in vars(top_level_model).items():
        if argname not in [cmd.name for cmd in SUPPORTED_COMMANDS]:
            setattr(namespace, argname, value)
        else:
            command_namespace = Namespace()
            command_namespace_args = value
            for command_argname, command_arg_value in vars(command_namespace_args).items():
                setattr(
                    command_namespace,
                    command_argname,
                    command_arg_value,
                )
            setattr(namespace, argname, command_namespace)
    return namespace


@app.post("/")
async def run_endpoint(top_level_model: TopLevelParser):
    argparse_namespace = create_argparse_namespace(top_level_model)
    stdout_stream = io.StringIO()
    stderr_stream = io.StringIO()
    with redirect_stderr(stderr_stream), redirect_stdout(stdout_stream):
        run_looper(argparse_namespace, None, True)
    return {
        "stdout": stdout_stream.getvalue(),
        "stderr": stderr_stream.getvalue()
    }
