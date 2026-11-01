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
  |-- AI generates code (Python: adaptability self-check, Step 3c)
  |     or, with source_ref, takes the file from that ref and renders it (adopt mode)
  |-- Fails if the commit changes a dependency file
  |-- Creates metadata/python/{library}.yaml (initial)
  |-- Python: adaptability smoke run, plus the predecessor's render on a regeneration (record-only)
  |-- Tests execution
  |-- Uploads preview to GCS staging (adaptability records under a private adapt/ prefix)
  |-- Creates PR --> main
       |
       v
impl-review.yml
  |-- Python: adaptability check of the PR's file and its predecessor (record-only)
  |-- AI evaluates code + image
  |-- Posts review comment with score
  |-- Updates metadata/python/{library}.yaml (quality_score, review feedback)
  |-- Adds [quality:XX] label
       |
       |-- Meet Threshold --> [ai-approved] --> impl-merge.yml
       |                                        |-- Refuses a PR that changes a dependency file
       |                                        |-- Squash merge
       |                                        |-- Promotes GCS: staging --> production
       |                                        |-- Triggers sync-postgres.yml
       |
       |-- Below Threshold --> [ai-rejected] --> impl-repair.yml (max 4 attempts)
       |                                       |-- Reads AI feedback
       |                                       |-- Fixes implementation
       |                                       |-- Python: reruns the adaptability smoke run (record-only)
       |                                       |-- Re-triggers impl-review.yml
       |
       |-- Regeneration (implementation already on main) --> regen gate, one review, no repair
                |-- Replace --> [regen:improved] (+ [regen:adapt] or [regen:adapt-overruled]) + [ai-approved] --> impl-merge.yml
                |-- Keep    --> (+ [regen:adapt-overruled]) [regen:kept] --> PR closed, live code and GCS unchanged
                                   |-- Stored review <-- re-score: [review-writeback] PR --> impl-merge.yml (writeback job)
```

#### Adaptability steps (Python, record-only)

Python implementations follow the Data block convention of [Adaptable catalogue code](../concepts/adaptable-code.md). These steps measure it. None of them fails a run, and the reviewer never sees their output:

| Workflow | Step | What it does |
|---|---|---|
| `impl-generate.yml` | Adaptability smoke run (record-only) | Runs the new source on perturbed tables (`core/smoke_run.py run`). On a regeneration it also renders the predecessor next to the new source in the same runner (`pair`) and runs the smoke run on it. It records the results under `$RUNNER_TEMP/adapt` without gating. |
| `impl-generate.yml` | Upload to GCS Staging | Clears `staging/{spec}/python/{library}/adapt/` and stages this run's smoke results, pair record, raw pair renders, and the generator's self-check log there, privately and never promoted. |
| `impl-repair.yml` | Adaptability smoke run (record-only) | Reruns the smoke run on the repaired file. |
| `impl-repair.yml` | Upload repaired plot to GCS staging | Replaces `adapt/new-smoke.json`, or removes the stale one when the repair run wrote none. |
| `impl-review.yml` | Set up Python | Pins the job's `python3` to `.python-version`, which the regen tools and the checker mirror need to parse PEP 758 `except A, B:`. |
| `impl-review.yml` | Adaptability check (record-only) | Runs the workflow-ref checker mirror on the PR's Python file and, on a regeneration, on its predecessor. It combines each with the staged smoke run into `/tmp/anyplot-adapt-new.json` and `/tmp/anyplot-adapt-prev.json`, asks the gate whether the adapt route holds (`regen_gate.py adapt-route`), and skips the review only when the route holds and the owner's `ADAPT_REVIEW_FREE` switch is on. |
| `impl-review.yml` | Add carried quality score label | On a review-free adapt merge, labels the PR with the stored score that carries over. |

`impl-merge.yml` promotes only the `plot-*` files from staging, so `adapt/` never reaches production; its cleanup removes `adapt/` with the rest of staging.

### Dependency pins and library versions

Each language's plotting stack is pinned in the repository:

| Language | Pin | Installed in the pipeline by | Kept current by |
|----------|-----|------------------------------|-----------------|
| Python | `uv.lock` | `uv sync --frozen --extra lib-{library}` in `impl-generate.yml` and `impl-repair.yml`, as `agents/renderer/Dockerfile` and CI install | Dependabot (`uv`, `/`) |
| JavaScript | `package.json` + `package-lock.json` at the root | `npm ci` in `.github/actions/setup-node` | Dependabot (`npm`, `/`) |
| Julia | `Project.toml` + `Manifest.toml` | `Pkg.instantiate()` in `.github/actions/setup-julia` | Hand-made PRs |
| R | Dated Posit snapshot in `.github/actions/setup-r` | `install.packages()` from the snapshot | Hand-made PRs |

Implementation PRs never change these files. A generation whose commit changes
`pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`,
`Project.toml`, `Manifest.toml` or `.python-version` fails in
`impl-generate.yml`, and `impl-merge.yml` refuses to merge an implementation PR
that changes one, which also covers repair commits. A re-resolved lock file
moves the library version for every implementation of the language: #9398
committed a `Manifest.toml` that a `Pkg.add` had re-resolved and moved Makie
from 0.22.10 to 0.21.9. A spec that needs a new package needs a dependency PR
first.

No version is written down by hand. The version an implementation was made
with is measured at generation time and stored in its metadata as
`library_version`, and `impl-review.yml` writes it into the file header. The
version on the Libraries page and each language's runtime version are read
from the pins by `core/library_versions.py` when `sync-postgres.yml` runs; a pin
that does not resolve keeps the stored value and logs a warning. So a minor or
patch bump, Dependabot's included, needs no other edit.

The example headers in `prompts/library/*.md` carry no version. Every prompt of
a locked library (Python, JavaScript, Makie) states the API level the generator
writes against
(`**API level:** ECharts 6.`), and `tests/unit/core/test_version_sources.py`
holds it to the lock's major, so a major bump updates the prompt in the same
PR. The same test checks that every pin resolves.

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
| `impl:{library}:failed` | Set by `impl-generate.yml` after three failed generation attempts for the pair within a 12-hour window, or by `impl-review.yml` when the PR still scores below 50 after four repair attempts. Infrastructure failures (provider incident, cloud auth, GitHub API) are retried on a separate cap of 5 and never set this label; a pair paused that way carries no label. A generation Claude stopped never sets it (see [When Claude stops a session](#when-claude-stops-a-session)), and an adopt-mode source failure doesn't either (see [Adopt implementations from a branch](#adopt-implementations-from-a-branch)). | Workflow |

### PR labels (on Pull Requests)

| Label | Meaning | Set By |
|-------|---------|--------|
| `ai-approved` | Quality check passed (based on cascading thresholds) | Workflow |
| `ai-rejected` | Quality check failed, triggers repair | Workflow |
| `ai-attempt-1/2/3/4` | Retry counter | Workflow |
| `ai-review-paused` | Claude stopped the PR's review (a spend or usage limit, or refused credentials): no score, no verdict. The watchdog skips the PR; pair mode or a manual rerun resumes it, and the next review removes the label (see [When Claude stops a session](#when-claude-stops-a-session)) | Workflow |
| `ai-repair-paused` | Claude stopped the PR's repair, next to `ai-rejected`; the attempt isn't used up. The watchdog skips the PR; pair mode or a manual restart resumes it, and the next repair removes the label | Workflow |
| `quality:XX` | Quality score (e.g., quality:92) | Workflow |
| `quality-poor` | Score < 50, needs fundamental fixes | Workflow |
| `regen` | Regeneration of an implementation that is live on main (marker for humans and the watchdog; `impl-review.yml` decides "regeneration" from `origin/main`) | Workflow |
| `regen:forced` | Regeneration dispatched with `regen_gate=false` or in adopt mode (`source_ref`): bypasses the regen gate and takes the fresh-generation path | Workflow |
| `regen:improved` | The regen gate replaced the live implementation (added before `ai-approved`) | Workflow |
| `regen:kept` | The regen gate kept the live implementation; the PR is closed unmerged | Workflow |
| `regen:adapt` | The regen gate replaced the live implementation on the adapt route (added after `regen:improved`); one of the two counts the owner reads before turning on `ADAPT_REVIEW_FREE` | Workflow |
| `regen:adapt-overruled` | The adapt route held before the review, and the review's floor turned it off (added before the verdict label, on a merge or a keep); the other count the owner reads before turning on `ADAPT_REVIEW_FREE` | Workflow |
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

**Nothing to repair.** A review below its threshold is still approved when it scores at least 80, names no defect, has every technical criterion (the 19 VQ, SC, DQ, and CQ items) at its maximum, and its checklist adds up to its score. A repair fixes defect lines, so such a review leaves a repair nothing to do: the points it withheld are design and library levels (DE, LM) that no line asks a repair to change. `impl-review.yml` reads both conditions (`regen_gate.py nothing-to-repair`, from `review_checklist.json` and `review_weaknesses.json`): a defect line that names a DE or LM criterion is repairable, and a technical point deducted without a defect line still gets its repair. The pull request gets a comment that says why it merged below the threshold.

**The workflow owns the verdict.** The stored `review.verdict` is what the workflow decided: `APPROVED` when the score met the threshold, when the nothing-to-repair rule applied, or when the regen gate merged, and `REJECTED` when a first generation goes to repair. A regeneration the gate keeps stores nothing on its own branch. It isn't the reviewer's opinion; a kept regeneration's write-back stores `APPROVED`, because the kept implementation stays live.

**The stored review is out of the working tree during a review.** Once a review has run, the pull request branch carries it: the `Quality: N/100` header and the metadata file with the score and the whole review. While a reviewer runs, the header reads `Quality: pending` and the metadata file is out of the workspace; both come back before the workflow stores the new review. This holds for every review, not only the ones after a repair, because a manual re-review or a watchdog retry of a scored pull request runs without an attempt label. The run log's `blind review:` notice shows the state the reviewer saw, and the commit that stores a review names no score. This hides the working-tree copies only. The branch history and the pull request stay reachable for a reviewer that goes looking: `git diff` shows the moved file, `git log -p` the earlier commit, and `gh` the earlier review comments and the `quality:N` label. Nothing mechanical closes those; the review prompt tells the reviewer not to open earlier reviews, the stored score, or another library's implementation of the spec.

**What the reviewer doesn't see.** The thresholds above and what follows from a score are in this file and in the workflow, not in the reviewer's prompts (`prompts/quality-criteria.md`, `prompts/workflow-prompts/ai-quality-review.md`). The reviewer scores 24 criteria and adds them up; it writes no verdict and doesn't know which score approves. Two rules shape that score:

- The 19 technical criteria (VQ, SC, DQ, CQ) start at their maximum, and every point below it is carried by a defect line that names the criterion. The workflow's format check counts the deductions without one (`weakness_format … silent=N` in the run log).
- The five judgment criteria (DE, LM) start at their default, and only evidence beyond what the spec and the style guide require raises them. An implementation that meets every requirement and adds nothing lands near 82.

A unit test (`tests/unit/prompts/test_prompts.py`) keeps the thresholds out of the three reviewer prompts and in this file.

### Review recovery

`impl-review.yml` re-runs a review at most once by itself, whatever the cause. A comment carrying the `<!-- review-retry:{spec}:{library} -->` marker records that retry:

- **No score.** The review wrote no `quality_score.txt` and no review comment ("Validate review output"): one retry through `repository_dispatch`.
- **Scored, then a later step failed before any verdict label landed.** For example, a GitHub 5xx on the `quality:N` label ("Re-dispatch review after a post-score failure"): one retry through `gh workflow run --ref` on the run's own ref. If the PR already has a verdict label (`ai-approved`, `ai-rejected`, `regen:improved`, or `regen:kept`), the step does nothing, and the watchdog's merge or repair cases take over. A verdict label that can't be added after three tries fails "Add preliminary verdict label (early)" on every path, including `regen:kept`, so this retry also covers a lost verdict label. A review-free adapt run (the review skipped on `ADAPT_REVIEW_FREE`) has the same retry when a step fails before its verdict label, such as the carried `quality:N` label; its comment names the stored score, because no review scored.

Both paths write the marker comment before they dispatch the retry, and they retry the comment and the dispatch three times each. A marker that can't be read counts as a spent retry, so a GitHub outage can't buy a second one. When the retry is spent, or the marker comment or the dispatch itself fails, the PR gets `ai-review-failed`. The watchdog re-dispatches the review once for a fresh generation and only flags a regeneration. A PR left with only `quality:N` and no verdict is picked up by the watchdog's never-reviewed case. `impl-review.yml` adds these labels with `GITHUB_TOKEN`, which doesn't start workflow runs, so `impl-review-retry.yml` reacts only to a label that a person adds.

`ai-review-failed` is removed by the review it asks for. Every review run removes the label when it starts ("Clear a stale ai-review-failed label", best effort). The watchdog leaves a PR with that label alone while a review of it is queued or running, and drops the label without a re-review when the PR already has a verdict label. This matters when GitHub accepts a dispatch but reports an error: the step then adds `ai-review-failed` although the re-review is already queued, and without these two guards the watchdog would start a second review of the same PR.

A review that Claude stopped, at a spend or usage limit or on refused credentials, takes neither path: it gets `ai-review-paused`, spends no retry, and the watchdog skips it (see [When Claude stops a session](#when-claude-stops-a-session)).

`impl-repair.yml` has the same one-retry rule for a repair run that crashes, recorded by a `<!-- repair-retry:{spec}:{library}:attempt-{n} -->` marker. It sums the marker count over all comment pages and treats a count it can't read as a spent retry. The watchdog's crashed-repair case takes over from there.

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

   **Code path.** When no improvement fixes a defect, a regeneration still replaces the live implementation when it fixes a code defect the previous review named. The review lists it under `code_improvements`, and the gate counts it when all of these hold: the previous weakness is a `CQ-04 (code): … → \`call\`` (or `→ remove`) line that the re-score classed a CQ-04 defect; CQ-04 scores higher in the new review than in the re-score; the new source calls the named call more often than the predecessor (or the target was a removal), where a comment, a string literal, or a definition of the same name doesn't count as a call; the new source is shorter; and the data scenario and encodings are unchanged, on any spec. The score tolerance and the regression rule apply as above, and visible suggestions ride along. The gate reads both sources (`--prev-impl`, `--new-impl`); without them the code path is off. A code-path replacement is a merge, so like any merge it writes no re-score back.

   **Adapt route.** A Python regeneration that converts the implementation to the adaptable-code convention ([Adaptable catalogue code](../concepts/adaptable-code.md)) changes the code but not the picture, so it has no visible improvement to carry it. It replaces the live implementation on render identity instead, when all of these hold:
   - the predecessor fails the adaptability check (the static check or the smoke run) and the new source passes both;
   - the two sources' renders, both made in the same `impl-generate.yml` runner ("Adaptability smoke run (record-only)") from the very sources the records checked, differ in at most 0.5 % of their pixels in each theme, at equal size; a size change fails, and so does a pair rendered from other source versions (`pair_stale`);
   - the new source has at most max(1.25 × prev, prev + 15) lines, and the canvas gate passed;
   - when the review ran: a score above 0, no regression, an unchanged data scenario and no added encoding (on any spec), and no VQ, SC, DQ, or CQ item below its value in the re-score.

   The route takes the place of three keeps: `no_visible_improvement`, `no_defect_improvement`, and `below_tolerance`. The score tolerance never applies to it: the reviewer's run-to-run spread and the re-score's offset from the stored score make any tolerance a coin flip, so the technical items are the floor instead. The CQ-04 code path keeps its tolerance. A replacement on the route carries the reason code `adapt_identity`. The gate reads three files: the two records that "Adaptability check (record-only)" writes, one per source, and the render pair that impl-generate staged. A missing or malformed record, a missing render pair, or an implementation in another language turns the route off, and the record says why. It never counts as a pass. A record whose status does not follow from its static and smoke results counts as malformed (`record_invalid`), and so does a render pair that does not name the PR's library.

   `impl-review.yml` evaluates the conditions that need no review before the review runs (`regen_gate.py adapt-route`, the `adapt_route` notice). When the repository variable `ADAPT_REVIEW_FREE` is `true` and those conditions hold, the review is skipped and the gate merges on them alone (`decide --review-skipped`), carrying the stored score and review forward. A skipped review whose route does not hold is kept as `no_score`. The variable is off by default, and only the owner turns it on. The evidence is the route-held PRs: `regen:adapt` marks a merge on which the route held before and after the review, and `regen:adapt-overruled` marks a PR whose route held before the review and whose review then turned it off (`decide --adapt-route-held`, the gate output `adapt_overruled`). Route-held PRs are the `regen:adapt` PRs plus the `regen:adapt-overruled` PRs. The owner turns the switch on only when the overruled share stays near zero over at least 50 route-held PRs:

   ```bash
   gh pr list --state merged --label regen:adapt --limit 1000 --json number --jq length
   gh pr list --state all --label regen:adapt-overruled --limit 1000 --json number --jq length
   ```

   **Adapt regression.** On every spec, when the predecessor passes the adaptability check and the new source fails it, the live implementation stays (`adapt_regression`), whatever else would replace it. The same holds without a smoke run: when the predecessor passes the static check, its smoke run is missing, stale, or skipped, and the new source fails the static check. Converted code stays converted.
4. Replace: `regen:improved`, then `regen:adapt` when the adapt route counted or `regen:adapt-overruled` when the review overruled it, then `ai-approved`, a PR comment with the same summary (stored, re-scored, and new score, improvements, regressions, reason), then the normal merge. Keep: `regen:adapt-overruled` when the review overruled the adapt route, then `regen:kept`, the PR is closed with that comment, the issue gets `impl:{library}:done` back, and the live code and GCS production stay as they are. The re-score of the live implementation becomes its stored review through a separate metadata PR (see [Stored review on a keep](#stored-review-on-a-keep)).

A crashed regen review is auto-retried once by `impl-review.yml`; after that the PR carries `ai-review-failed` and the watchdog only flags it — it never dispatches a further review for a regeneration. The same one-retry budget covers a review of any PR that scored but failed before a verdict label landed, for example on a GitHub 5xx (see [Review recovery](#review-recovery)).

Anything missing or malformed — no `review_regen.json`, an unknown weakness id, missing previous renders, a failed canvas gate, a score of 0 — keeps the live implementation. The classification never invalidates the file, but every gap points toward keep: an unclassified weakness counts as a suggestion, and without `prev_checklist` or the new review's `review_checklist.json` no criterion claim verifies, so only an `A good version shows:` property can carry the replacement.

Every review writes its weaknesses in the two formats: defect lines first, then at most three `Suggestion:` lines. Generation and repair fix the defects and decline every suggestion. A non-gating step in `impl-review.yml` ("Check review feedback format") runs `regen_gate.py check-feedback --warn-only` and reports lines in neither format, and claims the scores don't confirm, as warnings; the review runs the same check on itself before it finishes.

Every decision leaves three traces:

- **The gate record in the PR comment.** Both the keep and the replace comment end with an invisible `<!-- regen-gate-record:v1 {...} -->` marker: one line of JSON with the scores, improvement and regression counts (the improvements split into carriers, suggestions, and obsolete citations; the suggestions name additions, polish, and improvements without a kind apart, and a histogram counts the kind of every listed improvement, and `code` counts the code improvements the gate counted), the reason code (`merge`, `below_tolerance`, `no_visible_improvement`, `no_defect_improvement`, `regression`, `adapt_identity`, `adapt_regression`, `regen_json_invalid`, `canvas_failed`, and so on), and the provenance of both reviews (resolved model and rules version of this review and of the stored one). The `adapt` block holds the adapt route: `version` (the checker version), `prev` and `new` (each source's adaptability `status`, with its `static` and `smoke` statuses), `identity` (the share of differing pixels per theme), `counted`, `why` (`route` when it counted, otherwise the first condition that failed, such as `not_python`, `prev_passes`, `identity_dark`, or `technical_below`), `review` (`ran` or `skipped`), and `route_pre_review` (whether `adapt-route` held before the review: `true`, `false`, or `null` without adapt input). A keep record also says what happened to the re-score (`writeback`, see the next section). It holds no model-written text. PR comments are permanent, so read this first.
- **The notice line in the run log.** `::notice::regen_gate spec=… lib=… prev_stored=… prev_rescored=… new=… verdict=… code=… model=… criteria=… prev_lines=… new_lines=… adapt_counted=… adapt_why=… adapt_overruled=… reason=…`, where `prev_lines` and `new_lines` are the two sources' line counts, and `adapt_counted`, `adapt_why`, and `adapt_overruled` appear when the step passes the adapt files. Run logs expire.
- **The pair artifact.** `regen-pair-<pr>-<attempt>` on the `impl-review.yml` run, kept 60 days: both renders, both sources (the predecessor's with its score hidden), the previous review, this review's files, and the gate record. For a Python pair, `adapt/` adds both adapt records and what impl-generate staged for them: the smoke runs, `pair.json`, the raw renders of both sources, and the generator's self-check log. The predecessor's production renders are overwritten on the next merge, so this is the only copy of what the gate compared.

`uv run python -m automation.scripts.review_retest gate-report` aggregates the records across pull requests: merge rate, reason codes, how far re-scored predecessors land from their stored scores, the counted visible improvements and carriers, cited permissions and obsolete weaknesses, what happened to the re-scores of kept implementations, the merges the code path carried, and soft alarms. See [Review retest](review-retest.md#monitor-the-regen-gate).

### Stored review on a keep

A kept regeneration still reviewed the live implementation: the gate's re-score. That re-score becomes the implementation's stored review, so the next regeneration starts from current problems under the current model and rules. This happens on every keep, whether or not the model or the rules changed since the stored review.

1. The review writes the re-score as a full review, `review_prev.json` (step 8b of `ai-quality-review.md`, step 5): the image description of the production renders, the criteria checklist (item for item equal to `prev_checklist`, each category score the sum of its items), strengths, weaknesses (the predecessor defects `P1`, `P2`, … as defect lines, except one whose improvement the review names an `addition` or `polish`, which is written as a suggestion, then at most three suggestions), and a verdict. It has no score: the stored score is the gate's `prev_rescored`.
2. `impl-review.yml` ("Write back the re-score (regen keep)") checks the file with `automation/scripts/regen_writeback.py check`, confirms that `main` still holds the two files the review read, and commits the new `quality_score`, the five review fields, `review.model`, and `review.criteria_version` in the metadata, plus the number in the implementation's `Quality: N/100` header, on the branch `review-writeback/{spec}/{library}/{kept PR}`. It opens a PR labelled `review-writeback` with `GITHUB_TOKEN` and dispatches `impl-merge.yml`. `updated`, `review.rendered_at`, `impl_tags`, and the previews stay as they are: the code didn't change.
3. The `writeback` job of `impl-merge.yml` merges the PR with the admin token after three checks: the PR is the bot's, and its score, review model, and rules version equal the `prev_rescored`, `model`, and `criteria_version` of the kept PR's gate record (`check-pr`), the diff changes only those keys and the header number (`verify-diff`), and `main` hasn't changed the pair's files since the branch was cut (`check-fresh`, before every merge attempt). Then it triggers the database sync.

Any failure leaves the stored review as it was and closes the write-back PR; the keep itself is never held up. The keep record's `writeback` says what happened: `opened` (the PR exists and its merge was dispatched, not yet that it merged), `unchanged`, `no_rescore` (the gate had no valid `review_regen.json`), `invalid` (`review_prev.json` failed its check), `stale` (`main` changed the pair's files during the review), or `failed`. The kept comment has a matching **Stored review** line. A lost write-back heals at the pair's next gated regeneration, which re-scores the implementation again.

So a stored weakness list in the older format lasts only until the pair's first gated regeneration: a merge stores the new render's review, and a keep stores the re-score, both in the defect and suggestion format.

To replace an implementation without the gate, dispatch with `regen_gate=false` (`impl-generate.yml` or `bulk-generate.yml`): the PR is labelled `regen:forced` and takes the fresh-generation path, including the repair loop. If the repairs are exhausted, the PR is closed and the live implementation stays on main; nothing is deleted. A run in adopt mode (`source_ref`) is always forced this way; see [Adopt implementations from a branch](#adopt-implementations-from-a-branch).

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
| `impl-generate.yml` | Generates single implementation, or adopts one from a ref with `source_ref` |
| `impl-review.yml` | AI quality review |
| `impl-repair.yml` | Fixes rejected implementations |
| `impl-merge.yml` | Merges approved PRs, and the review write-back PRs a kept regeneration opens (job `writeback`) |
| `bulk-generate.yml` | Batch implementation generation |
| `review-retest.yml` | Dispatch-only measurement: re-runs the AI quality review on the frozen retest set (several fresh sessions per item, regen pairs in both orders) for one rules version, and reports score spread, verdict flips, weakness agreement, and gate order bias against a baseline arm. Read-only tokens; writes nothing outside its own artifacts. See [Review retest](review-retest.md) |
| `daily-regen.yml` | Cron-driven regeneration of the oldest implementations (once a day at 02:17 UTC, off the top of the hour to dodge GitHub's scheduler overload). A spec's age counts from the newer of its last merged update and the last activity on its spec issue (every regen touches the issue), so a kept regeneration is not re-picked the next night. Any activity on the issue — a comment, a label, a report — postpones that spec's regen the same way. With the repository variable `REGEN_PAIRS_PER_DAY`, the scheduled run regenerates single (spec, library) pairs instead of whole specs; see [Daily regeneration modes](#daily-regeneration-modes) |
| `watchdog-stuck-jobs.yml` | 6-hourly safety net: re-dispatches stuck reviews, repairs (including a repair that crashed after a rejection), merges and generations (straight to `impl-generate.yml`, marked only once the run exists), re-closes open `regen:kept` PRs, never rescues a regeneration into repair or re-dispatches its failed review (it flags it for manual attention instead; "regeneration" = the `regen` label or the implementation file on main, unless `regen:forced`), skips a PR whose review or repair Claude stopped (`ai-review-paused`, `ai-repair-paused`), and rescues daily-regen when its cron is silently starved by GitHub (>26 h without a run) |
| `report-validate.yml` | Validates user-submitted issue reports |
| `sync-postgres.yml` | Syncs `plots/` filesystem state to PostgreSQL on push to main, and runs `alembic upgrade head` against Cloud SQL first; a push that only adds a revision under `alembic/versions/` triggers it too, and so does one that changes a pin the library versions are read from (`uv.lock`, `package-lock.json`, `Manifest.toml`, `.python-version`, a setup action) |
| `sync-labels.yml` | Auto-syncs spec/impl labels after manual PR merges |
| `indexnow-submit.yml` | Pushes changed page URLs to IndexNow (Bing, Yandex, Seznam, Naver, Yep) on every push to main that touches `plots/`; a push that changes the workflow file itself or bumps `TEMPLATE_LAST_CHANGED` in `api/routers/seo.py` submits the full list, as does `workflow_dispatch` with `scope=sitemap` |
| `codeql.yml` | CodeQL scanning (actions, JavaScript/TypeScript, Python) on pushes to main, PRs and a weekly cron; `plots/**` is excluded from triggers and analysis, so pipeline PRs never start a scan |
| `ci-lint.yml` | Ruff lint check on PRs. `ci-lint.yml`, `ci-tests.yml`, `ci-image.yml`, `ci-migrations.yml` and `ci-changelog.yml` start no run on a PR that changes only `plots/*/implementations/**` and `plots/*/metadata/**`, which is what the plot pipeline's PRs touch: GitHub holds the runs of a PR that `GITHUB_TOKEN` opened for an approval that never comes, and they end as `failure` at the merge. A PR that also changes any other file, such as a spec PR, keeps every run. |
| `ci-tests.yml` | Unit and integration tests on PRs, including PRs into `feature/**`, on four pytest-xdist workers (`-n 4 --dist worksteal`) with coverage, in "Run Tests", which has no GCP access. "Run E2E Tests" runs after it, the only job that logs in to GCP: E2E against the Cloud SQL `test` database through the proxy, skipped for PRs by Dependabot and Google Jules. "Run Tests" also lints the "What a good version looks like" section on every run, even when no Python changed: the contract over every spec (blocking) and the style of the changed specs (warnings) |
| `ci-image.yml` | Builds `api/Dockerfile` and smoke-tests the container before merge — `/health`, the reported version against `pyproject.toml`, the runtime stage's COPY payload, non-root uid — plus hadolint on every Dockerfile it builds. Skips when only `plots/**` or frontend sources changed. A third job builds `agents/renderer/Dockerfile` when the renderer, the probe harness or the dependency lock changed: it renders a seaborn plot through the harness under the sandbox's rlimits with no network, checks that the image carries no ADK and reports the `pyproject.toml` version, and runs hadolint. A fourth job builds `agents/Dockerfile` when `agents/` (outside `agents/evals/`), `core/`, the catalogue prompt files the agents read or the dependency lock changed: it checks that `GET /v1/status` reports the model, provider and libraries its environment sets and the `pyproject.toml` version, that the production default refuses an anonymous caller with `401`, that the prompts and fonts are in the image and the eval cases are not, and that the service runs as uid 1000, and it runs hadolint |
| `ci-migrations.yml` | Job `Verify Migrations`: checks every Alembic revision on a throwaway PostgreSQL 18 service container before merge — exactly one head, `alembic upgrade head`, `alembic check`, a CHECK-constraint parity query (which `alembic check` cannot do), and a downgrade to the base commit's head and back. Runs the checks only when `alembic/`, `alembic.ini`, `core/database/`, `pyproject.toml` or `uv.lock` changed, and reports a skip otherwise. It catches two revisions forked from the same head only when the PR is pushed after the other revision merged, because ruleset `main` does not require up-to-date branches; otherwise the push run on `main` reports the second head after the merge. See [Database migrations](../reference/database.md#database-migrations) |
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

### Generate one library for one spec

To generate or regenerate a single (spec, library) pair, dispatch
`impl-generate.yml` directly. It's the workflow `bulk-generate.yml` dispatches
once per library:

```bash
gh workflow run impl-generate.yml -f specification_id=scatter-basic -f library=bokeh
```

`specification_id` and `library` are required. The optional inputs are the
following:

| Input | Default | Meaning |
|-------|---------|---------|
| `issue_number` | empty | The spec issue to report on; empty reads it from `plots/{spec-id}/specification.yaml` |
| `model` | `auto` | The generation model, also used for repair: `auto` routes as in [Generation model](#generation-model); `haiku`, `sonnet`, or `opus` pins one. Reviews always run on Opus |
| `change_request` | empty | A one-sentence hint the generator follows, such as the cross-library divergence note of the daily-regen similarity audit |
| `regen_gate` | `true` | For a pair that already has an implementation on `main`: one review decides keep or replace, with no repair. `false` forces the fresh-generation path with the repair loop and the `regen:forced` label (see [Regen gate](#regen-gate-regenerations)) |
| `source_ref` | empty | Adopt mode: take the file from this branch, tag, or commit SHA (see [Adopt implementations from a branch](#adopt-implementations-from-a-branch)) |
| `source_model` | empty | Adopt mode only: the model that wrote the adopted file, recorded as `generated_by` |

For example, to regenerate one pair on Opus with a hint:

```bash
gh workflow run impl-generate.yml -f specification_id=scatter-basic -f library=bokeh \
  -f model=opus -f change_request="Use a different data scenario from the matplotlib version."
```

### Adopt implementations from a branch

Adopt mode takes each implementation file from a branch, tag, or commit SHA of
the repository instead of generating it. Use it for code written outside the
pipeline, for example a `gemini/*` branch that migrated every MUI X
implementation to a new major version. The pipeline still owns everything
else: render, metadata, review, repair, merge, GCS promotion, and labels.
Nothing from the source branch is merged directly.

To adopt, pass `source_ref` to `bulk-generate.yml` or `impl-generate.yml`, and
name the model that wrote the code in `source_model`:

```bash
gh workflow run bulk-generate.yml -f specification_id=all -f library=muix \
  -f source_ref=gemini/muix-9 -f source_model=gemini-4-argon
```

Name the ref as the repository knows it, such as `main` or `gemini/muix-9`. A
leading `origin/` is dropped. `source_model` is optional and takes a model
name of letters, digits, `.`, `_`, and `-`, at most 40 characters. Both
workflows check both inputs before they print them, and any other value stops
the run, so a `bulk-generate.yml` run with a malformed value stops before its
first dispatch. Without `source_ref`, the run ignores `source_model` with a
warning. An adopted run differs from a generation in these ways:

- **The file comes from the ref.** The step "Adopt implementation from source
  ref" fetches the ref and takes exactly
  `plots/{spec-id}/implementations/{language}/{library}{ext}`, the file the
  generator would write. The Claude steps and the prompts overlay are skipped,
  and every later step runs unchanged.
- **It renders the file the way the generator does.** Both themes run with the
  generator's commands: `python -P` with `MPLBACKEND=Agg` for Python, and the
  browser render harness for JavaScript. `core.canvas` then checks both PNGs.
  A drift from the canvas only warns, because the canvas gate in
  `impl-review.yml` sends it to repair. Python and JavaScript only: an R or
  Julia run fails with an error.
- **It's always a forced regeneration.** The PR is labelled `regen:forced`
  whatever `regen_gate` says, so it takes the fresh-generation path with the
  repair loop and never the regen gate.
- **No pipeline model writes the code.** The routed model, Opus under
  `model=auto` as for any forced regeneration, still runs repair. The PR body
  names the source, its commit, and the `source_model` on a `**Generation:**`
  line, and keeps the repair model on its `**Model:**` line, which review and
  repair rescues read.
- **The metadata names the author and the source.** `generated_by` records the
  `source_model`, such as `gemini-4-argon`, or `adopted:{source_ref}` when the
  run has none. A new key, `adopted_from`, follows it with the ref and the full
  commit SHA the file came from, in the form `adopted_from: {source_ref} ({sha})`.
  A later regeneration by Claude rewrites the metadata without `adopted_from`.
- **A source failure is not retried.** When the file or the ref is missing, or
  the file doesn't render, the run comments on the spec issue and stops. It
  isn't retried, it doesn't count toward the 3-attempt cap, and it never sets
  `impl:{library}:failed`, because every retry would read the same file. Fix
  the file on the source branch, then dispatch again. A failure of the runner,
  such as an unreachable origin or a canvas check that can't run, and a failure
  in a later step, such as the push, the metadata, the upload, or the PR, are
  retried as usual, and the retry keeps `source_ref` and `source_model`.

Each adopted PR still gets an Opus review. At the default pace of 180 seconds,
one `bulk-generate.yml` run dispatches about 115 pairs before its 6-hour job
timeout, so a library across the whole catalogue needs a lower `pace_seconds`
or several runs. With `specification_id=all`, every spec whose file is missing
on the source ref gets an "Adoption Failed" comment. The watchdog's generation
rescues don't carry `source_ref` or `source_model`: a pair the watchdog
re-dispatches is generated by Claude.

### Daily regeneration modes

`daily-regen.yml` has two modes. The repository variable
`REGEN_PAIRS_PER_DAY` chooses the mode of the scheduled run:

| `REGEN_PAIRS_PER_DAY` | Scheduled run |
|-----------------------|---------------|
| Unset or empty | Spec mode, as before: the oldest spec (`count`, default 1), spec polish, the cross-library similarity audit, then `bulk-generate.yml` for all 15 libraries |
| A positive integer N | Pair mode: the N oldest implementations across the catalogue, the similarity audit for each spec among them, then one `impl-generate.yml` dispatch per pair |
| Anything else | The run stops with an error before it picks anything |

The variable changes only the scheduled run. A manual run keeps its inputs and
their meaning, and switches to pair mode only with the `pairs` input. The
watchdog's cron rescue replaces a missed scheduled run, so it forwards the
variable as `pairs`. A `specification_id` always wins over a pair count.

Pair mode picks the oldest pairs and never picks the same pair night after
night:

- A pair's age is its newest touch: its metadata `updated` timestamp
  (`created` when there's none), or its last real attempt, whichever is newer.
  A real attempt is an `implementation/{spec-id}/{library}` PR that was merged
  or closed, a `regen:kept` PR included, or a failed generation, which leaves
  an `<!-- impl-fail:{spec-id}:{library} -->` comment on the spec issue. A
  kept regeneration and a failed generation leave `updated` alone, so without
  the attempt record the same pair would come back the next night.
- A pair touched within the attempt window is skipped. The window is the
  `attempt_window_days` input, else the repository variable
  `REGEN_ATTEMPT_WINDOW_DAYS`, else 30 days. After the window, the pair queues
  behind every pair touched before it.
- An infrastructure failure, whose comment carries
  `<!-- impl-fail-cause:infra -->`, and a generation Claude stopped, whose
  comment carries `<!-- impl-paused-claude:… -->`, are not attempts: the pair
  stays at its place in the queue and comes back on a later night.
- A pair with an open implementation PR is skipped: its attempt is still
  running, stuck, or paused.
- Every pair of a spec whose issue saw activity within `min_age_hours`
  (default 20) is skipped for that night, as in spec mode.
- Only pairs with a metadata file are candidates, so pair mode never writes a
  first implementation. Gap backfill stays with `bulk-generate.yml`.

Before the new pairs, pair mode resumes the reviews and repairs that Claude
stopped: the open implementation PRs with `ai-review-paused` or
`ai-repair-paused`, oldest first. Each resume counts against N, so a night with
three paused PRs and `REGEN_PAIRS_PER_DAY=5` dispatches three resumes and two
new pairs. The job "Re-dispatch paused reviews and repairs" starts
`impl-review.yml` or `impl-repair.yml` with the arguments the watchdog's
rescues use, at the pace of the pair dispatches. While the stop lasts, a resume
is refused at its first request, which costs nothing, and pauses again.

The picker fails closed. When the implementation PR listing fails, the run
stops with an error, because that listing records the kept, closed, open, and
paused PRs. The kept-regeneration and issue listings degrade with a warning.
The picker reads the failed-generation comments only for the specs at the
front of the queue, at most 100 issues per run, and a spec whose comments
can't be read sits out the night. Spec mode keeps its own rule: a spec's age is
the newer of its metadata and any activity on its issue, so a kept or failed
regeneration moves the spec to the back of the queue, and so does an
infrastructure failure or any comment.

Pair mode skips the spec polish, because a spec rewritten for one library
would leave its other implementations written against the old text. It
dispatches each pair straight to `impl-generate.yml` with the arguments and
pace of `bulk-generate.yml` (180 seconds between dispatches, 120 seconds for a
pinned `sonnet` or `haiku`), and never through `bulk-generate.yml`: that
workflow's single concurrency group keeps one pending run and cancels the
older one. The regen gate, the review, and the merge are unchanged.

The picks go to the log and the run summary, so a dry run shows them:

```bash
gh workflow run daily-regen.yml -f pairs=5 -f dry_run=true
```

The dry run still runs the similarity audit, as in spec mode. With
`CLAUDE_AUTH=oidc`, run [Test the spend limit](#test-the-spend-limit) first,
before you set the variable. To turn pair mode on for the schedule, run
`gh variable set REGEN_PAIRS_PER_DAY --body 5`; to turn it off, run
`gh variable delete REGEN_PAIRS_PER_DAY`.

When Claude stops a pre-flight session (the spec polish or the similarity
audit), the night's dispatch for that spec is skipped and the run fails (see
[When Claude stops a session](#when-claude-stops-a-session)). In pair mode,
the similarity audit of each spec runs before that spec's pairs are
dispatched, one spec after another, so it works as the night's probe: once a
pair's generation, review, or repair has reached the limit, every later spec
of the night stops at its audit and dispatches nothing. Pairs that were
already dispatched fail at their first refused request, which costs nothing,
and are parked without a retry or a counted attempt. Their spec keeps its
pairs in the queue for a later night. The resumes don't wait for the audit:
they start in a job of their own, and while the stop lasts each one pauses
again at no cost.

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
| Adopt mode (`source_ref`): the file comes from that ref (see [Adopt implementations from a branch](#adopt-implementations-from-a-branch)) | None generates; the routed model runs repair (Opus, as for a forced regeneration) |
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

## Claude credentials

Every Claude step of the pipeline runs on one of three credentials. The
repository variable `CLAUDE_AUTH` chooses it for every run:

| `CLAUDE_AUTH` | Credential | Billed to |
|---------------|------------|-----------|
| Unset, empty, or `subscription` | The `CLAUDE_CODE_OAUTH_TOKEN` secret | The owner's Claude subscription, as before the switch |
| `oidc` | Workload identity federation: the job's GitHub OIDC token, exchanged for a short-lived Claude API token. The repository variables `CLAUDE_WIF_RULE_ID`, `CLAUDE_WIF_ORG_ID`, `CLAUDE_WIF_SERVICE_ACCOUNT_ID`, and `CLAUDE_WIF_WORKSPACE_ID` name the federation. | The API credits of the federation's workspace |
| `api` | The `ANTHROPIC_API_KEY` secret, the fallback when federation isn't available | The API credits of the key's workspace |
| Anything else | None: the job stops | Nothing |

The value ignores case. The switch covers all 13 Claude steps in the 8
workflows that run Claude: `daily-regen.yml`, `impl-generate.yml`,
`impl-repair.yml`, `impl-review.yml`, `report-validate.yml`,
`review-retest.yml`, `spec-create.yml`, and `util-claude.yml`. The models don't
change: the aliases `sonnet` and `opus` resolve to the same models on the API.

Every job that runs Claude starts with the step "Resolve Claude credentials".
It turns `CLAUDE_AUTH` into a mode, and every Claude step reads the step's
outputs, so a new mode changes only that step. Each Claude step gets exactly
one credential and leaves the others empty, because an API key or an OAuth
token silently shadows federation, and the action doesn't document which of
the two wins. The step stops the job with an error in these cases, and never
falls back to the subscription, so a broken switch can't spend the owner's
interactive quota:

- `CLAUDE_AUTH` has an unknown value.
- `CLAUDE_AUTH` is `api` and the `ANTHROPIC_API_KEY` secret is missing.
- `CLAUDE_AUTH` is `oidc` and one of the four `CLAUDE_WIF_*` variables is
  missing or isn't an ID.
- `CLAUDE_AUTH` is `oidc`, the run is one that federation refuses, and the
  `CLAUDE_CODE_OAUTH_TOKEN` secret is missing (see
  [Which runs federation accepts](#which-runs-federation-accepts)).

In `spec-create.yml` and `report-validate.yml`, the step runs only for an
issue that reaches Claude. In `impl-generate.yml`, it runs before the issue
number is known, so a stop never counts against the pair's three attempts.

With an API key, the action also classifies Claude's unconfirmed inline PR
comments with Haiku on that key and drops the ones it reads as test probes.
With the subscription or federation, it posts all of them. Only
`util-claude.yml` on a pull request writes inline comments.

### Which runs federation accepts

GitHub mints the OIDC token per job, and its `sub` claim names the trigger.
The federation rule accepts only the subject
`repo:MarkusNeusinger/anyplot:ref:refs/heads/main`, so with `CLAUDE_AUTH=oidc`
the Claude steps of these runs work:

| Workflow | Triggers | Subject |
|----------|----------|---------|
| `daily-regen.yml` | `schedule`, `workflow_dispatch` on `main` | `…:ref:refs/heads/main` |
| `impl-generate.yml` | `issues` (a `generate:` label), `workflow_dispatch` on `main` from bulk-generate, daily-regen, the watchdog, and its own retries | `…:ref:refs/heads/main` |
| `impl-review.yml` | `repository_dispatch`, `workflow_dispatch` on `main` | `…:ref:refs/heads/main` |
| `impl-repair.yml` | `workflow_dispatch` on `main` | `…:ref:refs/heads/main` |
| `spec-create.yml`, `report-validate.yml` | `issues` (a label) | `…:ref:refs/heads/main` |
| `util-claude.yml` | `issue_comment`, also on a pull request | `…:ref:refs/heads/main` |

Federation would refuse the other runs with `401 Authentication failed`, so
under `oidc` they use the subscription on purpose:

- `util-claude.yml` started by a `pull_request_review_comment` or a
  `pull_request_review`: the subject is `repo:MarkusNeusinger/anyplot:pull_request`.
- Any workflow dispatched on another branch, such as a branch smoke with
  `--ref feature/x` and the retries it dispatches on that branch: the subject
  is `…:ref:refs/heads/feature/x`.
- `review-retest.yml`: its review job has no `id-token` permission on
  purpose, because without it the action can't mint the Claude GitHub App
  token, so no session can write to the repository. A retest arm on `oidc`
  runs on the subscription.

"Resolve Claude credentials" recognizes these runs by the event name, the
ref, and the missing token request URL. It logs
`oidc not available for <event>/<ref>; using subscription` as a notice and in
the job summary, then runs the job on the `CLAUDE_CODE_OAUTH_TOKEN` secret. If
the secret is missing, it stops the job instead.

Every other job that runs Claude already has `id-token: write`, for the
Claude GitHub App token and, in some of them, Google Cloud. The federation
didn't add the permission to any job.

### Set up workload identity federation

1. In the Claude Console, open
   [Workload identity](https://platform.claude.com/settings/workload-identity-federation),
   click **Connect workload**, and select **GitHub Actions**. The wizard
   registers GitHub's issuer, creates a service account, and creates the
   federation rule.
2. Give the rule these values:
   - Subject prefix: `repo:MarkusNeusinger/anyplot:ref:refs/heads/main`.
   - Audience: `https://api.anthropic.com`, the action's default.
   - Claims: `repository_owner=MarkusNeusinger`, `repository=MarkusNeusinger/anyplot`,
     and `ref=refs/heads/main`.
   - Workspace: `ci-regen` only, with the scope `workspace:developer` and a
     token lifetime of 600 seconds. The action fetches a fresh GitHub token
     every 4 minutes and Claude Code exchanges it again, so a session longer
     than the lifetime keeps running.
3. Remove the `event_name=push` claim that the wizard fills in. With it, the
   rule refuses every scheduled, dispatched, and issue-triggered run, which is
   every run of the pipeline.
4. Set a spend limit on the `ci-regen` workspace.
5. Store the four IDs as repository variables. They're identifiers, not
   secrets. The organization ID is on the
   [Organization](https://platform.claude.com/settings/organization) page; the
   rule ID (`fdrl_…`), the service account ID (`svac_…`), and the workspace ID
   (`wrkspc_…`) belong to the resources the wizard created:

   ```bash
   gh variable set CLAUDE_WIF_RULE_ID --body fdrl_...
   gh variable set CLAUDE_WIF_ORG_ID --body 00000000-0000-0000-0000-000000000000
   gh variable set CLAUDE_WIF_SERVICE_ACCOUNT_ID --body svac_...
   gh variable set CLAUDE_WIF_WORKSPACE_ID --body wrkspc_...
   ```

6. Switch the pipeline to federation, as described in
   [Switch modes](#switch-modes).

A refused exchange always answers `401 Authentication failed`. The reason, such
as `match_subject_prefix`, is in the authentication history on the Workload
identity page.

### Switch modes

Switch with one command. Each takes effect with the next job that starts.

- Federation: `gh variable set CLAUDE_AUTH --body oidc`
- API key: run `gh secret set ANTHROPIC_API_KEY` once, which prompts for the
  value so the key stays out of your shell history, then
  `gh variable set CLAUDE_AUTH --body api`
- Subscription: `gh variable set CLAUDE_AUTH --body subscription`, or
  `gh variable delete CLAUDE_AUTH`

To check a switch, open the next Claude run: the step "Resolve Claude
credentials" logs `Claude credentials: <mode>`, and the cost line in the job
summary reads `auth=<mode>`. For an API key, create it in a workspace of its
own with a spend limit.

### Session cost

After every Claude step, the step "Claude session summary" writes one line to
the job summary and the log:

```text
claude-cost step=impl-generate auth=api model=claude-sonnet-5-5 total_cost_usd=0.2931
```

`total_cost_usd` is Claude Code's own estimate at API list price. On the
subscription it's what the session would have cost on the API. It reads
`n/a` when the session wrote no result, and the step never fails the job. The
weekly regen review sums these lines (`collect_week.py --costs`) and shows the
part that ran on API credits. Job logs measured from 2026-10-28 to 2026-10-31
put a generation on Sonnet at about $0.29 per implementation, a review on
Opus at about $1.10, and a repair with its re-review at about $2.70 per
implementation in all.

### When Claude stops a session

Two stops end the pipeline's work cleanly instead of counting as a failure of
the implementation:

- A Claude spend or usage limit, in every mode. Once the limit is reached,
  every request is refused until it resets or you raise it, and Claude Code's
  own retries can't get past it.
- Refused credentials, with `api` and `oidc` only: an invalid or revoked API
  key, or a federation exchange that the rule refuses. With the subscription,
  an authentication error keeps the handling it had before the switch.

For a limit, the pipeline recognizes these texts:

- A spend limit you set on the workspace or the organization (`oidc`, `api`):
  HTTP 400 `invalid_request_error`, with a message that starts with
  `You have reached your specified workspace API usage limits` or
  `You have reached your specified API usage limits`.
- The usage tier's monthly spend cap: HTTP 429 `rate_limit_error` with the
  `error_code` `enforced_spend_limit_reached` and no `retry-after` header.
- An empty credit balance: the API's `Your credit balance is too low`, Claude
  Code's `Credit balance is too low` or `Credit balance too low · Add funds`,
  and its error type `billing_error`.
- The subscription's usage limit (`subscription`): Claude Code's messages that
  start with one of the prefixes its SDK exports as
  `USAGE_LIMIT_ERROR_PREFIXES`, such as
  `You've hit your session limit · resets 12:30pm`, and the older
  `Claude AI usage limit reached`.

A transient rate limit, such as a per-minute token limit, is none of these:
it keeps its retry and the infrastructure path it took before.

For refused credentials, it recognizes the API's error types
`authentication_error` and `permission_error`, HTTP status 401 or 403 on the
failed request, Claude Code's error type `authentication_failed`, and the
texts `Authentication failed` and `invalid x-api-key`. A limit wins over its
status code: a 403 with a usage-limit message counts as a limit.

"Claude session summary" reads these texts only from the error fields of a
session that failed: the error result, Claude Code's error messages, and its
API retries. It never reads the conversation, which may quote the same text,
and never flags a session that ended well. When it finds one, it writes an
`::error::` and the line **Claude spend/usage limit reached (auth=oidc)** or
**Claude credentials refused (auth=oidc)**, with the mode, to the job summary,
and every path treats the stop as an infrastructure failure:

| Workflow | What happens |
|----------|--------------|
| `impl-generate.yml` | The retry is skipped, and "Stop when Claude stopped the session" fails the job. "Handle generation failure" parks the pair before it counts anything: it removes `generate:{library}` and `impl:{library}:pending`, puts `impl:{library}:done` back for a live implementation, and comments with the marker `<!-- impl-paused-claude:{spec-id}:{library} -->`. Nothing is retried, no attempt counts toward the cap of three, and the pair is never marked `impl:{library}:failed`, a first implementation included. No PR exists; the next generation recreates the branch. |
| `impl-review.yml` | No score, no verdict, and no regen gate decision, even when the session wrote `quality_score.txt` before it stopped: "Extract quality score" is skipped. "Validate review output" adds `ai-review-paused` and the "AI Review Paused" comment, without the auto re-review and without spending it. The PR stays open, and nothing is merged or closed. |
| `impl-repair.yml` | The retry is skipped. "Handle repair failure" restores `ai-rejected`, adds `ai-repair-paused`, and comments, without the auto-retry and without spending it. The attempt isn't used up. |
| `daily-regen.yml` | A spec polish or similarity audit that Claude stopped skips that spec's dispatch, and the entry fails. |
| `spec-create.yml`, `util-claude.yml` | The retry is skipped, and the job fails. |
| `report-validate.yml`, `review-retest.yml` | The step fails as before: the issue gets the "Validation Failed" comment, and the cell is collected as failed. |

The watchdog skips every PR with `ai-review-paused` or `ai-repair-paused`, so
it never spends its one-shot rescue on a stop. In pair mode, daily-regen
resumes the paused PRs first, oldest first (see
[Daily regeneration modes](#daily-regeneration-modes)), and the resumed review
or repair removes its label when it starts. A resume that pauses again while
the stop lasts puts the label back but posts no second comment when the PR's
latest bot comment is already the same pause. A parked pair keeps its place in
the queue: neither a parked generation nor a paused review or repair is a real
attempt.

In spec mode, or to resume sooner, resume the paused PRs yourself once the
limit resets or the credentials are fixed:

1. Rerun every paused review:

   ```bash
   gh pr list --label ai-review-paused --json number --jq '.[].number' \
     | xargs -I{} gh workflow run impl-review.yml -f pr_number={}
   ```

2. Restart every paused repair with the command in its "Repair Paused"
   comment, which names the PR, the pair, and the attempt.

Before this change, a subscription usage limit counted as the pair's own
failure: it used up the three attempts and marked a first implementation
`impl:{library}:failed`. A bulk run that reaches the subscription limit now
parks the rest of its pairs instead, and you re-dispatch them once the limit
resets.

### Test the spend limit

Test the stop on the first day of `CLAUDE_AUTH=oidc`, before you set
`REGEN_PAIRS_PER_DAY`, so that no nightly run spends the workspace while you
test:

1. In the Claude Console, set the `ci-regen` workspace's spend limit to the
   month's spend so far plus about 0.50 USD.
2. Dispatch one regeneration of a pair whose implementation is live on main:

   ```bash
   gh workflow run impl-generate.yml -f specification_id=SPEC_ID -f library=LIBRARY
   ```

   The generation on Sonnet costs about 0.29 USD and passes; the review on
   Opus costs about 1.10 USD and reaches the limit while it runs.
3. Check the `impl-review.yml` run: its summary shows **Claude spend/usage
   limit reached (auth=oidc)**, the PR has `ai-review-paused` and the "AI
   Review Paused (Claude spend/usage limit reached)" comment, no second review
   run started, and no verdict or `quality:` label was added. If the summary
   line is missing, the run's error text didn't match: read it in the log and
   extend `LIMIT_PATTERN`.
4. Check the spec issue: no `impl:{library}:failed` label, and no
   `impl-fail` comment for the pair.
5. Check the next watchdog scan: its log reads
   `PR #PR_NUMBER: paused (Claude stopped its review or repair) — skipped`,
   and it dispatched nothing for the PR.
6. Restore the spend limit, then rerun the review:

   ```bash
   gh workflow run impl-review.yml -f pr_number=PR_NUMBER
   ```

7. Check that the review removes `ai-review-paused`, finishes, and the regen
   gate decides as usual.

To test the generation path as well, set the limit to the spend so far plus
about 0.05 USD: the generation stops, the pair is parked as described above,
and its retry is skipped.

### Exposure

Each credential reaches only the Claude steps, and nothing else:
`tests/unit/workflows/test_claude_auth.py` checks that the API key appears only
in the action input and in the resolve step's `!= ''` test, and that no job
gained `id-token: write`. None of the eight workflows runs on `pull_request`
or `pull_request_target`, so a pull request from a fork never gets a
credential. `util-claude.yml` runs only for comments by owners, members, and
collaborators. `spec-create.yml` and `report-validate.yml` run on a label,
which only maintainers can add, but they read issue text that anyone can
write.

Federation adds no stored secret, but the trust lives in the Claude Console,
not in the repository:

- Any step of a job with `id-token: write` can mint an OIDC token. The
  federation rule accepts only `main`, so a token from a pull-request event or
  another branch is refused, but a step on `main` can exchange its token for a
  Claude API token whatever `CLAUDE_AUTH` says.
- Switching `CLAUDE_AUTH` back to `subscription` or `api` doesn't close that
  path. While you don't use `oidc`, disable the federation rule on the
  [Workload identity](https://platform.claude.com/settings/workload-identity-federation)
  page.
- The rule's claims name the repository and the ref, not the workflow. GitHub
  also signs the `job_workflow_ref` claim, the workflow file the job runs
  from, so adding it to the rule could narrow federation to the workflows
  that run Claude. This is unverified: check that the Console accepts the
  claim before you rely on it.
- The steps that run model-written code in a job with `id-token: write`
  unset `ACTIONS_ID_TOKEN_REQUEST_URL` and `ACTIONS_ID_TOKEN_REQUEST_TOKEN`
  first, so that code can't mint a token: "Adopt implementation from source
  ref" and "Adaptability smoke run (record-only)" in `impl-generate.yml`, and
  "Adaptability smoke run (record-only)" in `impl-repair.yml`. The
  adaptability check in `impl-review.yml` reads the code without running it.
  The switch doesn't change what a Claude session's own tools can reach.

A leaked federated token expires after 600 seconds, and an API key is billed
until you revoke it; the workspace's spend limit bounds either.

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
