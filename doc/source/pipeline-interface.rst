How to link your project to a pipeline
=============================================

One of the advantages of looper is that it decouples projects and pipelines, so you can have many projects that all use the same pipeline, or many pipelines running on the same project. This modular connection between pipelines and projects happens through a file called the `pipeline interface`. 

**If you're using one or more existing looper-compatible pipelines**, all you have to do is point your project config file at the `pipeline interface` files for any pipelines your project needs. For most casual users of pipelines, that's all you'll need to do;  you'll never need to create a new `pipeline interface` file. See the first section below, `Linking a looper-compatible pipeline`. Y 

But **if you need to make a new pipeline looper-compatible**, you do this by creating a `pipeline interface` file for the pipeline. This lets the pipeline author tell looper how to run the pipeline. See the second section below, `Linking a custom pipeline`.


Linking projects to looper-compatible pipelines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many projects will require only existing pipelines that are already looper-compatible. We maintain a (growing) list of public `looper-compatible pipelines <https://github.com/pepkit/hello_looper/blob/master/looper_pipelines.md>`_ that will get you started. This list includes pipelines for data types like RNA-seq, bisulfite sequencing, etc.

To use one of these pipelines, just clone the pipeline repository add the path to the pipeline's `pipeline_interface.yaml` file to the `pipeline_interfaces` attribute in the `metadata` section of your `project_config` file:

.. code-block:: yaml

  metadata:
    pipeline_interfaces: /path/to/pipeline_interface.yaml

This value should be the absolute path to the `pipeline interface` file (wherever you cloned the pipeline repository). After that, you just need to make sure your project definition provides all the necessary sample metadata required by the pipeline. For example, you will need to make sure your sample annotation sheet specifies the correct value under `protocol` that your linked pipeline understands. These details are specific to each pipeline and should be defined in the pipeline's README.

You can also **link more than one pipeline** to your project by simply adding other `pipeline interface` files to a list in the `metadata.pipeline_interfaces` field, like this:

.. code-block:: yaml

  metadata:
    pipeline_interfaces: [/path/to/pipeline_interface1.yaml, /path/to/pipeline_interface2.yaml]

For more details, see :ref:`connecting-multiple-pipelines`.

Linking a custom pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. HINT:: 

	If you're just a pipeline **user**, you don't need to worry about this section. This is for those who want to configure a new pipeline or an existing pipeline that isn't already looper-compatible.

Looper can connect samples to any pipeline, as long as it runs on the command line and uses text command-line arguments. These pipelines could be simple shell scripts, python scripts, perl scripts, or even pipelines built using a framework. Typically, we use python pipelines built using the `pypiper <http://pypiper.readthedocs.io>`_ package, which provides some additional power to looper, but this is optional.

Regardless of what pipelines you use, you will need to tell looper how to interface with your pipeline. You do that by specifying a **pipeline interface file**. The **pipeline interface** is a ``yaml`` file with two subsections:

1. ``protocol_mapping`` - maps sample ``protocol`` (aka ``library``) to one or more pipeline scripts.
2. ``pipelines`` -  describes the arguments and resources required by each pipeline script.

Let's start with a very simple example. A basic ``pipeline_interface.yaml`` file may look like this:


.. code-block:: yaml
    
    protocol_mapping:
      RRBS: rrbs_pipeline

    pipelines:
      rrbs_pipeline:
        name: RRBS
        path: path/to/rrbs.py
        arguments:
          "--sample-name": sample_name
          "--input": data_path


The first section specifies that samples of protocol ``RRBS`` will be mapped to the pipeline specified by key ``rrbs_pipeline``. The second section describes where the pipeline with key ``rrbs_pipeline`` is located and what command-line arguments it requires. Pretty simple. Let's go through these 2 sections in more detail:

.. include:: pipeline-interface-mapping.rst.inc

.. include:: pipeline-interface-pipelines.rst.inc

