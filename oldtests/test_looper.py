"""Initial, broad-scope looper oldtests.

Along with oldtests/oldtests.py, this is one of the initial unit test modules.
The primary function under test here is the creation of a project instance.

"""

import itertools
import logging
import random
from collections import defaultdict

import numpy.random as nprand
import pytest

from looper import build_parser
from looper.looper import aggregate_exec_skip_reasons
from oldtests.conftest import LOOPER_ARGS_BY_PIPELINE
from oldtests.helpers import named_param

_LOGGER = logging.getLogger("looper.{}".format(__name__))


@pytest.mark.usefixtures("write_project_files", "pipe_iface_config_file")
class SampleWrtProjectCtorTests:
    """Tests for `Sample` related to `Project` construction"""

    @named_param(
        argnames=["pipeline", "expected"],
        argvalues=list(LOOPER_ARGS_BY_PIPELINE.items()),
    )
    def test_looper_args_usage(self, pipe_iface, pipeline, expected):
        """Test looper args usage flag."""
        observed = pipe_iface.uses_looper_args(pipeline)
        assert (expected and observed) or not (observed or expected)


class RunErrorReportTests:
    """Tests for aggregation of submission failures."""

    SKIP_REASONS = [
        "Missing attribute.",
        "No metadata.",
        "No config file.",
        "Missing input(s).",
    ]
    SAMPLE_NAMES = {
        "Kupffer-control",
        "Kupffer-hepatitis",
        "microglia-control",
        "microglia-cancer",
        "Teff",
        "Treg",
        "Tmem",
        "MC-circ",
        "Mac-tissue-res",
    }

    @named_param(argnames="empty_skips", argvalues=[tuple(), set(), list(), dict()])
    def test_no_failures(self, empty_skips):
        """Aggregation step returns empty collection for no-fail case."""
        assert defaultdict(list) == aggregate_exec_skip_reasons(empty_skips)

    def test_many_samples_once_each_few_failures(self):
        """One/few reasons for several/many samples, one skip each."""

        # Looping is to boost confidence from randomization.
        # We don't really want each case to be a parameterization.
        for reasons in itertools.combinations(self.SKIP_REASONS, 2):
            original_reasons = []
            expected = defaultdict(list)

            # Choose one or both reasons as single-fail for this sample.
            for sample in self.SAMPLE_NAMES:
                this_sample_reasons = nprand.choice(
                    reasons, size=nprand.choice([1, 2]), replace=False
                )
                for reason in this_sample_reasons:
                    expected[reason].append(sample)
                original_reasons.append((this_sample_reasons, sample))

            observed = aggregate_exec_skip_reasons(original_reasons)
            assert expected == observed

    def test_same_skip_same_sample(self):
        """Multiple submission skips for one sample collapse by reason."""

        # Designate all-but-one of the failure reasons as the observations.
        for failures in itertools.combinations(
            self.SKIP_REASONS, len(self.SKIP_REASONS) - 1
        ):

            # Build up the expectations and the input.
            all_skip_reasons = []

            # Randomize skip/fail count for each reason.
            for skip in failures:
                n_skip = nprand.randint(low=2, high=5, size=1)[0]
                all_skip_reasons.extend([skip] * n_skip)

            # Aggregation is order-agnostic...
            random.shuffle(all_skip_reasons)
            original_skip_reasons = [(all_skip_reasons, "control-sample")]
            # ...and maps each reason to pair of sample and count.
            expected_aggregation = {
                skip: ["control-sample"] for skip in set(all_skip_reasons)
            }

            # Validate.
            observed_aggregation = aggregate_exec_skip_reasons(original_skip_reasons)
            assert expected_aggregation == observed_aggregation


class CliParserTests:
    """Tests for reading opts/args with the CLI parser"""

    @pytest.fixture
    def parser(self):
        """Provide a test case with a CLI parser."""
        return build_parser()

    @pytest.mark.parametrize("cmd", ["check", "clean", "destroy", "run", "summarize"])
    @pytest.mark.parametrize(
        "optarg",
        [
            ("dbg", None),
            ("env", "arb.yaml"),
            ("logfile", "tmp.log"),
            ("logging-level", "DEBUG"),
            ("verbosity", 1),
        ],
    )
    def test_subcommand_independent_options(self, cmd, optarg, parser, tmpdir):
        """Parse of subcommand-independent option succeeds."""
        opt, arg = optarg
        if opt in ["env", "logfile"]:
            arg = str(tmpdir.join(arg))
        cfg = str(tmpdir.join("dummy_config.yaml"))
        cmdl = "looper {} {} {}".format(self._render_optarg(opt, arg), cmd, cfg)
        opts = parser.parse_args(cmdl.split(" ")[1:])
        obs = vars(opts).get(opt.replace("-", "_"))
        exp = arg or True
        assert exp == obs

    @staticmethod
    def _render_optarg(opt, arg):
        """Helper for formatting flag vs. arg-accepting CLI option"""
        opt_text = "--" + opt
        return opt_text if arg is None else "{} {}".format(opt_text, arg)


def test_no_args(capfd):
    """Test CLI behavior when no opts/args are provided."""
    import subprocess
    import sys

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_output("looper")
    out, err = capfd.readouterr()
    print("OUT (below):\n{}".format(out))
    print("ERR (below):\n{}".format(err))
    lines = err.split("\n")
    if sys.version_info.major < 3:
        assert lines[0].startswith("usage: looper")
        assert [l for l in lines if l.strip()][-1].startswith(
            "looper: error: too few arguments"
        )
    else:
        assert lines[0].startswith("version")
        assert lines[1].startswith("usage")
