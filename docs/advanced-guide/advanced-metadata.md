# Advanced metadata features

We already covered how you can specify sample metadata using either a [simple csv file](../user-tutorial/initialize.md) or a [PEP](../user-tutorial/metadata.md).
But in that tutorial we covered only the basic features of PEPs.
PEPs are actually a lot more powerful, and many of those features are useful for looper projects.
Here, we'll show you a few of the more advanced features of PEPs and explain how they can be useful with looper. 
We still won't cover everything here, though.
If you want to see *all* the features of PEP, you should consult the [detailed PEP documentation](/spec/simple-example/).


!!! success "Learning objectives"
    - What else can PEPs do that can make my life easier?


!!! note
    These concepts aren't strictly about `looper`, they are about PEP. They just show you some examples of how your `looper` project could take advantage of PEP features.


## Implied attributes

At some point, you may have a situation where you need a single sample attribute (or column)
to populate several different pipeline arguments with different values.
In other words, the value of a given attribute may *imply* values for other attributes.
It would be nice if you didn't have to enumerate all of these secondary, implied attributes,
and could instead just infer them from the value of the original attribute?

For example, if my `organism` attribute is `human`, this implies a few other secondary attributes
(which may be project-specific): For one project, I want to set `genome` to `hg38` and `macs_genome_size` to `hs`.
Of course, I could just define columns called `genome` and `macs_genome_size`, but these would be constant across samples, so it feels inefficient and unwieldy.
Plus, changing the aligned genome would require changing the sample annotation sheet (every sample, in fact).
You can certainly do this with `looper`, but a better way is to handle these things at the project level.

As a more elegant alternative, PEP provides the `imply` sample modifier.
Instead of hard-coding `genome` and `macs_genome_size` in the sample annotation sheet,
you can simply specify that the attribute `organism` *implies* additional attribute-value pairs, which vary by sample based on the value of the `organism` attribute.
This lets you specify assemblies, genome size, and other similar variables all in your project config file.

To do this, just add an `imply` sample modifier. Example:

```yaml
sample_modifiers:
  imply:
    - if:
        organism: "human"
      then:
        genome: "hg38"
        macs_genome_size: "hs"
    - if:
        organism: "mouse"
      then:
        genome: "mm10"
        macs_genome_size: "mm"
```

In this example, any samples with organism set to `"human"` will automatically also have attributes for `genome` (`"hg38"`) and for `macs_genome_size` (`"hs"`).
Any samples with `organism` set to `"mouse"` will have the corresponding values.
A sample with `organism` set to `"frog"` would lack attributes for `genome` and `macs_genome_size`, since those columns are not implied by `"frog"`.

This system essentially lets you set global, species-level attributes at the project level instead of duplicating that information for every sample that belongs to a species.
Even better, it's generic, so you can do this for any partition of samples (just replace `organism` with whatever you like). 
This makes your project more portable and does a better job conceptually with separating sample attributes from project attributes.
After all, a reference assembly is not a property of a sample, but is part of the broader project context.


## The 'amend' project modifier for subprojects

PEP provides not only sample modifiers, but project modifiers.
You can use this to encode slightly different versions of a project, without duplicating the settings.
For example, say we have a project that we align to a particular reference genome, say "hg38".
We want to try running that on a different reference genome, say "hg19".
Rather than duplicate the whole project or sample table and change everything, we can actually do this using the `amend` project modifier.
Consider this PEP:

```yaml
sample_modifiers:
  append:
    genome: "hg38"

project_modifiers:
  amend:
    hg19_alignment:
      sample_modifiers:
        append:
          genome: "hg19"
```

This is using the `append` modifier to set the `genome` attribute to `hg38` for all samples.
We can then use `{sample.genome}` in the pipeline interface to pass `hg38` as a pipeline parameter.
But we also have an `amend` section, which defines an amendment called `hg19_alignment`.
If we activate this project with `--amend hg19_alignment`, then everything under that amendment will be attached to the PEP.
In this example, it will add a new append modifier, which sets the `genome` attribute to `hg19`.
Thus, reparameterizing this pipeline is as simple as choosing the amendment with the command line, `--amend hg19_alignment`.


## How to handle multiple input files

Sometimes a sample has multiple input files that belong to the same attribute. For example, a common use case is a single library that was spread across multiple sequencing lanes, yielding multiple input files that need to be merged, and then run through the pipeline as one. Dealing with multiple input files is described in detail in the [PEP documentation](https://pep.databio.org/spec/howto-multi-value-attributes/), but covered briefly here. PEP has two ways to merge these:

1. Use shell expansion characters (like `*` or `[]`) in your file path definitions (good for simple merges)
2. Specify a *sample subannotation tables* which maps input files to samples for samples with more than one input file (infinitely customizable for more complicated merges).

To accommodate complex merger use cases, this is infinitely customizable.

!!! warning
    Do not use *both* of these options for the same sample at the same time; that will lead to multiple mergers.

### Using wild cards in derived sources
To do the first option, simply change the data source specification to use wild card characters:

```yaml title="pep_config.yaml" hl_lines="4-6"
pep_version: 2.1.0
sample_table: sample_table.csv
sample_modifiers:
  append:
    file_path: source1
  derive:
    attributes: [file_path]
    sources:
      source1: "data/{sample_name}_*.txt"
```

### Using a subsample table
For the second option, provide a subsample table in your pep config file:

```yaml title="pep_config.yaml" hl_lines="3"
pep_version: 2.1.0
sample_table: sample_table.csv
subsample_table: subsample_table.csv
```

```csv title="Example subsample_table.csv"
sample_name,file_path
canada,data/canada_1.txt
canada,data/canada_2.txt
switzerland,data/switzerland_1.txt
switzerland,data/switzerland_2.txt
mexico,data/mexico_1.txt
mexico,data/mexico_2.txt
```

Make sure the `sample_name` column of this table matches, and then include any columns needed to point to the data.
Looper will automatically include all of these files as input passed to the pipelines.


!!! Important Note
    Mergers are *not* the way to handle different functional/conceptual *kinds* of input files (e.g., `read1` and `read2` for a sample sequenced with a paired-end protocol).
    Such cases should be handled as *separate derived columns* in the main sample annotation sheet if they're different arguments to the pipeline.


### Multi-value sample attributes behavior in the pipeline interface command templates

Both subsample tables and shell expansion characters lead to sample attributes with multiple values, stored in a list of strings as opposed to a standard scenario, where a single value is stored as a string (`single_attr`).

For example:
```
Sample
sample_name: canada
file_path: ['data/canada_1.txt', 'data/canada_2.txt']
single_attr: random_test_val
```

#### Access individual elements in lists

Pipeline interface author can leverage that fact and access the individual elements, e.g iterate over them and append to a string using the Jinja2 syntax:

```bash
pipeline_name: test_iter
pipeline_type: sample
command_template: >
  --input-iter {%- for x in sample.file_path -%} --test-individual {x} {% endfor %} # iterate over multiple values
  --input-single {sample.single_attr} # use the single value as is

```

This results in a submission script that includes the following command:
```bash
--input-iter  --test-individual data/canada_1.txt  --test-individual data/canada_2.txt
--input-single  random_test_val
```

#### Concatenate elements in lists

The most common use case is just concatenating the multiple values and separate them with space -- **providing multiple input values to a single argument on the command line**. Therefore, all the multi-value sample attributes that have not been processed with Jinja2 logic are automatically concatenated. For instance, the following command template in a pipeline interface will result in the submission script presented below:

Pipeline interface:
```bash
pipeline_name: test_concat
pipeline_type: sample
command_template: >
  --input-concat {sample.file_path} # concatenate all the values
```

Command in the submission script:
```bash
--input-concat  data/canada_1.txt data/canada_2.txt
```

## Others

Some other things you might find interesting:

- *imports* allow PEPs to [import other PEPs](https://pep.databio.org/spec/specification/#project-modifier-import), so you can re-use information across projects.


!!! tip "Summary"
    - You can use the `imply` sample modifier to eliminate redundant columns in your sample table.
    - You can use multiple input files for your pipeline using wildcards or subsample tables.
    - PEP provides many powerful features that work well with looper.

