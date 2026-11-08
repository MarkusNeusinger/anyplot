---
name: audit-catalogue
description: Audit the live plot catalogue and repair what is not good, in rounds — select candidate pairs with the bundled read-only select_candidates.py (thumbs-down votes from the production feedback table, low or capped review scores and kept defects, stale library versions or GCS renders, agent-validator refusals, or a sweep of a library or spec), audit them visually with the bundled audit_workflow.js (metadata, both renders with a cache-buster, the spec, the merged review; a skeptic per high or medium finding), publish the confirmed defects as a private Artifact page, and only after the owner picks fix Python and JavaScript pairs locally in fresh worktrees, check them with check_fix.py, and adopt them through the pipeline one bulk-generate run at a time with dispatch.sh (R and Julia through a forced regeneration with a change request, spec causes through a spec issue), then re-audit the merged results. Use when asked to audit the catalogue, check the thumbs-down plots, find and fix bad implementations, sweep a library, or "den Katalog durchsehen".
---

# Audit the catalogue and repair it

The catalogue's pairs (a spec in one library) pass an AI review before they
merge, and some still are not good: on 2026-11-08 a proportional-symbol map
merged as a Dorling cartogram at 84 although its own review scored SC-01 3/5,
and one pair's production renders stayed three months old after a silent
promote. This skill finds such pairs, shows them to the owner, and repairs the
ones he picks through the pipeline, so `quality_score`, the review, the
metadata and the GCS promotion stay the pipeline's (CLAUDE.md mandatory
workflow).

There is no schedule. Run a round when the owner asks, for example after a
library migration, when thumbs-down votes collect, or for a sweep of one
library.

A round has two owner gates. The owner picks the findings to fix (step 4),
and the owner approves the dispatch queue (step 7). Before the first gate
everything is read-only; nothing leaves the machine before the second.

## Rules

- **Read-only until the owner's picks.** Selecting, auditing and building the
  page read the repository, GitHub, the bucket and the database, and write
  only into the round directory. The feedback query runs in a transaction
  PostgreSQL holds read-only and returns counts.
- **Nothing goes out without the owner's OK for the queue.** No push, no
  dispatch, no issue, no label, no comment before he approved that round's
  `queue.txt` (and, for a spec issue, that issue by spec id). A generic "ok"
  authorizes nothing (CLAUDE.md external-system rule).
- **The pipeline owns the result.** Fixes reach `main` only through adopt mode
  (`bulk-generate.yml -f source_ref=<full SHA>`) or a forced regeneration.
  Never merge an implementation PR, write metadata, upload a render or edit a
  stored score.
- **Visitors' feedback stays private.** The selector reads only reactions and
  never a message, contact or session id. The round directory lies outside
  every git checkout (the scripts refuse a path inside one).
- **Pairs stay independent.** A fix agent reads its own pair's code, spec and
  renders, never another library's code (the regen independence rule). An
  auditor may open another library's renders of the same spec, only to judge a
  spec cause.
- **A skeptic decides what counts.** Every high or medium finding gets a
  skeptic that tries to refute it and defaults to refuted. Only what survives
  goes on the page as confirmed.
- **Rubric findings change no prompt.** A defect the review named and merged
  anyway is a finding for the rubric watch; a change to the reviewer's prompts
  needs a `review-retest.yml` arm first (CLAUDE.md).
- **Gemini runs through `gemini_review.py` only.** A second opinion on a round's
  plan uses `.claude/skills/zweitmeinung/gemini_review.py`; never run `agy`.

## 1 · Set up the round

1. Run `git fetch origin main`. Every script reads the catalogue from
   `origin/main` through git, never from a working tree.
2. Make the round directory outside the repository, private:
   `ROUND=~/anyplot-audit/$(date -u +%F)` and
   `mkdir -p "$ROUND" && chmod 700 ~/anyplot-audit "$ROUND"`. A second round
   on the same day takes a suffix (`2026-11-08b`).
3. Name the main checkout's `.env` for the votes:
   `ENV="$(git rev-parse --path-format=absolute --git-common-dir)/../.env"`.
   A worktree has none; the selector reads only `DATABASE_URL` and never
   prints it.
4. Confirm the round's extent with the owner before you start, as options
   (AskUserQuestion): the sources, the filters (a library, a spec list), the
   cap on audited pairs (about 60 per run), and the stop point.

## 2 · Select the candidates

```bash
S=.claude/skills/audit-catalogue
uv run --extra agents python $S/select_candidates.py --out "$ROUND/candidates.json" \
  --votes --env "$ENV" --scores --stale --gcs --readiness --min-rank 3
```

Combine the sources per round:

| Flag | Reads | Reason codes |
|---|---|---|
| `--votes` | `feedback` reactions per spec × language × library, one vote per visitor session | `thumbs_down` (more down than up since the metadata's `updated`), `thumbs_down_old_version` (only before it: cast on an older version) |
| `--scores` | the stored review in `metadata/*.yaml` | `no_score`, `below_threshold` (`--below`, default 85), `capped` (total below the item sum), `plot_type_below_max` (SC-01), `spec_compliance_below_max`, `technical_below_max`, `residual_defects` |
| `--stale` | `library_version` against `core.library_versions` | `library_behind` (an older API level), `old_update` (with `--older-than DAYS`) |
| `--gcs` | a HEAD on both production renders, with `?cb=<epoch>` | `render_missing`, `render_stale` (older than `updated`), `render_unchecked` |
| `--readiness` | the agent validator's scan, as the corpus tests run it | `validator_refusal` (any refusal but a map spec), `validator_error` |
| `--sweep` | every pair of the filtered universe | `sweep` |

- `--library`, `--language`, `--spec` and `--specs-file` narrow the universe
  first; `--sweep` needs one of them, or `--all`.
- The rank adds a weight per reason (`WEIGHTS` in the script) and only orders
  the list. `--min-rank` and `--limit` cut it; the script prints how many the
  limit dropped.
- The catalogue has no `needs_attention` field. `capped`, `residual_defects`
  and the items below their maximum stand in for it.
- The selector reads the stored review only. The audit reads the merged PR's
  review comment for what the merge kept (step 3).

Tell the owner the universe, the number of candidates per reason, and which
ones go to the audit. Cut to the agreed cap, by rank, and name what you cut.

## 3 · Audit

Build the workflow's input from the candidates and run
`.claude/skills/audit-catalogue/audit_workflow.js` with the Workflow tool
(`scriptPath`, absolute), with args such as:

```bash
MAIN=$(git rev-parse --path-format=absolute --git-common-dir | xargs dirname)   # the main checkout
jq --arg round "$ROUND" --arg repo "$MAIN" '{round: $round, repo: $repo, ref: "origin/main", label: "run1",
     pairs: [.candidates[] | {spec, language, library, reasons: [.reasons[] | "\(.code): \(.detail)"]}]}' \
  "$ROUND/candidates.json" > "$ROUND/args-run1.json"
```

Pass the file's content as the Workflow tool's `args` (a JSON object, not a
string).

- One auditor checks about six pairs (`group_size`): the metadata at the ref,
  both renders fetched with `?cb=<epoch>` and viewed, the spec, and the merged
  PR's review comment. It classifies each finding by severity, defect class
  and cause (`implementation`, `spec`, `pipeline`, `rubric`), with a one-sentence
  fix. A skeptic per high or medium finding re-downloads the renders and tries
  to refute it.
- The workflow cannot write files. Write its returned value to
  `$ROUND/audit-run1.json`; a later run of the same round takes the next
  label.
- Without the Workflow tool, run the same two prompts (`auditPrompt` and
  `verifyPrompt` in the script) through the Agent tool on Opus: one agent per
  group, then one skeptic per high or medium finding.

Auditors and skeptics make judgment calls, so they run on Opus (the
inherited session model; `agentic/docs/agent-operations.md`).

## 4 · Show the owner the confirmed defects

```bash
uv run python $S/build_page.py --round "$ROUND" --audit "$ROUND/audit-run1.json"
```

The script writes `$ROUND/findings.json` (every finding with an id: confirmed
high and medium first, then the unverified low notes, then the refuted claims)
and `$ROUND/page/audit.html`, which embeds each pair's two `_800.webp` renders.

1. Load the `artifact-design` skill, then publish `$ROUND/page/audit.html` with
   the Artifact tool as a private page (icon `chart`). The renders are public
   catalogue images, and the page holds no visitor data.
2. Give the owner the link and the headline: pairs audited, confirmed high
   and medium, and the causes.
3. The owner picks by id, or by a rule such as "all high and medium". When he
   is away, create a Todoist task in **Anyplot** with the link.

## 5 · Plan the picked fixes

Write `$ROUND/plan.md`: one line per picked id with its route.

| Cause and language | Route |
|---|---|
| `implementation`, Python or JavaScript | A local fix in a worktree (step 6), adopted from its pushed `claude/*` ref |
| `implementation`, R or Julia | A `regen` line: a forced regeneration with a one-sentence change request. Adopt mode cannot render R or Julia |
| `pipeline`, a stale or missing render | A re-render of the merged code: a `regen` line, or for Python and JavaScript `gh workflow run impl-generate.yml -f specification_id=<spec> -f library=<lib> -f source_ref=main -f source_model=<generated_by>` (`docs/workflows/overview.md`, "Promotion to production") |
| `spec` | A spec issue (`reference/spec-issue.md`), then the affected pairs' fixes once it merges |
| `rubric` | A report line and a Todoist task for the rubric watch; the pair's own defect still takes one of the routes above |

A change request is one sentence about the defect, for one library: "Draw the
decision boundary from a 200-step mesh so it does not show as a staircase."
Show the owner the plan with the open decisions as options (a deviation from
the spec, a held pair, a rebuild instead of a port).

## 6 · Fix locally

1. Make one shared JavaScript install for the round:
   `git worktree add --detach .claude/worktrees/audit-base origin/main`, then
   `source ~/.nvm/nvm.sh && nvm use 24 && npm ci` inside it. The main
   checkout's `node_modules` can lag the lock (MUI X 7.29.1 against 9.17.0 on
   2026-11-08).
2. Cut one fresh worktree per package of about ten files of one library:
   `git worktree add -b claude/audit-<date>-<lib>-<n> .claude/worktrees/audit-<lib>-<n> origin/main`,
   and link the install: `ln -s "$PWD/.claude/worktrees/audit-base/node_modules" .claude/worktrees/audit-<lib>-<n>/node_modules`.
   A fresh worktree per package keeps a long session from drifting.
3. Brief one Opus delegate per worktree. The brief names the confirmed
   findings with their evidence and fix, and states:
   - Edit files only with the Edit and Write tools; run all `git` inside your
     own worktree; leave the shared checkout on its branch.
   - Decide and document routine choices (a colour within the palette, a
     label position); return as a finding anything that changes what the
     plot shows, contradicts the spec, or would be expensive to redo.
   - Read only your pair's code, spec, metadata and renders, never another
     library's code.
   - One commit per spec; stage the file by path, never `git add -A` (the
     `node_modules` link shows as untracked); never commit a render.
   - Leave the header's `Quality:` and `Updated:` lines as they are:
     impl-review writes them.
   - Render and check each file with `check_fix.py --render`, look at both
     PNGs, and do not push.
4. Check every package yourself before anything leaves:

   ```bash
   uv run --extra agents python $S/check_fix.py --repo .claude/worktrees/audit-<lib>-<n> --ref HEAD \
     --render --out "$ROUND/renders/<lib>-<n>" <spec>/<lib> ...
   ```

   It checks the commit range (implementation files only, no render, no
   metadata, no `node_modules`), that `main` did not change a file since the
   fix was cut (adopt mode takes the whole file, so it would revert that), the
   header block, the agent validator against the base (a new refusal or a new
   `deprecated-api` hint fails), and with `--render` both themes on the canvas
   target and not blank. Look at the renders yourself.

R and Julia are not rendered locally: adopt mode cannot take them, so their
fix is a `regen` line and the pipeline renders it. The renderer's toolchain
image (`agents/renderer/toolchain.Dockerfile`) holds R 4.6.1 and Julia 1.13.2
if a local reproduction is ever needed.

## 7 · Dispatch, after the owner's OK

1. Write `$ROUND/queue.txt`, one package per line:

   ```text
   adopt muix claude/audit-2026-11-08-muix-1 claude-opus-5-5 cartogram-area-distortion burndown-sprint
   regen ggplot2 indicator-ema Use the 12- and 26-day periods the spec's example names.
   ```

2. Show the owner the queue with each package's `check_fix.py` lines and
   its renders. The repository is public, so a pushed ref is visible: nothing
   is pushed before his OK for the queue.
3. After his OK, push the refs
   (`git -C <worktree> push -u origin claude/audit-<date>-<lib>-<n>`; a
   `claude/*` push starts no workflow), then run the dry run, which resolves
   each ref to its SHA, checks every adopt line again there and dispatches
   nothing: `bash $S/dispatch.sh "$ROUND"`.
4. Start the dispatcher in the background (`run_in_background`):
   `bash $S/dispatch.sh "$ROUND" --execute`.

The dispatcher sends one line at a time, and only while no `bulk-generate`
run is queued or in progress. It resolves each ref to its full SHA, re-runs
`check_fix.py` there, dispatches only the specs that pass, and logs the rest.
Its state (`dispatch.state`) keeps a line from going out twice.

## 8 · Watch the pipeline

- Post a status line about every 10 minutes from
  `bash $S/pkg_status.sh "$ROUND"`: per spec the newest PR titled
  `feat(<lib>): implement <spec>` since the dispatch, its state and labels, and
  a summary per package.
- At the subscription's 5-hour limit the pipeline pauses reviews
  (`ai-review-paused`) and repairs (`ai-repair-paused`). After the limit
  resets, resume them one every 150 s:
  `bash $S/resume_paused.sh "$ROUND" --library <lib> --repairs` shows what it
  would run; add `--execute` to run it. The owner's OK for the queue covers
  these resumes; say in the status line that you started them.
- A stuck PR, a failed merge or a missing render is `babysit-pipeline`'s
  recovery recipe.

## 9 · Re-audit and close the round

1. When a package's PRs are merged, select its pairs again
   (`--spec <spec> ... --library <lib> --scores --gcs --sweep`) and run the
   audit workflow with the next label. A fix counts when its finding is gone
   and the renders are fresh; a new finding starts the next round.
2. After the merges, run `scripts/site-smoke.mjs` once (`/open-pr` §4).
3. Write `$ROUND/report.md` in English, Google style: the candidates per
   source, the confirmed findings and their routes, the PRs with their new
   scores, the re-audit, and the open owner decisions. Create one Todoist task
   per owner decision.
4. Clean up: stop the dispatcher, remove the merged fix worktrees and their
   local branches, and remove `.claude/worktrees/audit-base`. The `claude/*`
   refs on origin stay until the owner says otherwise.

## Gotchas

- **Always fetch renders with a cache-buster.** The bucket serves
  `Cache-Control: public, max-age=604800`. On 2026-11-08 a re-check without
  one still showed an August image after a correct promotion. Every script
  and prompt here adds `?cb=<epoch>`.
- **One bulk-generate run at a time.** GitHub keeps one pending run per
  concurrency group and cancels the older pending one, daily-regen's spec-mode
  run (02:17 UTC) included. Its pair mode dispatches `impl-generate.yml`
  directly and does not collide.
- **Pass the real model as `source_model`.** It becomes the metadata's
  `generated_by` (`claude-opus-5-5`, `gemini-4-argon`); without it the
  metadata says `adopted:<ref>`.
- **Adopt from the full SHA, not the branch name.** A ref that moves between
  the dry run and the bulk run's per-pair fetch adopts other code. The
  dispatcher resolves the SHA itself.
- **Adopt mode renders only Python and JavaScript.** An R or Julia adoption
  fails with an error; use a `regen` line (`regen_gate=false`).
- **A fix cut before a merge on the same pair is stale.** `check_fix.py`
  fails it with "main changed this file since the fix was cut"; cut it again
  from the current `main`.
- **A new validator refusal turns the corpus tests red.** On 2026-11-08
  tree-phylogenetic/muix tripped the SECURITY banned-name rule with a
  computed-key write, and the JavaScript corpus test failed on every later
  Python PR. Since #12647 those tests hold rules, not counts; before you touch
  a test that still pins a catalogue count, turn it into a rule.
- **A review can name a plot-type miss and still merge.** cartogram-area-distortion
  merged at 84 with SC-01 at 3/5. `plot_type_below_max` finds such pairs;
  classify the merge itself as a `rubric` finding.
- **Promotion fails loudly since #12819.** Before it, impl-merge logged "No
  staging files to promote", then "Promoted images to production", and
  passed with stale renders. A `render_stale` pair from before that fix needs
  a re-render, never a hand upload.
- **Votes before the last update were cast on an older version.** The
  selector splits them at the metadata's `updated`; an old-version reason is a
  hint to check whether the defect survived, not a defect.
- **The `node_modules` link is untracked, not ignored.** The `.gitignore`
  pattern `node_modules/` does not match a symbolic link, so `git status`
  shows `?? node_modules` and `git add -A` would commit it.
- **Local Python renders can fail for local reasons.** plotly needs a Chrome
  for kaleido and bokeh a Chrome driver; a failure with an environment error
  in the render log says nothing about the code. The pipeline's render decides.
- **The blank check warns on thin marks.** A tree or a sparse line chart is
  above the rubric's 95 % of one colour and still fine; `check_fix.py` fails
  only above the agents' 99.7 % and warns otherwise.
- **The spec channel has never run end to end.** File one spec issue first and
  follow it to `spec-ready` (`reference/spec-issue.md`).
- **Some findings are the owner's.** A rebuild instead of a port (contour-3d),
  a spec deviation (heatmap-geographic switching to square), or a missing
  encoder (qrcode-basic) goes to him as an option question, never into a fix
  brief.
- **A worktree has no `.env`.** `select_candidates.py --votes` stops with exit
  code 2 until you pass `--env`.
