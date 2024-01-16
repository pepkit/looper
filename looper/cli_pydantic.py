import pydantic_argparse

from .command_models.commands import TopLevelParser


def main() -> None:
    parser = pydantic_argparse.ArgumentParser(
        model=TopLevelParser,
        prog="looper",
        description="pydantic-argparse demo",
        add_help=True,
    )
    args = parser.parse_typed_args()
    print(args)


if __name__ == "__main__":
    main()
