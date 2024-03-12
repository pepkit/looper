# A simple utility, to be run in the root of a project, to prompt a user through
# configuring a .looper.yaml file for a new project. To be used as `looper init`.

import os

cfg = {}

print("This utility will walk you through creating a .looper.yaml file.")
print("See `looper init --help` for details.")
print("Use `looper run` afterwards to run the pipeline.")
print("Press ^C at any time to quit.\n")

looper_cfg_path = ".looper.yaml"  # not changeable

if os.path.exists(looper_cfg_path):
    print(f"File exists at '{looper_cfg_path}'. Delete it to re-initialize.")
    raise SystemExit

DEFAULTS = {  # What you get if you just press enter
    "pep_config": "databio/example",
    "output_dir": "results",
    "piface_path": "pipeline_interface.yaml",
    "project_name": os.path.basename(os.getcwd()),
}


cfg["project_name"] = (
    input(f"Project name: ({DEFAULTS['project_name']}) ") or DEFAULTS["project_name"]
)

cfg["pep_config"] = (
    input(f"Registry path or file path to PEP: ({DEFAULTS['pep_config']}) ")
    or DEFAULTS["pep_config"]
)

if not os.path.exists(cfg["pep_config"]):
    print(f"Warning: PEP file does not exist at '{cfg['pep_config']}'")

cfg["output_dir"] = (
    input(f"Path to output directory: ({DEFAULTS['output_dir']}) ")
    or DEFAULTS["output_dir"]
)

# TODO: Right now this assumes you will have one pipeline interface, and a sample pipeline
# but this is not the only way you could configure things.

piface_path = (
    input("Path to sample pipeline interface: (pipeline_interface.yaml) ")
    or DEFAULTS["piface_path"]
)

if not os.path.exists(piface_path):
    print(f"Warning: file does not exist at {piface_path}")

print(f"Writing config file to {looper_cfg_path}")
print(f"PEP path: {cfg['pep_config']}")
print(f"Pipeline interface path: {piface_path}")


with open(looper_cfg_path, "w") as fp:
    fp.write(
        f"""\
pep_config: {cfg['pep_config']}
output_dir: {cfg['output_dir']}
pipeline_interfaces:
  sample: {piface_path}
"""
    )
