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

If the user is on a non-`main` branch, that's fine — the candidate scan below works against `origin/main`-tracked
files as long as they're checked out, and step 2j explicitly bases each worktree on `origin/main` (not local
`main`), so staleness can't poison the PR base either.

### 1b. Pick the oldest spec

```bash
SPEC_INFO=$(uv run python -c "
from datetime import datetime, timezone
from pathlib import Path
import yaml

candidates = []
for spec_dir in sorted(Path('plots').iterdir()):
    if not spec_dir.is_dir() or spec_dir.name.startswith('.'):
        continue
    meta_dir = spec_dir / 'metadata' / 'python'
    if not meta_dir.is_dir():
        continue
    latest = None
    for yf in meta_dir.glob('*.yaml'):
        try:
            d = yaml.safe_load(yf.read_text(encoding='utf-8')) or {}
        except Exception:
            continue
        u = d.get('updated') or d.get('created')
        if u and (latest is None or str(u) > str(latest)):
            latest = u
    if latest is None:
        candidates.append((datetime.min.replace(tzinfo=timezone.utc), spec_dir.name))
        continue
    try:
        dt = datetime.fromisoformat(str(latest).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        candidates.append((dt, spec_dir.name))
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

If the spec itself genuinely needs improvement, edit `plots/{SPEC_ID}/specification.md` and note it in the log entry
in step 2k.

### 2d. Generate locally

```bash
mkdir -p plots/{SPEC_ID}/implementations/python/.regen-preview/{LIBRARY}
cd plots/{SPEC_ID}/implementations/python/.regen-preview/{LIBRARY} && \
  MPLBACKEND=Agg uv run python ../../{LIBRARY}.py
```

Up to 3 retries on script failure. After 3 failures → see "Per-library failure" below.

### 2e. Lint

```bash
uv run ruff format plots/{SPEC_ID}/implementations/python/{LIBRARY}.py
uv run ruff check --fix plots/{SPEC_ID}/implementations/python/{LIBRARY}.py
```

Fix any unfixable errors manually and re-run.

### 2f. Self-score

View `plots/{SPEC_ID}/implementations/python/.regen-preview/{LIBRARY}/plot.png` and score against the 6 categories
from `prompts/quality-criteria.md`:

```
VQ: __/30 | DE: __/20 | SC: __/15 | DQ: __/15 | CQ: __/10 | LM: __/10 → TOTAL: __/100
```

Apply the calibration defaults and score caps from `quality-criteria.md`. Median is 72-78 — don't inflate.

If `TOTAL < 90`: identify the 2-3 weakest criteria, fix them in code, re-run 2d-2e, re-score. **Up to 2 repair
iterations.** After 2, accept the current score and proceed.

### 2g. Update metadata

Edit `plots/{SPEC_ID}/metadata/python/{LIBRARY}.yaml`:

| Field | Value |
|-------|-------|
| `updated` | Current UTC timestamp ISO 8601 |
| `generated_by` | From `CLAUDE_MODEL` env var, or `claude --version`, or detected model name |
| `python_version` | From `uv run python --version` |
| `library_version` | From `uv run python -c "from importlib.metadata import version; print(version('{pip_package}'))"` |
| `quality_score` | `null` |
| `preview_url` | `https://storage.googleapis.com/anyplot-images/plots/{SPEC_ID}/{LIBRARY}/plot.png` |
| All other fields | **Keep unchanged** (especially `review`, `impl_tags`) |

**Pip-package mapping:** matplotlib→matplotlib, seaborn→seaborn, plotly→plotly, bokeh→bokeh, altair→altair,
plotnine→plotnine, pygal→pygal, highcharts→highcharts-core, letsplot→lets-plot.

### 2h. Update implementation header

Ensure the impl file's docstring is:

```python
""" anyplot.ai
{SPEC_ID}: {SPEC_TITLE}
Library: {LIBRARY} {lib_version} | Python {py_version}
Quality: /100 | Updated: {YYYY-MM-DD}
"""
```

### 2i. Process and stage image

```bash
PREVIEW_DIR="plots/{SPEC_ID}/implementations/python/.regen-preview/{LIBRARY}"
STAGING_PATH="gs://anyplot-images/staging/{SPEC_ID}/{LIBRARY}"

uv run python -m core.images process "${PREVIEW_DIR}/plot.png" "${PREVIEW_DIR}/plot.png"

gsutil cp "${PREVIEW_DIR}/plot.png" "${STAGING_PATH}/plot.png"
gsutil acl ch -u AllUsers:R "${STAGING_PATH}/plot.png" 2>/dev/null || true

if [ -f "${PREVIEW_DIR}/plot.html" ]; then
  gsutil cp "${PREVIEW_DIR}/plot.html" "${STAGING_PATH}/plot.html"
  gsutil acl ch -u AllUsers:R "${STAGING_PATH}/plot.html" 2>/dev/null || true
fi
```

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

PR_URL=$(gh pr create \
  --title "regen({SPEC_ID}): {LIBRARY}" \
  --body "$(cat <<EOF
Locally regenerated **{LIBRARY}** for **{SPEC_ID}**.

Quality: {SCORE}/100
- VQ: {vq}/30 | DE: {de}/20 | SC: {sc}/15 | DQ: {dq}/15 | CQ: {cq}/10 | LM: {lm}/10

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
