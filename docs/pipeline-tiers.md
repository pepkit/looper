# The concept of two-tiered pipelines

In our experience, we are typically interested in running two different types of commands: Those that operate on each sample independently, and those that operate on all samples simultaneously. Since sample-independent pipelines can be easily parallelized by sample, we distinguish these.

Looper divides pipelines into two types: *sample* pipelines and *project* pipelines.

This philosophy is conceptually similar to the [MapReduce](https://en.wikipedia.org/wiki/MapReduce) programming model, which applies a *split-apply-combine* strategy. In the case of running pipelines on sample-intensive research projects, we *split* the project into samples and *apply* the first tier of processing (the *sample* pipeline). We then *combine* the results in the second tier of processing (the *project* pipeline).

Looper doesn't require you to use this two-stage system, but it simply makes it easy to do so. Many pipelines operate only at the sample level and leave the downstream cross-sample analysis to the user.

## Sample pipelines

The typical use case is sample-level pipelines. These are run with `looper run`. The sample pipelines are described in the `sample_pipeline` section of a pipeline interface.

## Project pipelines

Optionally, a pipeline interface can add a `project_pipeline` section. A pipeline specified here will be run with `looper runp` (where the *p* stands for *project*). Running a project pipeline operates in almost exactly the same way as the sample pipeline, with 2 key exceptions: First, instead of creating a separate command for every sample, the `looper runp` will only create a single command for the project. And second, the command template itself will not have access to a `sample` namespace representing a particular sample, since it's not running on a particular sample; instead, it will have access to a `samples` (plural) namespace, which contains all the attributes from all the samples.

In a typical workflow, a user will first run the samples individually using `looper run`, and then, if the pipeline provides one, will run the project component using `looper runp` to summarize or aggregate the results into a project-level output.
