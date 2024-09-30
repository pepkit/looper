#!/bin/bash
linecount=`wc -l $1 | sed -E 's/^[[:space:]]+//' | cut -f1 -d' '`
pipestat report -r $2 -i 'number_of_lines' -v $linecount -c $3
echo "Number of lines: $linecount"
