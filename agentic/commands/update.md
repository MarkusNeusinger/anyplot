# Update Implementation

> Local interactive workflow for updating plot implementations. Spawns per-library Opus agents that modify, regenerate,
> and preview plots in parallel. The lead coordinates iteration based on user feedback and handles shipping (GCS upload,
> git branch, PR, review trigger).

## Context

@CLAUDE.md
@pyproject.toml

## Instructions

You are the **update-lead**. Your job is to coordinate a team of per-library updater agents, present results to the
user, iterate on feedback, and ship the final changes.

**Prerequisite**: This command uses agent teams (experimental). Ensure `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set
in your environment or Claude Code settings.

---

### Phase 1: Parse & Setup

Parse `$ARGUMENTS` using this format:

```
/update {spec-id} [{libraries}] [{description}]
/update {issue-url-or-number}
```

**Argument parsing rules:**

1. **Issue URL or `#N` number**: If the first argument is a GitHub URL containing `/issues/` or starts with `#`, run
   `gh issue view {number} --json title,body,labels` to extract:
    - `spec_id`: from issue body or labels (look for `spec:` label prefix or spec-id mention)
    - `libraries`: from issue body or labels (look for `impl:` label prefix or library mentions)
    - `description`: from issue title and body
2. **Normal arguments**: First arg is `spec_id`. Second arg (if comma-separated list of known libraries) is the library
   filter. Everything after is the `description`.
3. **Known libraries**: `matplotlib`, `seaborn`, `plotly`, `bokeh`, `altair`, `plotnine`, `pygal`, `highcharts`,
   `letsplot`
4. **Default libraries**: If no libraries specified, scan `plots/{spec_id}/implementations/` for existing `*.py` files (
   excluding `__init__.py`) — update all that exist.

**Validation:**

- Confirm `plots/{spec_id}/` exists (abort with helpful message if not)
- Confirm `plots/{spec_id}/specification.md` exists
- Confirm at least one implementation exists for the requested libraries
- List which libraries will be updated and ask user to confirm before proceeding

**Read specification once**: Read `plots/{spec_id}/specification.md` — you'll pass context to agents.

---

### Phase 2: Spec Optimization

The lead performs this directly (no extra agent). This ensures agents work against a high-quality spec.

1. **Read references**: Read `plots/{spec_id}/specification.md`, `plots/{spec_id}/specification.yaml`,
   `prompts/templates/specification.md`, `prompts/templates/specification.yaml`, and `prompts/spec-tags-generator.md`.

2. **Analyse the spec** against these dimensions:

   | Dimension | What to check |
   |-----------|---------------|
   | **Wording** | Description clear and concise? Applications realistic? Data fields include types and sizes? Notes actionable? |
   | **Missing sections** | All sections from `prompts/templates/specification.md` present? |
   | **Tag completeness** | All 4 tag dimensions (`plot_type`, `data_type`, `domain`, `features`) have at least 1 value? |
   | **Tag quality** | Naming conventions (lowercase, hyphens)? Values from recommended vocabulary in `prompts/spec-tags-generator.md`? Missing obvious tags? |
   | **Tag accuracy** | Do existing tags actually match the spec content? |

3. **Present numbered suggestions** to the user (e.g., "1. Add `time-series` to data_type tags", "2. Clarify data size in Data section").
   If the spec looks good, say so and move on.

4. **User responds** with one of:
   - `all` — apply all suggestions
   - `1,3` — apply only listed suggestions
   - `none` or `skip` — skip spec optimization, proceed as-is
   - Custom feedback — apply the user's specific instructions

5. **Apply accepted changes** to `specification.md` and/or `specification.yaml`, then proceed to Phase 3.

   > If any changes were made to `specification.md` or `specification.yaml` (tags, wording, etc.), update the `updated` field in `specification.yaml` to the current UTC timestamp in ISO 8601 format (e.g., `2026-02-15T10:30:00Z`).

---

### Phase 3: Create Team & Spawn Agents

1. **Create team**: `TeamCreate` with name `update-{spec_id}`

2. **Create one task per library**: Use `TaskCreate` with:
    - Subject: `Update {library} implementation for {spec_id}`
    - Description: Include spec_id, library, and the user's description

3. **Spawn one `general-purpose` opus agent per library** via `Task` tool with:
    - `team_name`: `update-{spec_id}`
    - `name`: `{library}`
    - `subagent_type`: `general-purpose`
    - `model`: `opus`
    - The **library agent prompt** (see below), with `{SPEC_ID}`, `{LIBRARY}`, `{DESCRIPTION}`, `{CONTEXT7_LIBRARY}`,
      `{PLOT_TYPE}`, and `{SPEC_TITLE}` filled in

   **Template variable reference** (lead must fill these):

   | Variable | Source |
   |----------|--------|
   | `{SPEC_ID}` | From Phase 1 parse |
   | `{LIBRARY}` | Current library name |
   | `{DESCRIPTION}` | User's description |
   | `{CONTEXT7_LIBRARY}` | Mapped library name for Context7 (see mapping below) |
   | `{PLOT_TYPE}` | Primary `plot_type` tag from `specification.yaml` |
   | `{SPEC_TITLE}` | Title from `specification.md` |

   **Context7 library name mapping:**

   | Library | Context7 name |
   |---------|---------------|
   | `matplotlib` | `matplotlib` |
   | `seaborn` | `seaborn` |
   | `plotly` | `plotly` |
   | `bokeh` | `bokeh` |
   | `altair` | `altair` |
   | `plotnine` | `plotnine` |
   | `pygal` | `pygal` |
   | `highcharts` | `highcharts-core` |
   | `letsplot` | `lets-plot` |

4. **Assign tasks immediately after spawning** — For each agent, call `TaskUpdate` with `owner: "{library}"` on the
   corresponding task right after spawning it. Do NOT skip this step — if tasks are left unassigned, agents will
   create their own duplicate tasks, leading to orphaned entries in the task list.

All agents run in parallel — each only touches its own library's files. Agents must NOT create files outside
their designated directories (see file containment rules in the agent prompt).

---

### Phase 4: Collect & Present

Agents report back via `SendMessage` (auto-delivered to you). Agents may report either **completed work** (`STATUS: done`) or **a conflict** (`STATUS: conflict`). Once all agents have reported:

1. **Handle conflicts first.** If any agent reports a conflict:
   - Present the conflict to the user clearly: which rule/spec is violated, what the agent suggests as alternatives
   - Ask the user to decide:
     - **Adjust the request** to comply with existing rules
     - **Update the rule or spec** — the user tells you which file to edit and how, you make the edit, then tell the agent to proceed
     - **Override** — explicitly tell the agent to proceed despite the conflict
   - Send the user's decision to the agent via `SendMessage`. The agent will then continue with Step 3.

2. **Present a summary to the user** for each library that completed successfully:
   - What was changed (bullet points from agent)
   - **Preview:** `{absolute path}/plots/{spec_id}/implementations/.update-preview/{library}/plot.png` (use the absolute path reported by the agent in its `IMAGE:` field — display it on its own line so terminal emulators render it as a clickable link)
   - Agent's quality score with category breakdown and number of local repair iterations
   - Any spec changes the agent made

   **After the summary**, create before/after comparison images and open them:

   a. **Download current GCS images** for each library:
   ```bash
   curl -sL "https://storage.googleapis.com/pyplots-images/plots/{spec_id}/{library}/plot.png" \
     -o "plots/{spec_id}/implementations/.update-preview/{library}/before.png"
   ```
   If curl fails (non-zero exit or empty file), the library has no previous version — pass `none` as before_path.

   b. **Create comparison images** for each library:
   ```bash
   uv run python -m core.images compare \
     plots/{spec_id}/implementations/.update-preview/{library}/before.png \
     plots/{spec_id}/implementations/.update-preview/{library}/plot.png \
     plots/{spec_id}/implementations/.update-preview/{library}/comparison.png \
     {spec_id} {library}
   ```
   If the before image doesn't exist, use `none` instead of the before path:
   ```bash
   uv run python -m core.images compare \
     none \
     plots/{spec_id}/implementations/.update-preview/{library}/plot.png \
     plots/{spec_id}/implementations/.update-preview/{library}/comparison.png \
     {spec_id} {library}
   ```

   c. **Open comparisons in eog** (instead of raw plot.png files):
   ```bash
   eog plots/{spec_id}/implementations/.update-preview/*/comparison.png &
   ```
   Run this via `Bash` tool with `run_in_background: true` so it doesn't block the conversation.

3. **Ask the user for feedback.** They can:
   - Give per-library feedback (e.g., "matplotlib looks good, seaborn needs more contrast")
   - Say **"ship"**, **"ok"**, **"looks good"**, or **"passt"** to proceed to shipping
   - Say **"abort"** to cancel everything

---

### Phase 5: Iterate

For per-library feedback:

1. Send the feedback to the specific idle teammate via `SendMessage` (e.g., to `seaborn`). This wakes them up.
2. The agent runs its conflict check again (Step 2) on the new feedback. If it detects a conflict, it reports back with `STATUS: conflict` instead of making changes — handle as in Phase 4.
3. If no conflict, the agent re-modifies, re-generates, reports back, and goes idle again.
4. Present updated results to the user.
5. Repeat until the user approves.

---

### Phase 6: Ship

**Only proceed when the user explicitly approves shipping.**

The lead handles all shipping directly (no delegation to teammates):

#### 6a. Code Quality

Run ruff format and check **sequentially first**, before any parallel version-info commands.
If parallel Bash calls are used and one fails, all sibling calls get cancelled — so always run ruff alone.

```bash
uv run ruff format plots/{spec_id}/implementations/*.py
uv run ruff check --fix plots/{spec_id}/implementations/*.py
```

If there are unfixable errors, fix them manually and re-run. The agents should have already run ruff in their
lint step, but this is a safety net.

#### 6b. Update Metadata YAML

For each updated library, edit `plots/{spec_id}/metadata/{library}.yaml`:

| Field             | Value                                                                     |
|-------------------|---------------------------------------------------------------------------|
| `updated`         | Current UTC timestamp in ISO 8601 (e.g., `2026-02-10T14:30:00+00:00`)     |
| `generated_by`    | Get from `CLAUDE_MODEL` env var, or detect via `claude --version` / model name |
| `python_version`  | Get from `uv run python --version`                                        |
| `library_version` | Get from `uv run python -c "from importlib.metadata import version; print(version('{package}'))"` where `{package}` is the pip package name (see mapping table below) |
| `quality_score`   | Set to `null` (CI review will fill this)                                  |
| All other fields  | **Keep unchanged** (including `review`, `impl_tags`, `preview_url`, etc.) |

**Library → Pip Package Mapping:**

| Library | Pip Package Name |
|---------|-----------------|
| matplotlib | `matplotlib` |
| seaborn | `seaborn` |
| plotly | `plotly` |
| bokeh | `bokeh` |
| altair | `altair` |
| plotnine | `plotnine` |
| pygal | `pygal` |
| highcharts | `highcharts-core` |
| letsplot | `lets-plot` |

#### 6c. Update Implementation Header

For each updated library, ensure the implementation file starts with:

```python
""" pyplots.ai
{spec_id}: {Title from specification}
Library: {library} {lib_version} | Python {py_version}
Quality: /100 | Updated: {YYYY-MM-DD}
"""
```

#### 6d. Copy Final Images

For each library, copy the preview images to the implementations directory for GCS upload:

```bash
cp plots/{spec_id}/implementations/.update-preview/{library}/plot.png plots/{spec_id}/implementations/plot.png
# Process images (optimization)
uv run python -m core.images process \
  plots/{spec_id}/implementations/plot.png \
  plots/{spec_id}/implementations/plot.png
```

Note: Since we process one library at a time for GCS upload, handle sequentially.

#### 6e. GCS Staging Upload

For each library:

```bash
STAGING_PATH="gs://pyplots-images/staging/{spec_id}/{library}"

# Upload PNG
gsutil cp plots/{spec_id}/implementations/plot.png "${STAGING_PATH}/plot.png"
gsutil acl ch -u AllUsers:R "${STAGING_PATH}/plot.png" 2>/dev/null || true

# Upload HTML if it exists (interactive libraries: plotly, bokeh, altair, highcharts, pygal, letsplot)
if [ -f "plots/{spec_id}/implementations/.update-preview/{library}/plot.html" ]; then
  gsutil cp "plots/{spec_id}/implementations/.update-preview/{library}/plot.html" "${STAGING_PATH}/plot.html"
  gsutil acl ch -u AllUsers:R "${STAGING_PATH}/plot.html" 2>/dev/null || true
fi
```

Update `preview_url` in the metadata YAML to point to the **production** URL
(matching `impl-generate.yml` — production URLs are set from the start, `impl-merge.yml` promotes
GCS files from staging to production on merge):

- `preview_url`: `https://storage.googleapis.com/pyplots-images/plots/{spec_id}/{library}/plot.png`

#### 6f. Clean Up Preview Directory

```bash
rm -rf plots/{spec_id}/implementations/.update-preview
```

#### 6g. Per-Library Branches, PRs & Reviews

**IMPORTANT:** The review pipeline (`impl-review.yml`) extracts `SPEC_ID` and `LIBRARY` from the branch name
pattern `implementation/{spec-id}/{library}`. Therefore, each library MUST get its own branch and PR.

Get `{owner}/{repo}` from `git remote get-url origin`.

**Why worktrees?** The main working tree contains modifications to ALL libraries (and potentially from other
parallel `/update` instances for different specs). Using `git stash`/`git checkout` would conflict with parallel
instances sharing the same stash stack and HEAD. `git worktree` creates an isolated working copy per branch —
each has its own HEAD, index, and working tree. Only the specific library's files are copied in, making it
physically impossible to accidentally commit another spec's changes.

**Step 1: For each library, create worktree → copy files → commit → push → PR**

Run sequentially for each library:

```bash
WORKTREE=".worktrees/{spec_id}-{library}"

# Create worktree with new branch based on main
git worktree add -b implementation/{spec_id}/{library} "$WORKTREE" main

# Copy only this library's changed files into the worktree
cp plots/{spec_id}/implementations/{library}.py "$WORKTREE/plots/{spec_id}/implementations/{library}.py"
cp plots/{spec_id}/metadata/{library}.yaml "$WORKTREE/plots/{spec_id}/metadata/{library}.yaml"
# If spec was changed (only for the first library):
cp plots/{spec_id}/specification.md "$WORKTREE/plots/{spec_id}/specification.md"
cp plots/{spec_id}/specification.yaml "$WORKTREE/plots/{spec_id}/specification.yaml"

# Commit and push from the worktree
cd "$WORKTREE"

git add plots/{spec_id}/implementations/{library}.py
git add plots/{spec_id}/metadata/{library}.yaml
# If spec was changed (only in first library branch):
git add plots/{spec_id}/specification.md
git add plots/{spec_id}/specification.yaml

git commit -m "update({spec_id}): {library} — {short description}

{description}"

git push -u origin implementation/{spec_id}/{library}

# Create PR (gh works in worktree context)
gh pr create \
  --title "update({spec_id}): {library} — {short description}" \
  --body "$(cat <<EOF
## Summary

Updated **{library}** implementation for **{spec_id}**.

**Changes:** {description}

### Changes
{bullet points of changes from agent}
- Quality: {score}/100 (after {N} local repair iterations)
  - VQ: {vq}/30 | DE: {de}/20 | SC: {sc}/15 | DQ: {dq}/15 | CQ: {cq}/10 | LM: {lm}/10

## Test Plan

- [x] Preview images uploaded to GCS staging
- [x] Implementation file passes ruff format/check
- [x] Metadata YAML updated with current versions
- [ ] Automated review triggered

---
Generated with [Claude Code](https://claude.com/claude-code) \`/update\` command
EOF
)"

# Trigger review for this PR
PR_NUMBER=$(gh pr view --json number -q '.number')
gh api repos/{owner}/{repo}/dispatches \
  -f event_type=review-pr \
  -f 'client_payload[pr_number]='"$PR_NUMBER"

# Return to repo root
cd -
```

**Step 2: Clean up worktrees**

After all libraries are processed:

```bash
# Remove each worktree
git worktree remove .worktrees/{spec_id}-{library} --force

# After all worktrees removed, prune stale entries
git worktree prune
```

Report all PR URLs to the user.

---

### Phase 7: Monitor Pipeline

After shipping PRs, shut down agents and clean up the team immediately — repairs are handled by the CI pipeline
(`impl-repair.yml`), not locally. The lead monitors progress until all PRs reach a terminal state.

#### 7a. Shut Down Team

Immediately after Phase 6 completes:

1. `SendMessage` with type `shutdown_request` to all agents
2. Wait for all agents to confirm shutdown
3. `TeamDelete` to clean up the team
4. Clean up preview directory:
   ```bash
   rm -rf plots/{spec_id}/implementations/.update-preview
   ```

#### 7b. Poll PR Status

Build a tracking table: `{library} → {pr_number, score, status}` where status is one of: `reviewing`, `approved`,
`repairing`, `merged`, `rejected`, `failed`, `not-feasible`.

Present the summary table to the user.

Poll every **90 seconds** using `gh pr view` for each PR:

```bash
gh pr view {pr_number} --json state,labels,mergedAt
```

Extract status from labels: `ai-approved`, `ai-rejected`, `quality:{score}`, `quality-poor`, `not-feasible`,
`ai-attempt-{N}`.

Update the table and inform the user when any status changes.

**How the CI repair pipeline works:**
- `impl-review.yml` scores the PR. If score < 90, it adds `ai-rejected` label.
- `impl-repair.yml` auto-triggers on `ai-rejected`: reads review feedback, runs Claude to fix, pushes, re-triggers review.
- Up to 3 attempts. After attempt 3: score >= 50 → `ai-approved` and merge; score < 50 → PR closed + `not-feasible`.
- `impl-merge.yml` auto-triggers on `ai-approved`: squash-merges, creates metadata, promotes GCS images.

**Exit conditions**: all PRs are `merged`, `not-feasible`, or closed — OR user says `abort`.

#### 7c. Handle Pipeline Failures

Only intervene if the CI pipeline itself fails (not for normal rejections — those are handled by `impl-repair.yml`).

**Stalled PRs** — if a PR shows no label changes for ~10 minutes:

1. Check workflow run status:
   ```bash
   gh run list --workflow=impl-review.yml --branch=implementation/{spec_id}/{library} --limit 1 --json status,conclusion
   gh run list --workflow=impl-repair.yml --branch=implementation/{spec_id}/{library} --limit 1 --json status,conclusion
   ```

2. If a workflow run failed, read logs:
   ```bash
   gh run view {run_id} --log-failed
   ```

3. Report the failure reason to the user and ask how to proceed:
   - **Re-trigger**: `gh api repos/{owner}/{repo}/dispatches -f event_type=review-pr -f 'client_payload[pr_number]='"$PR_NUM"`
   - **Skip**: move on, leave PR open for manual handling
   - **Abort**: stop monitoring entirely

#### 7d. Final Report

Once all PRs have reached a terminal state:

1. Present final summary table:

   | Library | PR | Quality Score | Attempts | Status |
   |---------|-----|--------------|----------|--------|
   | matplotlib | #1234 | 92 | 2 | merged |
   | seaborn | #1235 | 94 | 1 | merged |
   | pygal | #1236 | 45 | 3 | not-feasible |

2. Report any `not-feasible` libraries to the user — these may need manual intervention or a different approach.

3. Pull main to sync the merged changes:
   ```bash
   git checkout main
   git pull origin main
   ```
   This ensures the working tree is clean and up-to-date with all merged PRs.

---

## Library Agent Prompt

Use this prompt when spawning each per-library agent. Replace `{SPEC_ID}`, `{LIBRARY}`, `{DESCRIPTION}`,
`{CONTEXT7_LIBRARY}`, `{PLOT_TYPE}`, and `{SPEC_TITLE}` with actual values (see Phase 3 template variable reference).

---

You are **{LIBRARY}** on the `update-{SPEC_ID}` team. Your job is to update the {LIBRARY} implementation for
**{SPEC_ID}**.

**Task:** {DESCRIPTION}

### Step 1: Read Context

Read these files to understand what you're working with:

1. `plots/{SPEC_ID}/specification.md` — the specification (what the plot should show)
2. `plots/{SPEC_ID}/implementations/{LIBRARY}.py` — current implementation to update
3. `plots/{SPEC_ID}/metadata/{LIBRARY}.yaml` — review feedback from last review:
    - `review.strengths` — PRESERVE these (don't break what works)
    - `review.weaknesses` — FIX these
    - `review.criteria_checklist` — items with `passed: false` need fixing
    - `quality_score` — current score to beat
4. `prompts/library/{LIBRARY}.md` — library-specific rules (**CRITICAL**: follow these exactly)
5. `prompts/plot-generator.md` — base generation rules
6. `prompts/quality-criteria.md` — quality scoring criteria
7. **Context7 library documentation** — Query up-to-date library docs for idiomatic patterns:
   - Call `resolve-library-id` with `libraryName: "{CONTEXT7_LIBRARY}"` and `query: "how to create {PLOT_TYPE} chart with {CONTEXT7_LIBRARY}"`
   - Call `query-docs` with the resolved library ID and `query: "idiomatic patterns for creating {SPEC_TITLE} ({PLOT_TYPE}) with {CONTEXT7_LIBRARY}, including best practices for styling and layout"`
   - Use the returned documentation **together with** (not instead of) the static library rules from step 4

If `preview_url` exists in the metadata, view the current preview image to understand what the plot currently looks
like.

### Step 2: Conflict Check

**Before making any changes**, check whether the user's request conflicts with:
- **Generation rules** (`prompts/plot-generator.md`, `prompts/library/{LIBRARY}.md`)
- **Quality criteria** (`prompts/quality-criteria.md`)
- **The specification** (`plots/{SPEC_ID}/specification.md`)

**Common conflict types:**

| Conflict | Example | Rule Source |
|----------|---------|-------------|
| KISS violation | "Add a function to generate data" | `plot-generator.md` |
| Wrong output format | "Save as SVG" | `plot-generator.md` |
| Cross-library plotting | "Use matplotlib in plotnine" | `plot-generator.md` |
| Controversial data | "Use election results as data" | `plot-generator.md` |
| Spec mismatch | "Make it a bar chart" when spec says scatter | `specification.md` |
| Title format | Custom title without spec-id | `plot-generator.md` |
| Library-specific | Violates a rule in library file | `library/{LIBRARY}.md` |

If none of these apply, proceed to Step 3.

If you detect a conflict, **DO NOT proceed with the change.** Instead, report the conflict to `update-lead` via `SendMessage`:

```
LIBRARY: {LIBRARY}
STATUS: conflict

CONFLICT:
The requested change "{specific request}" conflicts with:
- {rule source}: {quote the specific rule}
- Reason: {explain why this is a conflict}

OPTIONS:
1. Adjust the request to: {suggest a compliant alternative}
2. Update the rule/spec to allow this (user must decide)
3. Proceed anyway (user must explicitly override)
```

Then go idle and wait for the lead to relay the user's decision. Only proceed once the conflict is resolved.

### Step 3: Modify Implementation

Edit `plots/{SPEC_ID}/implementations/{LIBRARY}.py`:

- Follow all rules from `prompts/plot-generator.md` and `prompts/library/{LIBRARY}.md`
- KISS structure: imports → data → plot → save
- Preserve review strengths, fix weaknesses
- Address the user's specific request: **{DESCRIPTION}**
- If no specific request was given, perform a comprehensive review across these dimensions:
  1. **Code Quality** — Cleanliness, variable names, unnecessary complexity, helpful comments
  2. **Data Choice** — Realistic data that showcases the plot type well, shows ALL features (e.g., outliers for boxplots, multiple trends for line charts), appropriate ranges/scales
  3. **Visual Design** — Colors, legibility at 4800x2700 canvas, layout balance, grid subtlety, marker sizing for data density
  4. **Spec Compliance** — Point-by-point check against `specification.md`
  5. **Library Feature Usage** (LF-01) — Does the code leverage distinctive library strengths? Basic usage is not enough
  6. **Code Transferability** — Can a user easily adapt this to their own data? Clear separation of data vs. plot logic? Meaningful variable names?
- **Respect the spec variant:** If the spec-id contains `basic`, the plot must stay basic. Do NOT add annotations, trendlines, regression lines, callout boxes, or other embellishments. Basic means clean and simple — storytelling comes from well-chosen data and visual clarity, not added elements.
- **No changes for the sake of changes:** If you find nothing meaningful to improve, report "no improvements needed" and leave the code unchanged. Do not make cosmetic or unnecessary changes just to show activity.

If the specification genuinely needs changes to improve the result, edit `plots/{SPEC_ID}/specification.md` and
explain what you changed and why. Do not edit the spec just for the sake of change.

### Step 4: Generate Locally

Run the implementation to generate the plot image. **IMPORTANT**: Each agent MUST run in its own isolated preview
directory to avoid race conditions with other parallel agents. All agents write `plot.png` — running in the shared
`implementations/` directory causes file conflicts.

**FILE CONTAINMENT RULES — CRITICAL:**
- You may ONLY write files to these locations:
  - `plots/{SPEC_ID}/implementations/{LIBRARY}.py` (the implementation itself)
  - `plots/{SPEC_ID}/implementations/.update-preview/{LIBRARY}/` (preview output directory)
  - `plots/{SPEC_ID}/specification.md` (only if spec changes are needed)
- **NEVER** create files in the project root, the `implementations/` directory directly, or any other location.
- **NEVER** download or save images outside `.update-preview/{LIBRARY}/`. If you need to view the current
  preview from GCS, use the URL directly with `WebFetch` or `Read` — do not download it to a local file.

```bash
mkdir -p plots/{SPEC_ID}/implementations/.update-preview/{LIBRARY}
cd plots/{SPEC_ID}/implementations/.update-preview/{LIBRARY} && MPLBACKEND=Agg uv run python ../../{LIBRARY}.py
```

This runs `{LIBRARY}.py` from the isolated `.update-preview/{LIBRARY}/` directory, so `plot.png` and `plot.html` land
there directly — no copy step needed, no race condition with other agents.

If the script fails, read the error, fix the implementation, and retry. **Up to 3 retries.**

### Step 5: Lint Fix

Run ruff to format and fix lint issues in the implementation before proceeding:

```bash
uv run ruff format plots/{SPEC_ID}/implementations/{LIBRARY}.py
uv run ruff check --fix plots/{SPEC_ID}/implementations/{LIBRARY}.py
```

If `ruff check` reports unfixable errors (exit code 1), read the error output and fix the code manually, then re-run.
Common issue: `B905` requires `zip()` calls to include `strict=True` or `strict=False`.

### Step 6: Process Images

Generate thumbnail and optimize:

```bash
uv run python -m core.images process \
  plots/{SPEC_ID}/implementations/.update-preview/{LIBRARY}/plot.png \
  plots/{SPEC_ID}/implementations/.update-preview/{LIBRARY}/plot.png
```

### Step 7: Quality Evaluation & Local Repair Loop

Before shipping, formally evaluate your implementation against the same criteria CI uses. This catches issues locally
(cheaper) instead of triggering expensive remote repair cycles.

**7a. View the generated image** at `plots/{SPEC_ID}/implementations/.update-preview/{LIBRARY}/plot.png`.

**7b. Score against all 6 quality categories** using the criteria from `prompts/quality-criteria.md` (read in Step 1).
Produce category totals only (no per-criterion notes needed):

```
VQ: __/30 | DE: __/20 | SC: __/15 | DQ: __/15 | CQ: __/10 | LM: __/10 → TOTAL: __/100
```

**Scoring calibration — apply these defaults strictly:**
- DE-01 = 4 (configured default, not exceptional) unless design is genuinely outstanding
- DE-02 = 2 (library defaults, minimal refinement) unless you added intentional polish
- DE-03 = 2 (data displayed, no storytelling) unless visual hierarchy clearly guides the viewer
- LM-01 = 3 (correct but not best patterns) unless you used high-level API expertly
- LM-02 = 1 (generic usage) unless you used a feature distinctive to this library
- **Median implementation scores 72-78, not 90+.** If your total is above 85, re-check — are you inflating?

**Apply score caps** (from quality-criteria.md):
- VQ-02 = 0 (severe overlap) → max 49
- VQ-03 = 0 (invisible elements) → max 49
- SC-01 = 0 (wrong plot type) → max 40
- DQ-02 = 0 (controversial data) → max 49
- DE-01 ≤ 2 AND DE-02 ≤ 2 (generic + no refinement) → max 75
- CQ-04 = 0 (fake functionality) → max 70

**7c. If score ≥ 90** → proceed to Step 8.

**7d. If score < 90** → repair locally (max **2 iterations**, separate from CI's 3 repair attempts after PR submission):
1. Identify the top 2-3 weakest categories/criteria dragging the score down
2. Fix the implementation code to address those specific weaknesses
3. Re-run the implementation (Step 4), re-lint (Step 5), re-process images (Step 6)
4. **Re-read the generated image** and **formally re-score** — produce the full VQ/DE/SC/DQ/CQ/LM breakdown again (fixes can introduce new issues)
5. If score ≥ 90 → proceed to Step 8
6. If score < 90 and iterations < 2 → repeat from substep 1
7. If score < 90 after 2 iterations → proceed to Step 8 anyway with your most recent score (ship to CI for fresh perspective)

### Step 8: Report to Lead

Send a message to `update-lead` via `SendMessage` with:

```
LIBRARY: {LIBRARY}
STATUS: done

CHANGES:
- {bullet point 1}
- {bullet point 2}
- ...

IMAGE: {absolute path to plots/{SPEC_ID}/implementations/.update-preview/{LIBRARY}/plot.png — use pwd to resolve}

QUALITY: {total}/100 (after {N} local repair iterations, 0 = passed first evaluation)
  VQ: {vq}/30 | DE: {de}/20 | SC: {sc}/15
  DQ: {dq}/15 | CQ: {cq}/10 | LM: {lm}/10

SPEC_CHANGES: {none, or describe what you changed in specification.md}

ISSUES: {none, or describe any problems encountered}
```

Then mark your task as completed via `TaskUpdate`.

**After reporting, go idle. The lead will wake you if the user has feedback for revisions.**

If the lead sends you feedback, repeat Steps 2-8 with the new instructions (including the conflict check).

---

## Usage Examples

```
# Update all existing implementations for a spec (no description)
/update area-basic

# Update single library
/update area-basic matplotlib

# Update specific libraries with description
/update area-basic matplotlib,seaborn fix the axis label overlap

# Update from a GitHub issue
/update #3970
/update https://github.com/MarkusNeusinger/pyplots/issues/3970
```
