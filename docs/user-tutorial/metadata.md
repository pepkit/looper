# Configuring your metadata

## Introduction

Previously, we used a `.csv` file to store metadata. This tutorial will guide you through how to use powerful features of PEP and PEPhub to make managing your metadata easier.


!!! success "Learning objectives"
    - How can I use PEPs as input instead of a `.csv`, and what benefit does this provide?
    - What is PEPhub, and how can it simplify my data analysis?



## Recap

In the first guide, we used a simple CSV file to specify our sample metadata in `metadata/sample_table.csv`, which looked like this:


```csv title="metadata/sample_table.csv"
sample_name,area_type,file_path
mexico,state,data/mexico.txt
switzerland,canton,data/switzerland.txt
canada,province,data/canada.txt
```

Then, we pointed to the CSV in the `.looper.yaml` config file:

``` yaml title=".looper.yaml" hl_lines="1"
pep_config: metadata/sample_table.csv  # pointer to metadata file
output_dir: results
pipeline_interfaces:
  - ['pipeline/pipeline_interface.yaml']
```

Now, we'll show you how to use more advanced features to make this better. 

## Using a PEP for derived attributes

Looper can read sample metadata as a PEP instead of as a CSV file.
This is a powerful framework for specifying sample metadata that allows you to make your metadata table easier to manage, easier to re-use, and more portable.
You can read the [detailed PEP documentation](/spec/simple-example/) for a complete description of features.
In this tutorial, we'll demonstrate one of the most useful PEP features: **derived attributes**.
Derived attributes will allow us to remove the file paths from the metadata table.
We will keep everything else about the project the same (the data, pipeline and interface, and looper configuration) and replace the `metadata/sample_table.csv` with a PEP.

The new sample metadata will use 2 files instead of one. We will still have the main `sample_table.csv` file, but we will add a `pep_config.yaml` file. 

## Set up a working directory

To start, let's set up a new root folder for this tutorial. We'll call it `pep_derived_attrs` since we'll be showing you how to use PEP derived attributes. Just copy over the previous tutorial folder (or download it from the [hello looper repository](https://github.com/pepkit/hello_looper)), since we're going to just make a few changes to that project.

```sh
cd ..
cp -r looper_csv_example pep_derived_attrs
rm -rf pep_derived_attrs/results  # remove results folder
```

## Remove paths from `sample_table.csv`

One of our goals is to remove the paths from the sample table.
The hard-coded paths tie the sample table to a particular compute environment, which is undesirable.
What if we change where the data are stored?
Or what if someone else wanted to download our project and run it locally?
They'd need to put the dataset in exactly the spot we did, relative to our metadata table.
That's not a major problem for a couple of small text files, but if you're dealing with hundreds of large biological data files, you probably don't want that data in the same physical location as your metadata and pipeline files.
It might even be on a different file system.
The PEP will help us simplify the sample table and make it portable.

First, edit the sample table to remove all the paths. Just replace them all with a variable, which we'll call `source1` (it can be whatever you like). Here's our revised table:

```csv title="metadata/sample_table.csv"
sample_name,area_type,file_path
mexico,state,source1
switzerland,canton,source1
canada,province,source1
```

One nice thing about this table is that it's more portable.
Now, it will be valid, even if it is removed from the data, because it no longer has paths that tie it to a specific computing environment.
But, wait -- we've lost the path information, which we will need to process the files.
We will move that information into the new `pep_config.yaml` file.

## Create `metadata/pep_config.yaml`

Next, create `metadata/pep_config.yaml` file, with this content:

```yaml title="metadata/pep_config.yaml"
pep_version: 2.1.0
sample_table: sample_table.csv
sample_modifiers:
  derive:
    attributes: [file_path]
    sources:
      source1: "data/{sample_name}.txt"
```

This is using a PEP feature called a "sample modifier", which will programmatically modify your sample metadata. The specific modifier is called the "derive" modifier, which has two arguments: `attributes` specifies which of the sample attributes (corresponding to your table's column headers) will be derived. In this case, it's the `file_path` attribute. Then, the `sources` argument provides a key-value pair. Any value with a source (here, `source1`) will be replaced with the corresponding value (`data/{sample_name}.txt`). These values are actually templates, and variables like `{sample_name}` will be replaced by the corresponding attribute from the sample. The result of this will be the same final metadata table we had earlier.

## Change `.looper.yaml` to point to the PEP

Finally, we need to change the `.looper.yaml` file to point to the new `pep_config.yaml` file, instead of to the `.csv` file directly:

```yaml hl_lines="1" title=".looper.yaml"
pep_config: metadata/pep_config.yaml
output_dir: results
pipeline_interfaces:
  - pipeline/pipeline_interface.yaml
```

And now we can run the project as we did before:

```sh
looper run
```

The results should be the same. 


## Simplifying constant attributes

Now, let's use another PEP sample modifier: the *append* modifier. This allows you to add sample attributes with constant values. Notice that our sample table now has a constant column. Every sample has `file_path` set to `source1`: 

```csv title="metadata/sample_table.csv"
sample_name,area_type,file_path
mexico,state,source1
switzerland,canton,source1
canada,province,source1
```

We can use the append modifier to simplify the table and save space. We do that with two quick steps. First, remove the `file_path` column from the table.


```csv title="metadata/sample_table.csv"
sample_name,area_type
mexico,state
switzerland,canton
canada,province
```

Then, add it back in to the config using an append sample modifier:

```yaml title="metadata/pep_config.yaml" hl_lines="4 5"
pep_version: 2.1.0
sample_table: sample_table.csv
sample_modifiers:
  append:
    file_path: source1
  derive:
    attributes: [file_path]
    sources:
      source1: "data/{sample_name}.txt"
```

Since the append modifier happens before the derive modifier, the samples will first have the `file_path` attribute added, with the `source1` value. Then, these will be derived as before. This configuration thus produces the same result as before, but now with a very streamlined sample table.

But what if your data sources are not the same? Say you have a set of samples where some of them are stored in one location, and others are stored in a separate location. You can still use the *derive* modifier, just specifying different sources in both your table and config, say, `source1` and `source2`, with different paths. The *append* trick wouldn't work, though because it adds constant attributes. In that case, you might use another sample modifier: the [*imply* modifier](/spec/specification/#sample-modifier-imply). The imply modifier adds sample attributes with values that depend on the value of an existing attribute. We will cover more details on the imply modifier in the advanced guides.


## Why is this useful?

In this simple example, we don't benefit much from using the derived columns, because there's no real harm in distributing a few text files along with your pipeline and sample metadata.
But in a real-world case, things can get much more complicated.
With big data, it starts to make a lot of sense to keep data separate from metadata, because it can be re-used for multiple projects.
We want to share our projects with others, and we're not sure they will necessarily store the data in the same location we do.
Paths start to get really long and unwieldy.
They might point to different places.
File systems can change, necessitating adjusting lots of variables.
The PEP sample modifiers can help us corral all this chaos to keep sample tables clean and portable.
They allow you to isolate any of these changes to the project configuration file, and minimize them to editing a single template variable.
For more information and a more detailed example, see: [How to eliminate paths from a sample table](/spec/howto-eliminate-paths/).

## PEPhub

What if you could point looper to a remote file, instead of having to store your metadata locally on disk?
This is where PEPhub comes in.
PEPhub is a web interface for storing PEPs. You can read more in the [PEPhub documentation](/pephub/).

This tutorial PEP is saved on PEPhub at <https://pephub.databio.org/databio/pep_derived_attrs>.

Looper allows us to point to these remote PEPs instead of to local files. Just change the `pep_config` to point to a registry path on PEPhub, like this:

```yaml hl_lines="1" title=".looper.yaml"
pep_config: "pephub.databio.org://databio/pep_derived_attrs:default"
output_dir: results
pipeline_interfaces:
  - pipeline/pipeline_interface.yaml
```

Now you can delete the `metadata` subfolder entirely, because we're not using it at all, but the `looper run` will give the same results.
Now with your metadata living on a remote server, it becomes even more clear how we can benefit from separating file paths from the sample table.


The next thing step is to have the pipeline results actually *populate* the table on PEPhub.
This is possible with looper, but it requires that we learn one more important tool: pipestat. This is what we'll study next.

!!! tip "Summary"
    - Looper will accept metadata as a `.csv`, but you can also use a PEP for more powerful management features.
    - PEPs allow you to simplify your table with programmatic sample modifiers, like `derive`, `append`, or `imply`. 
    - One common use of PEP sample modifiers is to remove file paths from sample tables, making them more portable.
    - PEPhub provides a web-based way to edit sample metadata, which can be consumed directly by looper.

