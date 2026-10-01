# Running project-level pipelines

So far, our example has been what we call a *sample-level pipeline*.
The `count_lines` pipeline from our [basic tutorial](initialize.md) runs one job per sample, and we want to do the same thing to each sample.

This is the most common use case for looper.

But sometimes, we need to run a single job on an entire project.
Looper calls that a *project-level* pipeline.

Here, we'll walk through a basic example of running a project-level pipeline using looper.

!!! success "Learning objectives"
    - What is the difference between sample-level and project-level pipelines?
    - How do I configure a project-level pipeline interface?
    - How do I run a project-level pipeline with `looper runp`?

A project-level pipeline is meant to run on the entire group of your samples, not each sample individually.

First we need to create a project-level pipeline. We would like to take the number of regions from each sample (file) and collect them into a single plot. This tutorial assumes you've completed [using a pep for derived attributes](metadata.md#using-a-pep-for-derived-attributes). You can always download the completed tutorial files from the [hello looper repository](https://github.com/pepkit/hello_looper).


Ensure you are in the `pep_derived_attrs` folder from the previous tutorial or after downloading the folder from the hello looper repository.

```shell
cd pep_derived_attrs
```

Next run the sample level pipeline so that the pipeline log files are available:

```shell
looper run
```

You can confirm the existence of log files by checking the `results/submission` folder:

`ls results/submission/`

```shell
count_lines_canada.log  count_lines_mexico.log  count_lines_switzerland.log 
count_lines_canada.sub  count_lines_mexico.sub  count_lines_switzerland.sub
```

If you open one of the `.log` files, you'll see that each contains the pipeline's results for this sample:

```shell
Number of lines: 10
```

This is because our sample-level pipeline prints the number of lines to the terminal. Looper logs this terminal output to a `.log` file. While not intended to be used as a results file, we can use the `.log` file in this case as an example.

First, we will need to add a `project_interface` to the `pipeline_interface` contained within `pep_derived_attrs/pipeline`:

```yaml title="pipeline_interface.yaml" hl_lines="5-7"
pipeline_name: count_lines
sample_interface:
  command_template: >
    pipeline/count_lines.sh {sample.file_path}
project_interface:
  command_template: >
    python3 {looper.piface_dir}/count_lines_plot.py {looper.output_dir}/submission/
```

Next, we must create our pipeline. Create a python file in the pipeline folder named `count_lines_plot.py`:

```py title="count_lines_plot.py"
import matplotlib.pyplot as plt
import os
import sys

results_dir = sys.argv[1] # Obtain the looper results directory passed via the looper command template

# Extract the previously reported sample-level data from the .log files
countries = []
number_of_regions = []
for filename in os.listdir(results_dir):
    if filename.endswith('.log'):
        file = os.path.join(results_dir, filename)
        with open(file, 'r') as f:
            for line in f:
                if line.startswith('Number of lines:'):
                    region_count = int(line.split(':')[1].strip())
                    number_of_regions.append(region_count)
                    country = filename.split('_')[2].split('.')[0]
                    countries.append(country)

# Create a bar chart of regions per country
plt.figure(figsize=(8, 5))
plt.bar(countries, number_of_regions, color=['blue', 'green', 'purple'])
plt.xlabel('Countries')
plt.ylabel('Number of regions')
plt.title('Number of regions per country')

# Save the image locally
save_location =  os.path.join(os.path.dirname(results_dir), "regions_per_country.png")
plt.savefig(save_location, dpi=150)

```

Make sure `count_lines_plot.py` is executable:

```sh
chmod 755 pipeline/count_lines_plot.py
```

If you run the project-level pipeline with the following command,
`looper runp -c .looper.yaml`, the project-level pipeline will run and a `regions_per_country.png` should appear in your results folder:

![Generated image](../img/regions_per_country.png)

That is how you can run a project-level pipeline via looper!

You can find even more details about project-level pipelines in [advanced run options](../advanced-guide/advanced-run-options.md#running-project-level-pipelines).