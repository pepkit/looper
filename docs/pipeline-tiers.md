# The concept of two-tiered pipelines

In our experience, we are typically interested in running two different types of commands: 1) those that operate on each sample independently; and 2) those that operate on all samples simultaneously. We distinguish these because first type can be easily parallelized by sample, but the second cannot. Looper thus divides pipelines into two types: *sample* pipelines and *project* pipelines.

This philosophy is conceptually similar to the [MapReduce](https://en.wikipedia.org/wiki/MapReduce) programming model, which applies a *split-apply-combine* strategy. In the case of running pipelines on sample-intensive research projects, we *split* the project into samples and *apply* the first tier of processing (the *sample* pipeline). We then *combine* the results in the second tier of processing (the *project* pipeline).

Looper doesn't require you to use this two-stage system, but it makes it easy to do. Many pipelines operate only at the sample level and leave the downstream cross-sample analysis to the user.

## Sample pipelines

A basic pipeline that runs on each sample independently is a sample-level pipeline. These are run with `looper run`. The pipeline interface that defines a sample pipeline must include `pipeline_type: "sample"`.

## Project pipelines

In contrast, project pipelines specify `pipeline_type: "project"` in the pipeline interface. These pipelines are run with `looper runp` (where the *p* stands for *project*). Running a project pipeline operates in almost exactly the same way as the sample pipeline, with 2 key differences: 

1) First, instead of creating a separate command for every sample, `looper runp` will only create *a single command for the project*. 
2) Second, the command template itself will not have access to a `sample` namespace representing a particular sample, since it's not running on a particular sample; instead, it will have access to a `samples` (plural) namespace, which contains all the attributes from all the samples.

## Typical use case

In a typical workflow, a user will first run the samples individually using `looper run`, and then, if the pipeline provides one, will run the project component using `looper runp` to summarize or aggregate the results into a project-level output.
