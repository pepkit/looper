
# Hello World! example for looper

This tutorial demonstrates how to install `looper` and use it to run a pipeline on a PEP project. 

## 1. Install the latest version of looper:

```console
pip install --user --upgrade https://github.com/pepkit/looper/zipball/master
```

## 2. Download and unzip the hello_looper repository

The [hello looper repository](http://github.com/pepkit/hello_looper) contains a basic functional example project (in `/project`) and a looper-compatible pipeline (in `/pipeline`) that can run on that project. Let's download and unzip it:



```python
!wget https://github.com/pepkit/hello_looper/archive/master.zip
```

```.output
--2019-04-24 08:35:57--  https://github.com/pepkit/hello_looper/archive/master.zip
Resolving github.com (github.com)... 192.30.253.112, 192.30.253.113
Connecting to github.com (github.com)|192.30.253.112|:443... connected.
HTTP request sent, awaiting response... 302 Found
Location: https://codeload.github.com/pepkit/hello_looper/zip/master [following]
--2019-04-24 08:35:57--  https://codeload.github.com/pepkit/hello_looper/zip/master
Resolving codeload.github.com (codeload.github.com)... 192.30.253.120, 192.30.253.121
Connecting to codeload.github.com (codeload.github.com)|192.30.253.120|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: unspecified [application/zip]
Saving to: ‘master.zip’

master.zip              [ <=>                ]   5.24K  --.-KB/s    in 0.005s  

2019-04-24 08:35:57 (981 KB/s) - ‘master.zip’ saved [5366]


```


```python
!unzip master.zip
```

```.output
Archive:  master.zip
47b9584b59841d54418699aafc8d8d13f201dac3
   creating: hello_looper-master/
  inflating: hello_looper-master/README.md  
   creating: hello_looper-master/data/
  inflating: hello_looper-master/data/frog1_data.txt  
  inflating: hello_looper-master/data/frog2_data.txt  
  inflating: hello_looper-master/looper_pipelines.md  
  inflating: hello_looper-master/output.txt  
   creating: hello_looper-master/pipeline/
  inflating: hello_looper-master/pipeline/count_lines.sh  
  inflating: hello_looper-master/pipeline/pipeline_interface.yaml  
   creating: hello_looper-master/project/
  inflating: hello_looper-master/project/project_config.yaml  
  inflating: hello_looper-master/project/sample_annotation.csv  

```

## 3. Run it

Run it by changing to the directory and then invoking `looper run` on the project configuration file.


```python
!cd hello_looper-master
```


```python
!looper run project/project_config.yaml
```

```.output
Command: run (Looper version: 0.11.0)
Traceback (most recent call last):
  File "/home/nsheff/.local/bin/looper", line 10, in <module>
    sys.exit(main())
  File "/home/nsheff/.local/lib/python3.5/site-packages/looper/looper.py", line 802, in main
    determine_config_path(args.config_file), subproject=args.subproject,
  File "/home/nsheff/.local/lib/python3.5/site-packages/looper/utils.py", line 104, in determine_config_path
    raise ValueError("Path doesn't exist: {}".format(root))
ValueError: Path doesn't exist: project/project_config.yaml

```

Voila! You've run your very first pipeline across multiple samples using `looper`!

# Exploring the results

Now, let's inspect the `hello_looper` repository you downloaded. It has 3 components, each in a subfolder:


```python
!tree hello_looper-master/*/
```

```.output
hello_looper-master/data/
├── frog1_data.txt
└── frog2_data.txt
hello_looper-master/pipeline/
├── count_lines.sh
└── pipeline_interface.yaml
hello_looper-master/project/
├── project_config.yaml
└── sample_annotation.csv

0 directories, 6 files

```

These are:

 * `/data` -- contains 2 data files for 2 samples. These input files were each passed to the pipeline.
 * `/pipeline` -- contains the script we want to run on each sample in our project. Our pipeline is a very simple shell script named `count_lines.sh`, which (duh!) counts the number of lines in an input file.
 * `/project` -- contains 2 files that describe metadata for the project (`project_config.yaml`) and the samples (`sample_annotation.csv`). This particular project describes just two samples listed in the annotation file. These files together make up a [PEP](http://pepkit.github.io)-formatted project, and can therefore be read by any PEP-compatible tool, including `looper`.




When we invoke `looper` from the command line we told it to `run project/project_config.yaml`. `looper` reads the [project/project_config.yaml](https://github.com/pepkit/hello_looper/blob/master/project/project_config.yaml) file, which points to a few things:

 * the [project/sample_annotation.csv](https://github.com/pepkit/hello_looper/blob/master/project/sample_annotation.csv) file, which specifies a few samples, their type, and path to data file
 * the `output_dir`, which is where looper results are saved. Results will be saved in `$HOME/hello_looper_results`.
 * the `pipeline_interface.yaml` file, ([pipeline/pipeline_interface.yaml](https://github.com/pepkit/hello_looper/blob/master/pipeline/pipeline_interface.yaml)), which tells looper how to connect to the pipeline ([pipeline/count_lines.sh](https://github.com/pepkit/hello_looper/blob/master/pipeline/)).

The 3 folders (`data`, `project`, and `pipeline`) are modular; there is no need for these to live in any predetermined folder structure. For this example, the data and pipeline are included locally, but in practice, they are usually in a separate folder; you can point to anything (so data, pipelines, and projects may reside in distinct spaces on disk). You may also include more than one pipeline interface in your `project_config.yaml`, so in a looper project, many-to-many relationships are possible.



## Pipeline outputs

Outputs of pipeline runs will be under the directory specified in the `output_dir` variable under the `paths` section in the project config file (see the [config files page](config-files.md)). Let's inspect that `project_config.yaml` file to see what it says under `output_dir`:



```python
!cat hello_looper-master/project/project_config.yaml
```

```.output
metadata:
  sample_annotation: sample_annotation.csv
  output_dir: $HOME/hello_looper_results
  pipeline_interfaces: ../pipeline/pipeline_interface.yaml

```

Alright, next let's explore what this pipeline stuck into our `output_dir`:



```python
!tree $HOME/hello_looper_results
```

```.output
/home/nsheff/hello_looper_results
├── results_pipeline
└── submission
    ├── count_lines.sh_frog_1.log
    ├── count_lines.sh_frog_1.sub
    ├── count_lines.sh_frog_2.log
    ├── count_lines.sh_frog_2.sub
    ├── frog_1.yaml
    └── frog_2.yaml

2 directories, 6 files

```


Inside of an `output_dir` there will be two directories:

- `results_pipeline` - a directory with output of the pipeline(s), for each sample/pipeline combination (often one per sample)
- `submissions` - which holds a YAML representation of each sample and a log file for each submitted job

From here to running hundreds of samples of various sample types is virtually the same effort!



## A few more basic looper options

Looper also provides a few other simple arguments that let you adjust what it does. You can find a [complete reference of usage](usage) in the docs. Here are a few of the more common options:

For `looper run`:

- `-d`: Dry run mode (creates submission scripts, but does not execute them) 
- `--limit`: Only run a few samples 
- `--lumpn`: Run several commands together as a single job. This is useful when you have a quick pipeline to run on many samples and want to group them.

There are also other commands:

- `looper check`: checks on the status (running, failed, completed) of your jobs
- `looper summarize`: produces an output file that summarizes your project results
- `looper destroy`: completely erases all results so you can restart
- `looper rerun`: rerun only jobs that have failed.


## On your own

To use `looper` on your own, you will need to prepare 2 things: a **project** (metadata that define *what* you want to process), and **pipelines** (*how* to process data). 
The next sections define these:

1. **Project**. To link your project to `looper`, you will need to [define your project](define-your-project.md) using PEP format. 
2. **Pipelines**. You will want to either use pre-made `looper`-compatible pipelines or link your own custom-built pipelines. Read how to [connect your pipeline](linking-a-pipeline.md) to `looper`.

