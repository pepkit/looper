"""Subcommand help messages for CLI.

Extracted to avoid importing looper.const (which triggers heavy package imports)
during CLI startup for --help.
"""

MESSAGE_BY_SUBCOMMAND = {
    "run": "Run or submit sample jobs.",
    "rerun": "Resubmit sample jobs with failed flags.",
    "runp": "Run or submit project jobs.",
    "table": "Write summary stats table for project samples.",
    "report": "Create browsable HTML report of project results.",
    "destroy": "Remove output files of the project.",
    "check": "Check flag status of current runs.",
    "clean": "Run clean scripts of already processed jobs.",
    "inspect": "Print information about a project.",
    "init": "Initialize looper config file.",
    "init-piface": "Initialize generic pipeline interface.",
    "link": "Create directory of symlinks for reported results.",
}
