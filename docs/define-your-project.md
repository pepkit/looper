# How to define a project

Most pipelines require a unique way to organize samples, but `looper` subscribes to [standard Portable Encapsulated Project (PEP) format](http://pepkit.github.io). PEP is a standardized way to represent metadata about your project and each of its samples. If you follow this format, then your project can be read not only by `looper`, but also by other software, like the [pepr R package](http://github.com/pepkit/pepr), or the [peppy python package](http://github.com/pepkit/peppy). 

Once you've specified a PEP, it's time to link it to the looper pipelines you want to use with the project. This is described in the next section on how to link a project to a pipeline).
