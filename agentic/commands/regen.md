# Regen Spec (Local-Friendly)

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

## Usage

```
/regen              # pick the oldest spec
/regen <spec-id>    # use the given spec instead (must exist on origin/main)
```

The slash command only takes a spec id on the **first** invocation (Plan mode). Once `.regen-plan.md` exists,
subsequent invocations resume that plan; the argument is ignored. To switch specs, `rm .regen-plan.md` first.

---

## How it works

`/regen` is **idempotent and resumable**. Each invocation does exactly one of three things — auto-detected from
`.regen-plan.md`:

| State file | Action |
|------------|--------|
| Missing | **Plan mode** — pick (or validate) the spec, write the checklist, exit |
| Has unchecked `- [ ]` items | **Execute mode** — do the next library, tick it off, exit |
| All items `- [x]` or `- [!]` | **Done mode** — archive the plan, exit |

Re-run `/regen` after each invocation. Per spec, expect ~10 invocations (1 plan + 1 per library + 1 finalize).
Each invocation runs entirely in the lead session — **no agent teams, no parallel agents** — keeping the working
context small.

All non-trivial logic lives in the Python helper at `agentic/workflows/modules/regen/`. The steps below call it
via `uv run python -m agentic.workflows.modules.regen <subcommand>`.

---

## Step 1: Detect mode

Check whether `.regen-plan.md` exists at repo root.

- **Missing** → go to **Plan mode**.
- **Present** → read it. If any line matches `- [ ] ` (unchecked), go to **Execute mode**. Otherwise **Done mode**.

---

## Plan mode

### 1a. Refresh local main

The picker reads metadata from the `origin/main` git tree (via `git show`), so a `git fetch` is required first.
If the user happens to be on `main`, fast-forward.

```bash
git fetch origin main
if [ "$(git symbolic-ref --short HEAD 2>/dev/null)" = "main" ]; then
  git pull --ff-only origin main
fi
```

### 1b. Pick (or validate) the spec

```bash
# /regen <spec-id> uses the given spec; bare /regen picks the oldest.
if [ -n "$ARGUMENTS" ]; then
  SPEC_INFO=$(uv run python -m agentic.workflows.modules.regen validate-spec "$ARGUMENTS")
else
  SPEC_INFO=$(uv run python -m agentic.workflows.modules.regen pick-oldest)
fi
SPEC_ID=$(echo "$SPEC_INFO" | cut -f1)
SPEC_LATEST=$(echo "$SPEC_INFO" | cut -f2)
```

If `validate-spec` fails (unknown spec), abort and tell the user.

### 1c. Write the plan

```bash
uv run python -m agentic.workflows.modules.regen write-plan "$SPEC_ID"
```

This single call lists the python implementations, extracts the spec title, and writes `.regen-plan.md` with
all libraries unchecked.

### 1d. Report and exit

Tell the user the plan was written, list the libraries, and ask them to run `/regen` again to start the first
library. Do **not** start working in this invocation.

---

## Execute mode

### 2a. Resolve the next library

```bash
NEXT=$(uv run python -m agentic.workflows.modules.regen next-library)  # exits 2 if none left
SPEC_ID=$(echo "$NEXT" | cut -f1)
SPEC_TITLE=$(echo "$NEXT" | cut -f2)
LIBRARY=$(echo "$NEXT" | cut -f3)
```

### 2b. Read working context (only what's needed)

1. `plots/{SPEC_ID}/specification.md`
2. `plots/{SPEC_ID}/specification.yaml` — for the primary `plot_type` tag and `issue` number
3. `plots/{SPEC_ID}/implementations/python/{LIBRARY}.py`
4. `plots/{SPEC_ID}/metadata/python/{LIBRARY}.yaml` — `review.strengths`, `review.weaknesses`, `review.criteria_checklist`
5. `prompts/library/{LIBRARY}.md` (CRITICAL — follow exactly)
6. `prompts/plot-generator.md`
7. `prompts/quality-criteria.md`

Skip Context7 by default — only consult it if step 2d reveals a clear library-API issue.

**Library Independence — DO NOT read sibling-library files.** This invocation
works on **one** library only. Never open another library's `.py` or `.yaml`
under `plots/{SPEC_ID}/implementations/` or `plots/{SPEC_ID}/metadata/` — not
even "for reference" or "to stay consistent". Each library is its own
interpretation of the spec; copying a sibling's data scenario, color choices,
aspect ratio, or layout makes the catalog show the same chart rendered by
different engines, which is the exact opposite of the catalog's purpose.
See `prompts/plot-generator.md` → "Library Independence" for the full rule.

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
chart.save(f"plot-{THEME}.png")
chart.save(f"plot-{THEME}.html")  # if interactive lib
```

Data colors (Okabe-Ito positions 1–7) **must be identical across both themes**; only chrome flips.

If the spec itself genuinely needs improvement, edit `plots/{SPEC_ID}/specification.md` and note it in the log entry
in step 2g.

### 2d. Render both themes

```bash
uv run python -m agentic.workflows.modules.regen render "$SPEC_ID" "$LIBRARY"
```

This sidesteps the self-import collision (impl named `altair.py` shadows `import altair`) by invoking
`uv run python -P <impl>` — the `-P` flag (Python ≥3.11) keeps the script's directory off `sys.path`, so
`import altair` resolves to the installed package. The impl runs **in place** (we do not copy it), so
`Path(__file__).parents[...]` in highcharts/pygal asset-resolution code keeps working. Cwd is set to
`.regen-preview/{LIBRARY}/` so the artifacts land there. Up to 3 retries per theme; missing `plot-light.png`
or `plot-dark.png` raises and the step exits non-zero. On failure see "Per-library failure" below.

### 2e. Lint

```bash
uv run ruff format plots/$SPEC_ID/implementations/python/$LIBRARY.py
uv run ruff check --fix plots/$SPEC_ID/implementations/python/$LIBRARY.py
```

Fix any unfixable errors manually and re-run.

### 2f. Evaluate the rendered plot (full review, not just a number)

The Cloud AI review pipeline (`impl-review.yml`) is **not** dispatched on regen PRs — `ai-approved` is set
directly. That means the regen flow is the **only** place the metadata's `quality_score` and `review` block
get filled in. Skipping this step leaves the merged metadata with stale or null evaluation data, which
breaks Postgres sync, the catalog UI, and the next regen's "previous review" lookup.

**Open both rendered PNGs** with the `Read` tool and inspect them as you would a Cloud AI review:

```
plots/$SPEC_ID/implementations/python/.regen-preview/$LIBRARY/plot-light.png
plots/$SPEC_ID/implementations/python/.regen-preview/$LIBRARY/plot-dark.png
```

Cross-check both: data shapes/positions/colors must be identical (Okabe-Ito positions 1–7), only the chrome
(background, text, grid, legend box) flips. If a render breaks (wrong-theme text, missing data, cut-off
content), that's a real defect — fix it before scoring.

Then produce a **full structured evaluation**:

1. **Score every item from `prompts/quality-criteria.md` individually.** All categories: Visual Quality
   (VQ-01…VQ-07), Design Excellence (DE-01…DE-03), Spec Compliance (SC-01…SC-04), Data Quality
   (DQ-01…DQ-03), Code Quality (CQ-01…CQ-05), Library Mastery (LM-01…LM-02). Median total is 72–78 — apply
   the anti-inflation calibration anchors and score caps from `quality-criteria.md`. Don't inflate.
2. **Write a 3–5 sentence `image_description`** describing what the plot actually shows.
3. **Distill 3–6 `strengths` and 1–4 `weaknesses`**.
4. **Pick a `verdict`:** `APPROVED` if the score meets the cascading threshold for review 1 (≥ 90) — or for
   subsequent reviews per `quality-criteria.md`. Otherwise `REJECTED`. The PR-label rule is simpler
   (`ai-approved` ≥ 50, `quality-poor` < 50) because regen accepts everything that wouldn't be auto-failed;
   the verdict here is the honest assessment.

Print the totals line for the user:

```
VQ: __/30 | DE: __/20 | SC: __/15 | DQ: __/15 | CQ: __/10 | LM: __/10 → TOTAL: __/100
```

If `TOTAL < 90`: identify the 2–3 weakest criteria, fix them in code, re-run 2d–2e, re-evaluate. **Up to 2
repair iterations.** After 2, accept the current evaluation and proceed.

Now build a JSON object matching the `QualityEval` shape (the dispatcher reads it from stdin in steps 2g and 2i):

```json
{
  "score": 90,
  "vq": 30, "de": 13, "sc": 15, "dq": 14, "cq": 10, "lm": 8,
  "image_description": "...",
  "strengths": ["...", "..."],
  "weaknesses": ["..."],
  "criteria_checklist": {
    "visual_quality": {"score": 30, "max": 30, "items": [{"id": "VQ-01", "name": "Text Legibility", "score": 8, "max": 8, "passed": true, "comment": "..."}]},
    "design_excellence": {"score": 13, "max": 20, "items": [...]},
    "spec_compliance": {"score": 15, "max": 15, "items": [...]},
    "data_quality": {"score": 14, "max": 15, "items": [...]},
    "code_quality": {"score": 10, "max": 10, "items": [...]},
    "library_mastery": {"score": 8, "max": 10, "items": [...]}
  },
  "verdict": "APPROVED"
}
```

Save it to `/tmp/regen-eval.json` so it can be piped into the next two steps.

### 2g. Update metadata + impl header

```bash
uv run python -m agentic.workflows.modules.regen write-metadata "$SPEC_ID" "$LIBRARY" < /tmp/regen-eval.json
SCORE=$(uv run python -c "import json; print(json.load(open('/tmp/regen-eval.json'))['score'])")
uv run python -m agentic.workflows.modules.regen update-impl-header "$SPEC_ID" "$LIBRARY" "$SCORE"
```

This writes the YAML with theme-aware preview URLs, full criteria_checklist, and verdict — preserving the
original `created` timestamp, `issue`, and `impl_tags` if the file already exists. The impl header's
`Quality:` line is rewritten to match.

### 2h. Stage images to GCS (both themes + responsive variants)

```bash
uv run python -m agentic.workflows.modules.regen stage-images "$SPEC_ID" "$LIBRARY"
```

Mirrors the `impl-generate.yml` pipeline: optimizes each theme PNG in place via `core.images process`,
generates `plot-{theme}_{400,800,1200}.{png,webp}` + full `plot-{theme}.webp` via `core.images responsive`,
then uploads the entire bundle to `gs://anyplot-images/staging/{SPEC_ID}/python/{LIBRARY}/` (the same path
`impl-merge.yml` promotes from to `gs://anyplot-images/plots/{SPEC_ID}/python/{LIBRARY}/`). ACL failures on
uniform-IAM buckets are swallowed.

### 2i. Worktree → commit → push → PR

```bash
PR_OUTPUT=$(uv run python -m agentic.workflows.modules.regen create-pr "$SPEC_ID" "$LIBRARY" < /tmp/regen-eval.json)
PR_URL=$(echo "$PR_OUTPUT" | sed -n '1p')
PR_NUMBER=$(echo "$PR_OUTPUT" | sed -n '2p')
```

Internally: fetches `origin/main`, creates `implementation/{SPEC_ID}/{LIBRARY}` worktree from it, copies the
regenerated files in, commits, pushes, opens the PR with the `**Parent Issue:** #N` marker (read from the
spec's `specification.yaml`) so `impl-merge.yml` can comment on the spec issue and add `impl:{LIBRARY}:done`.
Adds `quality:{SCORE}` plus `ai-approved` (≥ 50) or `quality-poor` (< 50) via REST. Always cleans up the
worktree afterward, even on failure.

### 2j. Tick off and log

```bash
VERDICT=$(uv run python -c "import json; print(json.load(open('/tmp/regen-eval.json'))['verdict'])")
uv run python -m agentic.workflows.modules.regen mark-done "$LIBRARY" "$PR_URL" "$SCORE" "$VERDICT"
```

### 2k. Report and exit

```
{LIBRARY} done — score {SCORE}, PR: {PR_URL}
Remaining: {N} libraries

Run /regen again for the next library.
```

Exit.

### Per-library failure

If any step fails irrecoverably (script won't run after 3 retries, `gh push` rejected, `gsutil` unauthenticated):

```bash
uv run python -m agentic.workflows.modules.regen mark-failed "$LIBRARY" "<reason>"
```

Records `- [!] {LIBRARY}` in the plan, appends a `FAILED — {reason}` log line, and cleans up the worktree +
preview dir. `[!]` items are skipped by future invocations. The user can edit them back to `[ ]` to retry.

Print the failure reason and exit.

---

## Done mode

If no `- [ ]` lines remain:

```bash
ARCHIVED=$(uv run python -m agentic.workflows.modules.regen archive)
echo "$ARCHIVED"
```

Tell the user the spec is complete and they can run `/regen` again to start the next oldest spec (or
`/regen <spec-id>` to target a specific one).

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

- altair: PR https://github.com/.../pull/1234, score 88, label ai-approved, verdict APPROVED (...)
- bokeh: PR https://github.com/.../pull/1235, score 91, label ai-approved, verdict APPROVED (...)
- highcharts: FAILED — gsutil not authenticated (...)
```

The user can:
- `cat .regen-plan.md` — see progress at any time
- `rm .regen-plan.md` — abandon the current plan
- Edit checkboxes manually — re-order, retry failures, skip libraries

---

## Notes

- **No agent teams.** Runs entirely in the lead session.
- **One library per invocation.** Restart-safe.
- **No Cloud AI review.** Each PR carries `quality:{N}` plus `ai-approved` (≥50) or `quality-poor` (<50).
  `impl-merge.yml` still triggers on `ai-approved` (squash-merge, GCS staging→production, `impl:{lib}:done` label,
  `sync-postgres.yml`).
- **`.gitignore`** must contain `.regen-plan.md`, `.regen-history/`, and `.regen-preview/`.
- **Helper module** lives at `agentic/workflows/modules/regen/` with unit tests under `tests/unit/agentic/regen/`.
  Subcommands are documented in `agentic/workflows/modules/regen/__main__.py`.
