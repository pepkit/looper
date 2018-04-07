FAQ
=========================

- Why isn't the ``looper`` executable in my path?
	By default, Python packages are installed to ``~/.local/bin``. You can add this location to your path by appending it (``export PATH=$PATH:~/.local/bin``).

- How can I run my jobs on a cluster?
	See :ref:`cluster resource managers <cluster-resource-managers>`.

- Which configuration file has which settings?
	Here's a list: :doc:`config files <config-files>`

- What's the difference between `looper` and `pypiper`?
	`Pypiper <http://pypiper.readthedocs.io/>`_ and `Looper <http://looper.readthedocs.io/>`_ work together as a comprehensive pipeline management system. `Pypiper <http://pypiper.readthedocs.io/>`_ builds individual, single-sample pipelines that can be run one sample at a time. `Looper <http://looper.readthedocs.io/>`_ then processes groups of samples, submitting appropriate pipelines to a cluster or server. The two projects are independent and can be used separately, but they are most powerful when combined.

- Why isn't looper submitting my pipeline: ``Not submitting, flag found: ['*_completed.flag']``?
	When using ``looper run``, looper first checks the sample output for flag files (which can be `_completed.flag`, or `_running.flag`, or `_failed.flag`). Typically, we don't want to resubmit a job that's already running or already finished, so by default, looper **will not submit a job when it finds a flag file**. This is what the message above is indicating. If you do in fact want to re-rerun a sample (maybe you've updated the pipeline, or you want to run restart a failed attempt), you can do so by just passing ``--ignore-flags`` to looper at startup. This will skip the flag check **for all samples**. If you only want to re-run or restart a few samples, it's best to just delete the flag files for the samples you want to restart, then use ``looper run`` as normal.

- How can I resubmit a subset of jobs that failed?
	By default, looper **will not submit a job that has already run**. If you want to re-rerun a sample (maybe you've updated the pipeline, or you want to run restart a failed attempt), you can do so by passing ``--ignore-flags`` to looper at startup, but this will **resubmit all samples**. If you only want to re-run or restart a few samples, it's best to just delete the flag files manually for the samples you want to restart, then use ``looper run`` as normal.	

- Can I pass additional command-line arguments to my pipeline on-the-fly?
	Yes! Any command-line arguments passed to `looper run` *that are not consumed by looper* will simply be handed off untouched to *all the pipelines*. This gives you a handy way to pass-through command-line arguments that you want passed to every job in a given looper run.	For example, you may run `looper run config.yaml -R` -- since `looper `does not understand `-R`, this will be passed to every pipeline.

	For example, pypiper pipelines understand the `--recover` flag; so if you want to pass this flag through `looper` to all your pipeline runs, you may run `looper run config.yaml --recover`. Since `looper `does not understand `--recover`, this will be passed to every pipeline. Obviously, this feature is limited to passing flags that `looper` does not understand, because those arguments will be consumed by `looper` and not passed through to individual pipelines.

- How can I analyze my project interactively?
	Looper uses the ``peppy`` package to model Project and Sample objects under the hood. These project objects are actually useful outside of looper. If you define your project using looper's :doc:`standardized project definition format <define-your-project>` , you can use the project models to instantiate an in memory representation of your project and all of its samples, without using looper. 

	If you're interested in this, you should check out the `peppy package <http://peppy.readthedocs.io/en/latest/models.html>`_. All the documentation for model objects has moved there.
