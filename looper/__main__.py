import sys

from .looper import main as looper_main
from .divvy import main as divvy_main

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "divvy":
            # call divvy if divvy arg is provided
            sys.exit(divvy_main())
        else:
            # call looper
            sys.exit(looper_main())
    except KeyboardInterrupt:
        print("Program canceled by user!")
        sys.exit(1)
