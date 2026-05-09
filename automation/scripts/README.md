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
