# Implement the following plan

Execute the plan below end-to-end, then report what changed.

## Instructions

- Read the entire plan first. Reason through it carefully before touching any code so the steps stay coherent.
- Implement every step in the order given. Do not skip steps or reorder unless the plan turns out to be wrong — in
  that case, stop and explain rather than improvising.
- Default to action: make the changes the plan describes (file edits, new files, scripts) rather than only
  suggesting them. Use parallel tool calls for independent reads/edits.
- Stay within scope. Only change what the plan requires:
  - No drive-by refactors, no extra abstractions, no speculative configurability, no defensive code for impossible
    states. A bug fix doesn't need surrounding cleanup; a feature doesn't need extra knobs.
  - No new comments, docstrings, or type hints on code you didn't touch.
- Run the plan's `Validation Commands` after the implementation steps and fix any failures before finishing.
- If you create temporary helper files or scratch scripts, delete them once the task is done.
- If a step is genuinely blocked (missing context, conflicting requirement, failing tests you didn't introduce),
  stop and ask — do NOT use `--no-verify`, mock data, or hard-coded test values to push through.

## Plan

$ARGUMENTS

## Report

- One concise bullet list of what was implemented (one bullet per plan step actually executed).
- Output of `git diff --stat` to show files and total lines changed.
- Validation commands run and their pass/fail status.
- Any plan steps that were skipped or deviated from, with a one-line reason.
