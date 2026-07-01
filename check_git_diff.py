# for every result.json in "agent_resolution_combined" folder,
# load the json, get all the "agent_diff"s,
# if there is binary file in the diff, print the instance_id and the file path

import json
import os
from pathlib import Path
import glob

agent_resolution_combined_folder = "agent_resolution_combined"

for result_file in glob.glob(os.path.join(agent_resolution_combined_folder, "**", "result.json"), recursive=True):
    with open(result_file, "r") as f:
        result = json.load(f)

    instance_id = result.get("instance_id", result_file)
    for entry in result.get("results", []):
        agent_diff = entry.get("agent_diff", "")
        if agent_diff is None:
            continue
        for line in agent_diff.splitlines():
            if line.startswith("Binary files"):
                # e.g. "Binary files a/path/to/file and b/path/to/file differ"
                parts = line.split()
                if len(parts) >= 3:
                    binary_file = parts[2].lstrip("ab/")
                    print(f"{instance_id}: {binary_file}")
                else:
                    print(f"{instance_id}: {line}")
                break
