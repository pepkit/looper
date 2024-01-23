import io
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout

import pydantic
from fastapi import FastAPI
from looper.cli_pydantic import run_looper
from looper.command_models.commands import SUPPORTED_COMMANDS, TopLevelParser

app = FastAPI(validate_model=True)

_UUID = None


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
            for command_argname, command_arg_value in vars(
                command_namespace_args
            ).items():
                setattr(
                    command_namespace,
                    command_argname,
                    command_arg_value,
                )
            setattr(namespace, argname, command_namespace)
    return namespace


class MainResponse(pydantic.BaseModel):
    """
    Response of the main endpoint.
    """

    stdout: str = pydantic.Field(
        description="Standard output produced by `looper` while running a command"
    )
    stderr: str = pydantic.Field(
        description="Standard error output produced by `looper` while running a command"
    )


@app.post("/")
async def main_endpoint(top_level_model: TopLevelParser) -> MainResponse:
    global _UUID
    argparse_namespace = create_argparse_namespace(top_level_model)
    stdout_stream = io.StringIO()
    stderr_stream = io.StringIO()
    with redirect_stderr(stderr_stream), redirect_stdout(stdout_stream):
        # TODO: as it stands, because of the `async def`, and the lacking `await`
        # in the following line, this endpoint is (I (Simeon) thing) currently blocking.
        # We would need to make `run_looper()` return a future, but it inherently does
        # not support `async` calls.
        # So one option would be to run `run_looper()` in its own thread whose
        # termination we can `await`, using `fastapi.run_in_threadpool`. But that fails
        # with an error stemming from the `yacman` library about `signal.signal` only
        # working in the main thread of the main interpreter. We have to investigate
        # how to solve this.
        _, _UUID = run_looper(argparse_namespace, None, True)
    return MainResponse(
        stdout=stdout_stream.getvalue(), stderr=stderr_stream.getvalue()
    )


@app.get("/status")
async def get_status():
    global _UUID
    if _UUID:
        print(_UUID)
        return {"UUID": _UUID}
    else:
        return {"UUID": "Not found"}
