# `pydantic`-based definitions of `looper` commands and their arguments

With the goal of writing an HTTP API that is in sync with the `looper` CLI, this module defines `looper` commands as `pydantic` models and arguments as fields in there.
These can then be used by the [`pydantic-argparse`](https://pydantic-argparse.supimdos.com/) library to create a type-validated CLI (see `../cli_pydantic.py`), and by the future HTTP API for validating `POST`ed JSON data. Eventually, the `pydantic-argparse`-based CLI will replace the existing `argparse`-based CLI defined in `../cli_looper.py`.
