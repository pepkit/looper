# Tutorial conclusion

## What you've accomplished

By completing this tutorial, you now know how to:

- **Set up a looper project** with a `.looper.yaml` config, pipeline interface, and sample table
- **Run pipelines** on your samples with `looper run`
- **Use PEP features** like derived attributes to simplify your sample metadata
- **Integrate pipestat** for structured result reporting and job monitoring
- **Run project-level pipelines** with `looper runp` for analyses that span all samples
- **Configure compute resources** with divvy to submit jobs to clusters

## Key points

!!! tip "Summary"
    - Looper separates your **data** (PEP), **pipeline** (interface), and **compute** (divvy) configurations
    - Sample-level pipelines run once per sample; project-level pipelines run once for the whole project
    - Pipestat provides standardized result reporting across different storage backends
    - Divvy templates let you run the same pipeline on any computing environment
    - All components are modular - use only what you need

## The PEPkit philosophy

One key takeaway from this tutorial is how modular everything is.
Each feature is optional - you don't have to use any of them if you don't want to.
You can also use all of them simultaneously if you need it.
You can even use each tool independently of looper in a completely different system.

That modularity is the core design philosophy of PEPkit.

## What's next?

- **[Advanced user guides](../advanced-guide/advanced-run-options.md)** - Details on run options, computing, and metadata management
- **[How-to recipes](../how-to/containers.md)** - Specific solutions for common use cases
- **[Developer tutorial](../developer-tutorial/writing-a-pipeline-interface.md)** - Create your own looper-compatible pipelines

Good luck!
