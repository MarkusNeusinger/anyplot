# Workflow Scripts

Reusable Python utilities for GitHub Actions workflows.

## Modules

### `workflow_utils.py`
Branch and issue parsing functions used across multiple workflows.

```python
from automation.scripts.workflow_utils import (
    extract_branch_info,    # Parse auto/{spec-id}/{library} branches
    extract_sub_issue,      # Extract sub-issue from PR body
    extract_parent_issue,   # Extract parent issue with fallback
    get_attempt_count,      # Count ai-attempt-X labels
    is_valid_library,       # Validate library name
)
```

### `label_manager.py`
Label operations and status transitions.

```python
from automation.scripts.label_manager import (
    get_status_transition,  # Calculate label changes for status
    get_quality_label,      # Get quality:* label for score
    get_quality_transition, # Calculate quality label changes
    is_approved,            # Check for ai-approved label
    is_rejected,            # Check for ai-rejected label
    get_current_status,     # Get current status from labels
    LabelChange,            # Dataclass with to_gh_args() method
)
```

### `workflow_cli.py`
CLI interface for use in GitHub Actions shell steps.

### `regen_gate.py`
Regen gate (stdlib, plus PyYAML for `context`): `context` writes the previous
review with stable weakness ids `W1..Wn` (used by `impl-generate.yml` and
`impl-review.yml`), `decide` turns the review's `review_regen.json` into
`merge` or `keep` with a reason code and, with `--record-out`, a gate record
(scores, counts, codes, provenance — no model-written text); `marker` turns
that record into the `<!-- regen-gate-record:v1 … -->` line both PR comments
carry, and `parse_record_markers` reads back only records that pass
`validate_record` (version 1, a known verdict, a code from `REASON_CODES`).
`sanitize-source` hides the predecessor's header score from the reviewer; with
`--pending` it resets the new file's header to `Quality: pending`
(`impl-generate.yml`). Both rewrite only a whole generated header line in the
first 15 lines, never a line that merely mentions a score. `impl-review.yml`
runs a copy taken from its own ref. `parse_characteristics` reads the spec's
characteristic bullets as `C1..Cn` (wrapped lines joined),
`characteristic_kind` reads each bullet's kind, and an improvement that cites
an `Expected, not a defect:` bullet is not counted.

### `review_provenance.py`
Review provenance (stdlib): `criteria-version` prints the rules version — git
blob ids of `prompts/quality-criteria.md`, `ai-quality-review.md`,
`default-style-guide.md` and the library prompt, as
`qc-….aqr-….sg-….lib-…` — plus the `prompts/` tree id; `model` reads the
resolved model id from the claude-code-action execution file (first
`system`/`init` message only) and prints an empty id when the file doesn't name
one, never the alias. `impl-review.yml` writes both into the metadata's
`review` block (an empty value removes the key) and the gate record (`n/a`).

### `spec_characteristics_lint.py`
Lint for the closing `## What a good version looks like` section of
`plots/*/specification.md`. Standard library only; it imports the parser from
`regen_gate.py`, so the lint and the gate read the same bullets. CI
(`ci-tests.yml`, "Run Tests") and spec-create run it with the runner's `python3`.

```bash
# Parser contract, blocking: exit 1 on any ::error
python3 -m automation.scripts.spec_characteristics_lint contract --all
# House style, warnings only: exit 0
python3 -m automation.scripts.spec_characteristics_lint style plots/scatter-basic/specification.md
# House style with the hard rules as errors (the backfill): exit 1 on any ::error
python3 -m automation.scripts.spec_characteristics_lint style --strict plots/scatter-basic/specification.md
```

### `review_retest.py`
Review retest harness (stdlib, plus PyYAML for the manifest and Pillow/numpy
for `freeze`'s pixel statistics), driven by `.github/workflows/review-retest.yml`:
`plan` and `bundle` (prep job), `materialize` and `collect` (one review cell,
run from a copy outside the workspace), `report` (aggregate job), plus the
local `validate` (the manifest; `--check-git` the pinned sources,
`--check-renders` every render's canvas from its PNG header, no download),
`gate-report` (production gate records from PR comments) and `freeze`
(builds and, with `--execute`, uploads a frozen set). A cell records the
resolved model id or `null`, with the alias apart as `model_alias`. On a
resume, `plan` reuses a cell only when its record matches the arm (set,
harness version, action pin, rules commit, spec source, the cell's model),
and `report` merges exactly the cells `plan` reused. An
overlaid `regen_gate.py` from the rules under test only receives the
`context`, `sanitize-source` and `decide` flags it has had since `02e1a7974`;
the header reset, the characteristic kinds and marker parsing come from the
harness's own copy. How to run it: `docs/workflows/review-retest.md`.

### `review_retest_metrics.py`
The retest's metrics as pure functions (no IO): per-criterion spread and
flips, totals, verdict straddle, weakness-topic agreement (taxonomy
`topics-v1`), named-defect and false-alarm rates, gate calibration and order
bias, arm comparison with a seeded bootstrap, and the gate monitor. Metrics
group by resolved model; a cell whose session named none is grouped as
`unresolved (<alias>)`. Improvement counts follow the gate record: `visible`
never includes a cited permission, which is counted apart.

### `close_issue_if_complete.py`
Closes a spec issue once every supported library is `impl:<lib>:done` or
`:failed`. Shared by `impl-merge.yml` and the kept-regen branch of
`impl-review.yml`.

### `spec_pr_guard.py`
Fail-closed file allowlist for the spec PR that the merge job in `spec-create.yml`
merges: the diff of the PR head against its merge base with `main` may only add or
modify `plots/{spec-id}/specification.md`, `specification.yaml`, and `.gitkeep`
placeholders, as regular 100644 files. Standard library only; the merge job runs it
with the runner's `python3`.

```bash
python3 automation/scripts/spec_pr_guard.py --spec-id scatter-basic --head <40-char sha>
# exit 0 = clean, 1 = violations (one per line), 2 = could not decide
```

## Usage in Workflows

### Option 1: Direct CLI (Recommended)

```yaml
- name: Extract branch info
  id: branch_info
  run: |
    INFO=$(uv run python -m automation.scripts.workflow_cli extract-branch "$BRANCH")
    echo "spec_id=$(echo $INFO | jq -r '.spec_id')" >> $GITHUB_OUTPUT
    echo "library=$(echo $INFO | jq -r '.library')" >> $GITHUB_OUTPUT

- name: Get attempt count
  id: attempts
  run: |
    LABELS=$(gh pr view $PR_NUM --json labels -q '.labels[].name' | tr '\n' ',')
    COUNT=$(uv run python -m automation.scripts.workflow_cli get-attempt-count "$LABELS")
    echo "count=$COUNT" >> $GITHUB_OUTPUT

- name: Update status labels
  run: |
    LABELS=$(gh pr view $PR_NUM --json labels -q '.labels[].name' | tr '\n' ',')
    ARGS=$(uv run python -m automation.scripts.workflow_cli status-transition "$LABELS" "testing")
    if [ -n "$ARGS" ]; then
      gh pr edit $PR_NUM $ARGS
    fi
```

### Option 2: Inline Python

```yaml
- name: Extract sub-issue
  id: sub_issue
  run: |
    SUB_ISSUE=$(uv run python -c "
    from automation.scripts.workflow_utils import extract_sub_issue
    result = extract_sub_issue('''$PR_BODY''')
    print(result if result else '')
    ")
    echo "number=$SUB_ISSUE" >> $GITHUB_OUTPUT
```

## CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `extract-branch` | Parse auto branch | `extract-branch auto/scatter-basic/matplotlib` |
| `extract-sub-issue` | Get sub-issue from PR body | `extract-sub-issue "Sub-Issue: #42"` |
| `extract-parent-issue` | Get parent issue | `extract-parent-issue "Parent: #100"` |
| `get-attempt-count` | Count attempts | `get-attempt-count "ai-attempt-1,testing"` |
| `status-transition` | Get label change args | `status-transition "generating" "testing"` |
| `quality-label` | Get quality label | `quality-label 95` |

## Benefits

1. **Testability** - 69 unit tests cover all functions
2. **Consistency** - Same parsing logic across all workflows
3. **Maintainability** - Fix bugs in one place
4. **Documentation** - Clear docstrings and examples
