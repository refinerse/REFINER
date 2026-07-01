---
name: resolve-other-comment
description: Resolves code review comments that do not fit neatly into documentation, bugfix, or refactoring — including restoring accidentally deleted code, removing incorrect or accidental additions, compatibility fixes, over-engineering removal, API surface improvements, and test coverage gaps. Use when given a review comment and diff hunk and the task intent is "other".
---

# Resolve Other Comment

## Task overview

You are given a code review comment that does not fit cleanly into documentation, bugfix, or refactoring. These comments typically identify something **wrong in kind** — the author introduced or removed something they shouldn't have, or the code violates a compatibility constraint, API convention, or project standard.

**Inputs:**

| Field | What it contains |
|---|---|
| `review_comment` | The reviewer's observation — often identifies what should or should not exist |
| `diff_hunk` | The author's change (`-` = before PR, `+` = author's addition/removal) |
| `file` | The file path relative to the repo root |

---

## Workflow

### Step 1 — Identify the nature of the comment

Determine which type of issue the reviewer is raising:

**Restore accidentally removed code**
Code that existed before the PR was deleted without intent. Reviewer asks "was this meant to be removed?" or "this should stay" or "restore this".
→ Put the deleted code back exactly as it was. The `-` lines in the diff show what to restore.

**Remove something that should not exist**
The author added something incorrect, unnecessary, or accidental — a wrong implementation, a backup file, a debug statement, a commented-out block left behind, a redundant field.
→ Delete the addition entirely. Check whether anything else now references it.

**Language version / environment compatibility**
The author used a construct that is not available in all supported environments (e.g. newer syntax, platform-specific behaviour, unsupported library version).
→ Replace with the compatible equivalent. The reviewer usually names the constraint (e.g. "still supports Python 3.8").

**Remove provider-specific or implementation-specific references**
The code names or references a specific vendor, provider, or internal detail in a place that should be generic.
→ Replace with a neutral, generic equivalent. Remove the specific mention from comments, identifiers, and strings.

**Remove over-engineering / unnecessary override**
The author added a custom implementation (e.g. `__init__`, `save`, extra methods) for something that a simpler or existing mechanism already handles.
→ Delete the custom implementation and let the base behaviour take over. Verify the simpler version still achieves the goal.

**Simplify initialisation or defaults**
The author initialised a dictionary or structure by spelling out all defaults explicitly when starting with an empty structure achieves the same result.
→ Replace with the minimal initialisation. The downstream code fills in what it needs.

**Improve type annotation or API surface**
A return type, parameter type, or field declaration is less precise, less idiomatic, or less useful than it should be.
→ Apply the more precise type or declaration the reviewer suggests (e.g. `Optional[X]` instead of `Union[X, None]` or `int | None`).

**Add missing test coverage**
The reviewer asks for a specific edge case or scenario to be tested that the author omitted.
→ Add the test case. Follow the existing test style in the file and cover precisely the scenario the reviewer describes.

**Make test assertions more explicit or robust**
The reviewer asks for a more precise assertion (e.g. specific tolerance, specific output shape, specific key).
→ Tighten the assertion to match what the reviewer specifies.

---

### Step 2 — Read the diff hunk

- `-` lines: what existed before the PR, currently in `/workspace`
- `+` lines: what the author added or changed

For **restoration** tasks, the `-` lines are what to put back.
For **removal** tasks, the `+` lines are what to delete.
For everything else, the hunk gives location and context.

---

### Step 3 — Read the target file

Before acting, read the region around the diff hunk:
- For **removal**: confirm nothing else in the file depends on what you are removing
- For **restoration**: find the right location to reinsert
- For **compatibility fixes**: find all occurrences of the incompatible construct in the file
- For **type/annotation changes**: check how the return value is used and whether the type change propagates

---

### Step 4 — Implement the change

Guiding principles:
- **If the reviewer says to remove something**, remove it fully — don't comment it out or leave a stub
- **If the reviewer says to restore something**, restore it exactly — don't rewrite or simplify it
- **If the reviewer names the compatible alternative**, use that exact form
- **If the reviewer asks for a test case**, match the structure and style of existing tests in the file
- **Follow the reviewer's wording closely** — "was this meant to be deleted?" means restore it; "this is wrong, remove" means delete it

---

### Step 5 — Self-check

1. If restoring: is the restored code in exactly the right location and unchanged from the original?
2. If removing: are there no remaining references to what was deleted?
3. If a compatibility fix: are all instances of the incompatible construct updated, not just one?
4. If a type change: is the declaration and any related import consistent?
5. Did I only change what the reviewer asked for?

---

## Key pitfalls

- **Distinguish "accidentally removed" from "intentionally removed".** Read the reviewer's question carefully. "Was this meant to be removed?" implies restore. "We don't need this anymore" implies delete.
- **Removing something may require import cleanup.** If you delete a class or function, remove its import if it is no longer used.
- **Compatibility fixes must be exhaustive.** If the incompatible syntax appears multiple times in the file, update all occurrences — not just the one in the hunk.
- **Don't add workarounds instead of fixing the underlying issue.** If an override is unnecessary, remove it entirely; don't simplify it into a smaller override.
- **Multi-comment instances.** One instance can have several review comments on different files or concerns — handle each independently.
