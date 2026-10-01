# Setting up pipestat

## Introduction

In our previous tutorials, we deployed the `count_lines.sh` pipeline.
The result of that pipeline was the number of provinces in several countries, which was simply printed into the log file.
In a real-life pipeline, we usually don't just want to dig results out of log files.
We would like to view the results in nice, tabular or HTML-based report. 
Looper does this through [pipestat](/pipestat/), another component in PEPkit.

Like the other PEPkit components, pipestat is a standalone tool.
You can read the complete details about pipestat as a standalone tool in the [pipestat documentation](https://pep.databio.org/pipestat/).
You can use pipestat without using looper, and vice versa, but using pipestat alongside looper unlocks a set of helpful tools such as html reports via `looper report`.

This tutorial will show you how to do that.

!!! success "Learning objectives"
    - What is pipestat? Why is it useful?
    - What is a pipestat-compatible pipeline?
    - How can I configure my looper workspace to use a pipestat-compatible pipeline effectively?
    - Where are pipestat results saved? How can I store results of my pipeline somewhere else?
    - How can I make my pipeline store results in PEPhub?
    - Can looper monitor whether my jobs are still running, failed, or already completed?


## A basic pipestat-compatible pipeline

All the options and features in this tutorial require a pipestat-compatible pipeline.
What does that mean?
[Configuring a pipeline to use pipestat](../developer-tutorial/developer-pipestat.md) will go into detail about how to make a pipeline pipestat-compatible.
Briefly, it just means these 3 criteria are fulfilled:

1. The pipeline specifies a [pipestat output schema](/pipestat/pipestat-specification/). This just tells pipestat what results a pipeline can report.
2. The pipeline uses `pipestat` to report results.
3. The looper pipeline interface specifies the path to that output schema in the `output_schema` key, like this:

```yaml  title="pipeline/pipeline_interface.yaml" hl_lines="2"
pipeline_name: count_lines
output_schema: pipestat_output_schema.yaml
sample_interface:
  command_template: >
    pipeline/count_lines.sh {sample.file_path} {sample.sample_name} {pipestat.config_file}
```

!!! note "Pipestat config handoff"
    The `{pipestat.config_file}` in the command template passes looper's merged pipestat configuration to the pipeline. Pipelines can also receive this config via the `PIPESTAT_CONFIG` environment variable using `inject_env_vars`. See the [developer pipestat tutorial](../developer-tutorial/developer-pipestat.md#pipestat-configuration-handoff) for details.

A pipeline that satisfies these criteria is pipestat-compatible, and for these pipelines, looper can give you a nice, web browsable report of results.
It can also help you manage job status of your runs.

To demonstrate, let's use a modified version of our `count_lines` pipeline that has been made pipestat-compatible.

Navigate to the [pipestat_example](https://github.com/pepkit/hello_looper/tree/master/pipestat_example) from the hello_looper repo.


## Configure where pipestat results will be stored

One goal of pipestat is that it allows you to configure a pipeline to store results in different places.
You can either store results in a simple file, in a database, or in PEPhub.
We'll start with the simplest option and configure pipestat to use a results file.
Configure pipestat to use a results file with these lines in the looper config file:

```yaml  title=".looper.yaml" hl_lines="5-6"
pep_config: metadata/pep_config.yaml
output_dir: results
pipeline_interfaces:
  - pipeline/pipeline_interface.yaml
pipestat:
  results_file_path: results.yaml
```

This instructs looper to configure pipestat to store the results in a `.yaml` file.
Looper will now configure the pipeline to report results into a `results.yaml` file.

Execute the run with:
```sh
looper run
```

You can now see the results reported in the `results.yaml` output file.

## Reporting results back to a database

!!! info "Using results file and a database backend"
    If you provide database credentials *and* a results file path, the results file path will take priority and results will only be reported to the local file.

### PostgreSQL
Pipestat also supports PostgreSQL databases as a backend. You will need to set up your own database or be provided the credentials to an existing database.

!!! info "Using docker to set up a temporary PostgreSQL database"
    If you are comfortable using docker, you can quickly set up an instance of a PostgreSQL database using the following command:

    ```bash
    docker run --rm -it --name looper_tutorial \
    -e POSTGRES_USER=looper_test_user \
    -e POSTGRES_PASSWORD=looper_test_pw \
    -e POSTGRES_DB=looper-test-db \
    -p 127.0.0.1:5432:5432 \
    postgres
    ```

Once you have those credentials, you can configure pipestat to use those credentials in the looper config file:
```yaml title=".looper.yaml" hl_lines="7-14"
pep_config: metadata/pep_config.yaml 
output_dir: results
pipeline_interfaces:
  - pipeline/pipeline_interface.yaml
pipestat:
  database:
    dialect: postgresql
    driver: psycopg2
    name: looper-test-db
    user: looper_test_user
    password: looper_test_pw
    host: 127.0.0.1
    port: 5432
```

### SQLite

You can also report results to a SQLite database. You will need to provide a path to the local SQLite database.
```yaml title=".looper.yaml" hl_lines="7"
pep_config: metadata/pep_config.yaml
output_dir: results
pipeline_interfaces:
  - pipeline/pipeline_interface.yaml
pipestat:
  database:
    sqlite_url: "sqlite:///yourdatabase.sqlite3"
```

Once the database credentials are added for either PostgreSQL or SQLite backends, execute the run with:
```sh
looper run
```

Using a database browser, you will now be able to view the reported results within the database of your choice.


## Reporting results back to PEPhub

In the previous tutorial, you configured looper to read sample metadata from PEPhub.
Now, by adding in pipestat integration, we can also report pipeline results *back* to PEPhub.
In this example, we'll report the results back to the demo PEP we used earlier, `databio/pipestat_demo:default`.
But you won't be able to report the results back to the demo repository because you don't have permissions.
So if you want to follow along, you'll first need to create your own PEP on PEPHub to hold these results.
Then, you can run this section yourself by replacing `databio/pipestat_demo:default` with the registry path to a PEP you control.

To configure pipestat to report results to PEPhub instead of to a file, we just change our looper config to point to a `pephub_path`:

```yaml  title=".looper.yaml" hl_lines="6"
pep_config: metadata/pep_config.yaml
output_dir: results
pipeline_interfaces:
  - pipeline/pipeline_interface.yaml
pipestat:
  pephub_path: "databio/pipestat_demo:default"
  flag_file_dir: results/flags
```

No other changes are necessary.
You will have to authenticate with PEPhub using `phc login`, and then looper will pass along the information in the generated pipestat config file.
Pipestat will read the `pephub_path` from the config file and report results directly to PEPhub using its API!



## Generating result reports

Now that you have your first pipestat pipeline configured with looper, there are many other, more powerful things you can add to make this even more useful.
For example, now that looper knows the structure of results your pipeline reports, it can automatically generate beautiful, project-wide results summary HTML pages for you.

### HTML reports

Looper provides an easy `report` command that creates an html report of all reported results.
You've already configured everything above.
To get the report, run the command:

```sh
looper report
```

This command will call `pipestat summarize` on the results located in your results location. In this case, the `results.yaml` file.

Here is an example html report for the above tutorial examples: [count lines report](/looper/count_lines_report/)

A more advanced example of an html report using `looper report` can be found here: [PEPATAC Gold Summary](https://pepatac.databio.org/en/latest/files/examples/gold/gold_summary.html)

### Create tables and stats summaries

Having a nice HTML-browsable record of results is great for human browsing, but you may also want the aggregated results in a machine-readable form for downstream analysis.
Looper can also create summaries in a computable format as  `.tsv` and `.yaml` files.

Run:
```sh
looper table
```

This will produce a `.tsv` file for aggregated primitive results (integers, strings, etc), as well as a `.yaml` file for any aggregated *object* results:
```
Looper version: 2.0.0
Command: table
Using looper config (.looper.yaml).
Creating objects summary
'count_lines' pipeline stats summary (n=4): results/count_lines_stats_summary.tsv
'count_lines' pipeline objects summary (n=0): results/count_lines_objs_summary.yaml

```


## Setting and checking status

Besides reporting results, another feature of pipestat is that it allows users to set pipeline *status*.
If your pipeline uses pipestat to set status flags, then looper can be used to check the status of pipeline runs.
To check the status of all samples, use:

```sh
looper check
```

For this example, the 'running' flag doesn't really help because the pipeline runs so fast that it immediately finishes.
But in a pipeline that will take minutes or hours to complete, it can be useful to know how many and which jobs are running.
That's why `looper check` can be helpful for these long-running pipelines.



!!! info "Do I have to use pipestat?"
    No. You can use looper just as we did in the first two tutorials to run any command.
    Often, you'll want to use looper to run an existing pipeline that you didn't create.
    In that case, you won't have the option of using pipestat, since you're unlikely to go to the effort of adapting someone else's pipeline to use it.
    For non-pipestat-compatible pipelines, you can still use looper to run pipelines, but you won't be able to use `looper report` or `looper check` to manage their output.
    
    **What benefits does pipestat give me?**
    If you *are* developing your own pipeline, then you might want to consider using pipestat in your pipeline.
    This will allow users to use `looper check` to check on the status of pipelines.
    It will also enable `looper report` and `looper table` to create summarized outputs of pipeline results.
    


!!! tip "Summary"
    - Pipestat is a standalone tool that can be used with or without looper.
    - Pipestat standardizes reporting of pipeline results. It provides a standard specification for how pipeline outputs should be stored; and an implementation to easily write results to that format from within Python or from the command line.
    - A pipeline user can configure a pipestat-compatible pipeline to record results in a file, in a database, or in PEPhub.
    - Looper synergizes with pipestat to add powerful features such as checking job status and generating html reports.

