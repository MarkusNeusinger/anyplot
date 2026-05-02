# Regen Oldest Spec (Local-Friendly)

> Single-spec, single-library-per-invocation regen flow. Designed to stay well under local-model context budgets
> (e.g. Gemma 3 26B at 256k) by doing exactly **one** thing per invocation and persisting state in `.regen-plan.md`
> at repo root. Restart Claude Code anytime — the next `/regen` resumes from where you left off.
>
> Functionally a local-model alternative to the GitHub `daily-regen.yml` workflow: produces the same per-library
> PRs with `quality:{N}` + `ai-approved`/`quality-poor` labels, so `impl-merge.yml` still handles squash-merge,
> GCS staging→production, and `impl:{lib}:done` issue labels. No Cloud AI review/repair is dispatched.

## Context

@CLAUDE.md

---

## How it works

`/regen` is **idempotent and resumable**. Each invocation does exactly one of three things — auto-detected from
`.regen-plan.md`:

| State file | Action |
|------------|--------|
| Missing | **Plan mode** — pick the oldest spec, write the checklist, exit |
| Has unchecked `- [ ]` items | **Execute mode** — do the next library, tick it off, exit |
| All items `- [x]` or `- [!]` | **Done mode** — archive the plan, exit |

Re-run `/regen` after each invocation. Per spec, expect ~10 invocations (1 plan + 1 per library + 1 finalize).
Each invocation runs entirely in the lead session — **no agent teams, no parallel agents** — keeping the working
context small.

---

## Step 1: Detect mode

Check whether `.regen-plan.md` exists at repo root.

- **Missing** → go to **Plan mode**.
- **Present** → read it. If any line matches `- [ ] ` (unchecked), go to **Execute mode**. Otherwise **Done mode**.

---

## Plan mode

### 1a. Refresh local main

Previous regen runs may have merged PRs remotely; without refreshing, the oldest-spec query below would read
stale local metadata and could re-pick a spec that was just completed. Fetch first; if the user is on `main`,
fast-forward it.

```bash
git fetch origin main
if [ "$(git symbolic-ref --short HEAD 2>/dev/null)" = "main" ]; then
  git pull --ff-only origin main
fi
```

**Branch caveat:** the picker below reads metadata YAML from `git show origin/main:…` rather than the working
tree, so the result is independent of which branch is checked out — even if the local checkout has stale
plots/ files, the oldest-spec selection reflects the current `main`. Step 2j also bases each worktree on
`origin/main`, so the PR base is always current.

### 1b. Pick the oldest spec

```bash
SPEC_INFO=$(uv run python -c "
import subprocess
from datetime import datetime, timezone
import yaml


def git_show(path: str) -> str:
    return subprocess.check_output(['git', 'show', f'origin/main:{path}'], text=True)


def list_specs():
    out = subprocess.check_output(['git', 'ls-tree', '-d', '--name-only', 'origin/main', 'plots/'], text=True)
    return [line.split('/')[-1] for line in out.splitlines() if line.strip() and not line.endswith('.')]


def list_meta_files(spec):
    try:
        out = subprocess.check_output(
            ['git', 'ls-tree', '--name-only', 'origin/main', f'plots/{spec}/metadata/python/'],
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [line for line in out.splitlines() if line.endswith('.yaml')]

candidates = []
for spec in sorted(list_specs()):
    if spec.startswith('.'):
        continue
    meta_files = list_meta_files(spec)
    if not meta_files:
        continue
    latest = None
    for path in meta_files:
        try:
            d = yaml.safe_load(git_show(path)) or {}
        except Exception:
            continue
        u = d.get('updated') or d.get('created')
        if u and (latest is None or str(u) > str(latest)):
            latest = u
    if latest is None:
        candidates.append((datetime.min.replace(tzinfo=timezone.utc), spec))
        continue
    try:
        dt = datetime.fromisoformat(str(latest).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        candidates.append((dt, spec))
    except Exception:
        continue
candidates.sort()
if candidates:
    dt, name = candidates[0]
    print(f'{name}\t{dt.isoformat()}')
")

SPEC_ID=$(echo "$SPEC_INFO" | cut -f1)
SPEC_LATEST=$(echo "$SPEC_INFO" | cut -f2)
```

If `SPEC_ID` is empty, abort — no eligible specs.

### 1c. List libraries

Scan `plots/$SPEC_ID/implementations/python/` for `*.py` files (excluding `__init__.py`). If empty, abort.

### 1d. Extract spec title

Read the first `# ` heading from `plots/$SPEC_ID/specification.md` → `SPEC_TITLE`.

### 1e. Write `.regen-plan.md`

Use the `Write` tool. Order libraries alphabetically. Only include libraries that actually have a `.py` file.

```markdown
# Regen plan: {SPEC_ID}

- Spec: `{SPEC_ID}`
- Title: `{SPEC_TITLE}`
- Latest implementation update: `{SPEC_LATEST}`
- Plan created: `{ISO 8601 UTC timestamp now}`

## Libraries

- [ ] altair
- [ ] bokeh
- [ ] matplotlib
- ...

## Log
```

### 1f. Report and exit

```
Plan written to .regen-plan.md
- Spec: {SPEC_ID} ({SPEC_TITLE})
- Libraries: {comma-separated list}

Run /regen again to start the first library.
```

Do **not** start working on a library in this invocation. Exit.

---

## Execute mode

### 2a. Read the plan

Read `.regen-plan.md`. Extract:
- `SPEC_ID` from the `- Spec:` line
- `SPEC_TITLE` from the `- Title:` line
- The first unchecked library (`- [ ] {library}`) → `LIBRARY`

### 2b. Read working context (only what's needed)

1. `plots/{SPEC_ID}/specification.md`
2. `plots/{SPEC_ID}/specification.yaml` — for the primary `plot_type` tag
3. `plots/{SPEC_ID}/implementations/python/{LIBRARY}.py`
4. `plots/{SPEC_ID}/metadata/python/{LIBRARY}.yaml` — `review.strengths`, `review.weaknesses`, `review.criteria_checklist`
5. `prompts/library/{LIBRARY}.md` (CRITICAL — follow exactly)
6. `prompts/plot-generator.md`
7. `prompts/quality-criteria.md`

Skip Context7 by default — only consult it if step 2d reveals a clear library-API issue.

### 2c. Modify the implementation

Edit `plots/{SPEC_ID}/implementations/python/{LIBRARY}.py`:

- Comprehensive review across: code quality, data choice, visual design, spec compliance, library feature usage,
  transferability.
- KISS structure: imports → data → plot → save.
- Preserve `review.strengths`, fix `review.weaknesses`.
- **Respect the spec variant:** if `SPEC_ID` contains `basic`, no annotations / trendlines / callouts.
- **No changes for the sake of changes:** if nothing meaningful to improve, leave the code unchanged and proceed.

**Theme-adaptive rendering is mandatory.** `impl-generate.yml` (and `impl-merge.yml` after it) require both
`plot-light.png` AND `plot-dark.png` to exist — the workflow errors out and refuses to merge if either is missing.
The implementation **must** read `ANYPLOT_THEME` (`light` or `dark`) and emit `plot-{THEME}.png` (and
`plot-{THEME}.html` for interactive libs). Mirror the theme-adaptive chrome pattern from `prompts/library/{LIBRARY}.md`:

```python
import os
THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"
# ... apply to background, text, grid, legend chrome
chart.save(f"plot-{THEME}.png")          # not "plot.png"
chart.save(f"plot-{THEME}.html")         # if interactive lib
```

Data colors (Okabe-Ito positions 1–7) **must be identical across both themes**; only chrome flips.

If the spec itself genuinely needs improvement, edit `plots/{SPEC_ID}/specification.md` and note it in the log entry
in step 2k.

### 2d. Generate both theme renders locally

The implementation file is named after its library (e.g. `altair.py`), which **collides with `import altair as alt`**
when run as a script — `sys.path[0]` is the script's directory, so the local file shadows the installed package and
the script crashes (`AttributeError: module 'altair' has no attribute 'X'`). Sidestep by copying the impl into the
preview dir under a non-colliding name and running that copy:

```bash
PREVIEW_DIR="plots/{SPEC_ID}/implementations/python/.regen-preview/{LIBRARY}"

# Always start from a clean slate. If a previous attempt left plot-light.png /
# plot-dark.png behind, the existence checks below would happily pass with
# stale artifacts even when the current code only regenerates one render.
rm -rf "$PREVIEW_DIR"
mkdir -p "$PREVIEW_DIR"
cp "plots/{SPEC_ID}/implementations/python/{LIBRARY}.py" "$PREVIEW_DIR/run_impl.py"

# Render both themes — required by impl-generate.yml / impl-merge.yml
for THEME in light dark; do
  (cd "$PREVIEW_DIR" && MPLBACKEND=Agg ANYPLOT_THEME="$THEME" uv run python run_impl.py)
done
```

After both runs the preview dir must contain at least `plot-light.png` and `plot-dark.png` (interactive libraries
also produce `plot-light.html` + `plot-dark.html`). Up to 3 retries on script failure. After 3 → see "Per-library
failure" below.

### 2e. Lint

```bash
uv run ruff format plots/{SPEC_ID}/implementations/python/{LIBRARY}.py
uv run ruff check --fix plots/{SPEC_ID}/implementations/python/{LIBRARY}.py
```

Fix any unfixable errors manually and re-run.

### 2f. Evaluate the rendered plot (full review, not just a number)

The Cloud AI review pipeline (`impl-review.yml`) is **not** dispatched on regen PRs — `ai-approved` is set
directly. That means the regen flow is the **only** place the metadata's `quality_score` and `review` block
get filled in. Skipping this step leaves the merged metadata with stale or null evaluation data, which
breaks Postgres sync, the catalog UI, and the next regen's "previous review" lookup.

**Open both rendered PNGs** with the `Read` tool and inspect them as you would a Cloud AI review:

```
plots/{SPEC_ID}/implementations/python/.regen-preview/{LIBRARY}/plot-light.png
plots/{SPEC_ID}/implementations/python/.regen-preview/{LIBRARY}/plot-dark.png
```

Cross-check both: data shapes/positions/colors must be identical (Okabe-Ito positions 1–7), only the chrome
(background, text, grid, legend box) flips. If a render breaks (wrong-theme text, missing data, cut-off
content), that's a real defect — fix it before scoring.

Then produce a **full structured evaluation**:

1. **Score every item from `prompts/quality-criteria.md` individually.** All categories: Visual Quality
   (VQ-01…VQ-07), Design Excellence (DE-01…DE-03), Spec Compliance (SC-01…SC-04), Data Quality
   (DQ-01…DQ-03), Code Quality (CQ-01…CQ-05), Library Mastery (LM-01…LM-02). Median total is 72–78 — apply
   the anti-inflation calibration anchors and score caps from `quality-criteria.md`. Don't inflate.

2. **Write a 3–5 sentence `image_description`** describing what the plot actually shows (data shape, colors,
   labels, key visual features, theme chrome). This is the field a future regen will read as "previous
   image description" to decide what to keep.

3. **Distill 3–6 `strengths` and 1–4 `weaknesses`** in concrete, actionable terms (no fluff). Strengths feed
   the "KEEP these" guidance; weaknesses feed "FIX these" on the next regen.

4. **Pick a `verdict`:** `APPROVED` if the score meets the cascading threshold for review 1 (≥ 90) — or for
   subsequent reviews per `quality-criteria.md`. Otherwise `REJECTED`. The PR-label rule in step 2j is
   simpler (`ai-approved` ≥ 50, `quality-poor` < 50) because regen accepts everything that wouldn't be
   auto-failed; the verdict here is the honest assessment.

Print the totals line for the user:

```
VQ: __/30 | DE: __/20 | SC: __/15 | DQ: __/15 | CQ: __/10 | LM: __/10 → TOTAL: __/100
```

If `TOTAL < 90`: identify the 2–3 weakest criteria, fix them in code, re-run 2d–2e, re-evaluate. **Up to 2
repair iterations.** After 2, accept the current evaluation and proceed.

### 2g. Update metadata

Edit `plots/{SPEC_ID}/metadata/python/{LIBRARY}.yaml` to match what `impl-generate.yml` writes (theme-aware preview
URLs under the `python/` segment — legacy single-render `preview_url`/`preview_html` fields must be removed if
present):

| Field | Value |
|-------|-------|
| `language` | `python` (add if missing) |
| `updated` | Current UTC timestamp ISO 8601 |
| `generated_by` | From `CLAUDE_MODEL` env var, or `claude --version`, or detected model name |
| `python_version` | From `uv run python --version` |
| `library_version` | From `uv run python -c "from importlib.metadata import version; print(version('{pip_package}'))"` |
| `quality_score` | The integer total from step 2f (e.g. `87`) — **never `null`**, since no Cloud review runs |
| `preview_url_light` | `https://storage.googleapis.com/anyplot-images/plots/{SPEC_ID}/python/{LIBRARY}/plot-light.png` |
| `preview_url_dark` | `https://storage.googleapis.com/anyplot-images/plots/{SPEC_ID}/python/{LIBRARY}/plot-dark.png` |
| `preview_html_light` | `…/plot-light.html` (interactive libs only — `plotly`, `bokeh`, `altair`, `highcharts`, `pygal`, `letsplot`) — else `null` |
| `preview_html_dark` | `…/plot-dark.html` (same condition) — else `null` |
| `review.image_description` | The 3–5 sentence description from step 2f |
| `review.strengths` | List from step 2f |
| `review.weaknesses` | List from step 2f |
| `review.criteria_checklist` | Per-category breakdown with one entry per criterion ID (`VQ-01`, …, `LM-02`), each with `score`, `max`, `passed`, `comment`. Totals must add up to `quality_score`. |
| `review.verdict` | `APPROVED` or `REJECTED` per step 2f's cascading-threshold judgment |
| `impl_tags`, `created` | **Keep unchanged** |
| Legacy `preview_url`, `preview_html` | **Remove** — replaced by the four `_light`/`_dark` fields |

**Pip-package mapping:** matplotlib→matplotlib, seaborn→seaborn, plotly→plotly, bokeh→bokeh, altair→altair,
plotnine→plotnine, pygal→pygal, highcharts→highcharts-core, letsplot→lets-plot.

### 2h. Update implementation header

Ensure the impl file's docstring is:

```python
""" anyplot.ai
{SPEC_ID}: {SPEC_TITLE}
Library: {LIBRARY} {lib_version} | Python {py_version}
Quality: {SCORE}/100 | Updated: {YYYY-MM-DD}
"""
```

`{SCORE}` is the integer total from step 2f — **must match `quality_score` in the metadata YAML**. Don't leave
`Quality: /100` blank; downstream tooling and humans both read this header.

### 2i. Process and stage images (both themes + responsive variants)

Mirror the `impl-generate.yml` pipeline: optimize each theme PNG in place, then generate the responsive
`plot-{theme}_{400,800,1200}.{png,webp}` + full `plot-{theme}.webp` variants, then upload the entire bundle
to `gs://anyplot-images/staging/{SPEC_ID}/python/{LIBRARY}/` (note the `python/` segment — `impl-merge.yml`
promotes from this exact path to `gs://anyplot-images/plots/{SPEC_ID}/python/{LIBRARY}/`).

```bash
PREVIEW_DIR="plots/{SPEC_ID}/implementations/python/.regen-preview/{LIBRARY}"
STAGING_PATH="gs://anyplot-images/staging/{SPEC_ID}/python/{LIBRARY}"

# Both renders are required — abort if either is missing
[ -f "${PREVIEW_DIR}/plot-light.png" ] || { echo "::error::missing plot-light.png"; exit 1; }
[ -f "${PREVIEW_DIR}/plot-dark.png"  ] || { echo "::error::missing plot-dark.png";  exit 1; }

# Optimize + responsive variants for each theme
for THEME in light dark; do
  uv run python -m core.images process    "${PREVIEW_DIR}/plot-${THEME}.png" "${PREVIEW_DIR}/plot-${THEME}.png"
  uv run python -m core.images responsive "${PREVIEW_DIR}/plot-${THEME}.png" "${PREVIEW_DIR}/"
done

# Upload PNGs + WebPs (originals + responsive) for both themes in one batch
gsutil -m -h "Cache-Control:public, max-age=604800" cp \
  "${PREVIEW_DIR}"/plot-light*.png "${PREVIEW_DIR}"/plot-light*.webp \
  "${PREVIEW_DIR}"/plot-dark*.png  "${PREVIEW_DIR}"/plot-dark*.webp \
  "${STAGING_PATH}/"
gsutil -m acl ch -u AllUsers:R "${STAGING_PATH}/plot-light*" "${STAGING_PATH}/plot-dark*" 2>/dev/null || true

# Interactive libraries also produce HTML for each theme
for THEME in light dark; do
  if [ -f "${PREVIEW_DIR}/plot-${THEME}.html" ]; then
    gsutil -h "Cache-Control:public, max-age=604800" cp \
      "${PREVIEW_DIR}/plot-${THEME}.html" "${STAGING_PATH}/plot-${THEME}.html"
    gsutil acl ch -u AllUsers:R "${STAGING_PATH}/plot-${THEME}.html" 2>/dev/null || true
  fi
done
```

The `acl ch` lines may fail with `Failed to set acl ... ensure you have OWNER-role access` on uniform-IAM
buckets — that's expected, the `|| true` swallows it.

### 2j. Worktree → commit → push → PR

```bash
WORKTREE=".worktrees/{SPEC_ID}-{LIBRARY}"

# Refresh the remote main ref before branching: a previous /regen invocation may have already merged
# its PR via impl-merge.yml, so basing this worktree on stale local `main` would push from outdated
# history (push rejection or merge conflict if two regen'd libraries touch shared spec files).
git fetch origin main
git worktree add -b implementation/{SPEC_ID}/{LIBRARY} "$WORKTREE" origin/main

cp plots/{SPEC_ID}/implementations/python/{LIBRARY}.py \
   "$WORKTREE/plots/{SPEC_ID}/implementations/python/{LIBRARY}.py"
cp plots/{SPEC_ID}/metadata/python/{LIBRARY}.yaml \
   "$WORKTREE/plots/{SPEC_ID}/metadata/python/{LIBRARY}.yaml"
# If you edited the spec in step 2c, also copy:
# cp plots/{SPEC_ID}/specification.md   "$WORKTREE/plots/{SPEC_ID}/specification.md"
# cp plots/{SPEC_ID}/specification.yaml "$WORKTREE/plots/{SPEC_ID}/specification.yaml"

cd "$WORKTREE"
git add plots/{SPEC_ID}/implementations/python/{LIBRARY}.py
git add plots/{SPEC_ID}/metadata/python/{LIBRARY}.yaml
# git add plots/{SPEC_ID}/specification.* if changed

git commit -m "regen({SPEC_ID}): {LIBRARY}"
git push -u origin implementation/{SPEC_ID}/{LIBRARY}

# impl-merge.yml extracts the spec issue number from the literal
# "**Parent Issue:** #N" line in the PR body and uses it to comment on
# the spec issue and add the impl:{library}:done label. Without the
# marker, the PR still merges but those downstream side effects are lost.
SPEC_ISSUE=$(uv run python -c "
import sys, yaml
data = yaml.safe_load(open('plots/{SPEC_ID}/specification.yaml')) or {}
issue = data.get('issue')
print(issue if issue else '', end='')
")
if [ -n "$SPEC_ISSUE" ]; then
  PARENT_LINE="**Parent Issue:** #${SPEC_ISSUE}"
else
  PARENT_LINE=""
fi

PR_URL=$(gh pr create \
  --title "regen({SPEC_ID}): {LIBRARY}" \
  --body "$(cat <<EOF
Locally regenerated **{LIBRARY}** for **{SPEC_ID}**.

Quality: {SCORE}/100
- VQ: {vq}/30 | DE: {de}/20 | SC: {sc}/15 | DQ: {dq}/15 | CQ: {cq}/10 | LM: {lm}/10

${PARENT_LINE}

Generated by \`/regen\` (local model, no Cloud AI review dispatched).
EOF
)")

PR_NUMBER=$(gh pr view --json number -q '.number')
gh pr edit "$PR_NUMBER" --add-label "quality:{SCORE}"
if [ {SCORE} -ge 50 ]; then
  gh pr edit "$PR_NUMBER" --add-label "ai-approved"
else
  gh pr edit "$PR_NUMBER" --add-label "quality-poor"
fi

cd -
git worktree remove "$WORKTREE" --force
git worktree prune
```

### 2k. Tick off and log

Edit `.regen-plan.md`:

- Change `- [ ] {LIBRARY}` to `- [x] {LIBRARY}`
- Append under `## Log`:

```
- {LIBRARY}: PR {PR_URL}, score {SCORE}, label {ai-approved|quality-poor} ({timestamp}){, spec edited if applicable}
```

### 2l. Report and exit

```
{LIBRARY} done — score {SCORE}, PR: {PR_URL}
Remaining: {N} libraries

Run /regen again for the next library.
```

Exit.

### Per-library failure

If any step fails irrecoverably (script won't run after 3 retries, `gh push` rejected, `gsutil` unauthenticated):

1. Append to `## Log`: `- {LIBRARY}: FAILED — {reason} ({timestamp})`
2. Change `- [ ] {LIBRARY}` to `- [!] {LIBRARY}`
3. Clean up: remove the worktree (`git worktree remove ... --force && git worktree prune`) and `.regen-preview/{LIBRARY}/` if they exist
4. Print the failure reason to the user and exit

`- [!]` items are skipped by future invocations. The user can edit them back to `- [ ]` to retry.

---

## Done mode

If no `- [ ]` lines remain:

1. Print final summary: counts of done / failed, list of PR URLs from the log.
2. Move `.regen-plan.md` to `.regen-history/{SPEC_ID}-{YYYYMMDD-HHMMSS}.md` (create directory if needed).
3. Tell the user: `Spec {SPEC_ID} complete. Run /regen to start the next oldest spec.`

Exit.

---

## State file format reference

`.regen-plan.md` (repo root, gitignored):

```markdown
# Regen plan: scatter-basic

- Spec: `scatter-basic`
- Title: `Basic Scatter Plot`
- Latest implementation update: `2025-11-12T08:14:00+00:00`
- Plan created: `2026-05-02T13:50:00Z`

## Libraries

- [x] altair
- [x] bokeh
- [ ] matplotlib       ← next pickup
- [ ] plotly
- [!] highcharts       ← failed, skipped (user can reset to `- [ ]`)

## Log

- altair: PR https://github.com/.../pull/1234, score 88, ai-approved (2026-05-02T14:02:00Z)
- bokeh: PR https://github.com/.../pull/1235, score 91, ai-approved (2026-05-02T14:18:00Z)
- highcharts: FAILED — gsutil not authenticated (2026-05-02T14:31:00Z)
```

The user can:
- `cat .regen-plan.md` — see progress at any time
- `rm .regen-plan.md` — abandon the current plan
- Edit checkboxes manually — re-order, retry failures, skip libraries

---

## Notes

- **No agent teams.** Runs entirely in the lead session. No `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` flag needed.
- **One library per invocation.** Restart-safe: kill Claude Code anytime, the next `/regen` picks up where the plan
  left off.
- **No Cloud AI review.** Each PR carries `quality:{N}` plus `ai-approved` (≥50) or `quality-poor` (<50).
  `impl-merge.yml` still triggers on `ai-approved` (squash-merge, GCS staging→production, `impl:{lib}:done` label,
  `sync-postgres.yml`). Verify nothing fired in the review/repair pipeline:
  ```bash
  gh run list --workflow=impl-review.yml --limit 5
  gh run list --workflow=impl-repair.yml --limit 5
  ```
- **Model-agnostic.** Whatever Claude Code is configured for (default Sonnet, or any local OpenAI/Anthropic-compatible
  endpoint via `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`) is what runs. No code path branches on model.
- **`.gitignore`** must contain `.regen-plan.md`, `.regen-history/`, and `.regen-preview/` (added alongside the
  existing `.update-preview/` and `.worktrees/` entries).

## Usage

```
/regen
```

No arguments. Run repeatedly — once to plan, once per library, once to finalize. Each invocation does exactly one
step.
