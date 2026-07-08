---
name: open-pr
description: Take a finished change from diff to an open, green, review-clean PR — run the matching verify skills and local CI gates first, then commit, push and open the PR via /pull_request, watch the pipeline AND the Copilot review, fix sensible findings, resolve the review threads, and watch any Cloud Build deploy after merge. Never merges unless the user explicitly authorizes it in this session. Use when asked to open or create a PR, ship a change, or finish up a change.
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

## 1 · Pre-PR gates (pick by what the diff touches)

```bash
git diff --name-only origin/main...
```

| Diff touches | Run |
|---|---|
| `app/` | `/verify-frontend` (drive the changed flow; both viewports, both themes) |
| `api/` | `/verify-api` (read sweep + the changed endpoint's payload) |
| `core/`, `tests/` | `/verify-core` (pytest + direct smoke) |
| `.github/workflows/`, `prompts/`, `automation/` | no live loop exists — reason through carefully, dry-run what's dry-runnable, and say so in the PR |
| `docs/`, `CLAUDE.md`, instruction files | check the sync duties: CLAUDE.md ↔ `.github/copilot-instructions.md` ↔ `agentic/commands/` where rules are duplicated |
| any nontrivial code | `/simplify` (built-in) for a quality pass |

A `/verify-*` gate only counts if the **diff's own flow** was driven —
rendering a proxy or asserting a 200 is not verification.

**Changelog gate:** every non-exempt PR adds its entries to
`CHANGELOG.md` under `[Unreleased]` before the PR opens (rule + 
exemptions in CLAUDE.md; the `/pull_request` command enforces the
same gate and appends the PR number after creation).

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
`copilot-pull-request-reviewer[bot]`. It usually lands within ~2 min;
if `gh pr view <num> --json reviewRequests,reviews` shows neither a
request nor a review after the checks pass, request it explicitly
(verified working):

```bash
gh api -X POST repos/{owner}/{repo}/pulls/<num>/requested_reviewers -f "reviewers[]=copilot-pull-request-reviewer[bot]"
```

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

## 4 · After merge (when it happens): watch the deploy

Merges to `main` touching `api/**`, `core/**`, or `pyproject.toml`
trigger a backend Cloud Build; `app/**` triggers the frontend build.
When such paths merged, watch until the build succeeds — a red Cloud
Build means production did NOT update even though the PR was green:

```bash
gcloud builds list --limit 3
gcloud builds log <id>   # on failure
```

## Gotchas

- **`isOutdated` ≠ `isResolved`.** A fix-push can outdate a Copilot
  thread while it stays unresolved; outdated threads still count
  against review-clean — resolve them explicitly.
- **Copilot reviews every push round.** New threads on changed lines
  are the loop working, not noise — but don't chase cosmetic nits
  past a couple of rounds; surface stalemates to the user.
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
