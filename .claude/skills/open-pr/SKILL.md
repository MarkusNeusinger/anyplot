---
name: open-pr
description: Take a finished change from diff to an open, green, review-clean PR — run the matching verify skills and local CI gates first, then commit, push and open the PR via /pull_request, watch the pipeline AND the Copilot review, fix sensible findings, resolve the review threads, and after a merge watch the Cloud Build deploys and check in a browser that the live site still renders (scripts/site-smoke.mjs). Detects local vs. cloud GitHub tooling (gh vs. GitHub MCP). Never merges unless the user explicitly authorizes it in this session. Use when asked to open or create a PR, ship a change, or finish up a change.
---

# Open a PR (ship a change)

From working tree to an open PR that is green and review-clean. The
end state is **an open PR, not a merged one** — the user merges (the
repo is squash-only, branches auto-delete). Merge only on an explicit
request in this session; a general "sounds good" is not merge
authorization (the permission classifier enforces this). Never touch
the automated pipeline's PRs: spec/impl/polish PRs are merged by
`impl-merge.yml` / auto-merge — manually merging them breaks
metadata, quality scores, and GCS promotion (CLAUDE.md, mandatory
workflow).

## 0 · Pick the GitHub interface (local vs. cloud)

This skill runs in two environments and the GitHub tooling differs.
Detect once, up front:

```bash
command -v gh >/dev/null && echo "gh path (local)" || echo "MCP path (cloud/web)"
```

- **`gh` present (local machine):** use the `gh`/`gh api` commands as
  written below.
- **`gh` absent (Claude Code on the web / remote container):** `gh`,
  `hub` and direct GitHub API access do **not** exist there. Use the
  GitHub MCP tools (`mcp__github__*`) instead. They are deferred —
  load each one's schema via `ToolSearch` with its **fully-qualified**
  name (a bare method name silently matches nothing), e.g.
  `select:mcp__github__create_pull_request,mcp__github__pull_request_read,mcp__github__resolve_review_thread`,
  before the first call.

`git` itself (commit / push / fetch) is identical in both — only the
PR/review/CI steps swap. The mapping:

| Step | `gh` (local) | GitHub MCP (cloud/web) |
|---|---|---|
| Create PR | `/pull_request` command (`gh pr create` inside) | follow `/pull_request`'s body format + changelog gate manually, create via `mcp__github__create_pull_request` (ready for review, not draft) |
| List PRs | `gh pr list` | `mcp__github__list_pull_requests` |
| Read PR / reviews | `gh pr view --json …` | `mcp__github__pull_request_read` |
| Watch CI | `gh pr checks` poll (§3a) | `mcp__github__actions_list` / `mcp__github__actions_get` / `mcp__github__get_job_logs` (+ `mcp__github__subscribe_pr_activity` to be woken on results) |
| List review threads | `gh api graphql … reviewThreads` (§3c) | `mcp__github__pull_request_read` (review-threads method) |
| Reply on a thread | `gh pr comment` | `mcp__github__add_reply_to_pull_request_comment` (thread) / `mcp__github__add_issue_comment` (PR-level) |
| Resolve a thread | `gh api graphql … resolveReviewThread` (§3d) | `mcp__github__resolve_review_thread` |
| Request Copilot review | `gh api -X POST … requested_reviewers`; a further round through GraphQL `requestReviews` (§3b) | `mcp__github__request_copilot_review` |
| Merge (only if authorized) | `gh pr merge` | `mcp__github__merge_pull_request` |

In the cloud, prefer `mcp__github__subscribe_pr_activity` over any
polling loop: CI/review events wake the session as
`<github-webhook-activity>` messages — never `sleep`-poll there.
`gcloud` is also absent in the cloud, so the §4 deploy watch is
local-only — in a cloud session, say so and hand the Cloud Build
watch to the user.

## 1 · Pre-PR gates (pick by what the diff touches)

```bash
git diff --name-only origin/main...
```

| Diff touches | Run |
|---|---|
| `app/` | `/verify-frontend` (drive the changed flow; both viewports, both themes) |
| `api/` | `/verify-api` (read sweep + the changed endpoint's payload) |
| `core/`, `tests/` | `/verify-core` (pytest + direct smoke) |
| `alembic/` | `/verify-migrations` (throwaway Postgres; the shared prod DB never sees an untested revision). CI verifies every migration on a throwaway PostgreSQL 18 (`Verify Migrations`, `.github/workflows/ci-migrations.yml`) for every PR touching `alembic/` or `core/database/`. |
| a Dockerfile: `api/`, `app/`, `agents/`, `agents/renderer/` (`Dockerfile`, `toolchain.Dockerfile`) | `docker run --rm -i hadolint/hadolint:v2.15.1 hadolint --failure-threshold warning - < <file>`, CI's hadolint version and threshold (`ci-image.yml`, hadolint-action v3.5.0). It must exit 0 and print no `warning` or `error` line; `info` lines such as DL3059 sit below the threshold. DL4006 showed locally on 2026-10-28 and still failed the renderer image's CI on 2026-10-31 |
| review rubric: `prompts/quality-criteria.md`, `prompts/workflow-prompts/ai-quality-review.md`, `prompts/default-style-guide.md`, review rules in `prompts/library/*.md`, review model routing | dispatch a candidate arm (`gh workflow run review-retest.yml -f rules_ref=<sha> -f label=<name> -f compare_to=<baseline run>`) and paste its snippet in the PR (`docs/workflows/review-retest.md`) |
| `.github/workflows/`, other `prompts/`, `automation/` | no live loop exists — reason through carefully, dry-run what's dry-runnable, and say so in the PR |
| `docs/`, `CLAUDE.md`, instruction files | `/write-docs` (layer choice, `docs/index.md` + cross-file sync duties) |
| new binaries, fonts, embedded assets | `/audit-licenses` (tracked-binary/payload/history sweep) |
| any nontrivial code | `/simplify` (built-in) for a quality pass |

A `/verify-*` gate only counts if the **diff's own flow** was driven —
rendering a proxy or asserting a 200 is not verification.

**Changelog gate:** every non-exempt PR adds `changelog.d/<slug>.md`
before the PR opens and adds nothing to `CHANGELOG.md` — that shared
spot is where sibling PRs conflict (rule + exemptions in CLAUDE.md,
format in `changelog.d/README.md`; the `/pull_request` command enforces
the same gate and appends the PR number after creation). Correcting the
wording of a bullet `[Unreleased]` already carries is allowed — identity
is the bold title, so only a new title is an added bullet — and a
fragment never ships the bare `(#NNNNN)` placeholder. Locally:
`uv run python -m tools.changelog check --base origin/main`.

**Gemini Flash check (owner, 2026-10-28 and 2026-10-29):** before a code PR
opens, run `/zweitmeinung` in its routine mode, Gemini 3.8 Flash alone on the
branch diff (`--diff-base origin/main`), and fix what it finds that is real.
Copilot gets one round per PR, so the point is that this round finds nothing.
Skip it for a diff made only of docs, instruction files (`CLAUDE.md`,
`.github/copilot-instructions.md`, skills, commands), changelog fragments, or
`plots/`, for a diff under about 20 lines, and for Dependabot bumps.

**Tests for new code, before the PR opens.** Every new code path gets its unit
test in the branch before the PR opens: `codecov/patch/backend` and
`codecov/patch/frontend` are checks like any other, and on #12484 and #12487
(2026-10-31) the patch check, not the review, was what kept the PR from being
ready. Judge like a reviewer, not by the percentage: uncovered NEW pure logic
that a unit test reaches cheaply gets a test — extracting a pure core from an
async/DB wrapper is the preferred move. Lines only a live DB/HTTP flow
exercises are the `/verify-api` sweep's job; leave those and say so in the PR
if the patch percentage looks alarming.

Then the local CI equivalents — the same commands the pipeline runs.
**Hard gate: do not open the PR while any of these is red.**

```bash
# backend (CI job "Run Linting" + "Run Tests"); ruff lives in the dev extra,
# which a fresh worktree's .venv lacks
uv run --extra dev ruff check . && uv run --extra dev ruff format --check .
uv run --extra typecheck mypy api core --pretty
uv run pytest tests/unit tests/integration -n auto  # CI: -n 4 --dist worksteal

# frontend, only if app/ changed (CI job "Run Frontend Tests")
cd app && yarn lint && yarn fm:check && yarn type-check && yarn test

# Cloud Build parity, if app/ changed — catches strict-TS errors HMR tolerated
cd app && yarn build
```

The `yarn build` step is not optional for `app/` diffs: a latent
`tsc` error that no PR check catches will fail the NEXT Cloud Build
after merge, deploying nothing while everything looks green (the
#6961/#7052 incident). Same logic backend-side: mypy runs in CI only
when Python files changed — run it locally regardless.

## 2 · Open the PR

Branch first (never commit on `main`), commit with a conventional
message, then use the **`/pull_request` command** — it owns the body
format (Summary / Plan / Test plan), the changelog gate, the push,
and the PR-ref follow-up. English throughout, no
"Generated with..." lines in the body. That repository rule outranks the
harness's attribution reminder for the PR body: the body may end with the
session link the reminder names, but never with its "Generated with…" line.
The commit trailers the reminder asks for (`Co-Authored-By`,
`Claude-Session`) stay.

**A multi-paragraph commit message goes through a file — and that
file belongs to this branch alone.** `git commit -F` keeps the prose
out of shell quoting, but the scratchpad is shared by every agent of
one session, so a generic `commitmsg.txt` gets overwritten by a
parallel agent and a later re-read commits someone else's text
(sibling repo, 2026-09-05: both a message and a body file were
clobbered mid-run). Take a private directory, which needs no
sanitising at all:

```bash
D=$(mktemp -d)                 # or, if you name it: BRANCH=$(git branch --show-current)
MSG="$D/commitmsg.txt"         #     SLUG=${BRANCH//\//-}; MSG="$D/commitmsg-$SLUG.txt"
```

A branch name is not a filename — `release/v1.2.3` turns the slash
into a directory that does not exist — so substitute the separators
if you derive the name, and never write into a `$SCRATCH` you have
not set yourself.

Write the file with the Write tool, then `git commit -F "$MSG"` in
the SAME step that wrote it — never re-read one a turn later to reuse
it, because between the two it may belong to another agent. These are
scratch input to one command, not a record; the record is the commit.

The same holds for a PR body you pass as `--body-file`. The mandated
`/pull_request` command does not take that path — it builds the body
inline with a quoted heredoc (`agentic/commands/pull_request.md`
step 6), which has no collision to avoid — so this applies when you
write a body file yourself.

## 3 · After opening: pipeline + review loop (do not skip)

Repeat until **both** hold: all checks pass AND zero unresolved
review threads.

**a. Watch the pipeline.** #12487 (2026-10-31) registered these 16
checks: `Run Linting`, `Run Tests`, `Run E2E Tests`, `Run Frontend Tests`,
`Changelog (fragment)`, `Verify Migrations`, `Build API image and smoke the
container`, `Build app image and smoke the origin gate`, `Build agents image
and smoke the service`, `Build renderer image and render through the
harness`, `Analyze (python|javascript-typescript|actions)`, `CodeQL`,
`codecov/patch/backend` and `codecov/patch/frontend`. Hadolint is not a
check of its own: each `Build … image` job runs it as a `Hadolint (<file>)`
step, so a lint finding shows as that job failing. The codecov patch checks
report last, after the test jobs upload coverage. Wait for checks to
REGISTER before watching — `gh pr checks --watch` right after creation can
exit on an empty list. Use a background poll so other work continues:

```bash
.claude/skills/open-pr/scripts/watch-checks.sh <num>    # run in the background
```

The bundled watcher re-reads the head on every poll, dedupes the
check runs by name (newest id wins, §3e), prints each check as it
finishes and exits once at least 10 runs exist and none is pending
(pass a smaller minimum as the second argument for a PR whose paths
start fewer checks). Its last line counts the checks that are not
green. It gives up after 90 polls, about 45 minutes, because a PR that
builds the renderer image takes 30 to 40: it then exits 1 with a `TIMEOUT`
line that names the checks still pending. On failure: `gh run view
--log-failed`, fix, push to the same branch, keep watching.

**b. Wait for the Copilot review.** Bot login:
`copilot-pull-request-reviewer[bot]`. It arrives about 5 minutes after
the PR is OPENED (1 to 7 minutes on 29 PRs, 2026-10-28 to 31) — not after
each push; see "One review per PR" below. If `gh pr view <num> --json
reviewRequests,reviews` shows neither a request nor a review after the
checks pass, request it explicitly:

```bash
gh api -X POST repos/{owner}/{repo}/pulls/<num>/requested_reviewers -f "reviewers[]=copilot-pull-request-reviewer[bot]"
```

For a further round, which the next paragraph allows only after a high or
critical fix, that REST call can return success and request nothing once
Copilot has reviewed the PR (#12200, 2026-10-15; it worked again on
2026-10-23). Request the round through GraphQL with Copilot's bot node id,
then wait for it with `watch-copilot.sh <num> 2`:

```bash
gh api graphql -F pr="$(gh pr view <num> --json id --jq .id)" -f query='
  mutation($pr: ID!) {
    requestReviews(input: {pullRequestId: $pr, botIds: ["BOT_kgDOCnlnWA"], union: true}) { pullRequest { number } }
  }'
```

`BOT_kgDOCnlnWA` is the reviewer's node id; if the mutation refuses it, read
the id again from any of its reviews (`reviews { nodes { author { login ...
on Bot { id } } } }` in a `pullRequest` query).

**One review per PR is the normal case now.** The ruleset "Automated
Copilot Code Review" (anyplot 10370785, kurrentschrift 18516317)
carries `review_on_push: false` since 2026-09-03 — the owner asked
for the churn to stop, and the setting, not any skill, was what
re-reviewed. Two consequences for this loop. A FIX push starts no new
Copilot run, so a `copilot-*` check on the new head SHA is
legitimately ABSENT; waiting for one that will never come is the
failure mode to avoid — see §3e for what to require instead. And a
further review is requested only while the previous round found
something high or critical — a real bug, a security or correctness
issue, a wrong mechanism — whose fix you pushed; a round with only
low and medium findings gets its fixes pushed and its threads
resolved, and that is the end (owner, 2026-10-23: each round costs
premium requests, and a docs PR had collected three over wording).
Each request re-reads the whole diff and
surfaces "previously missed" findings in files the push never
touched, which draws another push (kurrentschrift#406 collected ~15
requests in a day over a one-line docstring fix).

Fetch all three comment surfaces — they carry different content:

```bash
gh api repos/{owner}/{repo}/pulls/<num>/reviews    # review summaries (Copilot's overview)
gh api repos/{owner}/{repo}/pulls/<num>/comments   # inline file/line comments
gh api repos/{owner}/{repo}/issues/<num>/comments  # conversation (codecov, bots, humans)
```

**b2. Codecov** (the comment arrives in the conversation after the
coverage upload; the repo uses flags/components). A red
`codecov/patch/*` check means §1's test rule was missed: add the test to
the same branch, judged the way §1 says.

**c. List unresolved threads** (the id is needed for resolving):

```bash
gh api graphql -f query='query($owner:String!,$repo:String!,$pr:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$pr){reviewThreads(first:50){nodes{id isResolved isOutdated path comments(first:3){nodes{author{login} body}}}}}}}' -F owner=MarkusNeusinger -F repo=anyplot -F pr=<num> --jq '.data.repository.pullRequest.reviewThreads.nodes | map(select(.isResolved | not))'
```

**d. Per unresolved thread, judge — then act.** Apply real findings
(bugs, deploy-order risks, security, missed edge cases); skip pure
style noise or anything contradicting an explicit decision in the PR
body — state in chat which were applied vs skipped. Either way,
resolve the thread so the PR ends review-clean:

```bash
gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -F id=<thread-id>
```

**e. Stop condition.** Checks green, zero unresolved threads →
report the PR URL and final state. **Do not merge unless explicitly
authorized.**

**Merging on request: wait for the review, not just for green.**
When the owner does ask for the merge in this session, four
conditions, all read on the CURRENT head SHA — re-read it after every
push, `gh pr view <num> --json headRefOid`:

1. A draft is not reviewable — `gh pr ready <num>` first. Copilot
   does not review a draft, so a draft merged "green" was never
   reviewed, and `gh pr merge` on a draft fails anyway. Check
   `isDraft`.
2. Every non-Copilot check on the head SHA is `completed` and green.
   Dedupe the check runs **by name, newest wins**: a superseded run
   (a label re-trigger, a cancelled first attempt) stays beside the
   current one and reads as a red check that is not there any more.
   Dedupe on `.id`, which grows with creation and is always set — a
   check run carries no `created_at`, and `started_at` stays null
   until the run begins, so a `max_by(.started_at)` would hand the
   row to the OLD completed attempt while the new one is still
   queued, which is the failure this step exists to prevent.
   ```bash
   gh api repos/{owner}/{repo}/commits/$(gh pr view <num> --json headRefOid --jq .headRefOid)/check-runs \
     --jq '[.check_runs[]] | group_by(.name) | map(max_by(.id)) | .[] | "\(.name): \(.status) \(.conclusion // "")"'
   ```
3. **A Copilot review actually exists on the PR** — `gh pr view <num>
   --json reviews`, author `copilot-pull-request-reviewer`. The
   head-SHA check run does not prove one: a run reaches `completed`
   with conclusion `cancelled` and delivers nothing. So read the
   check run only to learn whether a round is still RUNNING
   (`queued`/`in_progress` means wait) and read the review list to
   learn whether one was ever delivered. Since `review_on_push` is
   off (§3b), the normal state after a fix push is no run on the head
   at all with the first round's review standing — that is reviewed,
   not unreviewed. If no review exists and the run was cancelled, one
   re-request is the whole budget; after that report
   green-and-unreviewed and let the owner decide, never loop.
4. Zero unresolved review threads (step c), outdated ones included.

**Merge state is two different fields; read each by its own name.**
`mergeable` (`gh pr view --json mergeable`) is `MERGEABLE`,
`CONFLICTING` or `UNKNOWN` — `UNKNOWN` right after another merge is
GitHub still computing, so keep polling. `mergeStateStatus` is the
richer enum, where the conflicting case is `DIRTY`. A conflict is not
transient and has a symptom worth knowing: GitHub starts no CI at
all, so the PR shows no red check, just none (#11212 and
kurrentschrift#524, 2026-09-04, both read as "checks pending" for a
while). Report it and merge `origin/main` into the branch instead of
waiting it out.

Poll all of this from ONE script rather than by hand, and kill a
stale wait loop with the bracket trick (`pkill -f "x[.]y"`), or
`pkill` matches its own calling shell. The bundled scripts in
`.claude/skills/open-pr/scripts/` cover the loops, run from the
repository root: `watch-checks.sh <num>` (§3a),
`watch-copilot.sh <num> [count]` (§3b–c: waits for `count` Copilot
reviews, 2 only when a high finding was fixed and another round
was requested, then prints the latest
summary, every inline comment and the unresolved thread ids) and
`watch-deploys.sh <merge-sha>` (§4).

## 4 · After merge (when it happens): watch the deploy

Merges to `main` touching `api/**`, `core/**`, or `pyproject.toml`
trigger a backend Cloud Build; `app/**` triggers the frontend build.
When such paths merged, watch until the build succeeds — a red Cloud
Build means production did NOT update even though the PR was green:

```bash
.claude/skills/open-pr/scripts/watch-deploys.sh <merge-sha>   # in the background
gcloud builds log --region=europe-west4 <id>                  # on failure
```

The watcher lists the regional builds whose `SHORT_SHA` (7
characters) matches the merge, prints each as it finishes, and exits
once at least one build appeared and none has been queued or working
for two polls in a row, since a merge starts one to four deploys
depending on its paths. When no build has appeared after 6 polls, about
3 minutes, it exits 0 with `no deploy for <sha>`: a triggered build is
queued within a minute, so the merge's paths triggered none (#12487, a
`.github/workflows/` merge, kept the old watcher waiting until it was
killed). It gives up with exit 1 after 60 polls (30 minutes), and exits
2 at once when `gcloud builds list` fails, so a lapsed login never reads
as "no deploy".

The `--region` flag is load-bearing: the `deploy-app` / `deploy-api`
triggers are **regional** (europe-west4), and the global `gcloud builds
list` answers with a handful of months-old global builds — all
`SUCCESS`, none from today — which reads like "nothing was triggered"
while both deploys are already done (2026-08-28, #10808 follow-through:
a 20-minute poll on the global list never saw the builds). Match the
`SHORT_SHA` column against the merge commit before trusting a row.

**Then check that the site renders — after every merge, whatever it
touched.** A green PR and a green deploy do not prove the bundle boots:
on 2026-10-22 vite 8.1.6 (#12225) passed every check and both, and every
page on anyplot.ai stayed blank for about 45 minutes until #12235. Once
the merge's deploys have finished (the watcher above shows them
`SUCCESS`; right after the merge when it triggered none), run:

```bash
source ~/.nvm/nvm.sh && nvm use 24 >/dev/null   # harness shells may still start on Node 22
SCRATCH=<the session scratchpad>
[ -d "$SCRATCH/node_modules/playwright-core" ] || \
  (cd "$SCRATCH" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i --silent playwright-core@1.64.1)
NODE_PATH="$SCRATCH/node_modules" node scripts/site-smoke.mjs
```

It loads `/`, `/plots` and `/scatter-basic` in headless Chromium,
checks `api.anyplot.ai/health`, and prints one `OK` or `FAIL` line per
check, with the entry bundle (`bundle=index-*.js`) that answered; it
never downloads a browser. A failed route counts too: the app's error
boundary ("Something went wrong") keeps the masthead and footer, so
the script looks for its text, not only for an empty page.

Without `gcloud` (a cloud session) the deploy cannot be watched, and
elapsed time proves nothing: Cloud Build may still be waiting for an
earlier deploy. For a merge that touches `app/`, run the script once
before the merge and wait until `bundle=` changes; until it does, or
when you cannot tell, report the post-merge check as unconfirmed
rather than passed.

- **Exit 1 is an incident.** Tell the owner at once with the failing
  lines and every merge since the last passing run, propose reverting
  the suspect merge (a revert PR is the fastest rollback), and land no
  further merge until the site renders again.
- **Exit 2** means no browser was found, so nothing was checked: say
  so, then load `/` and a spec page with the Playwright MCP and read
  its console errors instead.

**Finally, clean up without asking** (owner, 2026-10-22: a merge should
take its branch with it). GitHub deletes the remote branch on merge
(`delete_branch_on_merge`), but never the local one, and 212 merged
local branches had piled up by then. Work from the shared checkout,
never from inside the worktree you remove, and delete only what
merged: the local tip must be the PR head GitHub merged (not the
squash commit), or a commit pushed after the merge, or never pushed,
goes with it.

```bash
MAIN=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")   # the shared checkout
cd "$MAIN"
MERGED=$(gh pr view <pr> --json state,headRefOid --jq 'select(.state == "MERGED") | .headRefOid')
if [ -n "$MERGED" ] && [ "$MERGED" = "$(git rev-parse <branch>)" ]; then
  git worktree remove "$MAIN/.claude/worktrees/<name>"   # refuses if it has uncommitted changes
  git branch -D <branch>
else
  echo "local tip differs from the merged head: keep both and ask the owner"
fi
# keep the shared checkout current when it sits on main with no tracked changes
if [ "$(git -C "$MAIN" branch --show-current)" = main ] && git -C "$MAIN" diff --quiet HEAD; then
  git -C "$MAIN" pull -q --ff-only
fi
```

The pull matters because every agent of the session reads plans and
docs from the shared checkout: on 2026-10-28 a plan file read from it
did not exist yet, and it ended the session six commits behind
`origin/main`.

This covers merged PRs only. A branch whose PR is still open, a
branch whose tip differs from the merged head, and someone else's
worktree stay; deleting those still needs the owner's OK.

**Once per session, report the worktrees whose branch is gone from
`origin`** — the owner decides what goes; never delete one unasked. By
2026-10-31, 54 of 69 worktrees sat on branches that no longer existed
on `origin`, most of them left by older sessions:

```bash
remote=$(git -C "$MAIN" ls-remote --heads origin | sed 's#.*refs/heads/##')
git -C "$MAIN" worktree list --porcelain |
  awk '/^worktree /{sub(/^worktree /, ""); w=$0} /^branch /{sub(/^branch refs\/heads\//, ""); print $0 "\t" w}' |
  while IFS=$'\t' read -r b w; do grep -qxF "$b" <<<"$remote" || echo "no origin/$b: $w"; done
```

`ls-remote` asks `origin` itself, so a remote-tracking ref that a fetch
without `--prune` left behind does not hide a deleted branch. A branch
that was never pushed shows up too; say which ones in the report.

## Gotchas

- **Never update a PR branch with `GITHUB_TOKEN`** (`update-branch`
  from a workflow, or any push as `github-actions[bot]`) when its CI
  has to run: GitHub holds every run on that head at
  `action_required`, and the PR sits BLOCKED with no checks until
  someone approves them (`gh api -X POST
  repos/{owner}/{repo}/actions/runs/<id>/approve`). The `main` ruleset
  is not strict, so a branch behind `main` merges anyway; this is why
  `auto-update-pr-branches.yml` was retired after it put eight such
  commits on #12229 (2026-10-22).
- **`isOutdated` ≠ `isResolved`.** A fix-push can outdate a Copilot
  thread while it stays unresolved; outdated threads still count
  against review-clean — resolve them explicitly.
- **A fix push no longer starts a review round.** `review_on_push` is
  `false` since 2026-09-03 (§3b), so only an explicit re-request opens
  another one, and that only while the previous round had high or
  critical findings whose fixes you pushed (§3b). A round with only
  low and medium findings ends the loop: push the fixes, resolve the
  threads, never chase nits into another round; surface a stalemate
  to the user instead.
- **Stacked PRs die when their base squash-merges.** Don't stack; if
  work depends on an unmerged PR, wait for its merge (or do the work
  and rebase before opening).
- **The three comment APIs really differ** — Copilot's overview only
  appears in `/reviews`; codecov only in `/issues/<num>/comments`.
  Checking just `gh pr view --comments` misses content.
- **Auto-review may not fire at all** on some PRs — the first review
  usually lands 1 to 7 minutes after the PR opens (§3b), so don't wait
  past about 8 minutes without checking `reviewRequests`; request
  explicitly (§3b). But a missing review is never evidence the bot is
  inactive on this repo — reviews have landed well after that and
  carried real findings. Do not declare the task done while the review is
  outstanding; if the session ends first, say explicitly that the
  review is still pending.
- **Background-poll mechanics:** if you use the Monitor tool, load
  its schema first via ToolSearch (`select:Monitor`) — calling it
  unloaded is a rejected round trip. Whichever mechanism you use,
  kill it once the PR reaches its end state — leftover monitors fire
  confusing notifications into later, unrelated sessions.
- **Local gates first saves whole round trips** — anything red
  locally is guaranteed red in Actions, and CI's change-detection
  (paths filter) can SKIP a gate locally broken code would fail
  later.

## Troubleshooting

- Resolve mutation returns `NOT_FOUND` → the thread id is stale;
  re-run the §3c query and retry with the fresh id.
- `gh pr checks` shows nothing right after creation → checks haven't
  registered; wait a few seconds and retry.
