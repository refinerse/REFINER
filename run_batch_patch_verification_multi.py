#!/usr/bin/env python3
"""Replay MULTIPLE agents' patches per instance, sharing one container.

Container startup + ``pip install -e .`` dominate per-instance cost. Running
each agent in its own batch pays that cost once *per agent*. This script pays
it once *per instance*: it starts the image a single time, then for every agent
it resets the repo to ``head_commit``, applies that agent's stored patch,
reinstalls, and runs the (split) acceptance tests -- looping agents inside the
same container.

Output mirrors the per-agent layout of ``run_batch_patch_verification.py`` so
``report_eval_on_split.py`` works unchanged:

    <output-root>/<agent-label>/<instance_id>/result.json
    <output-root>/<agent-label>/summary.json

Each result.json carries the same fields as the single-agent script, including
the per-assertion counts (``total_assertions`` / ``assertions_passed`` /
``assertion_pass_rate``).

Usage:
  python run_batch_patch_verification_multi.py --workers 30
  python run_batch_patch_verification_multi.py \
      --agent vt_intent_merged_4=results_vt_intent_merged_4 \
      --agent combined=agent_resolution_combined --workers 30
"""
from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from execution.container_runtime import DockerContainerSession

# Reuse all the building blocks from the single-agent script.
from run_batch_patch_verification import (
    apply_patch_in_container,
    ensure_git_safe_directory,
    load_combined_result,
    load_dataset_instances,
    load_docker_image_map,
    load_existing_result,
    make_stub_result,
    placeholder_results_for_tests,
    reinstall_python_repo,
    resolve_docker_image,
    select_agent_diff,
    verified_tests_from_result,
    verify_with_counts,
    write_instance_result,
    write_summary,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_DATASET_FILE = "dataset/instances.jsonl"
DEFAULT_TESTGEN_DIR = "results_testgen_splitted"
DEFAULT_OUTPUT_ROOT = "evaluate_agent_patch_on_split"
DEFAULT_DOCKER_IMAGE_MAP_FILE = "instance_docker_image_map.csv"

# label -> patch directory
DEFAULT_AGENTS: list[tuple[str, str]] = [
    ("vt_intent_merged_4", "results_vt_intent_merged_4"),
    ("vt_sk_merged", "results_agent_resolution_vt_sk_merged"),
    ("agent_resolution_combined", "agent_resolution_combined"),
    ("pure_qwen_merged", "agents_results/results_agent_resolution_pure_qwen_merged"),
]


def _finalize_result(instance: dict, test_results: list[dict],
                     patch_apply_output: str, patch_diff: str) -> dict:
    """Build a successful per-agent result with assertion-level aggregates."""
    num_tests = len(test_results)
    num_passed = sum(1 for e in test_results if e["test_passed"])
    total_assertions = sum(e.get("num_assertions", 0) for e in test_results)
    assertions_passed = sum(e.get("assertions_passed", 0) for e in test_results)
    return {
        "instance_id": instance["instance_id"],
        "repo": instance["repo"],
        "patch_applied": True,
        "patch_apply_output": patch_apply_output,
        "patch_diff": patch_diff,
        "num_tests": num_tests,
        "num_tests_passed": num_passed,
        "test_pass_rate": (num_passed / num_tests) if num_tests else 0.0,
        "total_assertions": total_assertions,
        "assertions_passed": assertions_passed,
        "assertion_pass_rate": (assertions_passed / total_assertions) if total_assertions else 0.0,
        "results": test_results,
        "error": None,
    }


def _run_agent(session, instance, verified_tests, has_python,
               patch_result) -> dict:
    """Reset -> apply one agent's patch -> reinstall -> verify, in the open
    container. Returns the per-agent result dict (never raises)."""
    head_commit = instance["commit_to_review"]["head_commit"]

    # Reset to a clean head_commit so the previous agent's patch is gone.
    reset = session.run_command(
        f"git checkout --force {head_commit} && git clean -fd --quiet",
        timeout=120,
    )
    if reset.returncode != 0:
        error_message = f"git checkout failed: {reset.stderr[:500]}"
        return make_stub_result(
            instance, error=error_message,
            results=placeholder_results_for_tests(verified_tests, error=error_message),
        )

    if has_python:
        reinstall_python_repo(session)

    patch_diff, patch_error = select_agent_diff(patch_result)
    if patch_error or patch_diff is None:
        error_message = patch_error or "No replayable patch diff found"
        return make_stub_result(
            instance, error=error_message,
            results=placeholder_results_for_tests(verified_tests, error=error_message),
        )

    patch_applied, patch_apply_output = apply_patch_in_container(session, patch_diff)
    if not patch_applied:
        error_message = "git apply failed"
        return make_stub_result(
            instance, error=error_message, patch_applied=False,
            patch_apply_output=patch_apply_output, patch_diff=patch_diff,
            results=placeholder_results_for_tests(
                verified_tests, error=error_message, test_output=patch_apply_output),
        )

    if has_python:
        reinstall_python_repo(session)

    diff_result = session.run_command("git diff", timeout=30)
    applied_diff = diff_result.stdout
    if not applied_diff.strip():
        status_result = session.run_command("git status --porcelain", timeout=15)
        if not status_result.stdout.strip():
            error_message = "Patch applied but produced no working tree changes"
            return make_stub_result(
                instance, error=error_message, patch_applied=True,
                patch_apply_output=patch_apply_output, patch_diff=patch_diff,
                results=placeholder_results_for_tests(verified_tests, error=error_message),
            )
    else:
        patch_diff = applied_diff

    test_results = []
    for test in verified_tests:
        info = verify_with_counts(
            session=session,
            test_code=test["test_code"],
            test_filename=test["test_file"],
            language=test["language"],
        )
        test_results.append({
            "comment_index": test["comment_index"],
            "comment_text": test["comment_text"],
            "comment_type": test["comment_type"],
            "language": test["language"],
            "test_file": test["test_file"],
            "test_passed": info["passed"],
            "num_assertions": info["num_assertions"],
            "assertions_passed": info["assertions_passed"],
            "assertions_failed": info["assertions_failed"],
            "test_output": info["output"],
            "error": None,
        })

    return _finalize_result(instance, test_results, patch_apply_output, patch_diff)


def process_instance_multi(
    instance: dict,
    testgen_result: dict,
    docker_image: str,
    agents: list[tuple[str, dict]],   # (label, patch_result) for agents to run
    output_root: Path,
) -> dict[str, dict]:
    """Open the container once and evaluate every requested agent inside it."""
    instance_id = instance["instance_id"]
    out: dict[str, dict] = {}

    verified_tests = verified_tests_from_result(instance, testgen_result)
    if not verified_tests:
        for label, _ in agents:
            res = make_stub_result(instance, error="No successful generated tests found")
            write_instance_result(output_root / label, res)
            out[label] = res
        return out

    has_python = any(t["language"] == "python" for t in verified_tests)

    safe_name = instance_id.replace("/", "--").replace("@", "-")
    container_name = f"rb-multireplay-{safe_name}"
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, text=True)

    session = DockerContainerSession(docker_image, name=container_name)
    try:
        session.start()
        ensure_git_safe_directory(session)
        for label, patch_result in agents:
            try:
                res = _run_agent(session, instance, verified_tests, has_python, patch_result)
            except Exception as exc:  # one agent failing must not abort the rest
                logger.exception("[%s/%s] agent replay error", instance_id, label)
                res = make_stub_result(
                    instance, error=str(exc),
                    results=placeholder_results_for_tests(verified_tests, error=str(exc)),
                )
            write_instance_result(output_root / label, res)
            out[label] = res
    except Exception as exc:
        logger.exception("[%s] container-level error", instance_id)
        for label, _ in agents:
            if label in out:
                continue
            res = make_stub_result(
                instance, error=str(exc),
                results=placeholder_results_for_tests(verified_tests, error=str(exc)),
            )
            write_instance_result(output_root / label, res)
            out[label] = res
    finally:
        session.remove(force=True)

    return out


def parse_agents(values: list[str] | None) -> list[tuple[str, str]]:
    if not values:
        return DEFAULT_AGENTS
    agents = []
    for v in values:
        if "=" not in v:
            raise ValueError(f"--agent must be label=dir, got: {v}")
        label, _, d = v.partition("=")
        agents.append((label.strip(), d.strip()))
    return agents


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay multiple agents per shared container")
    parser.add_argument("--dataset-file", default=DEFAULT_DATASET_FILE)
    parser.add_argument("--testgen-dir", default=DEFAULT_TESTGEN_DIR)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--docker-image-map-file", default=DEFAULT_DOCKER_IMAGE_MAP_FILE)
    parser.add_argument("--agent", action="append",
                        help="label=patch_dir (repeatable). Defaults to the 4 known agents.")
    parser.add_argument("--workers", type=int, default=30)
    parser.add_argument("--repo", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    agents = parse_agents(args.agent)
    testgen_dir = Path(args.testgen_dir)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    resume = not args.no_resume

    dataset_file = Path(args.dataset_file)
    if not dataset_file.exists():
        logger.error("Dataset file not found: %s", dataset_file)
        sys.exit(1)

    docker_image_map = load_docker_image_map(Path(args.docker_image_map_file))
    logger.info("Loaded %d image mappings; agents: %s",
                len(docker_image_map), [a[0] for a in agents])

    all_dataset = load_dataset_instances(dataset_file)
    if args.repo:
        all_dataset = [i for i in all_dataset if i["repo"] == args.repo]
    if args.limit and len(all_dataset) > args.limit:
        all_dataset = all_dataset[: args.limit]
    logger.info("Loaded %d instances", len(all_dataset))

    # Per-agent accumulators for the summaries.
    agent_results: dict[str, list[dict]] = {label: [] for label, _ in agents}
    to_process: list[tuple] = []

    for instance in all_dataset:
        instance_id = instance["instance_id"]
        testgen_result = load_combined_result(testgen_dir, instance_id)

        # Figure out, per agent, what still needs running.
        agents_needed: list[tuple[str, dict]] = []
        for label, patch_dir in agents:
            existing = load_existing_result(output_root / label, instance_id) if resume else None
            if existing is not None:
                agent_results[label].append(existing)
                continue

            if testgen_result is None:
                stub = make_stub_result(instance, error="No combined testgen result found")
                write_instance_result(output_root / label, stub)
                agent_results[label].append(stub)
                continue

            patch_result = load_combined_result(Path(patch_dir), instance_id)
            if patch_result is None:
                stub = make_stub_result(instance, error="No combined patch result found")
                write_instance_result(output_root / label, stub)
                agent_results[label].append(stub)
                continue

            agents_needed.append((label, patch_result))

        if not agents_needed:
            continue

        docker_image = docker_image_map.get(instance_id) or resolve_docker_image(instance_id)
        to_process.append((instance, testgen_result, docker_image, agents_needed))

    if not to_process:
        for label, _ in agents:
            write_summary(output_root / label, agent_results[label], 0.0)
        logger.info("Nothing to run; wrote summaries for %d agents", len(agents))
        return

    start_time = time.time()
    processed = 0
    lock = threading.Lock()
    logger.info("Processing %d instance(s) x up-to-%d agents with %d workers",
                len(to_process), len(agents), args.workers)

    def _one(instance, testgen_result, docker_image, agents_needed):
        return process_instance_multi(
            instance=instance, testgen_result=testgen_result,
            docker_image=docker_image, agents=agents_needed, output_root=output_root,
        )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        fut_to_inst = {
            executor.submit(_one, inst, tr, img, an): inst
            for inst, tr, img, an in to_process
        }
        for fut in as_completed(fut_to_inst):
            inst = fut_to_inst[fut]
            try:
                out = fut.result()
            except Exception:
                logger.exception("[%s] instance task failed", inst["instance_id"])
                out = {}
            with lock:
                for label, res in out.items():
                    agent_results[label].append(res)
                processed += 1
                count = processed
            passed_summary = ", ".join(
                f"{label}:{res.get('num_tests_passed',0)}/{res.get('num_tests',0)}"
                for label, res in out.items()
            )
            logger.info("[%d/%d] %s -> %s", count, len(to_process), inst["instance_id"], passed_summary)
            if count % 10 == 0:
                with lock:
                    for label, _ in agents:
                        write_summary(output_root / label, list(agent_results[label]),
                                      time.time() - start_time)

    elapsed = time.time() - start_time
    logger.info("=== ALL AGENTS DONE in %.0fs ===", elapsed)
    for label, _ in agents:
        s = write_summary(output_root / label, agent_results[label], elapsed)
        logger.info(
            "  %-32s %d inst | %d/%d tests pass (%.1f%%) | %d/%d assertions pass (%.1f%%) | %d err",
            label, s["total_instances"], s["total_tests_passed"], s["total_tests"],
            s["overall_test_pass_rate"] * 100,
            s["assertions_passed"], s["total_assertions"], s["assertion_pass_rate"] * 100,
            s["total_errors"],
        )


if __name__ == "__main__":
    main()
