"""Build data.json for the comment viewer (viewer/index.html).

usage: python viewer/build_viewer_data.py viewer/data.json path/to/testgen_combined
GT_TESTGEN_DIR holds <instance_id>/result.json with the ground-truth tests (e.g. testgen_combined).
Model tests come from agents_results/results_testgen_<model>.
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path
R = Path(__file__).resolve().parent.parent  # repo root
GT = Path(sys.argv[2])
sys.path.insert(0, str(R))
from classify_validation_tests import classify_python, classify_js  # repo's structural/behavioural classifier
MODELS = {'sonnet': 'claude_sonnet_4.6', 'plus': 'qwen_3.6_plus', 'flash': 'qwen_3.6_flash'}
OUT_MAX = 2500
DIFF_MAX = 4000
# REFINER (task + validation test) agent run per backbone
RUNS = {
    'sonnet': 'claude_with_task_and_validation_test',
    'plus': 'pure_qwen_3.6_plus_with_task_and_validation_test',
    'flash': 'pure_qwen_3.6_flash_with_task_and_validation_test',
}

def cut(s, n): s = s or ''; return s if len(s) <= n else s[:n] + f'\n… [truncated {len(s)-n} chars]'
def file_diff(patch, path):
    # pull the section of a unified diff that touches `path`
    parts = re.split(r'(?m)^(?=diff --git )', patch or '')
    return ''.join(p for p in parts if p.startswith('diff --git') and f' b/{path}' in p.split('\n',1)[0])
def load(p):
    return json.loads(p.read_text()).get('results', []) if p.exists() else []
def match(entries, text, i, ok_only=False):
    # match by exact comment text (indices differ between result sets); fall back to index
    hits = [e for e in entries if e.get('comment_text') == text and (e.get('success') or not ok_only)]
    hits = hits or [e for e in entries if str(e.get('comment_index')) == str(i) and not ok_only and not e.get('comment_text')]
    return hits[0] if hits else None

def kind(code, file):
    if not code: return None, None
    return (classify_python if not file.endswith(('.js', '.ts')) else classify_js)(code)

def with_kind(t):
    if t: t['kind'], t['kind_why'] = kind(t['test'], t['file'])
    return t

def gt_test(e):
    return e and {'test': e.get('test_code', ''), 'file': (e.get('test_file') or '').split('/')[-1],
                  'before': e.get('before_passed'), 'after': e.get('after_passed'), 'ok': bool(e.get('success')),
                  'attempts': e.get('attempts_used'),
                  'before_out': cut(e.get('before_output'), OUT_MAX), 'after_out': cut(e.get('after_output'), OUT_MAX)}
def model_test(e):
    if not e: return None
    a = e.get('assessment') or {}
    return {'test': e.get('test_code', ''), 'file': (e.get('test_file') or '').split('/')[-1],
            'before': e.get('current_passed'), 'after': a.get('ground_truth_patch_passed'),
            'ok': a.get('current_fails_and_patch_passes'), 'attempts': e.get('attempts_used'),
            'before_out': cut(e.get('current_output'), OUT_MAX), 'after_out': cut(a.get('ground_truth_patch_output'), OUT_MAX)}

def split_vt_diff(path):
    """validation_tests.diff (diff -ru original/ current/) -> {test filename: per-file diff}."""
    if not path.exists(): return {}
    out = {}
    for part in re.split(r'(?m)^(?=diff -ru )', path.read_text()):
        m = re.match(r'diff -ru \S+/(\S+) ', part)
        if m: out[m.group(1)] = part if part.endswith('\n') else part + '\n'
    return out

def apply_diff(code, diff):
    """Apply a unified diff to `code` with patch(1); None if it does not apply."""
    with tempfile.TemporaryDirectory() as t:
        src, dst = Path(t, 'src'), Path(t, 'dst')
        src.write_text(code)
        r = subprocess.run(['patch', '-s', '-f', '-o', str(dst), str(src)], input=diff, text=True, capture_output=True)
        return dst.read_text() if r.returncode == 0 else None

def finalize(t, diff):
    # replace the generated test with the agent's revised (final) version
    if not t or not diff: return t
    final = apply_diff(t['test'] or '', diff)
    if final is None:
        t['revise_failed'], t['revise_diff'] = True, diff
    else:
        t['test'], t['revised'] = final, True
    return t

def run_outcome(path, text, i):
    # resolved = the ground-truth test passed on the agent's patch
    if not path.exists(): return None
    data = json.loads(path.read_text())
    e = match(data.get('results', []), text, i)
    if not e: return None
    ga = data.get('groundtruth_assessment')
    if ga:
        g = match(ga.get('results', []), text, i)
        resolved = g.get('passed') if g else None
    else:
        resolved = e.get('resolved')
    return {'resolved': resolved, 'own_test': e.get('validation_final_passed'),
            'revised': e.get('validation_test_revised'), 'intent': e.get('edit_intent'),
            'error': e.get('error'), 'diff': cut(e.get('agent_diff'), DIFF_MAX),
            'vt_diff': split_vt_diff(path.parent/'validation_tests.diff').get(e.get('validation_test_file'))}

out = []
for line in open(R/'dataset/instances.jsonl'):
    d = json.loads(line); iid = d['instance_id']
    gv = R/'agents_results/results_gt_validation_splitted'/iid/'result.json'
    if not gv.exists(): continue
    keep = {r['comment_index'] for r in json.loads(gv.read_text()).get('results', [])}
    gt = load(GT/iid/'result.json')
    models = {k: load(R/f'agents_results/results_testgen_{v}'/iid/'result.json') for k, v in MODELS.items()}
    for i, c in enumerate(d['reference_review_comments']):
        if i not in keep: continue
        ge = match(gt, c['text'], i, ok_only=True)
        tests = {'gt': with_kind(gt_test(ge))}
        refiner = {m: run_outcome(R/'agents_results'/r/iid/'result.json', c['text'], i) for m, r in RUNS.items()}
        tests.update({k: with_kind(finalize(model_test(match(m, c['text'], i)), (refiner[k] or {}).pop('vt_diff', None)))
                      for k, m in models.items()})
        out.append({
            'id': iid, 'ci': i, 'repo': d['repo'], 'pr': d['pull_number'], 'title': d['title'],
            'lang': d['language'], 'type': (ge or {}).get('comment_type'),
            'difficulty': d['metadata'].get('difficulty'), 'domain': d['metadata'].get('problem_domain'),
            'path': c['path'], 'line': c['line'], 'oline': c['original_line'],
            'sline': c['start_line'], 'osline': c['original_start_line'],
            'text': c['text'], 'hunk': cut(c['diff_hunk'], 20000),
            'fix': cut(file_diff(d['merged_patch'], c['path']), 15000),
            'tests': tests,
            'refiner': refiner,
        })
assert len(out) == 483, len(out)
for m in RUNS:
    print(f"REFINER {m}: resolved {sum(1 for o in out if (o['refiner'][m] or {}).get('resolved'))}/{sum(1 for o in out if o['refiner'][m])}", file=sys.stderr)
for k in ['gt', *MODELS]:
    have = [o['tests'][k] for o in out if o['tests'][k]]
    print(f"{k:7s} tests {len(have):3d}  fail-before&pass-after {sum(1 for t in have if t['ok']):3d}  "
          f"revised {sum(1 for t in have if t.get('revised')):3d}  revise-failed {sum(1 for t in have if t.get('revise_failed'))}  "
          f"structural {sum(1 for t in have if t['kind'] == 'structural'):3d}  behavioural {sum(1 for t in have if t['kind'] == 'behavioural'):3d}", file=sys.stderr)
Path(sys.argv[1]).write_text(json.dumps(out, separators=(',', ':')))
