import json
from pathlib import Path


MISSING_INSTANCES_DIR = Path("missing_instances")

for missing_instances_file in MISSING_INSTANCES_DIR.glob("missing_instances_*.txt"):
    ids = set(missing_instances_file.read_text().splitlines())
    with open("dataset/instances.jsonl", encoding="utf-8") as src, \
        open(missing_instances_file.with_suffix(".instances.jsonl"), "w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip():
                continue
            inst = json.loads(line)
            if inst["instance_id"] in ids:
                print(f"Writing {inst['instance_id']} to {missing_instances_file.with_suffix('.instances.jsonl')}")
                dst.write(json.dumps(inst, ensure_ascii=False))
                dst.write("\n")
