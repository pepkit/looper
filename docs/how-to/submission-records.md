# Track submitted jobs

For every job it really submits (not dry runs), looper writes
`<submission_dir>/<job_name>.submission.json` next to the `.sub` script.
A tool that drives looper can read these to find the jobs it submitted, for
example to poll the scheduler for them.

```json
{
  "job_name": "PIPELINE1_sample1",
  "job_id": "12345",
  "pid": null,
  "samples": ["sample1"],
  "pipeline": "PIPELINE1",
  "compute_package": "slurm",
  "submission_command": "sbatch",
  "script": "/path/to/submission/PIPELINE1_sample1.sub",
  "submitted_at": "2026-10-20T14:03:11.123456+00:00",
  "submit_stdout": "Submitted batch job 12345\n",
  "returncode": 0
}
```

- `job_id` comes from the submission command's output, matched with the
  compute package's `job_id_regex` (first capture group). Packages that
  submit with `sbatch`, `qsub` or `bsub` get a default; set `job_id_regex`
  yourself for other schedulers or for `sbatch --parsable`, or set it to
  `null` to leave the output alone.
- When no regex applies (for example local runs, where the "submission" is
  the pipeline itself), output is not captured, `job_id` is `null`, and `pid`
  holds the process id. The record is written when the process starts and
  again when it ends.
- Lumped jobs list every sample in `samples`; project-level (`runp`) jobs
  have an empty list. A failed submission still writes its record, with the
  non-zero `returncode`.
- Re-running overwrites the record for that job name.

## Recording the container environment

`looper run --record-environment` (or a `record_environment: true` compute
setting, for example `--compute record_environment=true`) adds an
`environment` block:

```json
"environment": {
  "crate": "databio/pepatac:1.1.3",
  "crate_digest": "zR9kiCcE6JTSkfJI7H9hfEsj9SdgklqL",
  "images": ["quay.io/biocontainers/samtools:1.23"],
  "image_digests": {"quay.io/biocontainers/samtools:1.23": "sha256:..."}
}
```

`crate` and `images` come from the `bulker_crate`, `docker_image` and
`apptainer_image` compute settings (plus the crate's images, from
`bulker crate digest --verbose`). Digests come from the local docker cache
(`docker image inspect`) or, for a local `.sif` file, its sha256. looper never
pulls images or contacts a registry; anything it cannot resolve is left out.
