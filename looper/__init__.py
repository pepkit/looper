"""Project configuration, particularly for logging.

Project-scope constants may reside here, but more importantly, some setup here
will provide a logging infrastructure for all of the project's modules.
Individual modules and classes may provide separate configuration on a more
local level, but this will at least provide a foundation.

"""

from importlib.metadata import version

__version__ = version("looper")

# Lazy imports - only loaded when accessed
_lazy_imports = {
    "DEFAULT_COMPUTE_RESOURCES_NAME": ".divvy",
    "ComputingConfiguration": ".divvy",
    "select_divvy_config": ".divvy",
    "COMPUTE_KEY": ".divvy",  # NEW_COMPUTE_KEY
    "SubmissionConductor": ".conductor",
    "write_submission_yaml": ".conductor",
    "PipelineInterface": ".pipeline_interface",
    "write_custom_template": ".plugins",
    "write_sample_yaml": ".plugins",
    "write_sample_yaml_cwl": ".plugins",
    "write_sample_yaml_prj": ".plugins",
    "Project": ".project",
}


def __getattr__(name):
    if name in _lazy_imports:
        module_path = _lazy_imports[name]
        import importlib

        module = importlib.import_module(module_path, __package__)
        value = getattr(module, name if name != "COMPUTE_KEY" else "NEW_COMPUTE_KEY")
        globals()[name] = value  # Cache for subsequent access
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return list(_lazy_imports.keys()) + ["__version__"]


__all__ = [
    "Project",
    "PipelineInterface",
    "SubmissionConductor",
    "ComputingConfiguration",
    "select_divvy_config",
]
