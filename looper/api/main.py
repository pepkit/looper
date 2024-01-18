from fastapi import FastAPI
from looper.command_models.commands import RunParserModel

app = FastAPI(validate_model=True)


@app.post("/run")
async def run_endpoint(run_model: RunParserModel):
    print(run_model)
    return run_model
