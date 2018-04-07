.. _project-config-file:

How to define a project
=============================================

``Looper`` subscribes to standard PEP format. So to use ``looper``, you first define your project using Portable Encapsulated Project (PEP) structure. PEP is a standardized way to represent metadata about your project and each of its samples. If you follow this format, then your project can be read not only by ``looper``, but also by other software, like the `pepr R package <http://github.com/pepkit/pepr>`_, or the `peppy python package <http://github.com/pepkit/peppy>`_. This will let you use the same metadata description for downstream data analysis.

The PEP format is simple and modular and uses 2 key files:

1. **Project config file** - a ``yaml`` file describing file paths and project settings
2. **Sample annotation sheet** - a ``csv`` file with 1 row per sample

You can find complete details of both files at `the official documentation for Portable Encapsulated Projects <https://pepkit.github.io/docs/home/>`_.

Once you've specified a PEP, it's time to link it to the looper pipelines you want to use with the project. You'll do this by adding one more line to your project config file to indicate the **pipeline_interfaces** you need. This is described in the next section on how to :doc:`link a project to a pipeline <linking-a-pipeline>`).
