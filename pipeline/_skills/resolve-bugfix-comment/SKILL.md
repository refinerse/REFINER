---
name: resolve-bugfix-comment
description: Resolves code review comments that request bug fixes — logic corrections, robustness improvements, API usage fixes, error message improvements, guard conditions, exception chaining, type/field changes, and test data accuracy. Use when given a review comment and diff hunk and the task intent is "bugfix".
---

# Resolve Bugfix Comment

## Task overview

You are given a code review comment on a PR. The diff hunk shows the **PR author's attempted implementation**. The reviewer's comment explains why it is **wrong, incomplete, or risky**. Your job is to implement a corrected version in the repository mounted at `/workspace`.

**Inputs:**

| Field | What it contains |
|---|---|
| `review_comment` | The reviewer's critique — describes the problem, sometimes the solution |
| `diff_hunk` | The author's attempted code change (`-` = before PR, `+` = author's attempt) |
| `file` | The file path relative to the repo root |

> **Critical:** The diff `+` lines are the *buggy* version under review. Do not apply them. Understand the reviewer's concern and write a corrected implementation.

---

## Workflow

### Step 1 — Diagnose the problem class

Identify what category of issue the reviewer is pointing out:

**Robustness / safety**
The author's code will crash or behave incorrectly under certain inputs or environments. Common signals: "what happens if X is None?", "use try/except", "this could fail when…"
→ Add a guard, a fallback, or wrap in error handling.

**Wrong API / method**
The author used an API that has the wrong semantics, is deprecated, or has side effects the reviewer wants to avoid. Reviewer usually names or links to the correct one.
→ Replace with the API the reviewer specifies. Read both usages to understand the difference.

**Incorrect logic / condition**
The author's condition is redundant, inverted, or misses a case. Reviewer may say "you can drop this", "this isn't right", or ask a pointed question about the logic.
→ Simplify or rewrite the condition. Check whether removing a branch changes behaviour before doing so.

**Error message quality**
The error/warning message is missing useful context (e.g. the actual value, the original exception, a hint on how to fix).
→ Extend the message string. For exception chaining, use `raise X from e` (Python) or the language-equivalent pattern.

**Wrong type / field**
The author used a type with constraints (e.g. max length) when a more flexible type was needed, or used the wrong collection/structure.
→ Swap to the type the reviewer specifies.

**Test/fixture integrity**
The test data is structurally incorrect (e.g. mismatched lengths, wrong reference values), causing the test to pass silently or produce misleading results.
→ Fix the data to be structurally valid and representative.

**Config / setting value**
A configuration key has the wrong value (e.g. severity level, flag, option).
→ Change the value to what the reviewer specifies.

**Compatibility / portability**
The code uses a construct that doesn't work in some environments, language versions, or transpilation targets.
→ Replace with the portable equivalent the reviewer describes.

---

### Step 2 — Read the diff hunk for intent

Even though the `+` lines are wrong, they tell you:
- The **region** of the file to work in
- The **intent** the author was trying to achieve
- What the correct fix needs to accomplish

Use the `-` lines to find the current state in `/workspace`.

---

### Step 3 — Read the target file

Open the file and read the function/block/config section. Before writing any fix:
- Check how similar cases are handled elsewhere in the file — match the pattern
- Check existing imports; the right utility is usually already available
- Understand the scope (function body, class field, config block, etc.)

---

### Step 4 — Implement the fix

Write the minimal change that addresses the reviewer's concern. Guiding principles:

- **If the reviewer names a specific API, pattern, or value** — use it exactly as described
- **If the reviewer asks a "what if" question** — your fix must handle that case
- **If the reviewer says to remove something** — remove it and verify the remaining logic is still correct
- **If the reviewer references an example elsewhere in the codebase** — read that example and follow its pattern
- **Preserve all surrounding code** — only touch what is needed

---

### Step 5 — Self-check

1. Does the fix address the *specific* concern the reviewer raised?
2. Have I handled the edge case or failure mode they described?
3. Is the fix consistent with how similar cases are handled in the same file?
4. Is the surrounding code intact and unaffected?
5. If the reviewer named a specific API/pattern/value, am I using it exactly?

---

## Key pitfalls

- **Don't apply the `+` lines.** They represent the buggy attempt, not the target state.
- **Reviewer describes the problem, not always the solution.** Infer the correct fix from the concern they raise.
- **Look for the specific API or approach the reviewer names or links to.** Use it, don't invent a different one.
- **Check existing imports before adding new ones.** Needed helpers are usually already imported.
- **Minimal edits only.** Avoid refactoring surrounding code.
- **Multi-comment instances.** One instance can have several comments on different files — handle each independently.
