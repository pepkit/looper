import os.path

import pipestat
import sys

# Very simple pipeline that calls pipestat
# takes arguments invoked during looper submission via command templates
text_file = sys.argv[
    1
]  # this is the sample we wish to process by reading the number of lines
sample_name = sys.argv[2]
results_file = sys.argv[3]
schema_path = sys.argv[4]

# Create pipestat manager and then report values
psm = pipestat.PipestatManager(
    schema_path=schema_path,
    results_file_path=results_file,
    record_identifier=sample_name,
)


text_file = os.path.abspath(text_file)
# Read text file and count lines
with open(text_file, "r") as f:
    result = {"number_of_lines": len(f.readlines())}

# The results are defined in the pipestat output schema.
psm.report(record_identifier=sample_name, values=result)

# end of pipeline
