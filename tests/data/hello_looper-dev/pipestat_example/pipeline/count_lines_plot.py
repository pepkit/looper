import matplotlib.pyplot as plt  # be sure to `pip install matplotlib`
import os
import pipestat
import sys

# A pipeline that retrieves previously reported pipestat results
# and plots them in a bar chart
results_file = sys.argv[1]
schema_path = sys.argv[2]

# Create pipestat manager
psm = pipestat.PipestatManager(
    schema_path=schema_path, results_file_path=results_file, pipeline_type="project"
)

# Extract the previously reported data
results = (
    psm.select_records()
)  # pipestat object holds the data after reading the results file
countries = [record["record_identifier"] for record in results["records"]]
number_of_regions = [record["number_of_lines"] for record in results["records"]]

# Create a bar chart of regions per country
plt.figure(figsize=(8, 5))
plt.bar(countries, number_of_regions, color=["blue", "green", "purple"])
plt.xlabel("Countries")
plt.ylabel("Number of regions")
plt.title("Number of regions per country")
# plt.show() # Showing the figure and then saving it causes issues, so leave this commented out.

# Save the image locally AND report that location via pipestat
# we can place it next to the results file for now
save_location = os.path.join(os.path.dirname(results_file), "regions_per_country.png")

plt.savefig(save_location, dpi=150)

result_to_report = {
    "regions_plot": {
        "path": save_location,
        "thumbnail_path": save_location,
        "title": "Regions Plot",
    }
}

psm.report(record_identifier="count_lines", values=result_to_report)
