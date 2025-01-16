import matplotlib.pyplot as plt
import os
import sys

results_dir = sys.argv[
    1
]  # Obtain the looper results directory passed via the looper command template

# Extract the previously reported sample-level data from the .log files
countries = []
number_of_regions = []
for filename in os.listdir(results_dir):
    if filename.endswith(".log"):
        file = os.path.join(results_dir, filename)
        with open(file, "r") as f:
            for line in f:
                if line.startswith("Number of lines:"):
                    region_count = int(line.split(":")[1].strip())
                    number_of_regions.append(region_count)
                    country = filename.split("_")[2].split(".")[0]
                    countries.append(country)

# Create a bar chart of regions per country
plt.figure(figsize=(8, 5))
plt.bar(countries, number_of_regions, color=["blue", "green", "purple"])
plt.xlabel("Countries")
plt.ylabel("Number of regions")
plt.title("Number of regions per country")

# Save the image locally
save_location = os.path.join(os.path.dirname(results_dir), "regions_per_country.png")
plt.savefig(save_location, dpi=150)
