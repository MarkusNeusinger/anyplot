# Review retest

> **Status (2026-10-07):** The harness (`automation/scripts/review_retest.py`), the workflow (`.github/workflows/review-retest.yml`), and three sets exist. Set v1 (`automation/retest/set-v1.yaml`) is frozen: `automation/retest/set-v1.lock.json` pins its 94 public renders. Set v2 (`automation/retest/set-v2.yaml`, the 12 regen pairs of verification round 1) is frozen too: `automation/retest/set-v2.lock.json` pins its 48 public renders. Set v3 (`automation/retest/set-v3.yaml`, the 15 first generations of `line-tanabe-sugano`) was frozen on 2026-10-02: `automation/retest/set-v3.lock.json` pins its 30 public renders. The workflow has no effect until someone dispatches it. The owner confirmed the ground-truth labels of sets v1 and v2 on 2026-09-30 and those of set v3 on 2026-10-07 (`labels: confirmed`), so reports now fill the label metrics each set supports: named-defect and false-alarm rates for fresh items, gate accuracy for regen pairs, and the carrier metric for pairs with a `fixes` label (set v2 only).

The AI quality review decides what reaches the catalogue, and a change to its rubric or its model used to be observable only on real pipeline runs. The review retest re-runs the review on a frozen set of implementations and regeneration pairs, several sessions per item, and reports how the scores, verdicts, and weaknesses spread and move. You run it as an *arm* (one rules version) and compare it against a *baseline* arm, so a rubric pull request can show its effect before it merges.

The retest measures the judge only. It never writes to a pull request, an issue, a label, `plots/`, GCS, or another workflow.

---

## When to run it

Run a candidate arm for any change to:

- `prompts/quality-criteria.md`
- `prompts/workflow-prompts/ai-quality-review.md`
- `prompts/default-style-guide.md`
- the review rules in `prompts/library/*.md`
- the review model routing in `impl-review.yml`

Generator-side changes (`prompts/workflow-prompts/impl-generate-claude.md`, `prompts/plot-generator.md`, the generator half of a library prompt) and `.github/workflows/` changes are still only observable on real regenerations. Say so in those pull requests.

---

## How it works

- **The set.** The `set` input picks a frozen set: `automation/retest/set-<set>.yaml` lists its items, and `set-<set>.lock.json` next to it holds the sha256, size, and the pairs' pixel statistics of its renders, which are public objects under `gs://anyplot-images/retest/sets/<set>/`. A *fresh* item is one implementation, reviewed the way a first implementation is. A *regen* item is a pair (new version and predecessor), reviewed the way a regeneration is: the new render blind, then the predecessor re-scored, then the regen gate. Sources are pinned by commit. The prep job downloads the renders anonymously over HTTPS and checks every hash.
  - **Set v1** (the default): 27 fresh items, one or two per library, and 10 bubble-basic regen pairs from the regen experiment, including three identity controls.
  - **Set v2**: the 12 regen pairs of verification round 1 (2026-09-27, #11951 to #11963 without #11955), each predecessor at `0ccb3fec1` and each new version at `28df16aed`, with the spec pinned at `0ccb3fec1`. It measures what set v1 can't: whether a regeneration merges on a fixed defect or on a suggestion. Two predecessors are off-canvas (bar-error/matplotlib at 4766 × 2670, bar-error/plotly at 4800 × 2700), so those two pairs run in the forward order only (`orders: forward` in the manifest).
  - **Set v3**: the 15 first generations of `line-tanabe-sugano` (#12019 to #12038, 2026-10-01), one fresh item per library, pinned at `cda962dc3` with the spec text of `ec0619261`, the text their live reviews saw. It's a probe near the approval line: the live attempt-1 scores were 85 to 91, with less spread between the libraries than one reviewer shows between two runs of the same file. It measures what sets v1 and v2 can't: how first reviews behave where one point decides the verdict, whether every deduction names a defect, and whether a wrong domain value is caught. Eight of the 15 files are the state after one repair, because a repair overwrites the staging render; each item's `note` says which.
- **An arm.** `rules_ref` names the commit whose `prompts/` and `automation/scripts/regen_gate.py` the reviewer uses. The harness itself always comes from the commit you dispatch, so you can measure any past or unmerged rules version from `main`; rules that predate the regen gate (`02e1a7974`) have no `regen_gate.py`, so only fresh items run on them. The harness hands an overlaid `regen_gate.py` only the `context`, `sanitize-source`, and `decide` flags it has had since `02e1a7974`, and takes everything newer (the header reset, the characteristic kinds, the record markers) from its own copy, so an old arm such as the baseline runs unchanged.
- **A cell.** One item, one order (regen pairs run forward and reversed), one run. Every cell is a fresh Claude session in its own job. With `models=production`, every cell runs on Opus, as `impl-review.yml` reviews (a unit test keeps the two equal).
- **What a session sees.** Exactly what `impl-review.yml` shows the reviewer, with these deliberate differences:
  - The file under review says `Quality: pending` in every arm (the state `impl-generate.yml` leaves since the header reset).
  - The checkout is shallow, the spec text is pinned to the set's `spec_commit` (unless `spec_source=rules_ref`), and the job has no GCP credentials.
  - There is no pull request: `PR_NUMBER` is `0`, `ATTEMPT` is `1`, and the prompt asks for the review comment in `review_comment.md`.
  - The session runs with `automation/retest/claude-settings.json`, which denies `gh`, `git push`, `git commit`, and `WebFetch`, and the job token is read-only with no `id-token`.
- **What comes out.** Each cell uploads `cell-<id>` (its review files and `record.json`, never the session transcript). The record's `model` is the model ID the session's execution file names, or `null` when it names none; the alias the session started with is kept apart as `model_alias`, never in its place. The aggregate job writes the report to the run summary and uploads `retest-report` (`retest-report.md`, `retest-report.json`, `records.jsonl`, `snippet.md`), kept 90 days.

---

## First runs after the merge

The pull request that adds the workflow can't dispatch it: a `workflow_dispatch`-only workflow must be on the default branch first. Run these in order once it has merged, each after the previous one has finished:

1. Smoke-test one cell. It is the first run to meet the idle check (step 1 of [Run a baseline and a candidate arm](#run-a-baseline-and-a-candidate-arm)): the prep job refuses while a pipeline run is queued, or in progress and less than six hours old, and `daily-regen` fires at 02:17 UTC and dispatches regenerations, so dispatch it once the pipeline is idle:

   ```bash
   gh workflow run review-retest.yml -f subset=f-bubble-basic-ggplot2 -f runs=1 -f label=smoke
   ```

2. Download the `cell-f-bubble-basic-ggplot2__r1` artifact and check that `record.json` names a resolved `model` (not `null`) and a `cost_usd`, and that `files/review_comment.md` exists.
3. Check the repository's activity in the run's time window: no new comment, label, pull request, issue, or workflow run other than the retest itself. The run also confirms that claude-code-action accepts the read-only job token.
4. Run the baseline arm on the set's baseline rules with production routing, every cell on Opus (87 sessions):

   ```bash
   gh workflow run review-retest.yml -f rules_ref=0674ab6b55acc71f5015a6aae07145424cbac7cb -f models=production -f label=baseline
   ```

   This step first ran on 2026-09-27 as run 36354452853, when `production` still sent regen cells to Sonnet. Its all-Opus counterpart is run 36389481950 (see [Run a baseline and a candidate arm](#run-a-baseline-and-a-candidate-arm)).

5. Run the one-time cross-model pass, the fresh core items on Sonnet (45 sessions), against the baseline's run ID. This pass is historical: it ran once on 2026-09-27 as run 36359464410, against the baseline 36354452853, and measured how far Sonnet scores sit above Opus.

   ```bash
   gh workflow run review-retest.yml -f rules_ref=0674ab6b55acc71f5015a6aae07145424cbac7cb -f models=sonnet -f label=cross-model-sonnet -f compare_to=<baseline-run-id> -f subset=f-bubble-basic-ggplot2,f-area-elevation-profile-seaborn,f-bar-horizontal-makie,f-bode-basic-altair,f-bar-diverging-plotnine,f-pie-basic-highcharts,f-bar-pareto-letsplot,f-waterfall-basic-muix,f-line-win-probability-chartjs,f-bubble-basic-d3,f-network-basic-bokeh,f-bar-diverging-likert-matplotlib,f-acf-pacf-plotly,f-line-stock-comparison-pygal,f-gantt-basic-echarts
   ```

6. Once the first production regenerations have run, read their gate records (see [Monitor the regen gate](#monitor-the-regen-gate)):

   ```bash
   uv run python -m automation.scripts.review_retest gate-report --since 2026-09-27
   ```

---

## Run a baseline and a candidate arm

1. Check that the production pipeline is idle. The prep job refuses while `impl-generate`, `impl-review`, `impl-repair`, `bulk-generate`, or `daily-regen` has a queued run or one that started less than six hours ago, because the retest shares the Claude usage window.
2. Dispatch the baseline from `main`:

   ```bash
   gh workflow run review-retest.yml -f rules_ref=0674ab6b55acc71f5015a6aae07145424cbac7cb -f models=production -f label=baseline
   ```

   The set's baseline is `0674ab6b5` (`baseline_rules_sha` in the manifest). With `models=production`, every cell runs on Opus. Re-run it whenever the resolved model IDs change.
3. Note the baseline's run ID once it finishes.
4. Dispatch the candidate from `main`, naming the commit that carries the rules change (a pushed branch commit works before the merge):

   ```bash
   gh workflow run review-retest.yml -f rules_ref=<candidate-sha> -f label=<short-name> -f compare_to=<baseline-run-id>
   ```

5. Open the candidate run's summary and paste the fenced snippet into the pull request body.

To measure on set v2, add `-f set=v2` to both arms, and give the baseline the rules the candidate branches from (`baseline_rules_sha` in `set-v2.yaml` is `9a6ed1952`):

```bash
gh workflow run review-retest.yml -f set=v2 -f rules_ref=9a6ed19528c5ecaa6b16ab84a9ed20c932d46445 -f label=v2-baseline
```

To measure on set v3, add `-f set=v3`. Its baseline runs `main`'s rules on the pinned spec text. A candidate that depends on a later spec clause (the every-root clause, a `Check values:` bullet) runs with `-f spec_source=rules_ref`, so the reviewer reads the spec text at `rules_ref`. Such a comparison changes the rules and the spec text together: attribute an effect by the label that only one of them can move, not by the arm.

```bash
gh workflow run review-retest.yml -f set=v3 -f label=v3-baseline
gh workflow run review-retest.yml -f set=v3 -f rules_ref=<candidate-sha> -f spec_source=rules_ref -f label=<short-name> -f compare_to=<baseline-run-id>
```

Compare two arms of the same set; the report flags "set changed" when they differ.

To finish an arm that stopped early (a usage limit, a cancelled run), dispatch it again with the same inputs and `resume_from=<run-id>`: cells that already produced a review are reused, and only the rest run.

A cell is reused only when its record was measured the way the new run measures: the same set, harness version (`HARNESS_VERSION`), action pin, rules commit, `spec_source`, and the model that cell runs on. The prep job drops any other record with a warning that names the mismatch, and that cell runs again; the report merges exactly the cells the prep job reused. The dispatch commit itself isn't compared, so you can resume from a newer `main`. Give `rules_ref` as a commit SHA: a branch name, or the default, resolves to a new commit once the branch moves, and then no cell matches.

Reuse a baseline only when the set, the harness version, the action pin, and the resolved models all match and it's less than 14 days old. A model alias (`sonnet`, `opus`) moves between releases, and the report flags "model changed" when two arms resolved different models.

The all-Opus baseline for set v1 at rules `0674ab6b5` is run 36389481950 (2026-09-28, every cell on `claude-opus-5`; its 45 fresh cells are reused from 36354452853). The regen cells of 36354452853 ran on Sonnet, so they are a Sonnet reference only; its fresh cells ran on Opus and stay valid. The all-Opus baseline that the lean-code change (#12005) was measured against is run 36782558185 (2026-10-01, rules `748d230c9`, 87 cells on `claude-opus-5`). The latest all-Opus arm on set v1 is run 37233543394 (2026-10-04, rules `c64630aa7`, the first-review scoring rubric of #12046, 87 cells on `claude-opus-5`). On set v3, the baseline at `main`'s rules on the pinned spec text is run 37051224946 (2026-10-02, rules `033e2795d`), and the latest arm is run 37223476129 (2026-10-04, rules `c64630aa7`, `spec_source=rules_ref`). The pull request merged with `main` after those arms ran, so its merged rules also carry the DQ-02 wording of #12050, which neither set exercises. A rubric pull request that runs a later all-Opus arm at its own rules updates this paragraph.

---

## Inputs

| Input | Default | Meaning |
|---|---|---|
| `rules_ref` | the dispatched commit | Commit or branch whose `prompts/` and `regen_gate.py` the reviewer uses |
| `label` | none | Arm name in the report |
| `set` | `v1` | The frozen set: `v1`, `v2`, or `v3` (`automation/retest/set-<set>.yaml` and its lock) |
| `subset` | `core` | `core`, `full`, or comma-separated item IDs of the chosen set |
| `models` | `production` | `production` (every cell on Opus, as `impl-review.yml` reviews), `sonnet`, or `opus` |
| `runs` | `3` | Sessions per item and order (1–10) |
| `orders` | `both` | Regen pairs: `both` orders or `forward` only; a pair marked `orders: forward` in its manifest runs forward either way |
| `spec_source` | `pinned` | `pinned` spec text, or the spec text at `rules_ref` (for spec backfills) |
| `compare_to` | none | Run ID of the baseline arm |
| `resume_from` | none | Run ID of an incomplete arm to finish; only its cells that match this arm are reused |
| `max_parallel` | `6` | Concurrent sessions |

The prep job also refuses more than 240 sessions, and regen cells on rules older than `02e1a7974` (the first regen gate with a blind re-score).

---

## Read the report

Every metric is grouped by kind (fresh or regen) and resolved model. A cell whose session named no model forms its own `unresolved (<alias>)` group, and any unresolved group raises the "model changed" flag in a comparison. A *unit* is an item for fresh cells and an item-order for regen cells.

- **Criteria.** Per criterion: mean, the share of runs at the maximum (a ceiling effect, not reliability), the pooled within-unit standard deviation, and the flip rate (units whose runs differ). Every pooled standard deviation in the report weights each unit by its degrees of freedom (runs − 1), so a unit that lost runs to a usage limit counts for less.
- **Totals.** The typed score (`quality_score.txt`) and the checklist sum, each with its pooled standard deviation, and the share of runs where they differ. Units with an auto-reject run are listed apart, because 0 against 90 would swamp any spread.
- **Verdicts.** Fresh units whose runs straddle the approval line of 90, and the pairwise disagreement rate.
- **Weaknesses.** Count per review; the mean pairwise topic Jaccard within a unit (taxonomy `topics-v1`); a Jaccard on criterion IDs when weaknesses start with one; the share of "add X" weaknesses; the share of below-maximum comments with no limiting word.
- **Silent deductions.** Of the technical items (the 19 VQ, SC, DQ, and CQ criteria) that a run scores below their maximum, the share that no defect line of that run names, and the share of runs with at least one. A deduction without a defect line leaves a repair nothing to act on, and it's how the same gap becomes a lost point on one library and a `Suggestion:` on another. DE and LM items are judgments and never count; a `Suggestion:` line names nothing; an auto-rejected run is left out. The metric reads the records' checklist and weaknesses, so a rebuilt report of an older arm shows it too. An arm on rules older than the defect line format has no defect lines, and every deduction there reads as silent.
- **Named defects and permission probes** (once the labels are confirmed). A defect is caught in a run when one of its criteria is below the maximum and its pattern matches a weakness or that criterion's comment. A permitted feature raises a false alarm when a weakness names it or a listed criterion is deducted with a comment that names it. A defect that is never caught is flagged as a possibly wrong label. A label with `spec_source: rules_ref` counts only in runs whose reviewer saw the spec text at `rules_ref`: set v3 uses it for a defect that only a later spec clause makes one.
- **Gate** (regen units). Verdict flip rate, accuracy against the expected verdicts, the spread of the re-score, the new score and their difference, and the tolerance calibration on identity and near-identical pairs (the share with `new − prev_rescored < −1`, the share claiming a visible improvement the gate counts). A counted improvement never cites an `Expected, not a defect:` bullet of the spec; the share of runs that cite one anyway is reported apart. On identity and near-identical pairs the calibration also reports the share claiming a *carrier* (a verified defect or an `A good version shows:` property, the only kind that can carry a merge), which should be near zero. The share of runs citing a weakness the review classed obsolete is reported apart as well, and **class flip** is the share of (unit, `W` id) pairs whose defect, suggestion, or obsolete class differs across runs. The harness classifies with its own copy of the gate, so a baseline arm on older prompts, which writes no classification, counts every cited `W` as a suggestion. **Order bias** is the mean of `rescore(X as predecessor) − blind(X as new)` over both versions of a pair; a negative value means a version scores lower when it is the predecessor, which biases the gate toward merge.
- **Forward merges without a labeled carrier** (`merges_without_carrier`, regen items with a `fixes` label). Of the forward-order runs the gate merged, the share in which no counted visible improvement (not a permission, a non-empty `where_visible`) matches one of the pair's `fixes` labels or cites an affirmative characteristic (a C ID of the spec the reviewer saw that isn't an `Expected, not a defect:` bullet). It reads only the improvements' `ref`, `what`, and `where_visible`, so it means the same under every rules version. Replayed on verification round 1, it gives 6 of 12: half of that round's merges rested on a suggestion or an obsolete weakness.
- **Comparison.** Paired by unit: the change in mean and pooled standard deviation with a 95% bootstrap interval (fixed seed), and soft flags: "noise up" when the interval for the change in spread lies above zero, "model changed", "harness changed", "set changed", and "label set differs" when the two arms counted different defects or probes (a spec-gated label, or a unit one arm lost).

With 15 items and 3 runs, the pooled standard deviation has about 30 degrees of freedom, and a shift of about 1 point in the mean total is detectable. Verdict-flip rates carry intervals of roughly ±15 points: read them as a direction, never as a gate.

---

## Cost and the usage window

API-equivalent cost per session, measured on set v1 core at rules `0674ab6b5`: $2.14 for an Opus fresh review (run 36354452853), $2.64 for an Opus regen review (run 36389481950), $0.76 for a Sonnet fresh review (run 36359464410), and $0.98 for a Sonnet regen review (run 36354452853). A set v1 core arm with production routing is 87 Opus sessions (15 fresh items × 3, 7 pairs × 2 orders × 3), about $207 and about 1.5 hours at 6 in parallel. A set v2 arm is 66 Opus regen sessions (10 pairs × 2 orders × 3, 2 forward-only pairs × 3), about $174. A set v3 arm is 45 Opus fresh sessions (15 items × 3). The lean-code arm of 2026-10-01 (run 36782726606) measured $2.67 for an Opus fresh review and $3.47 for an Opus regen review, above the constants the plan step still prints, so budget about $120 for a set v3 arm and about $270 for a set v1 core arm. Under the subscription token the real limit is the rolling usage window shared with production; an Opus session uses it about 2.7 to 2.8 times as fast as a Sonnet one. Matrix jobs start roughly in list order, which is run-major, so a partial arm still has balanced passes; this is best effort, not a guarantee.

---

## Curate, freeze, and refresh the set

The manifest is hand-curated; the lock and the public renders are written once by `freeze`. A frozen set is never rewritten: any change to an item or a render is a new set (`v2`, a new prefix, a new lock).

### Build and upload a set

Each upload is a one-time, owner-authorized write with no clobber and no deletes: set v1 is 94 objects (27 fresh items × 2 renders, 10 pairs × 4 renders; the core tier alone is 58), about 20 MB, set v2 is 48 objects (12 pairs × 4 renders), about 5.4 MB, and set v3 is 30 objects (15 fresh items × 2 renders), about 6.2 MB. Run it from the owner's checkout, where the snapshots live: `agentic/runs/regen-exp-bubble-basic/` for set v1, `agentic/runs/verify-b1-regens/` for set v2, and `agentic/runs/regen-exp-bubble-basic/tanabe-firstgen-2026-10-01/` for set v3. The commands below build set v1; for another set, add `--manifest automation/retest/set-<set>.yaml --lock automation/retest/set-<set>.lock.json` to steps 2, 3, and 5, and `--snapshots-root <checkout root>` when you run them from a worktree without the snapshots.

1. Fetch `main`, so `freeze` can check that no implementation changed after its pinned commit:

   ```bash
   git fetch origin main
   ```

2. Check every source without downloading a render. This reads only the 24-byte PNG header of each render (an HTTP range request for production objects) and reports every canvas, pin, and snapshot problem `freeze` would refuse, in one pass:

   ```bash
   uv run python -m automation.scripts.review_retest validate --check-git --check-renders
   ```

3. Build the set in a new local directory (a dry run: it downloads the production renders, copies the snapshot renders, checks canvases and hashes, measures the pairs, and prints the exact upload commands):

   ```bash
   uv run python -m automation.scripts.review_retest freeze --staging /tmp/retest-set-v1
   ```

4. Review the printed pixel statistics (identity pairs must be 0 %; a pair whose renders differ in size says so) and the `gcloud storage cp --no-clobber` commands.
5. Upload, verify every public object against the lock, and write the lock:

   ```bash
   uv run python -m automation.scripts.review_retest freeze --staging /tmp/retest-set-v1 --execute --write-lock
   ```

6. Commit the set's lock, for example `automation/retest/set-v1.lock.json`.
7. Smoke-test one cell of the new set, and check that the run left no comment, label, or dispatch behind. The workflow is on the default branch since set v1, so a later set can be tested from its own branch before it merges:

   ```bash
   gh workflow run review-retest.yml --ref <branch> -f set=<set> -f subset=<one item id> -f runs=1 -f label=smoke
   ```

   Set v1 was frozen in the pull request that added the workflow, so its smoke test is the first step of [First runs after the merge](#first-runs-after-the-merge).

`freeze` refuses while the pipeline is busy, when a render isn't on a canonical canvas (3200 × 1800 or 2400 × 2400), when a production render's implementation changed on `main` after the pinned commit, when a snapshot was taken at another commit, when an identity pair's renders differ, and when an object already exists with different content. It collects every refusal and lists them together at the end of the run. The one render that may be off-canvas is the predecessor of a pair marked `orders: forward`: `impl-review.yml` shows a predecessor as production stores it, but in the reversed order that render would be the version under review, which production's canvas gate keeps without a review.

### Confirm the labels

Defects, permitted features, fixes, and expected gate verdicts are ground truth. Each item's `note` is the pre-screen; the `defects`, `permitted`, `fixes`, and `expected` entries turn it into labels (the shapes are in the manifests' headers), and the owner confirms them by setting `labels: confirmed`. A `fixes` entry, on regen pairs only, names a predecessor defect that the forward new version visibly fixes: carrier criteria only (VQ, SC, DQ, or CQ, never DE, LM, or DQ-01), and a pattern matched against the `what` text of the review's improvements. `fixes: []` labels a pair whose new version fixes no defect; a pair without the key stays out of the carrier metric. The set v2 patterns match every improvement round 1 cited for a fixed defect and none of its suggestions or obsolete weaknesses, which `tests/unit/automation/scripts/test_retest_set_v2.py` checks. One set v2 label rests on no round-1 citation: at confirmation the owner read #11960 as a fixed defect round 1 did not cite (the gridline through the bold value label), so its pattern is checked against the retest arms' citations instead. While the manifest says `labels: draft`, `validate` checks the entries but every report ignores them, so no pull request quotes a miss rate against unconfirmed ground truth. Labels are versioned with the set but may be corrected without a new set; because they are applied when the report is built, a corrected label re-scores old records when you rebuild their report.

### Refresh

Refresh the set about once a year, or when the catalogue has moved on: copy a manifest to the next `set-v<N>.yaml`, curate, freeze it, and add `v<N>` to the options of the workflow's `set` input. Keep at least one true identity pair per language family and label the near-identical pairs with their measured pixel statistics. A set can also answer one question, as set v2 answers whether a regeneration merges on a fixed defect.

---

## Monitor the regen gate

Every production regen decision leaves a `<!-- regen-gate-record:v1 {...} -->` marker in its pull request comment (see [Regen gate](overview.md#regen-gate-regenerations)). `gate-report` reads the markers of every pull request labelled `regen:kept` or `regen:improved` and aggregates them:

```bash
uv run python -m automation.scripts.review_retest gate-report --since 2026-10-01
```

It reports the following:

- The number of decisions, the merge rate, and the reason codes.
- `prev_rescored − prev_stored` (mean, median, standard deviation, and bootstrap interval), split into *comparable* decisions (the stored review ran under the same model and the same `qc` and `aqr` rules version) and all, and by model and library.
- The share of decisions whose `new − prev_rescored` lies inside [−1, 0].
- The record's improvement counts as the gate wrote them: `visible` counts only the improvements the gate counted, never one that cites an `Expected, not a defect:` bullet or a weakness the re-score classed obsolete, and `permission` counts the cited permissions. The report shows the mean counted visible improvements per decision, how many decisions cited a permission, and how many were kept with nothing else counted. Records written before the obsolete class existed still count obsolete citations in `visible`.
- The carrier counts (records from the defect-and-suggestion gate on): the mean carriers per decision, the share with at least one carrier, the `no_defect_improvement` count, the share citing an obsolete weakness, and the shares with an unverified claim (a rule the scores don't confirm, or none) and with a design, library-mastery, or feature-coverage point.
- The kind counts (records from P3.1 on): the share of listed improvements that name a kind, the shares of decisions with an addition, with polish, and with a would-be carrier that names no kind, and the share of merges carried only by `P` or `new` items (predecessor defects the re-score found itself).
- One count per `writeback` value of the keep records (`opened`, `unchanged`, `no_rescore`, `invalid`, `stale`, `failed`): what happened to each kept implementation's re-score (see [Stored review on a keep](overview.md#stored-review-on-a-keep)). Keep records written before the write-back have no `writeback` and are left out. `opened` counts dispatched merges; compare it with the merged pull requests labelled `review-writeback` to find a stranded one.
- A weekly trend.

It raises soft alarms for possible contrast bias (at least 20 comparable decisions averaging −1.5 or lower), for `regen_json_invalid` in more than 10% of decisions, for a merge rate above 50% or below 5% over at least 30 decisions, for reviews that cite an `Expected, not a defect:` bullet or an obsolete weakness as an improvement in more than 10% of at least 10 decisions (the 8b prompt or the specs' characteristic kinds need a look), for unverified claims in more than 20% of at least 10 decisions (the review's self-check or the defect definitions need work), for a would-be carrier without a kind in more than 5% of at least 10 decisions (the 8b kind sentence or the self-check needs a look), and for `writeback: invalid` in more than 10% of at least 10 keep records (the prompt's `review_prev.json` step needs work). Design and library-mastery points raise no alarm: DE deductions are normal on specs that are not `-basic`.

For months most predecessors will carry stored reviews from other models and rules, so "all" measures rules, model, and render-age drift; the clean contrast-bias number is the retest's order bias on the frozen pairs.

---

## Read the live first reviews

The retest measures the reviewer on a frozen set. `first-reviews` reads what the reviewer did in production: the `## AI Review - Attempt N/3` comments of every first-generation pull request (branch `implementation/<spec>/<library>`, no `regen` label) created on or after a date. It only reads GitHub, costs nothing, and needs `gh`:

```bash
uv run python -m automation.scripts.review_retest first-reviews --since 2026-10-01
```

Add `--json <path>` to keep the aggregate. It reports the following:

- The attempt-1 scores: mean, standard deviation, histogram, how many reached the approval line of 90, and the share at 90 or 91. A pile at exactly the line with few scores just below it is the signature of a reviewer that aims at the line.
- Per spec, the spread of the attempt-1 scores between the libraries and the criteria on which no library differs. Compare the spread with the reviewer's run-to-run spread on one file (about 2 points on set v1): a smaller spread between 15 libraries means the scores don't tell the implementations apart.
- Silent deductions on the attempt-1 reviews, with the pull requests and the items (the same definition as in [Read the report](#read-the-report)).
- Per repair: the score before and after, the gain on the technical items against the gain on the judgment items (DE and LM), and whether the repair committed anything. A repair fixes defect lines, so a gain on the judgment items, or any gain without a commit, comes from the second review and not from the repair.

Run on the 15 `line-tanabe-sugano` pull requests of 2026-10-01, it gives a mean of 88.7 with 6 of 15 at exactly 90, a spread of 1.7 between the libraries (the sample standard deviation), 12 criteria without any variance, 7 silent deductions in 27 deducted technical items, and 14 of the 18 points that eight repairs gained on judgment items, 4 of them on a file that no repair commit touched (#12028).

---

## Limitations

- It measures the judge, not the generator.
- Small samples: report the intervals, grow the set from the core toward the full set, and never use the retest as a hard CI gate.
- The local `/regen` command writes metadata without the review provenance fields, so its decisions carry no gate record.
- Whether claude-code-action accepts the read-only job token is confirmed on the first smoke run after the merge; if it doesn't, the fallback is `pull-requests: read`, never a write permission.
- Set v1's spec text is pinned at `0674ab6b5`, before characteristic bullets carried their kind (`A good version shows:` / `Expected, not a defect:`). Arms on later rules therefore read the pinned sections by meaning, as the review prompt asks for an unlabeled section; measure a spec backfill with `spec_source=rules_ref`. Set v2's specs, pinned at `0ccb3fec1`, carry the kinds.
- Set v3 is one spec. It measures how the review behaves near the approval line, not across the catalogue; set v1 covers the breadth. Its label patterns carry a leading lookahead that skips `Suggestion:` lines, because a suggestion costs no points: a suggestion neither catches a defect nor raises a false alarm there, while the labels of set v1 count one either way.
- A label with `spec_source: rules_ref` reads the source, not the spec text. Set v3's lowest-root label assumes a `rules_ref` at or after `251b3efdb`, the first commit whose spec asks for every root. A comparison across spec sources counts different labels in the two arms, and the report flags it as "label set differs".
- The carrier metric matches words, not meaning: a review that describes a real fix in words no `fixes` pattern knows counts as a merge without a carrier. Read the runs it flags before you act on the number, and widen a pattern (a label correction, no new set) when it missed a genuine fix.
