import pydantic

class TopLevelParser(pydantic.BaseModel):
    """
    Top level parser that takes
    - commands (run, runp, check...)
    - arguments that are required no matter the subcommand
    """
    # commands
    ...

    # top-level arguments
    ...
