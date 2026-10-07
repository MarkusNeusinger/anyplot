---
name: review-regen-week
description: Weekly review of what daily-regen produced — collect every regeneration of the window with its gate record, review comment, write-back and pair artifact via the bundled collect_week.py, read the health metrics against their targets, open before/after renders for a sample, classify every finding (spec, rubric, generator, gate, workflow, one-off regen) and write a dated report plus Todoist tasks for owner decisions. Read-only on GitHub and production. Use when asked for the weekly regen review, to review the daily regens, what daily-regen did this week, how the regen gate behaved, or whether the nightly regenerations improved the catalogue.
---

# Weekly regen review

`daily-regen.yml` regenerates one spec per night (02:17 UTC): 15 pairs,
each reviewed once on Opus, and the regen gate either merges the new
version (`regen:improved`) or keeps the live one (`regen:kept`, with a
write-back of the re-score). Once a week you look at what that did to
the catalogue: what improved, what slipped through, and what needs a
fix in a spec, the rubric, the generator, the gate or a workflow.

The review is **read-only**. It never merges, closes, labels or
dispatches anything, and it writes nothing to production. Everything
it proposes goes to the owner as a finding or a Todoist task.

Before the first review, read [`reference/lessons.md`](reference/lessons.md):
it holds the gate rules and the scoring lessons that tell a real
problem from expected behavior. All commands run from the repo root.

## 1 · Set the window

1. Work from the main checkout, not a worktree: the reports live in
   the gitignored `agentic/runs/weekly-review/`, and next week's run
   needs this week's JSON. Run `git fetch origin main`.
2. Find the previous report: `ls agentic/runs/weekly-review/????-??-??.md`.
   The window starts on its date; pass its JSON as `--previous`, and
   the collector leaves out the PRs that report already decided and the
   runs it already counted. With no previous report, use the last 7
   days.
3. Run after the night's pipeline has finished (02:17 UTC plus about
   two hours). A regen PR without a verdict that is younger than three
   hours shows as `pending`, not `stuck`.
4. Say the window and the report path to the user before you start.

## 2 · Collect

Run the three collectors. All three only read GitHub.

```bash
D=$(date -u +%F); SINCE=<window start, YYYY-MM-DD>
OUT=agentic/runs/weekly-review
uv run python .claude/skills/review-regen-week/collect_week.py \
  --since "$SINCE" --out "$OUT/$D.json" \
  --previous "$OUT/<previous date>.json" --costs > "$OUT/$D-collect.md"
uv run python -m automation.scripts.review_retest gate-report \
  --since "$SINCE" --json "$OUT/$D-gate.json" > "$OUT/$D-gate.md"
uv run python -m automation.scripts.review_retest first-reviews \
  --since "$SINCE" --json "$OUT/$D-first.json" > "$OUT/$D-first.md"
```

- `collect_week.py` lists every PR labelled `regen` or `regen:forced`
  created in the window and writes one row per PR: the gate record
  (verdict, reason code, stored, re-scored and new score, carriers,
  `P`/`new` carriers, code fixes, kinds, write-back status), the
  parsed review (24-item checklist, category sums, silent deductions),
  the write-back PR, the review run and its
  `regen-pair-<pr>-<attempt>` artifact, the production render URLs,
  and flags. A forced regen takes the first-generation path and has
  no gate record; it is listed so you can check why it was forced. The
  collector also counts the window's pipeline runs by conclusion,
  prints the failed ones under the metric table, and with `--costs`
  sums `total_cost_usd` from every generate, review and repair job log
  (about one minute per 50 runs; leave it off for a quick look). Its
  stdout is the metric table and the PR table the report starts from;
  `◆` marks the render sample.
- `gate-report` adds the aggregate view and its soft alarms, among
  them contrast bias, the `regen_json_invalid` share, the merge rate,
  permission or obsolete citations, unverified claims, carriers
  without a kind, and write-back `invalid`.
- `first-reviews` covers first generations in the window (new
  libraries or new specs): the attempt-1 histogram, the share at
  exactly 90–91, silent deductions, and repair gains on judgment
  items.

## 3 · Read the metrics

Compare each number with its target and with last week's column. A
miss is a prompt to look, not a verdict: open the rows behind it.

| Metric | Target | When it misses, look at |
|---|---|---|
| Merge rate | 5–50 % over ≥ 30 decisions | High: are merges carried by real defects (§4)? Low: are good regens kept on technicalities (`no_visible_improvement` with visible fixes)? |
| Merges without a carrier | 0 | Every one is a gate bug unless the code path carried it (`code_fixes` ≥ 1). |
| Merges carried only by `P`/`new` | read each | The re-score found the defect itself. Real creep removal is fine; a "defect" invented to justify the new render is the motivated-classification risk. |
| `regen_json_invalid` | 0 (alarm > 10 %) | The review prompt's step 8b; a pattern across libraries is a prompt fix. |
| Unverified claims | 0 (alarm > 20 %) | The review claims a criterion moved that its own scores don't confirm. |
| Silent deductions | 0 since P10 (#12046) | A technical point deducted without a defect line leaves a repair nothing to fix. Reviews before 2026-10-04 still show them. |
| Write-back not merged | 0 | `writeback_stranded`: the PR opened but never merged — check its `impl-merge.yml` run. `invalid`/`stale`/`failed`: read the keep comment's **Stored review** line. `no_rescore` is not counted here: it follows from a gate failure the reason code already shows. |
| Keeps re-scored far below stored | read each | Flagged above 3 points when both reviews came from the same model family, above 13 across families. The Opus offset alone is about −9 on Sonnet-era stored scores; a drop past the limit is a defect the old review missed, or a harsh re-score. |
| New score mean | ≈ 80–88 | Above: inflation; check DE/LM items for credited compliance. |
| Scores ≥ 90 | rare | Each one must show design beyond the spec and style guide. Open its render. |
| Re-score − stored | ≈ −9 now, moving toward 0 | Shrinks as write-backs and merges replace Sonnet-era reviews. Use gate-report's *comparable* line for the clean number. |
| Identical review vectors in a spec | 0 | Anchoring: two libraries scored item for item the same. Read both reviews. |
| First reviews at exactly 90–91 | not a pile | A pile at the line with few at 88–89 is a reviewer aiming at the line. |
| Stuck or failed review PRs | 0 | `stuck`: open or verdict-less regen PR. `review_failed`: the watchdog only flags regens; one manual re-review is the owner's call. |
| daily-regen runs | one success per night | A missing night: did the watchdog's cron rescue fire? A run with no bulk-generate after it: check the preflight job. |
| Session cost | stable week to week | A jump with the same number of PRs means retries or long sessions; find the runs. |

Two ratios are worth a sentence in the report even when no threshold
fires: the reason-code mix of the keeps, and the share of merges whose
only carriers are `-basic` scope removals (expected during the
cleanup wave after the backfill, falling afterwards).

## 4 · Look at the renders

Numbers say where to look; only the renders say whether the catalogue
got better. `collect_week.py` picks the sample: every merge carried by
a `P` or `new` item, every keep flagged `big_drop`, every merge
without a carrier, every row with an unverified claim or a score of 90
or more, and a seeded random three of the rest.

Download each sampled pair (60-day retention):

```bash
gh run download <review_run> -n <pair_artifact> -D agentic/runs/weekly-review/$D/pairs/<pr>
```

The folder holds `prev/` and `new/` renders and sources,
`gate-summary.md` (the improvements the gate counted), the previous
review (`prev/anyplot-prev-review.md`), the re-score
(`review_prev.json`) and this review's files. Open both themes of
`prev/` and `new/`, read `gate-summary.md`, and answer:

1. **Real improvement?** Does each carrier show at the place it names,
   and is the new render better as a whole, not only on that item?
2. **A regression the review missed?** Look for something that got
   worse and is written up as a defect of the new render instead of a
   regression (lessons: the d3 hollow-legend-rings case). A merge with
   such a line is a gate miss.
3. **A stored defect the generator ignored?** Compare the previous
   review's defect lines with the new render. A defect that survives
   two regens of the same pair is a generator or spec finding.
4. **A spec contradiction?** Several libraries failing the same
   bullet, or a carrier that contradicts the Notes or the Data section,
   points at the spec, not the libraries.
5. **Domain correctness:** where the spec has `Check values:`, does
   the review's DQ-03 comment name the values it checked?

For a keep, the production render is the live (previous) one; for a
merge, production already shows the new one, and only the pair
artifact still has the predecessor.

## 5 · Classify every finding

Each finding gets one class, a proposed action, and an owner flag.

| Class | Typical evidence | Action | Who decides |
|---|---|---|---|
| Spec text fix | Same failure across libraries; a bullet stricter than Notes/Data; a domain spec without check values | Spec PR (`plots/`-only) per the spec-polish rules | Routine when it only aligns a bullet with the Notes; owner when it changes what the plot shows |
| Rubric fix | Systematic mis-scoring: silent deductions, credited compliance, anchoring, regression-as-defect | Plan + a `review-retest.yml` candidate arm against the baseline before any merge (CLAUDE.md) | Owner |
| Generator prompt | Stored defects ignored; the same code smell in many regens | Prompt PR; observable only on real runs, say so | Owner for direction, routine for a wording fix |
| Gate logic | A merge without a real carrier, a keep that discarded a visible fix, a wrong reason code | `regen_gate.py` change with unit tests, and an arm when it changes verdicts | Owner |
| Workflow | Stuck PRs, missed events, failed write-backs, missing nights | Workflow PR, or a one-time manual recovery from `babysit-pipeline` | Routine for a documented recovery; owner for a dispatch or rerun |
| One-off regen | A single bad merge or a wrong keep | `impl-generate.yml` dispatch for that pair (`regen_gate=false` only to force a replacement) | Owner names each dispatch |

## 6 · Write the report

Write `agentic/runs/weekly-review/<YYYY-MM-DD>.md` (gitignored), in
English, Google style:

1. **Summary** — five lines at most: decisions, merges and keeps, the
   one or two things that went well, the one or two that need action.
2. **Metrics** — the table from `$D-collect.md` with last week's
   column, plus the gate-report alarms and the first-review line.
3. **Findings** — one entry each: what you saw (PR, render, numbers),
   its class, the proposed action, and *owner decision* or *routine*.
4. **Render notes** — one line per sampled PR: improvement real or
   not, anything missed.
5. **Open from last week** — the previous report's findings and
   whether they moved.

Then:

- Create one Todoist task per owner decision in the **Anyplot**
  project (CLAUDE.md rule): the concrete action plus the PR, run or
  report link. Routine items stay in the report.
- Offer, in one line, a private Artifact page with the before/after
  renders of the sample. Build it only on a yes. The renders are
  public catalogue images, so the page needs no capabilities; link
  the GCS URL or embed the downloaded PNGs.
- Tell the user the report path, the headline and the task count.

## What not to do

- **No merges, closes, labels or dispatches.** Pipeline PRs belong to
  `impl-merge.yml`; a re-review or a regen dispatch needs the owner's
  named authorization (CLAUDE.md external-system rule).
- **No production writes** (GCS, Postgres, metadata on `main`)
  without named authorization, and a snapshot first.
- **No rubric change without an arm.** A finding about scoring
  becomes a plan plus a retest arm, never a direct prompt edit.
- **Never lower a line to restore a pass or merge rate.** A 90 must
  stay rare and earned; a low merge rate is a finding about the gate
  or the generator, not about the threshold.
- **Political specs use invented parties and data.** A render with a
  real party, parliament or election is a defect to fix, not to
  score around.
- **Implementations stay independent per library.** Never propose
  copying one library's data or approach into another; a similarity
  finding flags one library of an identical pair, in one sentence.
- **Don't treat a kept regen as a failure.** Keep is the gate's
  default when nothing verified improved; the write-back still
  refreshes the stored review.

## Gotchas

- **The window is by creation date, at day granularity.** Starting on
  the previous report's date and passing `--previous` covers every PR
  exactly once; a PR that was still open last week comes back. A
  `--previous` path that doesn't exist stops the collector.
- **Older records lack newer keys.** Reviews before #12046
  (2026-10-04) were allowed silent deductions; pre-P3.1 records lack
  `carriers_pn` and the kinds; pre-P8 records lack `improvements.code`,
  the third number of the carriers column. The tables show `–`; don't
  flag those as new problems.
- **The production "before" render is gone after a merge.** The pair
  artifact is the only copy, for 60 days. Download it in the week
  you review it.
- **A `merge_pn_only` row is not a problem by itself.** During the
  `-basic` cleanup wave most merges are P items that remove scope
  creep. Read the carriers; flag only those that name something the
  spec allows or that the render doesn't show.
- **Keyword counts over-match.** When you count a pattern across
  reviews or renders (`callout`, `orange`, `mean line`), read each
  hit before you report the number. Earlier counts were off in both
  directions (a hex comment said "orange" for a red).
- **Use a background watcher, not a promise to check back.** When a
  step waits on GitHub (a long `--costs` run, a pending write-back),
  run it with `run_in_background` and act on its exit, and post a
  status line every ~10 minutes.
- **After daily-regen runs** a pipeline problem (stuck PR, failed
  merge, missing render) is `babysit-pipeline`'s recovery recipe; this
  skill only finds and reports it.
