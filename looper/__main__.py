import sys

from .cli_looper import main
from .cli_divvy import main as divvy_main

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Program canceled by user!")
        sys.exit(1)
