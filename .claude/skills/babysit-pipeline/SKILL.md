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
  completion unreadable. Process strictly sequentially. (Backfill with
  `run_spec.sh` is the one exception — it reads completion per library
  from repo metadata rather than from "is anything running?", so it
  tolerates two specs in flight. See §5.)

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
- **Halt the whole queue** only on a failure CLUSTER: **≥3 distinct
  (spec, library) pairs** failing within minutes of each other = model
  daily quota exhausted; a fallback model via `-f model=` can finish
  leftovers. The threshold is pairs, full stop — the raw run count
  says nothing, because one impossible pair spends three runs on its
  own auto-retries, so two bad pairs already produce six failures with
  the pipeline entirely healthy (observed 2026-08-24).
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

**Several specs in parallel is fine — but only in this mode.** It
works because `run_spec.sh` decides per library from `origin/main`
metadata and reads liveness per spec (its own generate runs, its own
open `implementation/<spec>/*` PRs), so drivers never mistake each
other's runs for progress. `poll_spec.sh` and `monitor_spec.sh` must
still run one spec at a time: their stall logic reads *any* active
`impl-*` run as belonging to the spec they are watching (§3), so a
second spec in flight makes them call a stalled spec healthy. Never
mix the two modes on the same queue. The slot count is the user's
call: **2 is the default**, 4 with their OK. A 5-slot trial on
2026-09-01 was clean on the GitHub side (API quota untouched, impl-*
runner wait ≤4 min; only CodeQL piled up) — the binding limit is the
Claude usage window, which is why the user pulled it back the same
evening. Reducing means: stop launching and let in-flight PRs drain;
never cancel runs that already spent Claude time.

**For an unattended queue use the scheduler**,
`.claude/skills/babysit-pipeline/run_queue.sh <queue-dir> [slots]`,
started detached so it survives the session, with both streams
captured:

```bash
setsid nohup .claude/skills/babysit-pipeline/run_queue.sh agentic/runs/<run> 2 \
  > agentic/runs/<run>/queue.out 2>&1 &      # the 2 is the slot count
```

It keeps `[slots]` drivers in flight over
`<queue-dir>/full_queue.txt`, skips libraries already on main and
pairs recorded as `CONFIRMED GAP` in `deferred.log`, harvests every
driver's `RESULT=` line into `done.log` / `deferred.log`, and holds
new launches for 15 min while any throttle sign is present: GitHub
core quota below 800, **three or more distinct generate pairs failing
within 25 min** (§4's cluster rule), or a rate-limit signature in a
failed impl-* log. `DEADLINE=<epoch>` stops new launches at a fixed
time. A `rescue_specs.txt` (`<spec> <lib...>` lines) is re-checked
ahead of the queue and launched only once nothing for that spec is in
flight — the way to re-queue a spec that an outage cut short without
auto-closing PRs that are still under review or repair. Stop it with
`pkill -f run_queue.sh`; drivers keep watching (all their dispatches
went out at start), so "finish the current specs, start nothing new"
is exactly that. Keep the ledger next to the queue file in
`agentic/runs/` — a compaction or a crashed session resumes from it
without recounting.

**Report every ~10 minutes** from one cycle script: GitHub quota,
runner queue depth and impl-* queue age, impl-* failures of the last
30 min with the first `##[error]` line of each new one, the scheduler
log tail, per-spec progress from `origin/main` metadata, open impl
PRs with labels. A run of ~1600 pipeline runs on 2026-09-02 needed no
other signal.

**The one-retry rule.** A library that comes back missing gets
exactly one fresh targeted dispatch before it is deferred. This is
not optional politeness — on 2026-08-24 the single retry recovered
highcharts/treemap-basic, ggplot2/wireframe-3d-basic and
ggplot2/network-force-directed, all three of which had been read as
capability gaps. Two failures on the same pair → `deferred.log` with
the reason, move on, sweep at the end.

Check the run list before deferring, though: since #10627 the
workflow spends its own three attempts per campaign, so a pair that
comes back missing may already have failed three times, and the
manual retry adds nothing. There is no per-spec filter on the API, so
filter the output by run title:

```bash
gh run list --workflow=impl-generate.yml --limit 40 \
  --json conclusion,createdAt,displayTitle \
  --jq '.[] | select(.displayTitle | test("<spec>")) | "\(.createdAt) \(.conclusion) \(.displayTitle)"'
```

Three `Generate: <lib> for <spec>` failures minutes apart is a measured
gap; one failure is a flake worth the retry. The same check covers
`RESULT=TIMEOUT` with `recent generate failures: 0`, which only means
the failures fell outside the driver's 25-minute window, not that
nothing failed.

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
  2026-08-24, **42 sat on implementations that had since landed**
  (impl-merge clears the label on merge only since #11197). Take the
  label as a hint to check, never as the coverage answer.
- **A provider outage looks like a capability cliff.** On 2026-09-02
  03:15–03:45 UTC every Claude step ended `is_error:true` with
  `Internal error: directory mismatch ... tsconfig.json`; 27 pairs
  across three specs burned all three attempts in twenty minutes and
  two whole specs came back 0/6. That is a throttle signal, not six
  gaps: the scheduler's cluster rule held launches, and every pair
  regenerated fine once the incident was over. Since #11199 such
  failures no longer spend the pair's budget; before it, expect a
  re-dispatch inside the 12-hour window to run without auto-retry.
- **Rescuing an outage-hit spec has an order.** First let the
  pipeline finish what it can: PRs in `ai-review-failed` and stalled
  repairs are the watchdog's job (`gh workflow run
  watchdog-stuck-jobs.yml -f stale_hours=2` when you cannot wait for
  the cron; since #11198 it also covers `ai-rejected` +
  `ai-attempt-N` with a crashed repair — before that, dispatch
  `impl-repair.yml` yourself with the watchdog's parameters
  `pr_number`, `specification_id`, `library`, `attempt`). Only then
  put the spec on `rescue_specs.txt`: the driver's dispatch
  auto-closes every open PR of the pair, so a regeneration fired while
  a repair is mid-flight throws that work away.
- **A `Merge: PR #N` run that fails AFTER "Merge PR to main" leaves a
  silent hole: the squash is on main (metadata pointing at production
  URLs, the driver counts the pair as done) but the images are still in
  staging, the `impl:<lib>:done` label, issue close and Postgres sync
  never ran.** Seen on #11295 (2026-09-05, GCP auth step failed 5 s
  after the squash). Read the failed run's step list — a failure at or
  after `Authenticate to GCP` with `Merge PR to main` green is this
  case — then `gh workflow run impl-merge.yml -f pr_number=N`: the
  workflow treats an already-merged PR as success and runs the
  post-merge steps. Never promote the images by hand. Every status
  cycle should compare the pairs landed on main against
  `gs://anyplot-images/plots/<spec>/<lang>/<lib>/plot-light.png`; a
  merge failure in the run list is the trigger to look.
- **`Merge: PR #N` failing five times with "Head branch is out of
  date" while `mergeable` stays `UNKNOWN` is a stuck PR object, not a
  branch problem.** Seen on #10850 (2026-09-01): `update-branch` had
  pushed a merge commit, the branch ref moved, the pull request never
  registered it. Re-running impl-merge cannot help. With the user's OK
  push an empty commit to the PR branch (`git commit-tree` on the
  remote head, plain push) so GitHub re-syncs and recomputes
  mergeability, then re-dispatch `impl-merge.yml -f pr_number=N`;
  the merge itself stays with the workflow.
- **"Agent reports success, writes no file"** is a live intermittent
  failure (8 of 85 generate runs on 2026-08-24, ~9%): the Claude step
  ends `"subtype":"success","is_error":false` and the next step fails
  with `Implementation file not found in repository`. With retry
  budget left the workflow self-heals (`bubble-basic/highcharts`:
  failed 17:55, retried and succeeded 18:02, no human involved), so a
  single occurrence is noise — only a repeat on the same pair means
  anything.
- **Do not predict capability gaps — measure them.** The 2026-08-24
  backfill guessed four times which pairs were genuinely impossible
  (chartjs on treemap/sankey, plotnine on 3D, ggplot2 on wireframe,
  "static library vs. interactive spec") and every category-level
  guess was wrong: 17 of 20 parked pairs generated fine, pygal and
  chartjs each succeeded on the very plot types they were written off
  for, and `bar-3d-categorical` succeeded in plotnine while
  `scatter-3d` did not. Only three pairs failed with a full budget —
  plotnine on `scatter-3d`, `contour-3d`, `line-3d-trajectory`, all
  needing a spatial projection plotnine does not have, while the
  "3D" spec that is representable in 2D went through. A gap is real
  when three attempts under a fresh campaign budget say so, never
  because the pairing sounds implausible.
- **A spec id from an issue title may not exist.** `impl:*:failed`
  labels outlive their specs: of 26 spec IDs harvested that way, 14
  had no `plots/<spec>/` on main at all, and a dispatch for one dies
  at `Validate specification exists` seconds in. Intersect any
  label-derived list with `git ls-tree -d origin/main plots/` before
  queueing it.
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
