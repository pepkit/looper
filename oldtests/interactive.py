# This is just a little helper script to set up an interactive session
# to help writing test cases.
# You must be in the looper oldtests dir:
# cd $CODEBASE/looper/oldtests
# ipython

import conftest

print("Establishing Project and PipelineInterface for testing and exploration")
proj, pi = conftest.interactive()
