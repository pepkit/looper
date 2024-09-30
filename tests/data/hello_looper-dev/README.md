# Hello World! example for looper

This repository provides minimal working examples for the [looper pipeline submission engine](http://pep.databio.org/looper).

This repository contains examples

1. `/looper_csv_example` - A minimal example using _only_ csv for metadata.
2. `/pep_derived_attributes` - An basic example utilizing the PEP specification for metadata and deriving attributes from the metadata
3. `/pephub` - Example of how to point looper to a PEP stored on PEPhub and running a pipeline.
4. `/pipestat` - Example on how to use pipestat to report pipeline results when using looper.

Each example contains:

1. A looper config file (`.looper.yaml`).
2. Sample data plus metadata in PEP format (or pointer to PEPhub).
3. A looper-compatible pipeline.

Explanation and results of running the above examples can be found at [Looper: Hello World Tutorial](https://pep.databio.org/looper/tutorial/initialize/)
