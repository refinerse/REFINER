#!/usr/bin/env python3
"""Measure how close agent-generated patches are to the human (merged) patch.

For every result folder this computes two similarity metrics between the
agent's patch and the human's ``merged_patch`` from ``dataset/instances.jsonl``:

  - BLEU score (human patch = reference, agent patch = hypothesis)
  - Edit similarity (normalized Levenshtein: ``1 - dist / max(len)``)

Both metrics are computed on the *post-patch file content*: each patch is
applied to the file's content at ``base_commit`` (read from the local git
repos) and the resulting files are compared. Metrics are produced at two
granularities:

  - file level   -- one row per (instance, file)
  - function level -- one row per (instance, file, python function/method)

Only the files a human reviewer commented on are considered
(``reference_review_comments[].path``); every other file touched by either
patch is ignored. Function-level rows cover functions modified by either the
human or the agent inside those files (Python files only, parsed with ``ast``).

Outputs (written next to the first result dir by default):
  - ``patch_similarity_file.csv``      -- per (instance, file) rows
  - ``patch_similarity_function.csv``  -- per (instance, file, function) rows
and a summary table averaging each metric per result folder.
"""

from __future__ import annotations

import argparse
import ast
import csv
import difflib
import io
import json
import math
import re
import subprocess
import warnings
from collections import Counter
from pathlib import Path

import Levenshtein
from unidiff import PatchSet


DEFAULT_RESULT_DIRS = [
    Path("results_agent_resolution_vt_sk_merged"),
    Path("results_agent_resolution_mt_vt_sk_all"),
    Path("results_agent_resolution_mt_vt_sk_any_merged"),
    Path("results_agent_resolution_mt_vt_sk_gt_select_merged"),
    Path("agent_resolution_combined"),
]
SHORT_LABELS = [
    "with_vt_sk",
    "with_multi_vt_sk_all",
    "with_multi_vt_sk_any",
    "with_multi_vt_sk_gt_select",
    "claude",
]

DATASET_FILE = Path("dataset/instances.jsonl")
DEFAULT_REPOS_DIR = Path("/data/Documents/crab-dataset/crab-dataset/repos")
MISSING = "NA"

# BLEU-4 with uniform weights, Chen & Cherry (2014) "method 1" smoothing.
BLEU_MAX_N = 4
BLEU_WEIGHTS = [0.25, 0.25, 0.25, 0.25]
BLEU_SMOOTH_EPSILON = 0.1

CODE_TOKEN_RE = re.compile(r"[A-Za-z_]\w*|\d+|[^\sA-Za-z0-9_]")


# --------------------------------------------------------------------------- #
# Dataset / result loading
# --------------------------------------------------------------------------- #
def load_dataset(path: Path) -> dict[str, dict]:
    """Map instance_id -> instance dict (repo, base_commit, merged_patch, ...)."""
    index: dict[str, dict] = {}
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"WARNING: Could not parse {path}:{line_number}: {exc}")
                continue
            instance_id = data.get("instance_id")
            if instance_id is not None:
                index[str(instance_id)] = data
    return index


def load_result_index(root: Path) -> dict[str, dict]:
    """Load every result.json under a directory, keyed by instance_id."""
    index: dict[str, dict] = {}
    for result_file in sorted(root.rglob("result.json")):
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"WARNING: Could not read {result_file}: {exc}")
            continue
        instance_id = data.get("instance_id") or result_file.parent.name
        data["_dir"] = str(result_file.parent)
        index[str(instance_id)] = data
    return index


def get_agent_patch(result: dict) -> str:
    """Return the agent's full diff for an instance result.

    Prefers the ``agent.diff`` artifact file, falls back to the (repeated) full
    diff stored under ``results[].agent_diff`` in result.json.
    """
    result_dir = result.get("_dir")
    if result_dir:
        diff_file = Path(result_dir) / "agent.diff"
        if diff_file.exists():
            try:
                text = diff_file.read_text(encoding="utf-8")
                if text.strip():
                    return text
            except OSError:
                pass
    for entry in result.get("results", []):
        if isinstance(entry, dict):
            diff = entry.get("agent_diff")
            if isinstance(diff, str) and diff.strip():
                return diff
    return ""


# --------------------------------------------------------------------------- #
# Patch handling
# --------------------------------------------------------------------------- #
def split_patch_by_file(patch_text: str) -> dict[str, str]:
    """Split a multi-file unified diff into ``{path: single_file_diff_text}``.

    The path used is the post-image path (``b/<path>``) so renames map to their
    new name.
    """
    files: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for line in (patch_text or "").splitlines(keepends=True):
        if line.startswith("diff --git "):
            if current is not None:
                files[current] = "".join(buffer)
            buffer = [line]
            match = re.search(r" b/(.+?)\s*$", line)
            current = match.group(1) if match else None
        elif current is not None:
            buffer.append(line)
    if current is not None:
        files[current] = "".join(buffer)
    return files


def apply_file_diff(base_text: str | None, file_diff_text: str) -> str:
    """Apply a single-file unified diff to ``base_text`` and return the result.

    Hunks are applied at their stated offsets (the diffs were generated against
    exactly this base commit, so no fuzz is required).
    """
    patch_set = PatchSet(io.StringIO(file_diff_text))
    if not patch_set:
        return base_text or ""
    patched_file = patch_set[0]
    base_lines = (base_text or "").splitlines(keepends=True)
    out: list[str] = []
    idx = 0
    for hunk in patched_file:
        source_start = max(hunk.source_start - 1, 0)
        out.extend(base_lines[idx:source_start])
        idx = source_start
        for line in hunk:
            if line.is_context:
                out.append(line.value)
                idx += 1
            elif line.is_removed:
                idx += 1
            elif line.is_added:
                out.append(line.value)
    out.extend(base_lines[idx:])
    return "".join(out)


# --------------------------------------------------------------------------- #
# Repo / base content access
# --------------------------------------------------------------------------- #
class BaseContentProvider:
    """Reads file content at ``base_commit`` from local git checkouts (cached)."""

    def __init__(self, repos_dir: Path) -> None:
        self.repos_dir = repos_dir
        self._repo_cache: dict[str, Path | None] = {}
        self._content_cache: dict[tuple[str, str, str], str | None] = {}
        self.missing_repos: set[str] = set()

    def repo_path(self, repo: str) -> Path | None:
        if repo in self._repo_cache:
            return self._repo_cache[repo]
        # Support both the nested ("owner/name") and flat ("owner__name") layouts.
        path = None
        for candidate in (self.repos_dir / repo, self.repos_dir / repo.replace("/", "__")):
            if (candidate / ".git").exists():
                path = candidate
                break
        if path is None:
            self.missing_repos.add(repo)
        self._repo_cache[repo] = path
        return path

    def get(self, repo: str, commit: str, path: str) -> str | None:
        key = (repo, commit, path)
        if key in self._content_cache:
            return self._content_cache[key]
        repo_path = self.repo_path(repo)
        content: str | None = None
        if repo_path is not None:
            result = subprocess.run(
                ["git", "-C", str(repo_path), "show", f"{commit}:{path}"],
                capture_output=True,
            )
            if result.returncode == 0:
                content = result.stdout.decode("utf-8", "replace")
            else:
                content = None  # file did not exist at base (e.g. newly added)
        self._content_cache[key] = content
        return content


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
def tokenize_code(text: str) -> list[str]:
    return CODE_TOKEN_RE.findall(text or "")


def _ngram_counts(tokens: list[str], n: int) -> Counter:
    return Counter(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))


def bleu_score(reference: str, hypothesis: str) -> float:
    """Sentence BLEU-4 of ``hypothesis`` against ``reference`` (smoothed)."""
    ref_tokens = tokenize_code(reference)
    hyp_tokens = tokenize_code(hypothesis)
    if not hyp_tokens or not ref_tokens:
        return 1.0 if not hyp_tokens and not ref_tokens else 0.0

    log_precisions: list[float] = []
    for n in range(1, BLEU_MAX_N + 1):
        hyp_ngrams = _ngram_counts(hyp_tokens, n)
        total = sum(hyp_ngrams.values())
        if total == 0:
            continue
        ref_ngrams = _ngram_counts(ref_tokens, n)
        clipped = sum(min(count, ref_ngrams.get(ngram, 0)) for ngram, count in hyp_ngrams.items())
        # Chen & Cherry method 1: avoid log(0) for higher-order gaps.
        precision = clipped / total if clipped > 0 else BLEU_SMOOTH_EPSILON / total
        log_precisions.append(BLEU_WEIGHTS[n - 1] * math.log(precision))

    if not log_precisions:
        return 0.0

    # Brevity penalty.
    ref_len = len(ref_tokens)
    hyp_len = len(hyp_tokens)
    brevity = 1.0 if hyp_len > ref_len else math.exp(1 - ref_len / hyp_len)
    return brevity * math.exp(sum(log_precisions))


def edit_similarity(text_a: str, text_b: str) -> float:
    """Line-level normalized edit similarity: ``1 - levenshtein / max(len)``.

    Each distinct line is mapped to a single codepoint so the (C-accelerated)
    Levenshtein distance runs over line sequences rather than characters,
    keeping whole-file comparisons tractable.
    """
    lines_a = (text_a or "").splitlines()
    lines_b = (text_b or "").splitlines()
    if not lines_a and not lines_b:
        return 1.0

    mapping: dict[str, str] = {}

    def encode(lines: list[str]) -> str:
        chars = []
        for line in lines:
            if line not in mapping:
                mapping[line] = chr(len(mapping))
            chars.append(mapping[line])
        return "".join(chars)

    seq_a = encode(lines_a)
    seq_b = encode(lines_b)
    distance = Levenshtein.distance(seq_a, seq_b)
    longest = max(len(seq_a), len(seq_b))
    return 1.0 - distance / longest if longest else 1.0


def extract_functions(source: str) -> dict[str, str] | None:
    """Map qualified function name -> source text for a Python module.

    Returns ``None`` if the source does not parse (so callers can mark the
    function level as unavailable for that file).
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None

    functions: dict[str, str] = {}

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualname = f"{prefix}{child.name}"
                segment = ast.get_source_segment(source, child)
                if segment is not None:
                    functions[qualname] = segment
                visit(child, f"{qualname}.")
            elif isinstance(child, ast.ClassDef):
                visit(child, f"{prefix}{child.name}.")
            else:
                visit(child, prefix)

    visit(tree, "")
    return functions


# --------------------------------------------------------------------------- #
# Per-instance computation
# --------------------------------------------------------------------------- #
def commented_files(instance: dict) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for comment in instance.get("reference_review_comments", []):
        path = comment.get("path") if isinstance(comment, dict) else None
        if path and path not in seen:
            paths.append(path)
            seen.add(path)
    return paths


def reconstruct(base_text: str | None, patch_files: dict[str, str], path: str) -> str:
    """Post-patch content of ``path``: apply its diff, or keep base if untouched."""
    if path in patch_files:
        return apply_file_diff(base_text, patch_files[path])
    return base_text or ""


def compute_instance_rows(
    instance_id: str,
    instance: dict,
    result: dict,
    label: str,
    provider: BaseContentProvider,
) -> tuple[list[dict], list[dict], bool]:
    """Return (file_rows, function_rows, repo_available) for one instance."""
    repo = instance.get("repo", "")
    base_commit = instance.get("base_commit", "")
    if provider.repo_path(repo) is None:
        return [], [], False

    human_files = split_patch_by_file(instance.get("merged_patch", ""))
    agent_files = split_patch_by_file(get_agent_patch(result))

    file_rows: list[dict] = []
    function_rows: list[dict] = []

    for path in commented_files(instance):
        base_text = provider.get(repo, base_commit, path)
        human_text = reconstruct(base_text, human_files, path)
        agent_text = reconstruct(base_text, agent_files, path)

        file_rows.append(
            {
                "instance_id": instance_id,
                "repo": repo,
                "label": label,
                "file_path": path,
                "bleu": round(bleu_score(human_text, agent_text), 4),
                "edit_similarity": round(edit_similarity(agent_text, human_text), 4),
                "human_changed": int(path in human_files),
                "agent_changed": int(path in agent_files),
                "identical": int(human_text == agent_text),
            }
        )

        if not path.endswith(".py"):
            continue
        base_funcs = extract_functions(base_text or "")
        human_funcs = extract_functions(human_text)
        agent_funcs = extract_functions(agent_text)
        if human_funcs is None or agent_funcs is None:
            continue
        base_funcs = base_funcs or {}

        def changed(funcs: dict[str, str]) -> set[str]:
            return {name for name, src in funcs.items() if src != base_funcs.get(name)}

        human_changed = changed(human_funcs)
        agent_changed = changed(agent_funcs)
        touched = sorted(human_changed | agent_changed)
        for qualname in touched:
            human_src = human_funcs.get(qualname, "")
            agent_src = agent_funcs.get(qualname, "")
            function_rows.append(
                {
                    "instance_id": instance_id,
                    "repo": repo,
                    "label": label,
                    "file_path": path,
                    "function": qualname,
                    "bleu": round(bleu_score(human_src, agent_src), 4),
                    "edit_similarity": round(edit_similarity(agent_src, human_src), 4),
                    "in_human": int(qualname in human_funcs),
                    "in_agent": int(qualname in agent_funcs),
                    "human_changed": int(qualname in human_changed),
                    "agent_changed": int(qualname in agent_changed),
                }
            )

    return file_rows, function_rows, True


# --------------------------------------------------------------------------- #
# Over-edit (how much the agent changed beyond the human's gt patch)
# --------------------------------------------------------------------------- #
def changed_line_multisets(base_text: str | None, target_text: str) -> tuple[Counter, Counter]:
    """Lines changed going base -> target, as (added, removed) content multisets.

    Content-based (not position-based) so two patches that touch the same lines
    at different offsets still compare equal. A "replace" counts on both sides.
    """
    base_lines = (base_text or "").splitlines()
    target_lines = (target_text or "").splitlines()
    added: Counter = Counter()
    removed: Counter = Counter()
    matcher = difflib.SequenceMatcher(a=base_lines, b=target_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            removed.update(base_lines[i1:i2])
        if tag in ("replace", "insert"):
            added.update(target_lines[j1:j2])
    return added, removed


def count_diff_lines(file_diff_text: str) -> int:
    """Number of added + removed lines in a single-file unified diff."""
    total = 0
    for line in file_diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            total += 1
        elif line.startswith("-") and not line.startswith("---"):
            total += 1
    return total


def compute_over_edit(instance: dict, result: dict, provider: BaseContentProvider) -> dict | None:
    """How many lines the agent edited beyond the human's gt patch.

    The gt patch (``merged_patch``) is restricted to the hunks in files a human
    reviewer commented on. On those files the agent's changed lines (vs base) are
    compared, content-wise, against the human's changed lines; any agent change
    not made by the human is an *over-edit*. Edits the agent made in files the
    human never commented on are pure over-edits and are reported separately.

    Returns aggregated counts over the instance, or None if the repo is missing.
      gt_edit_lines     : human changed lines (added+removed) on commented files
      agent_edit_lines  : agent changed lines on commented files
      over_edited_lines : agent changed lines on commented files NOT in the gt
      extra_file_lines  : agent changed lines in non-commented files
      extra_files       : count of non-commented files the agent touched
    """
    repo = instance.get("repo", "")
    base_commit = instance.get("base_commit", "")
    if provider.repo_path(repo) is None:
        return None

    human_files = split_patch_by_file(instance.get("merged_patch", ""))
    agent_files = split_patch_by_file(get_agent_patch(result))
    commented = commented_files(instance)
    commented_set = set(commented)

    gt_edit_lines = agent_edit_lines = over_edited_lines = 0
    for path in commented:
        base_text = provider.get(repo, base_commit, path)
        human_text = reconstruct(base_text, human_files, path)
        agent_text = reconstruct(base_text, agent_files, path)
        human_added, human_removed = changed_line_multisets(base_text, human_text)
        agent_added, agent_removed = changed_line_multisets(base_text, agent_text)

        gt_edit_lines += sum(human_added.values()) + sum(human_removed.values())
        agent_edit_lines += sum(agent_added.values()) + sum(agent_removed.values())
        # Multiset difference: agent changes the human did not make.
        over_edited_lines += sum((agent_added - human_added).values())
        over_edited_lines += sum((agent_removed - human_removed).values())

    extra_file_lines = 0
    extra_files = 0
    for path, file_diff in agent_files.items():
        if path in commented_set:
            continue
        lines = count_diff_lines(file_diff)
        if lines:
            extra_files += 1
            extra_file_lines += lines

    return {
        "gt_edit_lines": gt_edit_lines,
        "agent_edit_lines": agent_edit_lines,
        "over_edited_lines": over_edited_lines,
        "extra_file_lines": extra_file_lines,
        "extra_files": extra_files,
    }


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def average(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def format_average(value: float | None, digits: int = 4) -> str:
    return MISSING if value is None else f"{value:.{digits}f}"


def summarize(
    labels: list[str],
    file_rows: list[dict],
    function_rows: list[dict],
    coverage: dict[str, tuple[int, int]],
) -> list[tuple[str, ...]]:
    def by_label(rows: list[dict], label: str, key: str) -> list[float]:
        return [row[key] for row in rows if row["label"] == label]

    rows: list[tuple[str, ...]] = []
    rows.append(
        ("Instances scored", *(str(coverage.get(label, (0, 0))[0]) for label in labels))
    )
    rows.append(
        ("Instances skipped (no repo)", *(str(coverage.get(label, (0, 0))[1]) for label in labels))
    )
    rows.append(("Files scored", *(str(len(by_label(file_rows, label, "bleu"))) for label in labels)))
    rows.append(
        ("File BLEU (avg)", *(format_average(average(by_label(file_rows, label, "bleu"))) for label in labels))
    )
    rows.append(
        (
            "File edit-sim (avg)",
            *(format_average(average(by_label(file_rows, label, "edit_similarity"))) for label in labels),
        )
    )
    rows.append(
        ("Functions scored", *(str(len(by_label(function_rows, label, "bleu"))) for label in labels))
    )
    rows.append(
        ("Function BLEU (avg)", *(format_average(average(by_label(function_rows, label, "bleu"))) for label in labels))
    )
    rows.append(
        (
            "Function edit-sim (avg)",
            *(format_average(average(by_label(function_rows, label, "edit_similarity"))) for label in labels),
        )
    )
    return rows


def format_table(headers: list[str], rows: list[tuple[str, ...]]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def fmt(row: tuple[str, ...]) -> str:
        return " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row))

    separator = "-+-".join("-" * width for width in widths)
    return "\n".join([fmt(tuple(headers)), separator, *(fmt(row) for row in rows)])


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "result_dirs",
        nargs="*",
        type=Path,
        default=DEFAULT_RESULT_DIRS,
        help="Result directories holding agent patches (default: the configured agent dirs)",
    )
    parser.add_argument("--labels", nargs="+", help="Short labels for the result directories")
    parser.add_argument("--dataset-file", type=Path, default=DATASET_FILE)
    parser.add_argument("--repos-dir", type=Path, default=DEFAULT_REPOS_DIR, help="Directory of local git checkouts")
    parser.add_argument("--output-dir", type=Path, default=None, help="Where to write CSVs (default: first result dir)")
    args = parser.parse_args()

    result_dirs = args.result_dirs
    if args.labels:
        labels = args.labels
    elif result_dirs == DEFAULT_RESULT_DIRS:
        labels = SHORT_LABELS
    else:
        labels = [path.name for path in result_dirs]
    if len(labels) != len(result_dirs):
        parser.error(f"Expected {len(result_dirs)} labels, got {len(labels)}.")
    if len(set(labels)) != len(labels):
        parser.error("Labels must be unique.")

    dataset = load_dataset(args.dataset_file)
    provider = BaseContentProvider(args.repos_dir)

    all_file_rows: list[dict] = []
    all_function_rows: list[dict] = []
    coverage: dict[str, tuple[int, int]] = {}

    for result_dir, label in zip(result_dirs, labels, strict=True):
        index = load_result_index(result_dir)
        scored = 0
        skipped = 0
        for instance_id, result in index.items():
            instance = dataset.get(instance_id)
            if instance is None:
                continue
            file_rows, function_rows, repo_available = compute_instance_rows(
                instance_id, instance, result, label, provider
            )
            if not repo_available:
                skipped += 1
                continue
            scored += 1
            all_file_rows.extend(file_rows)
            all_function_rows.extend(function_rows)
        coverage[label] = (scored, skipped)
        print(f"{label}: scored {scored} instances, skipped {skipped} (no local repo)")

    if provider.missing_repos:
        print(
            f"WARNING: {len(provider.missing_repos)} repos not found under {args.repos_dir} "
            f"(instances using them were skipped)."
        )

    output_dir = args.output_dir or result_dirs[0]
    file_csv = output_dir / "patch_similarity_file.csv"
    function_csv = output_dir / "patch_similarity_function.csv"
    write_csv(
        file_csv,
        all_file_rows,
        ["instance_id", "repo", "label", "file_path", "bleu", "edit_similarity",
         "human_changed", "agent_changed", "identical"],
    )
    write_csv(
        function_csv,
        all_function_rows,
        ["instance_id", "repo", "label", "file_path", "function", "bleu", "edit_similarity",
         "in_human", "in_agent", "human_changed", "agent_changed"],
    )

    summary_rows = summarize(labels, all_file_rows, all_function_rows, coverage)
    table = format_table(["Metric", *labels], summary_rows)

    print()
    print(f"Wrote {len(all_file_rows)} file rows to {file_csv}")
    print(f"Wrote {len(all_function_rows)} function rows to {function_csv}")
    print()
    print("Patch similarity vs human merged_patch (commented files only)")
    print(table)

    summary_csv = output_dir / "patch_similarity_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Metric", *labels])
        writer.writerows(summary_rows)


if __name__ == "__main__":
    main()
