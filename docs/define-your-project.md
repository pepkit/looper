# How to define a project

Most pipelines require a unique way to organize samples, but `looper` subscribes to [standard Portable Encapsulated Project (PEP) format](http://pepkit.github.io). PEP is a standardized way to represent metadata about your project and each of its samples. If you follow this format, then your project can be read not only by `looper`, but also by other software, like the [pepr R package](http://github.com/pepkit/pepr), or the [peppy python package](http://github.com/pepkit/peppy). You should read the instructions on [how to create a PEP](https://pepkit.github.io/docs/simple_example/) to use with `looper`.

Once you've have a basic PEP created, the next section shows you [how to add looper-specific configuration to the PEP config file](project-config-looper.md), or you can jump ahead to [linking a project to a pipeline](link-a-pipeline.md).
