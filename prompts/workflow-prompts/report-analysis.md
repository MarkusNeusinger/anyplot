# Report Analysis Prompt

Analyzes user-submitted issue reports and provides structured feedback.

## Task

Validate and structure a user-submitted issue report for an existing plot specification or implementation.

## Input

From the issue body, extract:
- **spec_id**: The specification ID (e.g., `scatter-basic`, `qrcode-basic`)
- **target**: "Specification" or "Implementation"
- **library**: The library name (if implementation issue)
- **category**: Visual, Data, Functional, or Other
- **description**: User's description of the issue

## Input Validation (Security)

**CRITICAL:** Before using any user-supplied values in commands, validate them:

1. **spec_id** must match pattern `^[a-z0-9-]+$` (lowercase letters, numbers, hyphens only)
2. **library** must be one of: `matplotlib`, `seaborn`, `plotly`, `bokeh`, `altair`, `plotnine`, `pygal`, `highcharts`, `letsplot`

If validation fails → post comment explaining invalid input, close issue, STOP.

## Validation Steps

1. **Validate spec_id format:**
   - Must match `^[a-z0-9-]+$`
   - If invalid → post comment, close issue, STOP

2. **Verify spec exists:**
   - Check if directory `plots/{spec_id}/` exists
   - If not found → post comment, close issue, STOP

3. **If implementation issue, verify library exists:**
   - Check if file `plots/{spec_id}/implementations/{language}/{library}.py` exists
   - If not found → post comment, close issue, STOP

4. **Read relevant files:**
   - `plots/{spec_id}/specification.md`
   - `plots/{spec_id}/metadata/{language}/{library}.yaml` (if impl)

5. **Analyze the issue:**
   - Is this a legitimate issue or misunderstanding?
   - Does the described problem match what's in the spec/metadata?
   - What might be the root cause?

## Output Format

Post a comment with this structure:

```markdown
## Report Analysis

**Specification:** `{spec_id}`
**Target:** {Specification / Implementation ({library})}
**Category:** {Visual / Data / Functional / Other}

### Problem Summary
{AI-structured version of the user's description - clear, concise, 2-3 sentences}

### Analysis
{Assessment of the issue:
- Is this a valid issue?
- What might be causing it?
- Brief technical insight if applicable}

### Recommended Action
- **Spec update needed:** {Yes/No} - {brief reason}
- **Regeneration needed:** {Yes/No} - {which libraries if yes}

---
**Next:** Add `approved` label when ready to fix.
```

## Label Updates

After posting the comment, update labels:

1. **Remove:** `report-pending`
2. **Add:** `report-validated`
3. **Add target label:**
   - For spec issues: `report:spec`
   - For impl issues: `report:impl` AND `report:impl:{library}`
4. **Add category label** (if category was selected):
   - Visual → `category:visual`
   - Data → `category:data`
   - Functional → `category:functional`
   - Other → `category:other`
   - If no category selected → skip category label

## Title Update

Update the issue title to format: `[{spec_id}] {brief description}`

Example: `[qrcode-basic] QR code not scannable`

Keep the description under 60 characters. Only use the validated spec_id.

## Important Notes

- Do NOT add the `approved` label
- Do NOT trigger any fix workflows
- Keep analysis concise but informative
- Be objective - some reports may be user misunderstandings
- If the issue is unclear, ask for clarification instead of closing
