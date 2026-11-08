---
name: audit-catalogue
description: Audit the live plot catalogue and repair what is not good, in rounds — select candidate pairs with the bundled read-only select_candidates.py (thumbs-down votes from the production feedback table, low or capped review scores and kept defects, stale library versions or GCS renders, agent-validator refusals, or a sweep of a library or spec), audit them visually with the bundled audit_workflow.js (metadata, both renders with a cache-buster, the spec, the merged review; a skeptic per high or medium finding), publish the confirmed defects as a private Artifact page, and only after the owner picks fix Python and JavaScript pairs locally in fresh worktrees, check them with check_fix.py, show them as a fixes gallery, and adopt them through the pipeline one bulk-generate run at a time with dispatch.sh under an OK bound to the queue (R and Julia through a forced regeneration with a change request, stale renders through a re-render, spec causes through a spec issue the owner files), then verify every merged pair end to end with verify_merged.py (code, metadata, database row, renders, API), re-audit a pair whose fix a repair changed, and re-audit the round. Use when asked to audit the catalogue, check the thumbs-down plots, find and fix bad implementations, sweep a library, or "den Katalog durchsehen".
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
everything is read-only. Before the second, only the fix refs may leave the
machine: a `claude/*` push starts no workflow. A round ends only when every
merged pair is verified on the live site: code, image and rating (step 9).

## Rules

- **Read-only until the owner's picks.** Selecting, auditing and building the
  page read the repository, GitHub, the bucket and the database, and write
  only into the round directory. The feedback query runs in a transaction
  PostgreSQL holds read-only and returns counts.
- **Nothing runs without the owner's OK for the queue.** No dispatch, no
  resume, no label, no comment before he approved that round's queue. Pushing
  the round's `claude/*` fix refs is the one early step: a push starts no
  workflow. The OK binds to the dry run's token, which covers `queue.txt` and
  every planned SHA; a changed queue needs a new dry run and a new OK. The same
  OK covers re-dispatching the round's paused reviews and repairs once a usage
  limit resets, with no OK of its own per resume. A generic "ok" authorizes
  nothing (CLAUDE.md external-system rule).
- **The owner files spec issues.** For a spec cause the skill writes the issue
  text (`reference/spec-issue.md`); the owner files it.
- **The pipeline owns the result.** Fixes reach `main` only through adopt mode
  (`bulk-generate.yml -f source_ref=<full SHA>`), a re-render from `main`, or a
  forced regeneration. Never merge an implementation PR, write metadata, upload
  a render or edit a stored score.
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
3. Name the main checkout's `.env` for the votes and the database check:
   `ENV="$(git rev-parse --path-format=absolute --git-common-dir)/../.env"`.
   A worktree has none; the scripts read only `DATABASE_URL` and never
   print it.
4. Read the pipeline's auth mode: `gh variable get CLAUDE_AUTH -R MarkusNeusinger/anyplot`.
   Under `oidc` or `api`, the round's reviews and repairs cost API credits and
   stop at the workspace's spend limit. Under `subscription`, every review and
   repair, this session and its fix delegates share the owner's 5-hour window;
   on 2026-11-08 that window ran out at 02:16 UTC, next to daily-regen's 02:17
   UTC tick, and paused 42 reviews. With `subscription`, keep adopt lines small
   and away from 02:17 UTC.
5. Confirm the round's extent with the owner before you start, as options
   (AskUserQuestion): the sources, the filters (a library, a spec list), the
   cap on audited pairs (about 60 per run), the stop point, and which window
   the round spends (API credits, or his subscription with this session's
   delegates).

## 2 · Select the candidates

```bash
S=.claude/skills/audit-catalogue
uv run --extra agents python $S/select_candidates.py --out "$ROUND/candidates.json" \
  --votes --env "$ENV" --scores --stale --gcs --readiness --min-rank 3 --limit 60
```

Combine the sources per round:

| Flag | Reads | Reason codes |
|---|---|---|
| `--votes` | `feedback` reactions per spec × language × library, one vote per visitor session on each side of the metadata's `updated` (`core.plot_votes`) | `thumbs_down` (more down than up since the metadata's `updated`), `thumbs_down_old_version` (more down than up before it, and no more up than down since: cast on an older version) |
| `--scores` | the stored review in `metadata/*.yaml` | `no_score`, `below_threshold` (`--below`, default 85), `capped` (total below the item sum), `plot_type_below_max` (SC-01), `spec_compliance_below_max`, `technical_below_max`, `residual_defects` (a kept defect line on an item below its maximum) |
| `--stale` | `library_version` against the pins at `--ref` (`core.library_versions`) | `library_behind` (an older API level), `old_update` (with `--older-than DAYS`) |
| `--gcs` | a HEAD on both production PNGs and both `_800.webp` variants the site shows, with `?cb=<epoch>` | `render_missing`, `render_stale` (older than `updated`), `render_unchecked` |
| `--readiness` | the agent validator's scan, as the corpus tests run it | `validator_refusal` (any refusal but a map spec), `validator_error` |
| `--sweep` | every pair of the filtered universe | `sweep` |

- The defaults are a score below 85 and at least one thumbs-down
  (`--min-down 1`). Opus reviews score about 8 below Sonnet's, so a round over
  Opus-reviewed pairs may pass `--below 80`.
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
- A skeptic that returns nothing gets one more try. A finding still without a
  verdict is `unverified`: the page shows it apart from the confirmed ones.
  Before the owner can pick it, run its skeptic once more by hand (the script's
  `verifyPrompt`, through the Agent tool on Opus) and tell him the verdict.
- The workflow cannot write files. Write its returned value to
  `$ROUND/audit-run1.json`; a later run of the same round takes the next
  label.
- Without the Workflow tool, run the same prompts (`auditPrompt` and
  `verifyPrompt` in the script, and `reauditPrompt` for step 9) through the
  Agent tool on Opus: one agent per group, then one skeptic per high or medium
  finding.

Auditors and skeptics make judgment calls, so they run on Opus (the
inherited session model; `agentic/docs/agent-operations.md`).

## 4 · Show the owner the confirmed defects

```bash
uv run python $S/build_page.py --round "$ROUND" --audit "$ROUND/audit-run1.json"
```

The script writes `$ROUND/findings.json` (every finding with an id: confirmed
high and medium first, then the unverified, the low notes, and the refuted
claims) and `$ROUND/page/audit.html`, which embeds the two `_800.webp` renders
of each confirmed and unverified pair.

1. Load the `artifact-design` skill, then publish `$ROUND/page/audit.html` with
   the Artifact tool as a private page (icon `chart`). The renders are public
   catalogue images, and the page holds no visitor data.
2. Give the owner the link and the headline: pairs audited, confirmed high
   and medium, unverified, and the causes.
3. The owner picks by id, or by a rule such as "all high and medium". A low
   note is listed with its id and stays pickable. When he is away, create a
   Todoist task in **Anyplot** with the link.

## 5 · Plan the picked fixes

Write `$ROUND/plan.md`: one line per picked id with its route.

| Cause and language | Route |
|---|---|
| `implementation`, Python or JavaScript | A local fix in a worktree (step 6), adopted from its pushed `claude/*` ref: an `adopt` line |
| `implementation`, R or Julia | A `regen` line: a forced regeneration with a one-sentence change request. Adopt mode cannot render R or Julia |
| `pipeline`, a stale or missing render | A fresh render of the merged code: a `rerender` line for Python and JavaScript (adopt mode from `main`, as `docs/workflows/overview.md`, "Promotion to production", describes), a `regen` line for R and Julia |
| `spec` | The text of a spec issue (`reference/spec-issue.md`), which the owner files; then the affected pairs' fixes once it merges |
| `rubric` | A report line and a comment on Todoist task `6hrcq56Pf3cMJJgf` (the rubric watch); the pair's own defect still takes one of the routes above |

A change request is one sentence about the defect, for one library: "Draw the
decision boundary from a 200-step mesh so it does not show as a staircase."
Show the owner the plan with the open decisions as options (a deviation from
the spec, a held pair, a rebuild instead of a port).

## 6 · Fix locally

1. Make one shared install for the round, JavaScript and Python:

   ```bash
   git worktree add --detach .claude/worktrees/audit-base origin/main
   BASE=$(git -C .claude/worktrees/audit-base rev-parse --show-toplevel)
   (cd "$BASE" && source ~/.nvm/nvm.sh && nvm use 24 && npm ci && npx playwright install chromium)
   uv sync --project "$BASE" --frozen --extra agents
   ```

   The main checkout's `node_modules` can lag the lock (MUI X 7.29.1 against
   9.17.0 on 2026-11-08). `npx playwright install chromium` is a no-op when the
   browser is already in `~/.cache/ms-playwright`. Every `check_fix.py` run
   below goes through `$BASE/.venv` (`UV_PROJECT_ENVIRONMENT`), so a Python
   render adds its library's extra there instead of building a full venv in
   each fix worktree.
2. Cut one fresh worktree per package of about ten files of one library:
   `git worktree add -b claude/audit-<date>-<lib>-<n> .claude/worktrees/audit-<lib>-<n> origin/main`,
   and link the install: `ln -s "$BASE/node_modules" .claude/worktrees/audit-<lib>-<n>/node_modules`.
   A fresh worktree per package keeps a long session from drifting.
3. Brief one Opus delegate per worktree. A package of more than about 20 files
   may go to the Gemini lane instead, as a `/gemini-task` brief with
   `check_fix.py` as its acceptance; its fixes still land on a `claude/*` ref.
   The brief names the confirmed findings with their evidence and fix, and
   states:
   - Edit files only with the Edit and Write tools; run all `git` inside your
     own worktree; leave the shared checkout on its branch.
   - Decide and document routine choices (a colour within the palette, a
     label position); return as a finding anything that changes what the
     plot shows, contradicts the spec, or would be expensive to redo.
   - Read only your pair's code, spec, metadata and renders, never another
     library's code.
   - Fix against the review's own rules: `prompts/library/<lib>.md` and
     `prompts/quality-criteria.md`. A fix that leaves no defect line and all 19
     technical items (VQ, SC, DQ, CQ) at their maximum merges at 80 or more
     without a paid repair round (the nothing-to-repair rule,
     `docs/workflows/overview.md`).
   - One commit per spec; stage the file by path, never `git add -A` (the
     `node_modules` link shows as untracked); never commit a render.
   - Leave the header's `Quality:` and `Updated:` lines as they are:
     impl-review writes them.
   - Render and check each file with `check_fix.py --render`, look at both
     PNGs, and do not push.

   Under `CLAUDE_AUTH=subscription`, a usage limit stops the delegates too.
   One commit per spec is the resume point: `git -C <worktree> log --oneline origin/main..`
   shows what is done; brief a delegate on the rest after the reset.
4. Check every package yourself before anything leaves:

   ```bash
   UV_PROJECT_ENVIRONMENT="$BASE/.venv" uv run --project "$BASE" --frozen --extra agents \
     python $S/check_fix.py --repo .claude/worktrees/audit-<lib>-<n> --ref HEAD \
     --render --out "$ROUND/renders/<lib>-<n>" <spec>/<lib> ...
   ```

   It checks the commit range (implementation files only, no render, no
   metadata, no `node_modules`), that `main` did not change a file since the
   fix was cut (adopt mode takes the whole file, so it would revert that), the
   header block, the agent validator against the base (a new refusal or a new
   `deprecated-api` hint fails), and with `--render` both themes on the canvas
   target and not blank. The render gets a scrubbed environment: no token or
   database URL of your shell reaches the code. Look at the renders yourself.

What renders locally: the JavaScript libraries through `render.mjs`, exactly
as the pipeline runs it (tested on MUI X), and the Python libraries through
the pipeline's own command. matplotlib, seaborn, plotnine, altair and letsplot
need nothing more; pygal needs the system's `libcairo2`. plotly (kaleido) and
bokeh need a Chrome and have never rendered locally through this path, so a
failed render of theirs with an environment error in the log says nothing
about the code: the pipeline's render decides. R and Julia are not rendered
locally: adopt mode cannot take them, so their fix is a `regen` line and the
pipeline renders it. The renderer's toolchain image
(`agents/renderer/toolchain.Dockerfile`) holds R 4.6.1 and Julia 1.13.2 if a
local reproduction is ever needed.

## 7 · Dispatch, after the owner's OK

1. Write `$ROUND/queue.txt`, one package per line:

   ```text
   adopt muix claude/audit-2026-11-08-muix-1 claude-opus-5-5 cartogram-area-distortion burndown-sprint
   rerender matplotlib claude-opus-5-5 heatmap-annotated
   regen ggplot2 indicator-ema Use the 12- and 26-day periods the spec's example names.
   ```

   A `rerender` line takes the merged metadata's `generated_by` as its model,
   so the author survives the re-render. Adopt lines go out at a pace of 120 s
   per spec (`PACE`; adopt mode generates nothing, and ten Opus adopt packages
   ran at 120 s on 2026-11-08); `PACE=` leaves bulk-generate's own 180 s.
2. Push each checked package's ref whenever it is ready:
   `git -C <worktree> push -u origin claude/audit-<date>-<lib>-<n>`. A
   `claude/*` push starts no workflow, so it needs no OK; the repository is
   public, so the ref is visible from then on.
3. Run the dry run: `bash $S/dispatch.sh "$ROUND"`. It resolves each adopt ref
   to its SHA (origin's, or the local branch's before the push), checks every
   line, writes `$ROUND/queue.plan`, and prints an approval token over the
   queue and the planned SHAs. It dispatches nothing.
4. Build the fixes gallery, then load the `artifact-design` skill and publish
   `$ROUND/page/fixes.html` as a second private Artifact (icon `chart`):

   ```bash
   uv run python $S/build_page.py --round "$ROUND" --fixes F01 F03 ...
   ```

   It takes the audit's F ids and the re-audit's R ids (`findings-reaudit.json`,
   step 9). Per picked pair it puts the production `_800.webp` (with `?cb=`) next to the
   local render of `check_fix.py --render`, both themes, with the finding ids
   and fix sentences. R, Julia, and a plotly or bokeh pair whose local render
   failed show the production side and "renders in the pipeline".
5. Show the owner the dry run's output with its token, each package's
   `check_fix.py` lines and the gallery's link. Ask as options
   (AskUserQuestion), and name in the question what the OK covers:
   "dispatching this queue (token `<token>`), and re-dispatching this round's
   paused reviews and repairs after a usage limit resets".
6. After his OK, start the dispatcher in the background (`run_in_background`):
   `bash $S/dispatch.sh "$ROUND" --execute --approved <token>`. A ref that is
   not on origin yet waits. Prefix it with
   `UV_PROJECT_ENVIRONMENT="$BASE/.venv"` when the checkout you run the skill
   from has no `.venv`.

The dispatcher sends one line at a time, and only while no `bulk-generate`
run is queued or in progress; a `rerender` or `regen` line also waits for its
own pair's `impl-generate` run. It adopts each line from the planned SHA and
refuses a line whose ref moved off it, re-runs `check_fix.py` there against
the current `main`, dispatches only the specs that pass, and logs the rest.
Its state (`dispatch.state`) keeps a line from going out twice, also when `gh`
reported a failure for a dispatch GitHub accepted. When `queue.txt` or
`queue.plan` changes, it stops: the changed queue needs a new dry run and a
new OK, and the restart skips what already went out.

## 8 · Watch the pipeline

- Post a status line about every 10 minutes from
  `bash $S/pkg_status.sh "$ROUND"`: per spec the newest PR titled
  `feat(<lib>): implement <spec>` since the dispatch, its state and labels, and
  a summary per package.
- At the subscription's 5-hour limit the pipeline pauses reviews
  (`ai-review-paused`) and repairs (`ai-repair-paused`). After the limit
  resets, and only when the owner's queue OK named the resumes (step 7), resume
  them one every 150 s: `bash $S/resume_paused.sh "$ROUND" --repairs` shows
  what it would run for this round's pairs; add `--execute` to run it, and say
  in the status line that you started them. `--all-open` takes every paused PR
  in the repository and needs the owner to name it.
- A stuck PR, a failed merge or a missing render is `babysit-pipeline`'s
  recovery recipe.

## 9 · Verify, re-audit and close the round

1. When a package's PRs are merged and the `Sync: PostgreSQL` run that
   followed the last merge has completed, verify every pair end to end,
   read-only:

   ```bash
   git fetch origin main
   uv run --extra agents python $S/verify_merged.py --round "$ROUND" --env "$ENV"
   ```

   Per pair it checks that the code on `main` equals the fix below the header,
   that the metadata carries `quality_score`, `updated` and the line's
   `generated_by` and a `library_version` at the pinned API level, that the
   database's `impls` row and the API return the same three values, and that
   both production PNGs and both `_800.webp` variants are fresh (with a
   cache-buster). Then check that the pages render:
   `node scripts/site-smoke.mjs $(cat "$ROUND/verify-pages.txt")` (the
   `playwright-core` recipe is in the script's header). Each pair gets one
   status:

   - `ok`: verified.
   - `pending`: not merged yet (`pkg_status.sh` says where it stands), or a
     sync run created since its update is still queued or in progress. Run the
     verifier again later.
   - `marked`: a repair or a later merge changed lines the fix added, so the
     merged code is not the fix the owner saw. It never passes silently. The
     verifier writes `$ROUND/reaudit-<time>.json`; run `audit_workflow.js` with
     its content as `args`, so a skeptic re-audits the merged production
     renders (with `?cb=`) and the merged review against the pair's finding.
     Write the result to `$ROUND/audit-reaudit-<time>.json` and run
     `build_page.py --round "$ROUND" --audit <that file> --name reaudit --id-prefix R`.
     Then run the verifier again: it reads the saved result. A pair the
     skeptic judged clean passes with a note; any other stays `marked`, comes
     back on `page/reaudit.html` as a finding for the owner to pick, and gets
     no new re-audit file. The verdict holds for the merged state it judged
     (the metadata's `updated` and the code on `main`); a later change to the
     pair needs a new re-audit. Never a hand merge.
   - `closed`: the pair's PR closed without a merge, so the fix did not pass
     the pipeline. Its finding returns to the plan, as a new fix or the
     owner's call; never a hand merge.
   - `failed`: the route says what to do. Read the PR for a code or metadata
     difference, add the suggested `rerender` or `regen` line for stale
     renders (a changed queue, so a new dry run and a new OK), and ask the
     owner before anyone re-runs the database sync.
2. Select the verified pairs again
   (`--spec <spec> ... --library <lib> --scores --gcs --sweep`) and run the
   audit workflow with the next label. A fix counts when its finding is gone;
   a new finding starts the next round.
3. After the merges, run `scripts/site-smoke.mjs` once on its default pages
   (`/open-pr` §4).
4. Write `$ROUND/report.md` in English, Google style: the candidates per
   source, the confirmed findings and their routes, the specs the dispatcher
   skipped or refused with the reason (`grep -E 'refused|skip' "$ROUND/dispatch.log"`),
   so no picked pair vanishes between the dispatch and the report, the PRs
   with their new scores, the verification with the marked and closed pairs,
   the re-audit, and the open owner decisions.
   Say that visitors can still see an old image for up to a week after a
   correct promotion, because edge caches keep a render for its `max-age` of
   604800 s. Create one Todoist task per owner decision.
5. Clean up: stop the dispatcher by its background task, or with
   `pkill -f "dispatch[.]sh"` (a bare `pkill -f dispatch.sh` also matches the
   shell that runs it). Remove the merged fix worktrees and their local
   branches, and `.claude/worktrees/audit-base`, from the main checkout:
   `git -C "$MAIN" worktree remove .claude/worktrees/audit-<lib>-<n>`. Never
   remove a worktree from a shell inside it, which then loses its directory.
   The `claude/*` refs on origin stay until the owner says otherwise.

## Gotchas

- **Always fetch renders with a cache-buster.** The bucket serves
  `Cache-Control: public, max-age=604800`. On 2026-11-08 a re-check without
  one still showed an August image after a correct promotion. Every script
  and prompt here adds `?cb=<epoch>`.
- **One bulk-generate run at a time.** GitHub keeps one pending run per
  concurrency group and cancels the older pending one, daily-regen's spec-mode
  run (02:17 UTC) included. Its pair mode dispatches `impl-generate.yml`
  directly and does not collide. A `rerender` or `regen` line waits behind a
  bulk run too: sent next to one, it would add a second stream of generations
  at the same pace.
- **A bulk run holds about 115 specs.** `bulk-generate.yml` times out after
  360 minutes and paces 180 s per spec; keep an adopt line well below that.
- **Pass the real model as `source_model`.** It becomes the metadata's
  `generated_by` (`claude-opus-5-5`, `gemini-4-argon`); without it the
  metadata says `adopted:<ref>`.
- **Adopt from the full SHA, not the branch name.** A ref that moves between
  the dry run and the bulk run's per-pair fetch adopts other code. The
  dispatcher adopts the SHA the approved dry run planned and refuses a ref
  that moved.
- **A refused line stays refused.** `dispatch.state` keys a line by its text.
  To retry after a fix, push the re-cut fix to a new ref (`…-<n>b`), change
  the line, run the dry run, and ask for a new OK.
- **Adopt mode renders only Python and JavaScript.** An R or Julia adoption
  or re-render fails with an error; use a `regen` line (`regen_gate=false`).
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
  hint to check whether the defect survived, not a defect. A visitor may rate
  each new version once, so the same session can count on both sides.
- **The `node_modules` link is untracked, not ignored.** The `.gitignore`
  pattern `node_modules/` does not match a symbolic link, so `git status`
  shows `?? node_modules` and `git add -A` would commit it.
- **The blank check warns on thin marks.** A tree or a sparse line chart is
  above the rubric's 95 % of one colour and still fine; `check_fix.py` fails
  only above the agents' 99.7 % and warns otherwise.
- **Cloudflare refuses the default Python user agent.** `api.anyplot.ai`
  answers `Python-urllib` with 403; `verify_merged.py` sends its own, and a
  cache-buster past the edge's 300 s.
- **The spec channel has never run end to end.** Its first real case is the
  test: write that one issue's text, the owner files it, and follow it to
  `spec-ready` (`reference/spec-issue.md`) before the next.
- **The verifier's database read has run on SQLite only.** The first round
  that passes `--env` is its first production read of the `impls` table.
- **Some findings are the owner's.** A rebuild instead of a port (contour-3d),
  a spec deviation (heatmap-geographic switching to square), or a missing
  encoder (qrcode-basic) goes to him as an option question, never into a fix
  brief.
- **A worktree has no `.env`.** `select_candidates.py --votes` and
  `verify_merged.py` stop with exit code 2 until you pass `--env` (or
  `--no-db` for the verifier).
