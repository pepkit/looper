from argparse import Namespace

from fastapi import FastAPI
from looper.command_models.commands import RunParserModel

app = FastAPI(validate_model=True)


def create_argparse_namespace(run_model: RunParserModel) -> Namespace:
    # Create an argparse namespace from the submitted run model
    namespace = Namespace()
    for arg in vars(run_model):
        setattr(namespace, arg, getattr(run_model, arg))
    return namespace


@app.post("/run")
async def run_endpoint(run_model: RunParserModel):
    argparse_namespace = create_argparse_namespace(run_model)
    print(argparse_namespace)
    return run_model
