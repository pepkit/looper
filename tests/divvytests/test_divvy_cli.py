"""Tests for the divvy CLI entry point (divvy_main)."""

import os


class TestDivvyMainImport:
    def test_divvy_main_is_importable(self):
        from looper.__main__ import divvy_main

        assert callable(divvy_main)


class TestDivvyList:
    def test_list_exits_zero(self):
        from looper.__main__ import divvy_main

        ret = divvy_main(["list"])
        assert ret == 0

    def test_list_output_contains_packages(self, capsys):
        from looper.__main__ import divvy_main

        divvy_main(["list"])
        captured = capsys.readouterr()
        assert "default" in captured.out
        assert "slurm" in captured.out


class TestDivvyInit:
    def test_init_creates_config(self, tmp_path):
        from looper.__main__ import divvy_main

        config_path = str(tmp_path / "new_config" / "divvy_config.yaml")
        ret = divvy_main(["init", "--config", config_path])
        assert ret == 0
        assert os.path.exists(config_path)


class TestDivvyInspect:
    def test_inspect_default_package(self, capsys):
        from looper.__main__ import divvy_main

        ret = divvy_main(["inspect"])
        assert ret == 0
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_inspect_slurm_package(self, capsys):
        from looper.__main__ import divvy_main

        ret = divvy_main(["inspect", "--package", "slurm"])
        assert ret == 0
        captured = capsys.readouterr()
        assert "SBATCH" in captured.out


class TestDivvyWrite:
    def test_write_creates_script(self, tmp_path):
        from looper.__main__ import divvy_main

        outfile = str(tmp_path / "test_submit.sh")
        ret = divvy_main(
            [
                "write",
                "--package",
                "slurm",
                "--compute",
                "code=echo hello",
                "jobname=test",
                "--outfile",
                outfile,
            ]
        )
        assert ret == 0
        assert os.path.exists(outfile)
        with open(outfile) as f:
            contents = f.read()
        assert "echo hello" in contents

    def test_write_no_outfile_prints_to_stdout(self, capsys):
        from looper.__main__ import divvy_main

        ret = divvy_main(
            [
                "write",
                "--package",
                "slurm",
                "--compute",
                "code=echo hello",
                "jobname=test",
            ]
        )
        assert ret == 0
        captured = capsys.readouterr()
        assert "echo hello" in captured.out
        assert "SBATCH" in captured.out
