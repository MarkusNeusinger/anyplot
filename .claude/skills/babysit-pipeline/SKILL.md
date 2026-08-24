---
name: babysit-pipeline
description: Run and monitor the bulk-generate / impl-* pipeline for one or more specs to full 15-library coverage — dispatch sequentially, poll with the bundled checked-in scripts (never hand-rolled loops), read completion from impl:{lib}:done labels + GCS spot-checks, apply the correct stall thresholds, and report progress proactively. Also covers gap backfill across the whole catalogue (computing the missing set from repo metadata, the per-spec driver, the one-retry rule). Use when asked to babysit, run bulk-generate, regenerate specs, monitor the pipeline, close coverage gaps, or bring specs to full coverage.
---

# Babysit the generation pipeline

The spec → impl pipeline (bulk-generate → impl-generate → impl-review
→ impl-repair → impl-merge) is fully automated; babysitting means
dispatching, watching, and intervening ONLY at the documented points.
Never manually merge pipeline PRs, never hand-create metadata
(CLAUDE.md mandatory workflow). All commands from the repo root.

## 0 · Before dispatching

- **Confirm the queue with the user first**: which specs, in what
  order, which model, and the stop-point — users have had to
  interject mid-run ("no new spec after X").
- `git fetch origin main` before computing any coverage/inventory —
  stale main has produced wrong counts.
- One spec at a time: bulk-generate serializes dispatch via a
  concurrency group, but overlapping impl pipelines across specs make
  completion unreadable. Process strictly sequentially.

## 1 · Dispatch

```bash
gh workflow run bulk-generate.yml -f specification_id=<spec> -f library=all
# targeted single library instead (leaves good impls alone):
gh workflow run impl-generate.yml -f specification_id=<spec> -f library=<lib> -f model=<model>
```

`model` threads through generate→review→repair→merge. impl-generate
auto-closes any existing open PR for the same spec/lib.

## 2 · Monitor — use the bundled scripts, don't hand-roll

Completion signal = the spec issue carries all 15 `impl:{lib}:done`
labels (impl-merge sets each atomically with the repo commit + GCS
promotion; at 15/15 the issue auto-closes).

**Oneshot status:**

```bash
.claude/skills/babysit-pipeline/monitor_spec.sh <spec-id> <issue-number>
```

Prints per-library done/pending/failed plus
`STATUS=COMPLETE|IN_PROGRESS|NEEDS_ATTENTION` (COMPLETE includes a
GCS production spot-check).

**Background poller** (3-min interval; exits — re-invoking the agent
— on completion, stall, or timeout; default cap 130 min):

```bash
.claude/skills/babysit-pipeline/poll_spec.sh <spec-id> <issue-number> [max_minutes]
```

Run it via Bash `run_in_background: true`, NOT a foreground loop and
NOT `sleep` chains. Its log lands OUTSIDE the repo at
`~/.cache/anyplot-babysit/poll_<spec>.log` (override with
`POLL_LOG_DIR`). Ad-hoc driver scripts (multi-spec queues) go in
the session scratchpad or `agentic/runs/` (gitignored) — never
`/tmp`, and prefer extending the bundled scripts over rewriting them.

**Report a one-line status to the user roughly every 10 minutes**
(done-count, active runs, ETA) and flag suspected stalls immediately
with evidence — never let the user ask "still running?".

## 3 · Reading the signals correctly

- **Timing**: ~55–75 min per fresh spec end-to-end (15 dispatches
  paced ~120 s apart ≈ 30 min, then the generate→review→repair→merge
  tail). `impl:done` labels lag and cluster near the end — **0/15 at
  21 min is normal, NOT a stall**.
- **Repairs are routine** (`Repair: <lib> … (attempt 1)`) — most libs
  need one; the 4-attempt cascade (90/80/70/60/50) is the design.
- **Review/merge runs are titled `Review: PR #N` / `Merge: PR #N`** —
  no spec name, so you cannot filter them by spec. Because specs run
  sequentially, ANY in_progress/queued `bulk-generate`/`impl-*` run
  belongs to the current spec; `poll_spec.sh` already encodes this.
  A real stall = no label progress for ~15 min AND pipeline idle.
- **GCS production path**:
  `gs://anyplot-images/plots/{spec}/{language}/{library}/plot-{light,dark}.{png,webp}`
  (+ `_400/_800/_1200` sizes; `.html` for JS libs). Staging under
  `gs://anyplot-images/staging/...` empties on promotion.

## 4 · Intervening (only at these points)

- **`NEEDS_ATTENTION` / failed libs**: a fresh targeted
  `impl-generate` regen of that one lib is almost always the right
  move — it auto-closes the bad PR. Stale `ai-review-failed` PRs on
  old branches keep re-failing review (score=0) even on a strong
  model: regenerate fresh, don't re-review.
- **Never run concurrent re-reviews on the same PR** (manual dispatch
  + auto-retry + a rescuer loop once raced labels into
  `quality:89` + `ai-review-failed` with no merge). At most one
  re-review at a time, only when no `Review: PR #N` run is active.
- **Defer, don't halt**: one stuck library must not stop a multi-spec
  queue — log it, cap ~90 min/spec, move on, and sweep leftovers at
  the end with targeted regens.
- **Halt the whole queue** only on a failure CLUSTER (≥5 failed
  `Generate:` runs in minutes = model daily quota exhausted; a
  fallback model via `-f model=` can finish leftovers).
- Closing/merging pipeline PRs or issues yourself is out of bounds
  (CLAUDE.md external-write rule + mandatory workflow).

## 5 · Gap backfill (many specs, partial coverage)

Different job from babysitting one fresh spec: dozens of older specs
each miss a few libraries, usually the ones added after they were
generated (JS libs, muix, makie).

**Compute the missing set from repo metadata, never from labels.**
Most of those specs have closed issues, so `impl:{lib}:done` labels
are absent or stale. `plots/{spec}/metadata/{lang}/{lib}.yaml` on
`origin/main` is the durable signal — it is also what
`run_spec.sh` polls.

```bash
git fetch origin main
git ls-tree --name-only -r origin/main -- plots/ \
  | awk -F/ '$3=="metadata" && NF==5 {f=$5; sub(/\.[^.]+$/,"",f); print $2" "f}' \
  | sort -u          # → "<spec> <lib>" pairs that exist
```

Diff that against the 15-library registry per spec dir, write
`<n-missing> <spec> <lib...>` sorted fewest-missing-first, and work
the file top-down: the cheap specs finish early and the progress
number moves.

**One spec per driver invocation** —
`.claude/skills/babysit-pipeline/run_spec.sh <spec> <model> <lib>...`
dispatches that spec's missing libraries staggered ~150 s
apart, then polls until each metadata file lands, and exits with
`RESULT=COMPLETE|PARTIAL|TIMEOUT`. Run it via Bash
`run_in_background: true`; it skips libraries already on main, so
re-running it after a partial result retries exactly the gaps.

**Two specs in parallel is fine** (~4 specs/h vs ~2); ten concurrent
`impl-generate` runs showed no rate-limit effects. Keep a ledger —
`done.log` / `deferred.log` next to the queue file in `agentic/runs/`
— and append the result line before dispatching the next spec, so a
compaction or a crashed session can resume without recounting.

**The one-retry rule.** A library that comes back missing gets
exactly one fresh targeted dispatch before it is deferred. This is
not optional politeness — on 2026-08-24 the single retry recovered
highcharts/treemap-basic, ggplot2/wireframe-3d-basic and
ggplot2/network-force-directed, all three of which had been read as
capability gaps. Two failures on the same pair → `deferred.log` with
the reason, move on, sweep at the end.

## Gotchas

- **`Marking <lib> as failed: N generation attempts` counts more than
  this run.** The number comes from `<!-- impl-fail:spec:lib -->`
  marker comments on the issue, and nothing deletes them; before the
  campaign-window fix (#10627) it spanned the issue's whole lifetime,
  so a pair that failed twice in some old campaign was capped at ONE
  attempt forever. Read the `Previous failures for <lib>/<spec>: N`
  notice in the log before concluding a library "can't do" a plot
  type — a high N there means the cap fired, not that generation was
  tried three times today.
- **`impl:<lib>:failed` is terminal and it lies about coverage.**
  Nothing re-dispatches it: watchdog case 3 fires once, then only
  logs `already retried by watchdog — needs manual attention`. Audit
  it against metadata before trusting it — of 87 such labels on
  2026-08-24, **42 sat on implementations that had since landed**.
  Take the label as a hint to check, never as the coverage answer.
- **"Agent reports success, writes no file"** is a live intermittent
  failure (8 of 85 generate runs on 2026-08-24, ~9%): the Claude step
  ends `"subtype":"success","is_error":false` and the next step fails
  with `Implementation file not found in repository`. With retry
  budget left the workflow self-heals (`bubble-basic/highcharts`:
  failed 17:55, retried and succeeded 18:02, no human involved), so a
  single occurrence is noise — only a repeat on the same pair means
  anything.
- **Static library + interactive/3D spec is the one gap that is
  usually real.** plotnine, pygal, seaborn, matplotlib and ggplot2
  against `*-interactive`, `*-drilldown`, `*-realtime`, `*-streaming`,
  `slider-*`, `*-3d` specs make up most genuine dead ends; 18 of the
  45 real gaps behind those labels were exactly this shape. Still
  give them the one retry, then defer without further ceremony.
- **The scripts' library list is a copy** of `core/constants.py`'s
  registry (15 libs). When a library is added/removed, update
  `monitor_spec.sh`'s `ALL_LIBS` and `run_spec.sh`'s `lang_of` in the
  same PR.
- **`gsutil` must be authenticated** for the GCS spot-check; a
  credentials failure reads as "incomplete" — check
  `gsutil ls gs://anyplot-images/ | head -1` before trusting a
  NEEDS_ATTENTION verdict that hinges on GCS.
- **Kill leftover pollers** when the queue ends or the user stops it —
  orphaned background tasks fire confusing notifications into later
  sessions.
