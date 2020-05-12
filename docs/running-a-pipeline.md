# How to run a pipeline

## Basic steps

You first have to [define your project](defining-a-project.md). This will give you a PEP linked to a pipeline. Next, we'll run the pipeline.

## Looper run

The basic command is `looper run`. To run your pipeline, just:

```bash
looper run project_config.yaml
```

This will submit a job for each sample. That's basically all there is to it; after this, there's a lot of powerful options and tweaks you can do to control your jobs. Here we'll just mention a few of them.

- **Dry runs**. You can use `-d, --dry-run` to create the job submission scripts, but not actually run them. This is really useful for testing that everything is set up correctly before you commit to submitting hundreds of jobs.
- **Limiting the number of jobs**. You can `--limit` to test a few before running all samples.
- **Grouping jobs**. You can use `--lump` or `--lumpn` to group jobs. [More details on grouping jobs](grouping-jobs.md).
- **Changing compute settings**. You can use `--package`, `--settings`, or `--compute` to change the compute templates. Read more in [running on a cluster](running-on-a-cluster.md).
- **Time delay**. You can stagger submissions to not overload a submission engine using `--time-delay`.
- **Use rerun to resubmit jobs**. To run only jobs that previously failed, try `looper rerun`.
- **Tweak the command on-the-fly**. The `--command-extra` arguments allow you to pass extra arguments to every command straight through from looper.
- **Adjust the pipeline on-the-fly**. You can override the existing pipeline interfaces with `--pipeline-interfaces`.