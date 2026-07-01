```
cd /data/Documents/crab-dataset2/dataset/my_agent
set -a && source .env && set +a
printf '%s\n' 'Avaiga__taipy-833@24559da' > /tmp/testgen_one.txt
python run_batch_testgen.py \
  --instances-file /tmp/testgen_one.txt \
  --workers 1 \
  --max-attempts 1 \
  --no-resume \
  --output-dir smoke_results_batch
```

python run_batch_testgen.py \
  --instances-file missing_instances/missing_instances_with_vt_sk.txt \
  --workers 12 \
  --max-attempts 5 \
  --max-generation-retries 5 \
  --no-resume 

python merge_testgen_results.py \
  --original-dir results_testgen_merged_success_false \
  --retry-dir results_testgen \
  --output-dir results_testgen_merged_retry_3 \
  --overwrite


python run_batch_testgen.py \
  --comments-file results_testgen_all/failed_success_comments.csv \
  --output-dir results_testgen_retry_success_false \
  --max-attempts 5 \
  --max-generation-retries 5 \
  --workers 4

python "analyze_results_testgen_all.py" --results-dir "results_testgen_all" --output-csv "results_testgen_all/comment_summary.csv" --write-failed-comments "results_testgen_all/failed_success_comments.csv"

python analyze_results_testgen_all.py \
  --results-dir results_testgen_retry_success_false \
  --output-csv results_testgen_retry_success_false/comment_summary.csv \
  --write-failed-comments results_testgen_retry_success_false/failed_success_comments.csv

python analyze_results_testgen_all.py --results-dir results_testgen_all

python merge_testgen_results.py \
  --original-dir results_testgen_all \
  --retry-dir results_testgen_retry_success_false \
  --output-dir results_testgen_merged_success_false \
  --overwrite


python - <<'PY'
import json
from pathlib import Path

ids = set(Path("failed_replay_with_validation_tests.txt").read_text().splitlines())

with open("dataset/instances.jsonl", encoding="utf-8") as src, \
     open("failed_replay_with_validation_tests.instances.jsonl", "w", encoding="utf-8") as dst:
    for line in src:
        if not line.strip():
            continue
        inst = json.loads(line)
        if inst["instance_id"] in ids:
            dst.write(json.dumps(inst, ensure_ascii=False))
            dst.write("\n")
PY

python run_batch_agent_resolution_validation_test.py \
  --dataset-file failed_replay_with_validation_tests.instances.jsonl \
  --validation-test-dir results_testgen_merged_success_false \
  --output-dir results_agent_resolution_validation_test_failed_replay \
  --workers 30

python run_batch_testgen.py \
  --comments-file results_testgen_all/failed_success_comments.csv \
  --output-dir results_testgen_retry_success_false \
  --max-attempts 5 \
  --max-generation-retries 5 \
  --workers 4

python merge_testgen_results.py \
  --original-dir results_testgen_merged_success_false \
  --retry-dir results_testgen_retry_2 \
  --output-dir results_testgen_merged_retry_2 \
  --overwrite


python run_batch_agent_resolution_validation_test.py \
  --dataset-file retry_instances.instances.jsonl \
  --validation-test-dir results_testgen_merged_retry_2 \
  --output-dir results_agent_resolution_validation_test_retry_2 \
  --workers 30


python run_batch_agent_resolution_with_intent.py \
  --workers 30 \
  --intent-file dataset/comment_intent.jsonl
  --output-dir agents_results/agent_resolution_with_skill

python run_agent_resolution_vt_sk.py --instance-id 'sympy__sympy-26515@2c01ca9' --validation-test-dir agents_results/results_testgen_merged_retry_2 
python run_batch_agent_resolution_vt_sk.py --workers 30 --validation-test-dir agents_results/results_testgen_merged_retry_2 
python run_batch_agent_resolution_vt_sk.py --workers 30 --validation-test-dir agents_results/results_testgen_merged_retry_2 --dataset-file retry_instances.instances.jsonl --output-dir results_agent_resolution_vt_sk_retry_26_lose


python run_batch_agent_resolution.py --workers 30 \
--dataset-file missing_instances/missing_instances_pure_qwen.instances.jsonl  \
--output-dir results_agent_resolution_pure_qwen

python run_batch_agent_resolution_validation_test.py --workers 2 \
--dataset-file missing_instances/missing_instances_with_vt.instances.jsonl  \
--validation-test-dir agents_results/results_testgen_merged_retry_2 \
--output-dir agents_results/results_agent_resolution_validation_test_merged

python run_batch_agent_resolution_vt_sk.py --workers 12 \
--validation-test-dir agents_results/results_testgen_merged_retry_3 \
--dataset-file missing_instances/missing_instances_with_vt_sk.instances.jsonl \
--output-dir results_agent_resolution_vt_sk_retry_12_regenerate_tests

python run_batch_agent_resolution_with_intent.py \
--intent-file dataset/comment_intent.jsonl \
--workers 2 \
--dataset-file missing_instances/missing_instances_with_vt.instances.jsonl \
--output-dir agents_results/agent_resolution_with_intent  

python run_batch_agent_resolution_vt_sk.py --workers 30 \
--validation-test-dir agents_results/results_testgen_merged_retry_3 \
--dataset-file missing_instances/missing_instances_with_vt_sk.instances.jsonl \
--output-dir results_agent_resolution_vt_sk_retry_165_fail_new_prompt


python run_batch_agent_resolution_mt_vt_sk.py \
--dataset-file dataset/instances.jsonl \
--validation-test-dir results_agent_testgen_multi \
--output-dir results_agent_resolution_mt_vt_sk_any \
--no-resume --workers 30

python run_batch_agent_resolution_mt_vt_sk_gt_select.py \
--dataset-file dataset/instances.jsonl \
--validation-test-dir results_agent_testgen_multi \
--output-dir results_agent_resolution_mt_vt_sk_gt_select \
--no-resume --workers 30 \
--limit 1

missing_instances/missing_instances_with_mt_vt_sk_gt_select.instances.jsonl

python run_batch_agent_resolution_mt_vt_sk_gt_select.py \
--dataset-file missing_instances/missing_instances_with_mt_vt_sk_gt_select.instances.jsonl \
--validation-test-dir results_agent_testgen_multi \
--output-dir results_agent_resolution_mt_vt_sk_gt_select_retry \
--no-resume --workers 30


python run_batch_agent_resolution.py --workers 30 \
--dataset-file dataset/instances.jsonl  \
--output-dir results_agent_resolution_pure_qwen


missing_instances/missing_instances_with_mt_vt_sk_any.instances.jsonl

python run_batch_agent_resolution_mt_vt_sk.py \
--dataset-file missing_instances/missing_instances_with_mt_vt_sk_any.instances.jsonl \
--validation-test-dir results_agent_testgen_multi \
--output-dir results_agent_resolution_mt_vt_sk_any_retry_3 \
--no-resume --workers 30


python run_batch_agent_resolution_with_intent.py \
  --workers 30 \
  --output-dir agents_results/agent_resolution_with_intent_only

missing_instances/missing_instances_with_intent_only.instances.jsonl

python run_batch_agent_resolution_with_intent.py \
  --workers 30 \
  --dataset-file missing_instances/missing_instances_with_intent_only.instances.jsonl \
  --output-dir agents_results/agent_resolution_with_intent_only_retry


# Judge whether each agent diff resolves its review comment, and (for failing
# acceptance tests) whether the test is too strict. Uses deepseek/deepseek-v4-flash
# via OpenRouter (needs OPENROUTER_API_KEY in .env).

# Dry run: build prompts only, no API calls (for review)
python judge_test_strictness.py --dry-run

# Full run over all comments
python judge_test_strictness.py --workers 16

# Re-judge only the records that failed to parse, merging fixes back in place
# (raise --max-tokens; deepseek spends tokens on reasoning and can truncate JSON)
python judge_test_strictness.py \
  --rerun-parse-failures acceptance_test_strictness/strictness_judgements.jsonl \
  --max-tokens 4096 --workers 12

# Optional: judge only comments whose acceptance test failed
python judge_test_strictness.py --only-failed --workers 16

# Same analysis for other resolution folders. Output is auto-named per folder
# as acceptance_test_strictness/<folder>__strictness_judgements.jsonl.
# Use --schema vt_sk for validation-test results (validation_final_passed/output),
# --schema intent for test_passed/test_output results.

# pure-qwen (reference)
python judge_test_strictness.py --workers 16 \
  --resolution-dir agents_results/results_agent_resolution_pure_qwen_merged --schema intent
python judge_test_strictness.py \
  --rerun-parse-failures acceptance_test_strictness/results_agent_resolution_pure_qwen_merged__strictness_judgements.jsonl \
  --resolution-dir agents_results/results_agent_resolution_pure_qwen_merged --schema intent \
  --max-tokens 4096 --workers 12

# vt_sk (comparison)
python judge_test_strictness.py --workers 16 \
  --resolution-dir results_agent_resolution_vt_sk_merged --schema vt_sk
python judge_test_strictness.py \
  --rerun-parse-failures acceptance_test_strictness/results_agent_resolution_vt_sk_merged__strictness_judgements.jsonl \
  --resolution-dir results_agent_resolution_vt_sk_merged --schema vt_sk \
  --max-tokens 4096 --workers 12

# NOTE: --schema vt_sk reads the per-comment pass/fail from the instance-level
# `groundtruth_assessment` block (the agent SEES the validation test and overfits
# to it, so validation_final_passed is ~99% and meaningless; groundtruth re-runs
# the canonical tests against the agent patch and is the real signal).

# Export the side-by-side comparison table (Markdown to stdout + CSV)
python export_strictness_comparison.py --csv acceptance_test_strictness/comparison.csv

python run_batch_agent_resolution_vt_sk.py \
    --dataset-file dataset/instances.jsonl \
    --validation-test-dir agents_results/results_testgen_merged_retry_3 \
    --intent-file intent_classification/comment_intent_qwen.jsonl \
    --output-dir results_vt_intent \
    --workers 30 > results_vt_intent.log


# =============================================================================
# vt_sk no-test fallback + retry / merge / compare pipeline
# =============================================================================
# Context: results_vt_intent (above) only ran the 464/485 comments that had a
# generated validation test; 21 comments (testgen success=false) were dropped.
# Added a naive intent-only fallback in agent_resolver_vt_sk.py so comments with
# no validation test are still resolved from edit intent (judged by groundtruth).

set -a && source .env && set +a   # LLM keys for testgen

# 1) Re-run test generation for the 21 dropped comments.
#    missing_21_comments.csv: header instance_id,comment_index (the not-run comments).
python run_batch_testgen.py \
  --comments-file missing_21_comments.csv \
  --output-dir results_testgen_retry_4 \
  --max-attempts 5 --max-generation-retries 5 \
  --workers 19 --no-resume

# 2) Merge new tests over the previous testgen set (8/21 recovered).
python merge_testgen_results.py \
  --original-dir agents_results/results_testgen_merged_retry_3 \
  --retry-dir results_testgen_retry_4 \
  --output-dir results_testgen_merged_retry_4 --overwrite

# 3) Re-run the 19 affected instances into results_vt_intent WITH the fallback.
#    (Deleted those 19 result dirs first so resume reprocesses only them while
#     loading the other 320 from disk; summary rebuilt over all 339.)
python run_batch_agent_resolution_vt_sk.py \
  --dataset-file dataset/instances.jsonl \
  --validation-test-dir results_testgen_merged_retry_4 \
  --intent-file intent_classification/comment_intent_qwen.jsonl \
  --testgen-dir testgen_combined \
  --output-dir results_vt_intent \
  --workers 19 > results_vt_intent_fallback_rerun.log

# 4) Best-of retry: re-run a curated list (rerun.txt) into a fresh folder.
#    Build the dataset subset from rerun.txt first:
python - <<'PY'
import json
ids=[l.strip() for l in open("rerun.txt") if l.strip()]
ds={json.loads(l)["instance_id"]: l.strip() for l in open("dataset/instances.jsonl") if l.strip()}
with open("rerun_subset.instances.jsonl","w") as f:
    for i in ids:
        if i in ds: f.write(ds[i]+"\n")
print("wrote", sum(1 for i in ids if i in ds), "instances")
PY

python run_batch_agent_resolution_vt_sk.py \
  --dataset-file rerun_subset.instances.jsonl \
  --validation-test-dir results_testgen_merged_retry_4 \
  --intent-file intent_classification/comment_intent_qwen.jsonl \
  --testgen-dir testgen_combined \
  --output-dir results_vt_intent_rerun \
  --workers 24 --no-resume > results_vt_intent_rerun.log

# 5) Merge current best + new rerun, keeping the higher resolution_rate per
#    instance. Edit results_dirs / new_dir at the top of the script, e.g.
#      results_dirs = ["results_vt_intent", "results_vt_intent_rerun"]
#      new_dir      = "results_vt_intent_merged"
python merge_2_results_folder.py

# 6) Compare vs pure_qwen / with_vt / with_intent_only. Point the with_vt_intent
#    default dir (DEFAULT_RESULT_DIRS) at the merged folder inside the script.
python compare_validation_test_vs_pure_qwen_replay.py