---
name: resolve-refactoring-comment
description: Resolves code review comments that request structural or style improvements — renaming, extracting constants or methods, simplifying control flow, removing dead code, moving code to the right location, replacing hardcoded values with configurable ones, and improving test structure. Use when given a review comment and diff hunk and the task intent is "refactoring".
---

# Resolve Refactoring Comment

## Task overview

You are given a code review comment on a PR. The diff hunk shows the **PR author's working implementation**. The reviewer's comment explains how it should be **structured or expressed differently**. The code typically does the right thing; the goal is to make it cleaner, more maintainable, or more consistent.

**Inputs:**

| Field | What it contains |
|---|---|
| `review_comment` | The reviewer's structural or style critique |
| `diff_hunk` | The author's working implementation (`-` = before PR, `+` = author's attempt) |
| `file` | The file path relative to the repo root |

> **Key distinction:** Unlike bugfixes, the `+` lines usually represent correct intent. The reviewer is asking for a different *shape* — not a different *behaviour*. Preserve the logic while restructuring.

---

## Workflow

### Step 1 — Identify the structural concern

Determine which category of refactoring the reviewer is requesting:

**Rename for clarity or specificity**
Names that are too generic, ambiguous, or misnamed. Reviewer may propose a specific name, or ask a question that implies one ("what about `X`?").
→ Rename the identifier consistently everywhere it appears in the file (parameter, field, variable, class, method, etc.).

**Replace hardcoded value with a reference or constant**
A literal value (magic number, hardcoded string, embedded config) that should be derived from an existing attribute, computed once, or named.
→ If it never changes: extract to a module-level constant. If it should be user-configurable: add a parameter with a default. If it already exists elsewhere: reference that source instead.

**Use an existing helper or API instead of reimplementing**
The author manually implemented logic that an already-available method/utility handles.
→ Find the existing helper (often mentioned or hinted at by the reviewer) and replace the manual implementation with a call to it.

**Simplify control flow**
Nested `if` that can be flattened, redundant conditions, verbose constructs with idiomatic equivalents.
→ Collapse, deduplicate, or replace with the idiomatic form. Verify the simplified version is logically equivalent.

**Move code to the right location**
Code placed in the wrong file, class, method scope, or position within a method (e.g. initialisation scattered instead of grouped at the top).
→ Move without changing logic. Update all references if needed.

**Extract to a constant, method, or variable**
Inline logic repeated or verbose enough that it deserves a name. Reviewer may say "move this to a variable" or "this deserves a constant".
→ Extract and replace all inlined occurrences with the named form.

**Remove dead or redundant code**
Helpers no longer called, conditions that are always true, temporary scaffolding, workarounds (like `**kwargs` added just to satisfy a type checker) that are no longer needed.
→ Delete and ensure nothing now breaks.

**Improve test structure**
Tests that are too large, fragile, repetitive, or placed in the wrong file.
Common signals: "parametrize these", "simplify the test data", "move this to the right test file", "don't hardcode the entire expected output".
→ Refactor the test: add `@pytest.mark.parametrize`, simplify fixtures, replace full-output assertions with targeted ones, move to the appropriate module.

**Make configurable instead of hardcoded**
A constant that a user might reasonably want to change. Reviewer says "allow users to set this" or "why is this hardcoded?".
→ Promote to a constructor/method parameter with the current value as the default. Guard usage to handle the None/disabled case.

---

### Step 2 — Read the diff hunk for intent and location

The `+` lines show the working version you are restructuring. Extract:
- The intended behaviour (what must be preserved)
- The exact region of the file to change
- The name/value that the reviewer wants restructured

---

### Step 3 — Read the target file

Open the file and understand the surrounding context before making any change:
- For **renames**: find every occurrence of the current name in the file
- For **constant extraction**: confirm the value appears only in this location, or identify all occurrences
- For **using existing helpers**: read the helper's signature and confirm it covers the needed case
- For **code movement**: understand both the source location and destination, and check for any dependencies
- For **test refactoring**: understand the full test method and what it is validating

---

### Step 4 — Implement the restructuring

Principles:
- **Preserve behaviour exactly.** The logic must produce the same results after restructuring.
- **Be consistent.** If you rename something, update every occurrence in the file. If you extract a constant, replace every inline use.
- **Follow existing conventions.** Match the naming style, constant placement, import order, and parameter style already used in the file.
- **If the reviewer proposes a specific name or value**, use it exactly.
- **If the reviewer asks a question**, infer the answer from context and apply it (e.g. "what about `X`?" means rename to `X`).

---

### Step 5 — Self-check

1. Is the behaviour unchanged after restructuring?
2. Is the change consistent — no orphaned references to old names, no duplicate definitions?
3. Does the result follow the conventions used elsewhere in the file?
4. If the reviewer proposed specific wording or a name, did I use it exactly?
5. Did I change only what the reviewer asked for — no unrelated edits?

---

## Key pitfalls

- **Don't change behaviour while restructuring.** Renaming a field must also update all serialisation/deserialisation code that references it. Collapsing a condition must produce the same truth table.
- **Rename everywhere in the file, not just the definition.** A renamed parameter, field, or constant must be updated at all call sites, usages, and docstrings in scope.
- **Reviewer's question implies a directive.** "What about `X`?" or "Is it possible to use `Y`?" is a request to make that change.
- **Check both the source and destination when moving code.** Moving a test to another file means adding necessary imports; moving initialisation to the top of a method means all subsequent code still works.
- **When extracting a constant, remove all inline uses.** Partial extraction (constant defined but inline value still present) is worse than neither.
- **Multi-comment instances.** One instance can have several review comments on different files or aspects — handle each one independently.
