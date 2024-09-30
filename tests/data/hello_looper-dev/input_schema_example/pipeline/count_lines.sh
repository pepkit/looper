#!/bin/bash
linecount=`wc -l $1 | sed -E 's/^[[:space:]]+//' | cut -f1 -d' '`
export area_type=$2
echo "Number of ${area_type}s: $linecount"
