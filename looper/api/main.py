import io
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
import secrets
from typing import Dict, TypeAlias

import fastapi
from fastapi import FastAPI
import pydantic

from looper.cli_pydantic import run_looper
from looper.command_models.commands import SUPPORTED_COMMANDS, TopLevelParser

JobId: TypeAlias = str

class Job(pydantic.BaseModel):
    id: JobId = pydantic.Field(
        default_factory=lambda: secrets.token_urlsafe(4),
        description="The unique identifier of the job"
    )
    status: str = pydantic.Field(
        default="in_progress",
        description="The current status of the job. Can be either `in_progress` or `completed`."
    )
    progress: int = 0
    stdout: str | None = pydantic.Field(default=None,
        description="Standard output produced by `looper` while performing the requested action"
    )
    stderr: str | None = pydantic.Field(default=None,
        description="Standard error output produced by `looper` while performing the requested action"
    )

app = FastAPI(validate_model=True)
jobs: Dict[str, Job] = {}


async def background_async(top_level_model: TopLevelParser, job_id: JobId) -> None:
    argparse_namespace = create_argparse_namespace(top_level_model)
    stdout_stream = io.StringIO()
    stderr_stream = io.StringIO()
    with redirect_stderr(stderr_stream), redirect_stdout(stdout_stream):
        # TODO: as it stands, because of the `async def`, and the lacking `await`
        # in the following line, this endpoint is (I (Simeon) think) currently blocking.
        # We would need to make `run_looper()` return a future, but it inherently does
        # not support `async` calls.
        # So one option would be to run `run_looper()` in its own thread whose
        # termination we can `await`, using `fastapi.run_in_threadpool`. But that fails
        # with an error stemming from the `yacman` library about `signal.signal` only
        # working in the main thread of the main interpreter. We have to investigate
        # how to solve this.
        run_looper(argparse_namespace, None, True)

    jobs[job_id].status = "completed"
    jobs[job_id].stdout = stdout_stream.getvalue()
    jobs[job_id].stderr = stderr_stream.getvalue()


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

@app.post("/", status_code=202)
async def main_endpoint(top_level_model: TopLevelParser, background_tasks: fastapi.BackgroundTasks) -> Dict:
    job = Job()
    jobs[job.id] = job
    background_tasks.add_task(background_async, top_level_model, job.id)
    return {"job_id": job.id}


@app.get("/status/{job_id}")
async def get_status(job_id: JobId):
    return jobs[job_id]
