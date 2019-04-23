# Grouping many jobs into one

By default, `looper` will translate each row in your `sample_table` into a single job. But perhaps you are running a project with tens of thousands of rows, and each job only takes mere minutes to run; in this case, you'd rather just submit a single job to process many samples. `Looper` makes this easy with the `--lump` and `--lumpn` command line arguments.

## Lumping jobs by job count: `--lumpn`

It's quite simple: if you want to run 100 samples in a single job submission script, just tell looper `--lumpn 100`.

## Lumping jobs by input file size: `--lump`

But what if your samples are quite different in terms of input file size? For example, your project may include many small samples, which you'd like to lump together with 10 jobs to 1, but you also have a few control samples that are very large and should have their own dedicated job. If you just use `--lumpn` with 10 samples per job, you could end up lumping your control samples together, which would be terrible. To alleviate this problem, `looper` provides the `--lump` argument, which uses input file size to group samples together. By default, you specify an argument in number of gigabytes. Looper will go through your samples and accumulate them until the total input file size reaches your limit, at which point it finalizes and submits the job. This will keep larger files in independent runs and smaller files grouped together.

