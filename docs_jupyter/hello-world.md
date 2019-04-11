
# Hello World! example for looper

`Looper` is a pipeline submission engine (see [looper source code](https://github.com/pepkit/looper); [looper documentation](http://looper.readthedocs.org)). This repository contains a basic functional example project (in [/project](/project)) and a looper-compatible pipeline (in [/pipeline](/pipeline)) that can run on that project. This repository demonstrates how to install `looper` and use it to run the included pipeline on the included PEP project. 

## 1. Install the latest version of looper:

```console
pip install --user --upgrade https://github.com/pepkit/looper/zipball/master
```

## 2. Download and unzip the hello_looper repository



```python
!wget https://github.com/pepkit/hello_looper/archive/master.zip
```

    --2019-04-11 18:14:45--  https://github.com/pepkit/hello_looper/archive/master.zip
    Resolving github.com (github.com)... 192.30.253.113, 192.30.253.112
    Connecting to github.com (github.com)|192.30.253.113|:443... connected.
    HTTP request sent, awaiting response... 302 Found
    Location: https://codeload.github.com/pepkit/hello_looper/zip/master [following]
    --2019-04-11 18:14:45--  https://codeload.github.com/pepkit/hello_looper/zip/master
    Resolving codeload.github.com (codeload.github.com)... 192.30.253.121, 192.30.253.120
    Connecting to codeload.github.com (codeload.github.com)|192.30.253.121|:443... connected.
    HTTP request sent, awaiting response... 200 OK
    Length: unspecified [application/zip]
    Saving to: ‘master.zip’
    
    master.zip              [ <=>                ]   5.24K  --.-KB/s    in 0.004s  
    
    2019-04-11 18:14:45 (1.18 MB/s) - ‘master.zip’ saved [5366]
    



```python
!unzip master.zip
```

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


## 3. Run it


```python
!cd hello_looper-master
```


```python
!looper run project/project_config.yaml
```

    Command: run (Looper version: 0.11.0dev)
    Using default config file, no global config file provided in environment variable(s): ['DIVCFG', 'PEPENV']
    Loading divvy config file: /home/nsheff/.local/lib/python3.5/site-packages/divvy/submit_templates/default_compute_settings.yaml
    Activating compute package 'default'
    Setting sample sheet from file '/home/nsheff/code/looper/docs_jupyter/hello_looper-master/project/sample_annotation.csv'
    Finding pipelines for protocol(s): anySampleType
    Known protocols: anySampleType
    [36m## [1 of 2] frog_1 (anySampleType)[0m
    Writing script to /home/nsheff/hello_looper_results/submission/count_lines.sh_frog_1.sub
    Job script (n=1; 0.00 Gb): /home/nsheff/hello_looper_results/submission/count_lines.sh_frog_1.sub
    Compute node: puma
    Start time: 2019-04-11 18:14:46
    Number of lines: 4
    [36m## [2 of 2] frog_2 (anySampleType)[0m
    Writing script to /home/nsheff/hello_looper_results/submission/count_lines.sh_frog_2.sub
    Job script (n=1; 0.00 Gb): /home/nsheff/hello_looper_results/submission/count_lines.sh_frog_2.sub
    Compute node: puma
    Start time: 2019-04-11 18:14:46
    Number of lines: 7
    
    Looper finished
    Samples valid for job generation: 2 of 2
    Successful samples: 2 of 2
    Commands submitted: 2 of 2
    Jobs submitted: 2
    [0m
