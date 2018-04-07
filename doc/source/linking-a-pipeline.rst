How to link a project to a pipeline
=============================================

One of the advantages of looper is that it decouples projects and pipelines, so you can have many projects that all use the same pipeline, or many pipelines running on the same project. This modular connection between pipelines and projects happens through a file called the `pipeline interface`. 

**If you're using one or more existing looper-compatible pipelines**, all you have to do is point your project config file at the `pipeline interface` files for any pipelines your project needs. For most casual users of pipelines, that's all you'll need to do;  you'll never need to create a new `pipeline interface` file. 

But **if you need to make a new pipeline looper-compatible**, you do this by creating a `pipeline interface` file for the pipeline. This lets the pipeline author tell looper how to run the pipeline. This is explained in the next section, `Writing a pipeline interface`.

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