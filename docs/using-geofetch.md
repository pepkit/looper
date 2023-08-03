# How to set up a new GEO project

You can use [geofetch](http://geofetch.databio.org) to quickly set up a project to run with looper.

## Download data

```
geofetch -i GSE69993 --just-metadata -m metadata
```

## Initialize looper

Make it easier to run looper without specifying the config

```
looper init metadata/*.yaml
```

## Convert to fastq

Now, you can convert the files from sra into fastq format:

```
looper run --amend sra_convert
```

## Run pipeline

Add a pipeline interface to link to a project

(Experimental)

```
looper mod "pipeline_interfaces: /path/to/piface.yaml"
```
