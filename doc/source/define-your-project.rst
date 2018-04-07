.. _project-config-file:

How to define a project
=============================================

To use ``looper`` with your project, you must define your project using Portable Encapsulated Project (PEP) structure. PEP is a standardized way to represent metadata about your project and each of its samples. If you follow this format, then your project can be read not only by ``looper``, but also by other software, like the `pepr R package <http://github.com/pepkit/pepr>`_, or the `peppy python package <http://github.com/pepkit/peppy>`_. This will let you use the same metadata description  for downstream data analysis.

The PEP format is simple and modular. You should read the complete documentation at `the PEP website <https://pepkit.github.io/docs/home/>`_. You need to supply 2 files:

1. **Project config file** - a ``yaml`` file describing file paths and project settings
2. **Sample annotation sheet** - a ``csv`` file with 1 row per sample

With those two simple files, you can run looper. You can find more advanced details of both annotation sheets and project config files at `the PEP website <https://pepkit.github.io/docs/home/>`_. 

Once you've specified your project in PEP format, it's time to link it to the looper pipelines you want to use with the project. You'll do this by adding one more line to your project config file, the **pipeline_interfaces**, which points to your looper-compatible pipelines. This is described in the next section, :doc:`linking the pipeline interface <pipeline-interface>`).
