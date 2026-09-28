# Review retest

> **Status (2026-09-27):** The harness (`automation/scripts/review_retest.py`), the workflow (`.github/workflows/review-retest.yml`), and set v1 (`automation/retest/set-v1.yaml`) exist, and set v1 is frozen: `automation/retest/set-v1.lock.json` pins its 94 public renders. The workflow has no effect until someone dispatches it, and GitHub dispatches a `workflow_dispatch`-only workflow only once it is on the default branch, so its first run, the one-cell smoke test in [First runs after the merge](#first-runs-after-the-merge), happens right after it merges. The ground-truth labels in the manifest are proposals (`labels: draft`) until the owner confirms them; until then the named-defect, false-alarm, and gate-accuracy metrics stay empty.

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

- **The set.** `automation/retest/set-v1.yaml` lists the items. A *fresh* item is one implementation, reviewed the way a first implementation is. A *regen* item is a pair (new version and predecessor), reviewed the way a regeneration is: the new render blind, then the predecessor re-scored, then the regen gate. Sources are pinned by commit; renders are public objects under `gs://anyplot-images/retest/sets/v1/`, and `automation/retest/set-v1.lock.json` holds their sha256, size, and the pairs' pixel statistics. The prep job downloads them anonymously over HTTPS and checks every hash.
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

To finish an arm that stopped early (a usage limit, a cancelled run), dispatch it again with the same inputs and `resume_from=<run-id>`: cells that already produced a review are reused, and only the rest run.

A cell is reused only when its record was measured the way the new run measures: the same set, harness version (`HARNESS_VERSION`), action pin, rules commit, `spec_source`, and the model that cell runs on. The prep job drops any other record with a warning that names the mismatch, and that cell runs again; the report merges exactly the cells the prep job reused. The dispatch commit itself isn't compared, so you can resume from a newer `main`. Give `rules_ref` as a commit SHA: a branch name, or the default, resolves to a new commit once the branch moves, and then no cell matches.

Reuse a baseline only when the set, the harness version, the action pin, and the resolved models all match and it's less than 14 days old. A model alias (`sonnet`, `opus`) moves between releases, and the report flags "model changed" when two arms resolved different models.

The all-Opus baseline for set v1 at rules `0674ab6b5` is run 36389481950 (2026-09-28, every cell on `claude-opus-5`; its 45 fresh cells are reused from 36354452853). The regen cells of 36354452853 ran on Sonnet, so they are a Sonnet reference only; its fresh cells ran on Opus and stay valid. A rubric pull request that runs a later all-Opus arm at its own rules updates this paragraph.

---

## Inputs

| Input | Default | Meaning |
|---|---|---|
| `rules_ref` | the dispatched commit | Commit or branch whose `prompts/` and `regen_gate.py` the reviewer uses |
| `label` | none | Arm name in the report |
| `subset` | `core` | `core`, `full`, or comma-separated item IDs |
| `models` | `production` | `production` (every cell on Opus, as `impl-review.yml` reviews), `sonnet`, or `opus` |
| `runs` | `3` | Sessions per item and order (1–10) |
| `orders` | `both` | Regen pairs: `both` orders or `forward` only |
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
- **Named defects and permission probes** (once the labels are confirmed). A defect is caught in a run when one of its criteria is below the maximum and its pattern matches a weakness or that criterion's comment. A permitted feature raises a false alarm when a weakness names it or a listed criterion is deducted with a comment that names it. A defect that is never caught is flagged as a possibly wrong label.
- **Gate** (regen units). Verdict flip rate, accuracy against the expected verdicts, the spread of the re-score, the new score and their difference, and the tolerance calibration on identity and near-identical pairs (the share with `new − prev_rescored < −1`, the share claiming a visible improvement the gate counts). A counted improvement never cites an `Expected, not a defect:` bullet of the spec; the share of runs that cite one anyway is reported apart. **Order bias** is the mean of `rescore(X as predecessor) − blind(X as new)` over both versions of a pair; a negative value means a version scores lower when it is the predecessor, which biases the gate toward merge.
- **Comparison.** Paired by unit: the change in mean and pooled standard deviation with a 95% bootstrap interval (fixed seed), and soft flags: "noise up" when the interval for the change in spread lies above zero, "model changed", "harness changed", "set changed".

With 15 items and 3 runs, the pooled standard deviation has about 30 degrees of freedom, and a shift of about 1 point in the mean total is detectable. Verdict-flip rates carry intervals of roughly ±15 points: read them as a direction, never as a gate.

---

## Cost and the usage window

API-equivalent cost per session, measured on set v1 core at rules `0674ab6b5`: $2.14 for an Opus fresh review (run 36354452853), $2.64 for an Opus regen review (run 36389481950), $0.76 for a Sonnet fresh review (run 36359464410), and $0.98 for a Sonnet regen review (run 36354452853). A core arm with production routing is 87 Opus sessions (15 fresh items × 3, 7 pairs × 2 orders × 3), about $207 and about 1.5 hours at 6 in parallel. Under the subscription token the real limit is the rolling usage window shared with production; an Opus session uses it about 2.7 to 2.8 times as fast as a Sonnet one. Matrix jobs start roughly in list order, which is run-major, so a partial arm still has balanced passes; this is best effort, not a guarantee.

---

## Curate, freeze, and refresh the set

The manifest is hand-curated; the lock and the public renders are written once by `freeze`. A frozen set is never rewritten: any change to an item or a render is a new set (`v2`, a new prefix, a new lock).

### Build and upload a set

The upload is a one-time, owner-authorized write of 94 objects (27 fresh items × 2 renders, 10 pairs × 4 renders; the core tier alone is 58), about 20 MB, with no clobber and no deletes. Run it from the owner's checkout, where the regen-experiment snapshots live under `agentic/runs/regen-exp-bubble-basic/`.

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

4. Review the printed pixel statistics (identity pairs must be 0 %) and the `gcloud storage cp --no-clobber` commands.
5. Upload, verify every public object against the lock, and write the lock:

   ```bash
   uv run python -m automation.scripts.review_retest freeze --staging /tmp/retest-set-v1 --execute --write-lock
   ```

6. Commit `automation/retest/set-v1.lock.json`.
7. Smoke-test one cell of the new set, and check that the run left no comment, label, or dispatch behind. The workflow is on the default branch since set v1, so a later set can be tested from its own branch before it merges:

   ```bash
   gh workflow run review-retest.yml --ref <branch> -f subset=<one item id> -f runs=1 -f label=smoke
   ```

   Set v1 was frozen in the pull request that added the workflow, so its smoke test is the first step of [First runs after the merge](#first-runs-after-the-merge).

`freeze` refuses while the pipeline is busy, when a render isn't on a canonical canvas (3200 × 1800 or 2400 × 2400), when a production render's implementation changed on `main` after the pinned commit, when a snapshot was taken at another commit, when an identity pair's renders differ, and when an object already exists with different content. It collects every refusal and lists them together at the end of the run.

### Confirm the labels

Defects, permitted features, and expected gate verdicts are ground truth. Each item's `note` is the pre-screen; the `defects`, `permitted`, and `expected` entries turn it into labels (the shapes are in the manifest's header), and the owner confirms them by setting `labels: confirmed`. While the manifest says `labels: draft`, `validate` checks the entries but every report ignores them, so no pull request quotes a miss rate against unconfirmed ground truth. Labels are versioned with the set but may be corrected without a new set; because they are applied when the report is built, a corrected label re-scores old records when you rebuild their report.

### Refresh

Refresh the set about once a year, or when the catalogue has moved on: copy the manifest to `set-v2.yaml`, curate, and freeze `v2`. Keep at least one true identity pair per language family and label the near-identical pairs with their measured pixel statistics.

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
- The record's improvement counts as the gate wrote them: `visible` counts only the improvements the gate counted, never one that cites an `Expected, not a defect:` bullet, and `permission` counts those citations. The report shows the mean counted visible improvements per decision, how many decisions cited a permission, and how many were kept with nothing else counted.
- A weekly trend.

It raises soft alarms for possible contrast bias (at least 20 comparable decisions averaging −1.5 or lower), for `regen_json_invalid` in more than 10% of decisions, for a merge rate above 50% or below 5% over at least 30 decisions, and for reviews that cite an `Expected, not a defect:` bullet as an improvement in more than 10% of at least 10 decisions (the 8b prompt or the specs' characteristic kinds need a look).

For months most predecessors will carry stored reviews from other models and rules, so "all" measures rules, model, and render-age drift; the clean contrast-bias number is the retest's order bias on the frozen pairs.

---

## Limitations

- It measures the judge, not the generator.
- Small samples: report the intervals, grow the set from the core toward the full set, and never use the retest as a hard CI gate.
- The local `/regen` command writes metadata without the review provenance fields, so its decisions carry no gate record.
- Whether claude-code-action accepts the read-only job token is confirmed on the first smoke run after the merge; if it doesn't, the fallback is `pull-requests: read`, never a write permission.
- The spec text is pinned at `0674ab6b5`, before characteristic bullets carried their kind (`A good version shows:` / `Expected, not a defect:`). Arms on later rules therefore read the pinned sections by meaning, as the review prompt asks for an unlabeled section; measure a spec backfill with `spec_source=rules_ref`.
