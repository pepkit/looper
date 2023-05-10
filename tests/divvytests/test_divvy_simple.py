import looper.divvy as divvy
import os
import pytest
from collections import OrderedDict

from yacman import YacAttMap

# For interactive debugging:
# import logmuse
# logmuse.init_logger("divvy", "DEBUG")


class TestPackageaAtivation:
    def test_activate_package(self):
        dcc = divvy.ComputingConfiguration()
        dcc.activate_package("default")
        t = dcc.compute.submission_template
        t2 = dcc["compute"]["submission_template"]
        assert t == t2
        dcc.activate_package("slurm")
        t = dcc.compute.submission_template
        t2 = dcc["compute"]["submission_template"]
        assert t == t2


class TestWriting:
    def test_write_script(self):
        dcc = divvy.ComputingConfiguration()
        dcc
        dcc.activate_package("singularity_slurm")
        extra_vars = {
            "singularity_image": "simg",
            "jobname": "jbname",
            "code": "mycode",
        }
        dcc.write_script("test.sub", extra_vars)
        with open("test.sub", "r") as f:
            contents = f.read()
        assert contents.find("mycode") > 0
        assert contents.find("{SINGULARITY_ARGS}") < 0
        os.remove("test.sub")


# class TestAdapters:
#     @pytest.mark.parametrize(
#         "compute",
#         [
#             dict({"mem": 1000, "test": 0}),
#             YacAttMap({"mem": 1000, "test": 0}),
#             OrderedDict({"mem": 1000, "test": 0}),
#         ],
#     )
#     @pytest.mark.parametrize("package", ["singularity_slurm", "slurm"])
#     def test_write_script_adapters(self, compute, package):
#         """Test successful adapter sourcing from various Mapping types"""
#         dcc = divvy.ComputingConfiguration()
#         dcc.activate_package(package)
#         extra_vars = {"compute": compute}
#         dcc.write_script("test.sub", extra_vars)
#         with open("test.sub", "r") as f:
#             contents = f.read()
#             assert contents.find("1000") > 0
#         os.remove("test.sub")
#
#     def test_adapters_overwitten_by_others(self):
#         dcc = divvy.ComputingConfiguration()
#         dcc.activate_package("singularity_slurm")
#         compute = YacAttMap({"mem": 1000})
#         extra_vars = [{"compute": compute}, {"MEM": 333}]
#         dcc.write_script("test1.sub", extra_vars)
#         with open("test1.sub", "r") as f:
#             contents = f.read()
#             assert not (contents.find("1000") > 0)
#             assert contents.find("333") > 0
#         os.remove("test1.sub")
#

# def test_update():
# 	# probably will be removed later
# 	dcc1 = divvy.ComputingConfiguration()
# 	dcc1.update_packages("code/divvy/tests/data/pepenv-master/cemm.yaml")
# 	dcc2 = divvy.ComputingConfiguration()
# 	y = yacman.load_yaml("code/divvy/tests/data/pepenv-master/cemm.yaml")
# 	dcc2.update(y)
# 	dcc1 == dcc2

# class ptest(object):
# 	@property
# 	def doubleslash(self):
# 		return '//'

# p = ptest()
# p.doubleslash
