# Workflow overview

## How anyplot automation works

anyplot uses GitHub Actions to automate the entire plot lifecycle: from specification creation to implementation generation, quality review, and deployment.

---

## The two main pipelines

### 1. Specification pipeline

```
Issue + [spec-request] label
       |
       v
spec-create.yml
  |-- Creates branch: specification/{spec-id}
  |-- Generates: specification.md + specification.yaml
  |-- Claude opens the PR --> main as claude[bot] (CI runs without a manual approval)
  |-- Posts analysis comment
       |
       v (repository owner adds [approved] label to Issue)
       |
spec-create.yml (merge job)
  |-- Verifies the PR: opened by the Claude app, from specification/{spec-id}
  |   into main, references the issue, changes only the spec files
  |-- Enables auto-merge: GitHub squash-merges once the required checks pass
  |-- Waits up to 15 minutes for the merge to land
  |-- Dispatches sync-postgres.yml
  |-- Adds [spec-ready] label
```

The spec PR is opened by the Claude GitHub App rather than by the workflow's
`GITHUB_TOKEN`. Since GitHub's
[2026-06-11 change](https://github.blog/changelog/2026-06-11-bot-created-pull-requests-can-run-workflows-if-approved/),
workflow runs on a pull request that `GITHUB_TOKEN` opens or updates wait at
`action_required` until someone approves them, so a `GITHUB_TOKEN` spec PR never
got the required checks and could not merge on its own.

The merge job acts only on an `approved` label that the repository owner adds.
It refuses, with a comment on the issue, any PR that fails a check — for
example, one that changes a file outside `plots/{spec-id}/specification.md`,
`specification.yaml`, and the `.gitkeep` placeholders under `implementations/`
and `metadata/`. Don't approve pending workflow runs for such a PR, and don't
merge it by hand. If the merge doesn't land within 15 minutes, the job turns
auto-merge off again and says so on the issue; once the checks are green,
re-run the job or remove and re-add `approved`.

#### The "What a good version looks like" section

Every `specification.md` that spec-create writes ends with a
`## What a good version looks like` section: 3-6 one-line bullets that name what
a viewer sees in a good render of that plot type. Each bullet starts with its
kind, and each bullet has one kind:

- `A good version shows:` is an affirmative property. The review deducts points
  when a render misses or violates it, and it's the only kind a regeneration
  can cite as an improvement.
- `Expected, not a defect:` is a permission: something that can look like a
  flaw but is inherent to the type, such as overlapping bubbles in a dense
  bubble chart. The review never penalizes it, and generation never targets it.
  How a good version handles it goes in its own `A good version shows:` bullet.

Every section has at least one bullet of each kind. How the pipeline uses it:

- The AI review (`impl-review.yml`) scores every implementation against this
  section: it never lists something an `Expected, not a defect:` bullet names
  as a weakness, and it deducts when an `A good version shows:` property is
  missing. When a spec has no section, the review infers the same from
  Description, Data, and Notes.
- Generation and repair build toward the `A good version shows:` bullets and
  decline review weaknesses that contradict the section.
- The daily spec polish (`daily-regen.yml`) never adds, edits, or removes the
  section.
- The Postgres sync doesn't store the section, so the website doesn't show it.
- CI checks the section on every PR and every push to `main`. The "Run Tests"
  job runs `automation/scripts/spec_characteristics_lint.py`: `contract` over
  every spec, which blocks, and `style` over the changed specs, which only
  warns. A spec PR whose section fails the contract can't merge: fix the
  section on the branch, then remove and re-add `approved`.

The regen gate numbers the bullets `C1`..`Cn` in document order and never
compares these ids across PRs. Append new bullets at the end, and edit a
section only when no regeneration PR for that spec is open.

On a `-basic` spec, the `A good version shows:` bullet that sets the basic
variant's scope names reference lines, highlights, and callouts, as excluded
or, where the Notes allow them, as allowed. The review and regeneration read
that list as complete, so a layer the bullet leaves out reads as permitted. The
style lint warns (W7) when one of the three is missing.

When you review a spec PR before adding `approved`, check this section too: it
must describe the plot type rather than generic ideals such as "no overlap",
contain no numeric thresholds, and not contradict Description, Data, or Notes.

### 2. Report pipeline

See [Report Issues](report-issue.md) for details.

One unified template: **report-plot-issue.yml** - Report any plot problem (spec or implementation)

```
User reports issue (from anyplot.ai or GitHub)
       |
       v (report-pending label auto-added)
       |
report-validate.yml
  |-- Validates spec/impl exists
  |-- AI analyzes the issue
  |-- Posts structured analysis comment
  |-- Updates labels: report-validated + category:*
       |
       v
Ready for maintainer review (fix manually)
```

### 3. Implementation pipeline

```
Issue + [generate:{library}] label  OR  workflow_dispatch
       |
       v
impl-generate.yml
  |-- Creates branch: implementation/{spec-id}/{library}
  |-- AI generates code
  |-- Creates metadata/python/{library}.yaml (initial)
  |-- Tests execution
  |-- Uploads preview to GCS staging
  |-- Creates PR --> main
       |
       v
impl-review.yml
  |-- AI evaluates code + image
  |-- Posts review comment with score
  |-- Updates metadata/python/{library}.yaml (quality_score, review feedback)
  |-- Adds [quality:XX] label
       |
       |-- Meet Threshold --> [ai-approved] --> impl-merge.yml
       |                                        |-- Squash merge
       |                                        |-- Promotes GCS: staging --> production
       |                                        |-- Triggers sync-postgres.yml
       |
       |-- Below Threshold --> [ai-rejected] --> impl-repair.yml (max 4 attempts)
       |                                       |-- Reads AI feedback
       |                                       |-- Fixes implementation
       |                                       |-- Re-triggers impl-review.yml
       |
       |-- Regeneration (implementation already on main) --> regen gate, one review, no repair
                |-- Replace --> [regen:improved] + [ai-approved] --> impl-merge.yml
                |-- Keep    --> [regen:kept] --> PR closed, live code and GCS unchanged
                                   |-- Stored review <-- re-score: [review-writeback] PR --> impl-merge.yml (writeback job)
```

---

## Label system

### Specification labels (on Issues)

| Label | Meaning | Set By |
|-------|---------|--------|
| `spec-request` | New specification request | User |
| `spec-ready` | Specification merged, ready for implementations | Workflow |

### Implementation labels (on Issues)

| Label | Meaning | Set By |
|-------|---------|--------|
| `generate:{library}` | Trigger generation for library | User |
| `impl:{library}:pending` | Generation in progress | Workflow |
| `impl:{library}:done` | Implementation merged to main | Workflow |
| `impl:{library}:failed` | Set by `impl-generate.yml` after three failed generation attempts for the pair within a 12-hour window, or by `impl-review.yml` when the PR still scores below 50 after four repair attempts. Infrastructure failures (provider incident, cloud auth, GitHub API) are retried on a separate cap of 5 and never set this label; a pair paused that way carries no label. | Workflow |

### PR labels (on Pull Requests)

| Label | Meaning | Set By |
|-------|---------|--------|
| `ai-approved` | Quality check passed (based on cascading thresholds) | Workflow |
| `ai-rejected` | Quality check failed, triggers repair | Workflow |
| `ai-attempt-1/2/3/4` | Retry counter | Workflow |
| `quality:XX` | Quality score (e.g., quality:92) | Workflow |
| `quality-poor` | Score < 50, needs fundamental fixes | Workflow |
| `regen` | Regeneration of an implementation that is live on main (marker for humans and the watchdog; `impl-review.yml` decides "regeneration" from `origin/main`) | Workflow |
| `regen:forced` | Regeneration dispatched with `regen_gate=false`: bypasses the regen gate and takes the fresh-generation path | Workflow |
| `regen:improved` | The regen gate replaced the live implementation (added before `ai-approved`) | Workflow |
| `regen:kept` | The regen gate kept the live implementation; the PR is closed unmerged | Workflow |
| `review-writeback` | A metadata PR that stores a kept regeneration's re-score as the live implementation's review (branch `review-writeback/{spec}/{library}/{kept PR}`); `impl-merge.yml` merges it | Workflow |

### Approval labels

| Label | Meaning | Set By |
|-------|---------|--------|
| `approved` | Human approved specification | Maintainer |
| `rejected` | Human rejected | Maintainer |

### Report labels (on Issues)

| Label | Meaning | Set By |
|-------|---------|--------|
| `report-pending` | Report submitted, awaiting validation | Auto (template) |
| `report-validated` | AI validated, ready for review | Workflow |
| `report:spec` | Issue with specification | Workflow |
| `report:impl` | Issue with implementation | Workflow |
| `report:impl:{library}` | Specific library affected | Workflow |
| `category:visual` | Design/visual issues | Workflow |
| `category:data` | Data quality issues | Workflow |
| `category:functional` | Non-functional elements | Workflow |
| `category:other` | Other issues | Workflow |

---

## Quality workflow (cascading thresholds)

- **Review 1 (Initial)**: Score >= 90
- **Review 2 (Repair 1)**: Score >= 80
- **Review 3 (Repair 2)**: Score >= 70
- **Review 4 (Repair 3)**: Score >= 60
- **Review 5 (Repair 4)**: Score >= 50
- **Failure**: < 50 after 4 repairs -> close PR, mark as failed (a forced regeneration keeps its live implementation and stays `impl:{library}:done`)

The cascade applies to fresh generations only. A regeneration takes the regen gate below.

### Review recovery

`impl-review.yml` re-runs a review at most once by itself, whatever the cause. A comment carrying the `<!-- review-retry:{spec}:{library} -->` marker records that retry:

- **No score.** The review wrote no `quality_score.txt` and no review comment ("Validate review output"): one retry through `repository_dispatch`.
- **Scored, then a later step failed before any verdict label landed.** For example, a GitHub 5xx on the `quality:N` label ("Re-dispatch review after a post-score failure"): one retry through `gh workflow run --ref` on the run's own ref. If the PR already has a verdict label (`ai-approved`, `ai-rejected`, `regen:improved`, or `regen:kept`), the step does nothing, and the watchdog's merge or repair cases take over.

The marker comment is written before the retry is dispatched, and a marker that can't be read counts as a spent retry, so a GitHub outage can't buy a second one. When the retry is spent, or the marker comment or the dispatch itself fails, the PR gets `ai-review-failed`. The watchdog re-dispatches the review once for a fresh generation and only flags a regeneration. A PR left with only `quality:N` and no verdict is picked up by the watchdog's never-reviewed case. `impl-review.yml` adds these labels with `GITHUB_TOKEN`, which doesn't start workflow runs, so `impl-review-retry.yml` reacts only to a label that a person adds.

The generation retry of `impl-generate.yml` and the post-score review retry run on the ref of the run that failed: a run dispatched from a feature branch retries on that branch, and a production run retries on `main`. The no-score review retry still goes through `repository_dispatch`, which always runs on `main`.

---

## Regen gate (regenerations)

A regeneration is an implementation PR for a (spec, library) pair that already has an implementation on main — for example every PR that `daily-regen.yml` produces. It gets one review and no repair loop, and the live implementation is replaced only when the new one is visibly better:

1. `impl-review.yml` detects the regeneration from `origin/main` (the implementation file exists there), downloads the predecessor's production renders to `/tmp/anyplot-prev-plot-{light,dark}.png` (outside the working directory), and writes the previous review with stable weakness ids `W1`..`Wn` — without its stored scores — to `/tmp/anyplot-prev-review.md`. Each `W` is tagged by its format: `(defect)` for a line that names the criterion it violates (`VQ-02 (light): … → …. Likely cause: ….`), `(suggestion)` for a `Suggestion: …` line, and `(older review)` for a line from before the two formats.
2. The review scores the new render blind (the prompt never shows it the stored score, and `impl-generate.yml` resets the new file's `Quality: N/100` header, which a regeneration inherits from its predecessor, to `Quality: pending` before the PR opens), then re-scores the predecessor's renders against the same criteria and writes its before/after judgement to `review_regen.json` (step 8b of `prompts/workflow-prompts/ai-quality-review.md`). The re-score records its 24 item scores (`prev_checklist`), classifies every previous weakness as a defect, a suggestion, or obsolete (an `Expected, not a defect:` bullet covers it), and gives every predecessor defect it found (`P1`, `P2`, …) the criterion it violates.
3. `automation/scripts/regen_gate.py` decides. Replace requires all of:
   - new score >= re-scored predecessor - 1 (the stored score is display-only);
   - at least one improvement with a named, visible location that doesn't cite an `Expected, not a defect:` bullet of the spec or a weakness the re-score classed obsolete (neither is ever an improvement; the gate lists such an item as not counted);
   - at least one visible improvement fixes a defect: a visual, spec, data (not feature coverage), or code defect (a defect-class weakness or a predecessor defect) that scores higher in the new review than in the re-score, or an `A good version shows:` property, and the review names its kind `fix` or `removal`. Suggestions, design, library-mastery, and feature-coverage points, additions of optional features, polish of an element the spec's scope excludes, improvements without a kind, and obsolete weaknesses never carry a replacement;
   - no regressions. On a `*-basic` spec, a replaced data scenario or added encodings count as regressions unless a change request asked for them.
4. Replace: `regen:improved`, then `ai-approved`, a PR comment with the same summary (stored, re-scored, and new score, improvements, regressions, reason), then the normal merge. Keep: `regen:kept`, the PR is closed with that comment, the issue gets `impl:{library}:done` back, and the live code and GCS production stay as they are. The re-score of the live implementation becomes its stored review through a separate metadata PR (see [Stored review on a keep](#stored-review-on-a-keep)).

A crashed regen review is auto-retried once by `impl-review.yml`; after that the PR carries `ai-review-failed` and the watchdog only flags it — it never dispatches a further review for a regeneration. The same one-retry budget covers a review of any PR that scored but failed before a verdict label landed, for example on a GitHub 5xx (see [Review recovery](#review-recovery)).

Anything missing or malformed — no `review_regen.json`, an unknown weakness id, missing previous renders, a failed canvas gate, a score of 0 — keeps the live implementation. The classification never invalidates the file, but every gap points toward keep: an unclassified weakness counts as a suggestion, and without `prev_checklist` or the new review's `review_checklist.json` no criterion claim verifies, so only an `A good version shows:` property can carry the replacement.

Every review writes its weaknesses in the two formats: defect lines first, then at most three `Suggestion:` lines. Generation and repair fix the defects and decline every suggestion. A non-gating step in `impl-review.yml` ("Check review feedback format") runs `regen_gate.py check-feedback --warn-only` and reports lines in neither format, and claims the scores don't confirm, as warnings; the review runs the same check on itself before it finishes.

Every decision leaves three traces:

- **The gate record in the PR comment.** Both the keep and the replace comment end with an invisible `<!-- regen-gate-record:v1 {...} -->` marker: one line of JSON with the scores, improvement and regression counts (the improvements split into carriers, suggestions, and obsolete citations; the suggestions name additions, polish, and improvements without a kind apart, and a histogram counts the kind of every listed improvement), the reason code (`merge`, `below_tolerance`, `no_visible_improvement`, `no_defect_improvement`, `regression`, `regen_json_invalid`, `canvas_failed`, and so on), and the provenance of both reviews (resolved model and rules version of this review and of the stored one). A keep record also says what happened to the re-score (`writeback`, see the next section). It holds no model-written text. PR comments are permanent, so read this first.
- **The notice line in the run log.** `::notice::regen_gate spec=… lib=… prev_stored=… prev_rescored=… new=… verdict=… code=… model=… criteria=… reason=…`. Run logs expire.
- **The pair artifact.** `regen-pair-<pr>-<attempt>` on the `impl-review.yml` run, kept 60 days: both renders, both sources (the predecessor's with its score hidden), the previous review, this review's files, and the gate record. The predecessor's production renders are overwritten on the next merge, so this is the only copy of what the gate compared.

`uv run python -m automation.scripts.review_retest gate-report` aggregates the records across pull requests: merge rate, reason codes, how far re-scored predecessors land from their stored scores, the counted visible improvements and carriers, cited permissions and obsolete weaknesses, what happened to the re-scores of kept implementations, and soft alarms. See [Review retest](review-retest.md#monitor-the-regen-gate).

### Stored review on a keep

A kept regeneration still reviewed the live implementation: the gate's re-score. That re-score becomes the implementation's stored review, so the next regeneration starts from current problems under the current model and rules. This happens on every keep, whether or not the model or the rules changed since the stored review.

1. The review writes the re-score as a full review, `review_prev.json` (step 8b of `ai-quality-review.md`, step 5): the image description of the production renders, the criteria checklist (item for item equal to `prev_checklist`, each category score the sum of its items), strengths, weaknesses (the predecessor defects `P1`, `P2`, … as defect lines, except one whose improvement the review names an `addition` or `polish`, which is written as a suggestion, then at most three suggestions), and a verdict. It has no score: the stored score is the gate's `prev_rescored`.
2. `impl-review.yml` ("Write back the re-score (regen keep)") checks the file with `automation/scripts/regen_writeback.py check`, confirms that `main` still holds the two files the review read, and commits the new `quality_score`, the five review fields, `review.model`, and `review.criteria_version` in the metadata, plus the number in the implementation's `Quality: N/100` header, on the branch `review-writeback/{spec}/{library}/{kept PR}`. It opens a PR labelled `review-writeback` with `GITHUB_TOKEN` and dispatches `impl-merge.yml`. `updated`, `review.rendered_at`, `impl_tags`, and the previews stay as they are: the code didn't change.
3. The `writeback` job of `impl-merge.yml` merges the PR with the admin token after three checks: the PR is the bot's, and its score, review model, and rules version equal the `prev_rescored`, `model`, and `criteria_version` of the kept PR's gate record (`check-pr`), the diff changes only those keys and the header number (`verify-diff`), and `main` hasn't changed the pair's files since the branch was cut (`check-fresh`, before every merge attempt). Then it triggers the database sync.

Any failure leaves the stored review as it was and closes the write-back PR; the keep itself is never held up. The keep record's `writeback` says what happened: `opened` (the PR exists and its merge was dispatched, not yet that it merged), `unchanged`, `no_rescore` (the gate had no valid `review_regen.json`), `invalid` (`review_prev.json` failed its check), `stale` (`main` changed the pair's files during the review), or `failed`. The kept comment has a matching **Stored review** line. A lost write-back heals at the pair's next gated regeneration, which re-scores the implementation again.

So a stored weakness list in the older format lasts only until the pair's first gated regeneration: a merge stores the new render's review, and a keep stores the re-score, both in the defect and suggestion format.

To replace an implementation without the gate, dispatch with `regen_gate=false` (`impl-generate.yml` or `bulk-generate.yml`): the PR is labelled `regen:forced` and takes the fresh-generation path, including the repair loop. If the repairs are exhausted, the PR is closed and the live implementation stays on main; nothing is deleted.

The local `/regen` command (`agentic/commands/regen.md`) is an owner override without the review gate; it only withholds `ai-approved` when the new score is more than one point below the stored score.

---

## Key principles

1. **Decoupled**: Each library runs independently (no single point of failure)
2. **Partial OK**: 6/9 implementations done = fine
3. **No merge conflicts**: Per-library metadata files
4. **Auto-sync**: Database updated on every merge to main
5. **GCS flow**: staging --> production only after merge

---

## Workflow files

Located in `.github/workflows/`:

| Workflow | Purpose |
|----------|---------|
| `spec-create.yml` | Creates new specifications |
| `impl-generate.yml` | Generates single implementation |
| `impl-review.yml` | AI quality review |
| `impl-repair.yml` | Fixes rejected implementations |
| `impl-merge.yml` | Merges approved PRs, and the review write-back PRs a kept regeneration opens (job `writeback`) |
| `bulk-generate.yml` | Batch implementation generation |
| `review-retest.yml` | Dispatch-only measurement: re-runs the AI quality review on the frozen retest set (several fresh sessions per item, regen pairs in both orders) for one rules version, and reports score spread, verdict flips, weakness agreement, and gate order bias against a baseline arm. Read-only tokens; writes nothing outside its own artifacts. See [Review retest](review-retest.md) |
| `daily-regen.yml` | Cron-driven regeneration of the oldest implementations (once a day at 02:17 UTC, off the top of the hour to dodge GitHub's scheduler overload). A spec's age counts from the newer of its last merged update and the last activity on its spec issue (every regen touches the issue), so a kept regeneration is not re-picked the next night. Any activity on the issue — a comment, a label, a report — postpones that spec's regen the same way |
| `watchdog-stuck-jobs.yml` | 6-hourly safety net: re-dispatches stuck reviews, repairs (including a repair that crashed after a rejection), merges and generations (straight to `impl-generate.yml`, marked only once the run exists), re-closes open `regen:kept` PRs, never rescues a regeneration into repair or re-dispatches its failed review (it flags it for manual attention instead; "regeneration" = the `regen` label or the implementation file on main, unless `regen:forced`), and rescues daily-regen when its cron is silently starved by GitHub (>26 h without a run) |
| `report-validate.yml` | Validates user-submitted issue reports |
| `sync-postgres.yml` | Syncs `plots/` filesystem state to PostgreSQL on push to main |
| `sync-labels.yml` | Auto-syncs spec/impl labels after manual PR merges |
| `indexnow-submit.yml` | Pushes changed page URLs to IndexNow (Bing, Yandex, Seznam, Naver, Yep) on every push to main that touches `plots/`; a push that changes the workflow file itself or bumps `TEMPLATE_LAST_CHANGED` in `api/routers/seo.py` submits the full list, as does `workflow_dispatch` with `scope=sitemap` |
| `codeql.yml` | CodeQL scanning (actions, JavaScript/TypeScript, Python) on pushes to main, PRs and a weekly cron; `plots/**` is excluded from triggers and analysis, so pipeline PRs never start a scan |
| `ci-lint.yml` | Ruff lint check on PRs |
| `ci-tests.yml` | Unit + integration tests on PRs. Its "Run Tests" job also lints the "What a good version looks like" section on every run, even when no Python changed: the contract over every spec (blocking) and the style of the changed specs (warnings) |
| `ci-image.yml` | Builds `api/Dockerfile` and smoke-tests the container before merge — `/health`, the reported version against `pyproject.toml`, the runtime stage's COPY payload, non-root uid — plus hadolint on both Dockerfiles. Skips when only `plots/**` or frontend sources changed |
| `notify-deployment.yml` | Records GitHub deployment events for `app` / `api` |
| `bot-serving-check.yml` | Daily synthetic monitor: curls the Cloud Run origin with crawler UAs and fails on non-200 or a page that is not the prerendered one. Routes are derived from the `@router.get("/seo-proxy/…")` decorators in `api/routers/seo.py` and the expected spec title from `plots/<spec>/specification.yaml`, so no literal here can go stale. A failure opens (or comments on) the fixed-title issue **Bot serving check is red**; the next green run closes it — the bot→seo-proxy path is invisible to human traffic and needs its own alarm |
| `util-claude.yml` | On-demand `@claude` utility (issue/PR comments) |

---

## Bulk operations

```bash
# All libraries for one spec:
gh workflow run bulk-generate.yml -f specification_id=scatter-basic -f library=all

# One library across all specs:
gh workflow run bulk-generate.yml -f specification_id=all -f library=matplotlib
```

**Concurrency limit**: Max 3 parallel implementations globally.

---

## Pipeline models

The pipeline chooses two models separately: the generation model, which writes
and repairs an implementation, and the review model, which scores it. The other
pipeline LLM steps use fixed models: `spec-create.yml` runs on Opus, and the
spec polish and cross-library similarity audit in `daily-regen.yml` run on
Sonnet.

### Generation model

`impl-generate.yml` picks the generation model for each (spec, library) pair
and threads it into every repair of that pair's PR:

| Situation | Generation model |
|-----------|------------------|
| First implementation: the pair has no implementation file on `origin/main` yet | Opus |
| Regeneration: the pair already has an implementation on `origin/main` | Sonnet |
| Forced regeneration: a regeneration dispatched with `regen_gate=false` (see [Regen gate](#regen-gate-regenerations)) | Opus |
| Explicit `model` input (`haiku`, `sonnet`, or `opus`) | That model, for every pair |

The routing applies whenever nobody chooses a model: a `generate:{library}`
label, a `bulk-generate.yml` or `daily-regen.yml` run with the default
`model=auto`, and the watchdog's generation retries. A failed generation
forwards its resolved model to its own retry, so a first run stays on Opus.
The run summary, the issue preview comment, and the PR body show the resolved
model; the preview comment and the summary also show why, for example
`opus (first implementation)`.

Review and repair runs that arrive without a model, such as
`impl-review-retry.yml`, the watchdog's review and repair rescues, or a manual
`gh workflow run impl-review.yml -f pr_number=N`, read the `**Model:**` line
from the PR body, so an explicit pin survives a rescue and still reaches every
repair. `impl-review.yml` resolves this value only to forward it to repair; it
never chooses the review model. Only a PR without that line is routed again.

If `origin/main` can't be read, `impl-generate.yml` fails instead of guessing.
Review and repair log a warning and assume a first run (Opus).

To pin one generation model for a whole run, pass it explicitly. The pin covers
generation and repair; the reviews still run on Opus.

```bash
gh workflow run bulk-generate.yml -f specification_id=scatter-basic -f library=all -f model=sonnet
```

`bulk-generate.yml` waits 180 seconds between dispatches for `model=auto` or
`opus`, and 120 seconds for `sonnet` or `haiku`; `pace_seconds` overrides
either default. The 120-second default dates from when a pinned run also
reviewed on its own model. Its reviews now run on Opus, so pass
`pace_seconds=180` for a large pinned run.

### Review model

Every quality review runs on Opus, whatever model generated the
implementation. That covers the review of a first implementation, the review
after each repair, and the regen gate's session, which re-scores the live
implementation and reviews the new render in one go. On a keep, that re-score
becomes the live implementation's stored review
([Stored review on a keep](#stored-review-on-a-keep)). `impl-review.yml` is the
only pipeline workflow that runs a quality review, and it chooses the review
model itself: no other workflow forwards one. The
[retest harness](review-retest.md) (`review-retest.yml`) runs the same review
on a frozen set, for measurement only.

To review one PR on another model, for example for an experiment, dispatch
`impl-review.yml` with `review_model`:

```bash
gh workflow run impl-review.yml -f pr_number=123 -f review_model=sonnet
```

The pin covers that run and its own auto-retry. A later review of the same PR,
after a repair or a rescue, runs on Opus again. The run summary and the notice
line name both models, for example
`review model: opus, generation model: sonnet from PR body`.

Opus scores lower than Sonnet: on the 14 fresh core items both scored under
the same rules, it averaged 77.5 against Sonnet's 85.7 (retest runs
36354452853 and 36359464410; a 15th item auto-rejected on Opus).
Most stored scores come from Sonnet or Haiku reviews, so a pair reviewed on
Opus usually stores a lower score than the one it replaces, on a merge and,
through the write-back, on a keep. `review.model` names the model behind a
stored score.

An alias such as `opus` points at a newer model after each release, so
`impl-review.yml` stores what actually ran. The metadata's `review` block
records the resolved model ID (`review.model`, for example `claude-opus-5`),
the rules version the reviewer read (`review.criteria_version`, the git blob
IDs of `prompts/quality-criteria.md`, `ai-quality-review.md`,
`default-style-guide.md`, and the library prompt), and when the reviewed render
was made (`review.rendered_at`). These keys aren't synced to the database.
A value the run can't determine is left out, and any value an earlier review
wrote for that key is removed with it. For example, an execution file that
names no model leaves `review.model` out, never filled with the alias, and the
gate record and notice line show `model=n/a`.

---

## CLI model tiers

The agentic workflows use abstract model tiers (`small`, `medium`, `large`) instead of CLI-specific model names. This allows the same command to work across different AI tools.

| Tier | Purpose | Claude | Copilot | Gemini |
|------|---------|--------|---------|--------|
| small | Fast/cheap tasks | haiku | gpt-4o-mini | gemini-2.0-flash |
| medium | Balanced tasks | sonnet | gpt-4o | gemini-2.0-flash-thinking |
| large | Complex tasks | opus | o1 | gemini-2.5-pro |

### Usage

```bash
# Use large tier (default for plan_build)
uv run agentic/workflows/plan_build.py "Add feature X" --model large

# Use medium tier with Copilot
uv run agentic/workflows/prompt.py "Quick fix" --model medium --cli copilot
```

### Override mappings

Override the default model for any tier via environment variables:

```bash
# Linux/WSL
export CLI_MODEL_CLAUDE_LARGE=claude-opus-4-7
export CLI_MODEL_COPILOT_MEDIUM=gpt-4-turbo

# Windows PowerShell
$env:CLI_MODEL_CLAUDE_LARGE = "claude-opus-4-7"
$env:CLI_MODEL_COPILOT_MEDIUM = "gpt-4-turbo"
```

All environment variable names follow the pattern: `CLI_MODEL_{CLI}_{TIER}`
