# Spec Validator

## Role

You validate whether a plot specification is complete and follows the simplified template.

## Task

Validate the spec file and provide feedback on missing or problematic elements.

## Input

Markdown specification from `plots/{spec-id}/specification.md`

## Output

```json
{
  "valid": true,
  "spec_id": "scatter-basic",
  "score": 95,

  "sections": {
    "title": {"present": true, "valid": true},
    "description": {"present": true, "valid": true},
    "data": {"present": true, "valid": true},
    "tags": {"present": true, "valid": true},
    "use_cases": {"present": true, "valid": true}
  },

  "issues": [],

  "recommendation": "approve"
}
```

---

## Required Sections

### 1. Title (Critical)

```markdown
# {spec-id}: {Descriptive Title}
```

**Checks**:
- Spec ID present in title
- Descriptive title (not just ID)
- Spec ID format: `{type}-{variant}[-{modifier}]`

### 2. Description (Critical)

```markdown
## Description

2-4 sentences describing what the plot shows, when to use it,
and what makes it useful.
```

**Checks**:
- At least 2 sentences
- Explains what the plot visualizes
- Explains when/why to use it

### 3. Data (Critical)

```markdown
## Data

**Required columns:**
- `column_name` (type) - description

**Example:** *(optional)*
```python
data = pd.DataFrame({...})
```
```

**Checks**:
- Has "Required columns" with at least one column
- Each column has: name, type (numeric/categorical/datetime), description
- Example is optional but if present must be valid Python

**Valid column types**: numeric, categorical, datetime, boolean, string

### 4. Tags (Required)

```markdown
## Tags

scatter, correlation, basic
```

**Checks**:
- At least 2 tags
- Comma-separated

### 5. Use Cases (Required)

```markdown
## Use Cases

- Realistic scenario with domain context
- Another use case
```

**Checks**:
- At least 2 use cases
- Specific and realistic (not generic)

---

## Scoring

| Section | Weight |
|---------|--------|
| title | 25 |
| description | 30 |
| data | 25 |
| tags | 10 |
| use_cases | 10 |

**Score ≥ 80**: Approve
**Score 60-79**: Needs minor fixes
**Score < 60**: Reject

---

## Spec ID Validation

Format: `{type}-{variant}[-{modifier}]`

**Valid Types**:
scatter, line, bar, histogram, box, violin, heatmap, pie, area, contour, 3d, network, treemap, sankey, candlestick, radar, funnel, waterfall

**Valid Variants**:
basic, grouped, stacked, horizontal, multi, animated, interactive, regression, correlation, distribution

**Examples**:
- `scatter-basic` ✓
- `bar-grouped-horizontal` ✓
- `heatmap-correlation` ✓
- `pie-basic` ✓

---

## Rules

- **Strict on Critical Sections**: Title, Description, Data must be complete
- **Simple is Better**: Short, focused specs are preferred
- **AI Decides Details**: Quality criteria, parameters, styling are handled by central prompts
- **Constructive**: Always provide concrete improvement suggestions
