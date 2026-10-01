## Create a folder of linked similar objects

Looper has the ability to create a folder containing symlinks to similar objects (e.g. images). This is helpful if your pipeline reports many objects, and you would like to see all the same type of object in one place.

You must configure [pipestat](../user-tutorial/user-pipestat.md) to use this feature. 

Once your pipeline has finished running, you can run the command:

```shell
looper link
```

This command will create symlinks of all objects of the same type and place them into a subfolder within the results folder for convenient browsing. For a how-to guide on reporting objects such as images using pipestat, see [report objects](report-objects.md).


