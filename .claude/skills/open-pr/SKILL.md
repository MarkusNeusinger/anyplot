---
name: open-pr
description: Take a finished change from diff to an open, green, review-clean PR — run the matching verify skills and local CI gates first, then commit, push and open the PR via /pull_request, watch the pipeline AND the Copilot review, fix sensible findings, resolve the review threads, and watch any Cloud Build deploy after merge. Detects local vs. cloud GitHub tooling (gh vs. GitHub MCP). Never merges unless the user explicitly authorizes it in this session. Use when asked to open or create a PR, ship a change, or finish up a change.
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
| Request Copilot review | `gh api -X POST … requested_reviewers` (§3b) | `mcp__github__request_copilot_review` |
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
| `alembic/` | `/verify-migrations` (throwaway Postgres; the shared prod DB never sees an untested revision) |
| `.github/workflows/`, `prompts/`, `automation/` | no live loop exists — reason through carefully, dry-run what's dry-runnable, and say so in the PR |
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

Then the local CI equivalents — the same commands the pipeline runs.
**Hard gate: do not open the PR while any of these is red.**

```bash
# backend (CI job "Run Linting" + "Run Tests")
uv run ruff check . && uv run ruff format --check .
uv run --extra typecheck mypy api core --pretty
uv run pytest tests/unit tests/integration

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
"Generated with..." lines in the body.

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

**a. Watch the pipeline.** Check names: `Run Linting`, `Run Tests`,
`Run Frontend Tests`, `Analyze (python|javascript-typescript|actions)`,
`CodeQL`. Wait for checks to REGISTER before watching — `gh pr checks
--watch` right after creation can exit on an empty list. Use a
background poll so other work continues:

```bash
gh pr checks <num>   # poll every ~20 s, up to ~10 min per check
```

On failure: `gh run view --log-failed`, fix, push to the same branch,
keep watching.

**b. Wait for the Copilot review.** Bot login:
`copilot-pull-request-reviewer[bot]`. It arrives a few minutes after
the PR is OPENED — not after each push; see "One review per PR"
below. If `gh pr view <num> --json reviewRequests,reviews` shows
neither a request nor a review after the checks pass, request it
explicitly (verified working):

```bash
gh api -X POST repos/{owner}/{repo}/pulls/<num>/requested_reviewers -f "reviewers[]=copilot-pull-request-reviewer[bot]"
```

**One review per PR is the normal case now.** The ruleset "Automated
Copilot Code Review" (anyplot 10370785, kurrentschrift 18516317)
carries `review_on_push: false` since 2026-09-03 — the owner asked
for the churn to stop, and the setting, not any skill, was what
re-reviewed. Two consequences for this loop. A FIX push starts no new
Copilot run, so a `copilot-*` check on the new head SHA is
legitimately ABSENT; waiting for one that will never come is the
failure mode to avoid — see §3e for what to require instead. And a
fresh review is requested only after a SUBSTANTIVE rework (new
behaviour, a reworked mechanism), never after every push: each
request re-reads the whole diff and surfaces "previously missed"
findings in files the push never touched, which draws another push
(kurrentschrift#406 collected ~15 requests in a day over a one-line
docstring fix). Stop once a round yields no new inline comments but
only carried-over items.

Fetch all three comment surfaces — they carry different content:

```bash
gh api repos/{owner}/{repo}/pulls/<num>/reviews    # review summaries (Copilot's overview)
gh api repos/{owner}/{repo}/pulls/<num>/comments   # inline file/line comments
gh api repos/{owner}/{repo}/issues/<num>/comments  # conversation (codecov, bots, humans)
```

**b2. Codecov triage** (comment arrives after coverage upload; the
repo uses flags/components). Judge like a reviewer, not a hard gate:
uncovered NEW pure logic that a unit test reaches cheaply gets a test
in the same PR — extracting a pure core from an async/DB wrapper is
the preferred move. Lines only a live DB/HTTP flow exercises are the
`/verify-api` sweep's job; leave those and say so in the PR if the
patch percentage looks alarming.

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
`pkill` matches its own calling shell.

## 4 · After merge (when it happens): watch the deploy

Merges to `main` touching `api/**`, `core/**`, or `pyproject.toml`
trigger a backend Cloud Build; `app/**` triggers the frontend build.
When such paths merged, watch until the build succeeds — a red Cloud
Build means production did NOT update even though the PR was green:

```bash
gcloud builds list --region=europe-west4 --limit 3 \
  --format='table(id,status,createTime,substitutions.TRIGGER_NAME,substitutions.SHORT_SHA)'
gcloud builds log --region=europe-west4 <id>   # on failure
```

The `--region` flag is load-bearing: the `deploy-app` / `deploy-api`
triggers are **regional** (europe-west4), and the global `gcloud builds
list` answers with a handful of months-old global builds — all
`SUCCESS`, none from today — which reads like "nothing was triggered"
while both deploys are already done (2026-08-28, #10808 follow-through:
a 20-minute poll on the global list never saw the builds). Match the
`SHORT_SHA` column against the merge commit before trusting a row.

## Gotchas

- **`isOutdated` ≠ `isResolved`.** A fix-push can outdate a Copilot
  thread while it stays unresolved; outdated threads still count
  against review-clean — resolve them explicitly.
- **A fix push no longer starts a review round.** `review_on_push` is
  `false` since 2026-09-03 (§3b), so only an explicit — and
  substantive — re-request opens another one. When a round does run,
  new threads on the changed lines are the loop working, not noise —
  but don't chase cosmetic nits past a couple of rounds; surface
  stalemates to the user.
- **Stacked PRs die when their base squash-merges.** Don't stack; if
  work depends on an unmerged PR, wait for its merge (or do the work
  and rebase before opening).
- **The three comment APIs really differ** — Copilot's overview only
  appears in `/reviews`; codecov only in `/issues/<num>/comments`.
  Checking just `gh pr view --comments` misses content.
- **Auto-review may not fire at all** on some PRs — don't wait past
  ~5 min without checking `reviewRequests`; request explicitly (§3b).
  But a missing review is never evidence the bot is inactive on this
  repo — reviews have landed well after 5 min and carried real
  findings. Do not declare the task done while the review is
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
