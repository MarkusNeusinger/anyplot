---
name: babysit-pipeline
description: Run and monitor the bulk-generate / impl-* pipeline for one or more specs to full 15-library coverage — dispatch sequentially, poll with the bundled checked-in scripts (never hand-rolled loops), read completion from impl:{lib}:done labels + GCS spot-checks, apply the correct stall thresholds, and report progress proactively. Use when asked to babysit, run bulk-generate, regenerate specs, monitor the pipeline, or bring specs to full coverage.
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

## Gotchas

- **The scripts' library list is a copy** of `core/constants.py`'s
  registry (15 libs). When a library is added/removed, update
  `monitor_spec.sh`'s `ALL_LIBS`/`lang_of` in the same PR.
- **`gsutil` must be authenticated** for the GCS spot-check; a
  credentials failure reads as "incomplete" — check
  `gsutil ls gs://anyplot-images/ | head -1` before trusting a
  NEEDS_ATTENTION verdict that hinges on GCS.
- **Kill leftover pollers** when the queue ends or the user stops it —
  orphaned background tasks fire confusing notifications into later
  sessions.
