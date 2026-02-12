import secrets
from argparse import ArgumentParser, Namespace
from typing import Dict

import fastapi
import pydantic
import uvicorn
from fastapi import FastAPI, HTTPException

from looper.api import stdout_redirects
from looper.cli_pydantic import run_looper
from looper.command_models.commands import SUPPORTED_COMMANDS, TopLevelParser

stdout_redirects.enable_proxy()


class Job(pydantic.BaseModel):
    id: str = pydantic.Field(
        default_factory=lambda: secrets.token_urlsafe(4),
        description="The unique identifier of the job",
    )
    status: str = pydantic.Field(
        default="in_progress",
        description="The current status of the job. Can be `in_progress`, `completed`, or `failed`.",
    )
    console_output: str | None = pydantic.Field(
        default=None,
        description="Console output produced by `looper` while performing the requested action",
    )
    error: str | None = pydantic.Field(
        default=None,
        description="Error message if the job failed",
    )


app = FastAPI(validate_model=True)
jobs: Dict[str, Job] = {}


def background_async(top_level_model: TopLevelParser, job_id: str) -> None:
    argparse_namespace = create_argparse_namespace(top_level_model)
    output_stream = stdout_redirects.redirect()

    try:
        run_looper(argparse_namespace)
        jobs[job_id].status = "completed"
    except Exception as e:
        jobs[job_id].status = "failed"
        jobs[job_id].error = str(e)
    finally:
        # Here, we should call `stdout_redirects.stop_redirect()`, but that fails for reasons discussed
        # in the following issue: https://github.com/python/cpython/issues/80374
        # But this *seems* not to pose any problems.
        jobs[job_id].console_output = output_stream.getvalue()


def create_argparse_namespace(top_level_model: TopLevelParser) -> Namespace:
    """
    Converts a TopLevelParser instance into an argparse.Namespace object.

    This function takes a TopLevelParser instance, and converts it into an
    argparse.Namespace object compatible with run_looper().

    :param TopLevelParser top_level_model: An instance of the TopLevelParser model
    :return argparse.Namespace: An argparse.Namespace object representing
        the parsed command-line arguments.
    """
    namespace = Namespace()

    # Find which command was specified and set it
    command_name = None
    for cmd in SUPPORTED_COMMANDS:
        cmd_value = getattr(top_level_model, cmd.name, None)
        if cmd_value is not None:
            command_name = cmd.name
            # Add all command arguments to the namespace
            for argname, value in vars(cmd_value).items():
                setattr(namespace, argname, value)
            break

    namespace.command = command_name

    # Add top-level arguments
    namespace.silent = top_level_model.silent
    namespace.verbosity = top_level_model.verbosity
    namespace.logdev = top_level_model.logdev

    return namespace


@app.post(
    "/",
    status_code=202,
    summary="Run Looper",
    description="Start a `looper` command with arguments specified in "
    "`top_level_model` in the background and return a job identifier.",
)
async def main_endpoint(
    top_level_model: TopLevelParser, background_tasks: fastapi.BackgroundTasks
) -> Dict:
    job = Job()
    jobs[job.id] = job
    background_tasks.add_task(background_async, top_level_model, job.id)
    return {"job_id": job.id}


@app.get(
    "/status/{job_id}",
    summary="Get job status",
    description="Retrieve the status of a job based on its unique identifier.",
)
async def get_status(job_id: str) -> Job:
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return jobs[job_id]


@app.get(
    "/jobs",
    summary="List all jobs",
    description="Retrieve a list of all submitted jobs with their IDs and statuses.",
)
async def list_jobs() -> Dict:
    return {"jobs": [{"id": job.id, "status": job.status} for job in jobs.values()]}


def main() -> None:
    parser = ArgumentParser("looper-serve", description="Run looper HTTP API server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host IP address to use (127.0.0.1 for local access only)",
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port the server listens on"
    )
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
