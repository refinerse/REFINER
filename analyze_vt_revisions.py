#!/usr/bin/env python3
"""How often does a refinement agent revise its validation test, and how often
does the revision succeed?

Per comment:
  revised    result.json says validation_test_revised.
  successful the original test was NOT fail-before/pass-after on the ground-truth
             patch (testgen assessment), and the revised test IS.

Nothing in the agent run executes a revised test on the GT commits, so each one
is run in Docker on head_commit (before) and merged_commit (after). The original
test is re-run alongside it as a control: `control_matches_testgen` shows whether
the environment still reproduces the testgen verdict. The control never changes
the success verdict.

Results are cached per instance in <output-dir>/<agent>/, so reruns are cheap.

Usage:
  python analyze_vt_revisions.py agents_results/claude_with_task_and_validation_test \
      --testgen-dir agents_results/results_testgen_claude_sonnet_4.6
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from execution.container_runtime import DockerContainerSession
from pipeline import dataset_utils, test_runner
from run_batch_agent_resolution_vt_sk import load_docker_image_map

# _docker_run_on_version reports these as passed=False, which would otherwise be
# indistinguishable from a real "fails before".
INFRA_FAILURES = ("git checkout failed", "Command timed out", "npx/node.js is not installed")


def split_diff(text: str) -> dict[str, str]:
    """validation_tests.diff (diff -ru original/ current/) -> {test filename: diff}."""
    out = {}
    for part in re.split(r"(?m)^(?=diff -ru )", text):
        m = re.match(r"diff -ru \S+/(\S+) ", part)
        if m:
            out[m.group(1)] = part if part.endswith("\n") else part + "\n"
    return out


def apply_diff(source: Path, diff: str, dest: Path) -> bool:
    return subprocess.run(
        ["patch", "-s", "-f", "-o", str(dest), str(source)],
        input=diff, text=True, capture_output=True,
    ).returncode == 0


def infra_error(result) -> bool:
    return any(s in out for out in (result.before_output, result.after_output) for s in INFRA_FAILURES)


def is_success(orig_fail_to_pass: bool, before_passed, after_passed, error: bool) -> bool:
    return not orig_fail_to_pass and not error and before_passed is False and after_passed is True


def process_instance(instance_dir: Path, testgen_dir: Path, image: str, cache: Path, timeout: int) -> list[dict]:
    if cache.exists():
        return json.loads(cache.read_text())

    data = json.loads((instance_dir / "result.json").read_text())
    instance_id = data["instance_id"]
    revised = [r for r in data["results"] if r.get("validation_test_revised")]
    testgen = {
        int(r["comment_index"]): r
        for r in json.loads((testgen_dir / instance_id / "result.json").read_text())["results"]
    }
    diffs = split_diff((instance_dir / "validation_tests.diff").read_text())
    instance = dataset_utils.load_instance(instance_id)
    head, merged = instance["commit_to_review"]["head_commit"], instance["merged_commit"]

    rows = []
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "-", f"vtrev-{instance_dir.parent.name}-{instance_id}")
    with tempfile.TemporaryDirectory() as tmp, DockerContainerSession(image, name=safe_name) as session:
        for r in revised:
            idx, name = int(r["comment_index"]), r["validation_test_file"]
            tg = testgen[idx]
            orig_before = tg["current_passed"]
            orig_after = tg["assessment"]["ground_truth_patch_passed"]
            orig_f2p = not orig_before and orig_after
            row = {
                "instance_id": instance_id, "comment_index": idx, "test_file": name,
                "language": r["language"], "orig_before_passed": orig_before,
                "orig_after_passed": orig_after, "orig_fail_to_pass": orig_f2p,
                "revised_before_passed": None, "revised_after_passed": None,
                "revised_fail_to_pass": None, "control_before_passed": None,
                "control_after_passed": None, "control_matches_testgen": None,
                "error": "", "successful": False,
            }
            rows.append(row)

            original = testgen_dir / instance_id / name
            revised_file = Path(tmp) / str(idx) / name
            revised_file.parent.mkdir()
            if name not in diffs or not apply_diff(original, diffs[name], revised_file):
                row["error"] = "diff did not apply"
                continue

            def run(path):
                return test_runner.run_test_pair_docker(
                    session, path, head, merged, comment_index=idx,
                    language=r["language"], timeout=timeout,
                )

            new, control = run(revised_file), run(original)
            row.update(
                revised_before_passed=new.before_passed, revised_after_passed=new.after_passed,
                revised_fail_to_pass=new.success, control_before_passed=control.before_passed,
                control_after_passed=control.after_passed,
                control_matches_testgen=(control.before_passed, control.after_passed) == (orig_before, orig_after),
                revised_before_output=new.before_output, revised_after_output=new.after_output,
            )
            if infra_error(new):
                row["error"] = "infrastructure failure (checkout/timeout/no npx)"
            row["successful"] = is_success(orig_f2p, new.before_passed, new.after_passed, bool(row["error"]))

    cache.write_text(json.dumps(rows, indent=1))
    return rows


def main() -> None:
    assert is_success(False, False, True, False)
    assert not is_success(True, False, True, False)   # already valid: nothing to fix
    assert not is_success(False, False, True, True)   # "fail" was a timeout/checkout error
    assert not is_success(False, True, True, False)   # still passes before
    assert not is_success(False, None, None, False)   # never ran

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("agent_dir", type=Path)
    parser.add_argument("--testgen-dir", type=Path, required=True)
    parser.add_argument("--docker-image-map", type=Path, default=Path("instance_docker_image_map.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("validation_test_analysis/revisions"))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=60, help="per-test seconds (testgen used 60)")
    args = parser.parse_args()

    images = load_docker_image_map(args.docker_image_map)
    cache_dir = args.output_dir / args.agent_dir.name
    cache_dir.mkdir(parents=True, exist_ok=True)

    todo = []
    for result_file in sorted(args.agent_dir.glob("*/result.json")):
        data = json.loads(result_file.read_text())
        if any(r.get("validation_test_revised") for r in data["results"]):
            todo.append((result_file.parent, data["instance_id"]))

    def work(item):
        instance_dir, instance_id = item
        cache = cache_dir / f"{instance_dir.name}.json"
        try:
            rows = process_instance(instance_dir, args.testgen_dir, images[instance_id], cache, args.timeout)
        except Exception as exc:  # one broken container must not lose the other instances
            print(f"FAILED {instance_id}: {exc!r}", flush=True)
            return [{"instance_id": instance_id, "error": f"instance failed: {exc!r}", "successful": False}]
        print(f"done {instance_id}: {sum(r['successful'] for r in rows)}/{len(rows)}", flush=True)
        return rows

    with ThreadPoolExecutor(args.workers) as pool:
        rows = [row for rows in pool.map(work, todo) for row in rows]

    fields = [k for k in rows[0] if not k.endswith("_output")] if rows else []
    for row in rows:
        fields += [k for k in row if k not in fields and not k.endswith("_output")]
    out_csv = args.output_dir / f"{args.agent_dir.name}.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    outcome = defaultdict(int)
    for row in rows:
        outcome[(row.get("revised_before_passed"), row.get("revised_after_passed"))] += 1
    success = sum(r["successful"] for r in rows)
    print(f"\n{args.agent_dir.name}")
    print(f"  revised comments:    {len(rows)} (instances: {len(todo)})")
    print(f"  originally valid:    {sum(bool(r.get('orig_fail_to_pass')) for r in rows)}")
    print(f"  successful revision: {success}/{len(rows)}" + (f" ({success / len(rows):.1%})" if rows else ""))
    print(f"  revised test (before_passed, after_passed): {dict(outcome)}")
    print(f"  errors:              {sum(bool(r.get('error')) for r in rows)}")
    print(f"  control != testgen:  {sum(r.get('control_matches_testgen') is False for r in rows)}")
    print(f"  wrote {out_csv}")


if __name__ == "__main__":
    main()
