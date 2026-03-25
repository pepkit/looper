import pytest
from yacman import YAMLConfigManager

import looper.divvy as divvy
from looper.divvy import select_divvy_config

# For interactive debugging:
# import logmuse
# logmuse.init_logger("divvy", "DEBUG")


class TestPackageAtivation:
    def test_activate_package(self):
        dcc_filepath = select_divvy_config(None)
        dcc = divvy.ComputingConfiguration().from_yaml_file(filepath=dcc_filepath)
        dcc.activate_package("default")
        t = dcc.compute["submission_template"]
        t2 = dcc["compute_packages"]["default"]["submission_template"]
        # assert t == t2
        dcc.activate_package("slurm")
        t = dcc.compute["submission_template"]
        t2 = dcc["compute_packages"]["slurm"]["submission_template"]
        # assert t == t2


class TestWriting:
    def test_write_script(self, tmp_path):
        dcc_filepath = select_divvy_config(None)
        dcc = divvy.ComputingConfiguration.from_yaml_file(filepath=dcc_filepath)
        dcc.activate_package("singularity_slurm")
        extra_vars = {
            "singularity_image": "simg",
            "jobname": "jbname",
            "code": "mycode",
        }
        outfile = str(tmp_path / "test.sub")
        dcc.write_script(outfile, extra_vars)
        with open(outfile, "r") as f:
            contents = f.read()
        assert contents.find("mycode") > 0
        assert contents.find("{SINGULARITY_ARGS}") < 0


class TestAdapters:
    @pytest.mark.parametrize(
        "compute",
        [
            {"mem": 1000, "test": 0},
            YAMLConfigManager({"mem": 1000, "test": 0}),
        ],
    )
    @pytest.mark.parametrize("package", ["singularity_slurm", "slurm"])
    def test_write_script_adapters(self, compute, package, tmp_path):
        """Test successful adapter sourcing from various Mapping types"""
        dcc_filepath = select_divvy_config(None)
        dcc = divvy.ComputingConfiguration.from_yaml_file(filepath=dcc_filepath)
        dcc.activate_package(package)
        extra_vars = {"compute": compute}
        outfile = str(tmp_path / "test.sub")
        dcc.write_script(outfile, extra_vars)
        with open(outfile, "r") as f:
            contents = f.read()
            assert contents.find("1000") > 0

    def test_adapters_overwritten_by_others(self, tmp_path):
        dcc_filepath = select_divvy_config(None)
        dcc = divvy.ComputingConfiguration.from_yaml_file(filepath=dcc_filepath)
        dcc.activate_package("singularity_slurm")
        compute = YAMLConfigManager({"mem": 1000})
        extra_vars = [{"compute": compute}, {"MEM": 333}]
        outfile = str(tmp_path / "test1.sub")
        dcc.write_script(outfile, extra_vars)
        with open(outfile, "r") as f:
            contents = f.read()
            assert not (contents.find("1000") > 0)
            assert contents.find("333") > 0
