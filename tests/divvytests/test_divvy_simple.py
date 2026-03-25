
import pytest
from yacman import YAMLConfigManager

import looper.divvy as divvy
from looper.divvy import select_divvy_config

# For interactive debugging:
# import logmuse
# logmuse.init_logger("divvy", "DEBUG")


@pytest.fixture(autouse=True)
def _unset_divcfg(monkeypatch):
    """Ensure tests use the built-in default config, not a user's DIVCFG."""
    monkeypatch.delenv("DIVCFG", raising=False)


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
        dcc.activate_package("apptainer_slurm")
        extra_vars = {
            "apptainer_image": "simg",
            "jobname": "jbname",
            "code": "mycode",
        }
        outfile = str(tmp_path / "test.sub")
        dcc.write_script(outfile, extra_vars)
        with open(outfile, "r") as f:
            contents = f.read()
        assert contents.find("mycode") > 0
        assert contents.find("{APPTAINER_ARGS}") < 0


class TestAdapters:
    @pytest.mark.parametrize(
        "compute",
        [
            {"mem": 1000, "test": 0},
            YAMLConfigManager({"mem": 1000, "test": 0}),
        ],
    )
    @pytest.mark.parametrize("package", ["apptainer_slurm", "slurm"])
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
        dcc.activate_package("apptainer_slurm")
        compute = YAMLConfigManager({"mem": 1000})
        extra_vars = [{"compute": compute}, {"MEM": 333}]
        outfile = str(tmp_path / "test1.sub")
        dcc.write_script(outfile, extra_vars)
        with open(outfile, "r") as f:
            contents = f.read()
            assert not (contents.find("1000") > 0)
            assert contents.find("333") > 0


class TestPrePostCommand:
    def test_pre_post_command_appear_in_script(self, tmp_path):
        """Test PRE_COMMAND/POST_COMMAND appear in rendered script"""
        dcc_filepath = select_divvy_config(None)
        dcc = divvy.ComputingConfiguration.from_yaml_file(filepath=dcc_filepath)
        dcc.activate_package("default")
        extra_vars = {
            "code": "echo hello",
            "pre_command": "module load python",
            "post_command": "echo done",
        }
        outfile = str(tmp_path / "test.sub")
        dcc.write_script(outfile, extra_vars)
        with open(outfile, "r") as f:
            contents = f.read()
        assert "module load python" in contents
        assert "echo done" in contents

    def test_pre_post_command_default_to_empty(self, tmp_path):
        """Test PRE_COMMAND/POST_COMMAND default to empty (no unreplaced placeholders)"""
        dcc_filepath = select_divvy_config(None)
        dcc = divvy.ComputingConfiguration.from_yaml_file(filepath=dcc_filepath)
        dcc.activate_package("default")
        extra_vars = {"code": "echo hello"}
        outfile = str(tmp_path / "test.sub")
        dcc.write_script(outfile, extra_vars)
        with open(outfile, "r") as f:
            contents = f.read()
        assert "{PRE_COMMAND}" not in contents
        assert "{POST_COMMAND}" not in contents


class TestBulkerSlurm:
    def test_bulker_slurm_package(self, tmp_path):
        """Test bulker_slurm package has sbatch and bulker activate"""
        dcc_filepath = select_divvy_config(None)
        dcc = divvy.ComputingConfiguration.from_yaml_file(filepath=dcc_filepath)
        dcc.activate_package("bulker_slurm")
        assert dcc.compute["submission_command"] == "sbatch"
        extra_vars = {
            "code": "echo hello",
            "bulker_crate": "mycrate",
        }
        outfile = str(tmp_path / "test.sub")
        dcc.write_script(outfile, extra_vars)
        with open(outfile, "r") as f:
            contents = f.read()
        assert "SBATCH" in contents
        assert "bulker activate" in contents


class TestApptainer:
    def test_apptainer_package(self, tmp_path):
        """Test apptainer package uses apptainer commands, not singularity"""
        dcc_filepath = select_divvy_config(None)
        dcc = divvy.ComputingConfiguration.from_yaml_file(filepath=dcc_filepath)
        dcc.activate_package("apptainer")
        extra_vars = {
            "code": "echo hello",
            "apptainer_image": "myimage.sif",
            "jobname": "testjob",
        }
        outfile = str(tmp_path / "test.sub")
        dcc.write_script(outfile, extra_vars)
        with open(outfile, "r") as f:
            contents = f.read()
        assert "apptainer" in contents
        assert "singularity" not in contents

    def test_apptainer_slurm_package(self, tmp_path):
        """Test apptainer_slurm has SLURM headers and apptainer commands"""
        dcc_filepath = select_divvy_config(None)
        dcc = divvy.ComputingConfiguration.from_yaml_file(filepath=dcc_filepath)
        dcc.activate_package("apptainer_slurm")
        assert dcc.compute["submission_command"] == "sbatch"
        extra_vars = {
            "code": "echo hello",
            "apptainer_image": "myimage.sif",
            "jobname": "testjob",
        }
        outfile = str(tmp_path / "test.sub")
        dcc.write_script(outfile, extra_vars)
        with open(outfile, "r") as f:
            contents = f.read()
        assert "SBATCH" in contents
        assert "apptainer" in contents
        assert "singularity" not in contents
