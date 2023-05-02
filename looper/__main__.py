import sys

from .looper import main as looper_main
from .divvy import main as divvy_main

if __name__ == "__main__":
    try:
        sys.exit(looper_main())
    except KeyboardInterrupt:
        print("Program canceled by user!")
        sys.exit(1)
