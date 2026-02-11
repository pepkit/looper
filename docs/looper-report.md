# Create a Browsable HTML Report

Looper can create a browsable html report of all project results using the command:

```terminal
looper report --looper-config .your_looper_config.yaml
```

Beginning in Looper 1.7.0, the ``--portable`` flag can be used to create a shareable, zipped version of the html report.

An example html report out put can be found here: [PEPATAC Gold Summary](https://pepatac.databio.org/en/latest/files/examples/gold/gold_summary.html)

Note: pipestat must be configured by looper to perform this operation. Please see the pipestat section for more information: [Using pipestat](pipestat.md)