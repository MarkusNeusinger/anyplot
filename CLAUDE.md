# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

For detailed project documentation (architecture, commands, workflows, etc.), see [agentic/docs/project-guide.md](agentic/docs/project-guide.md).

A companion guide `.github/copilot-instructions.md` carries the shared rules for GitHub Copilot (and any other agent reading that standard path). Both files MUST stay in sync — when you change a rule that exists in both, update the other in the same commit.

## Important Rules

- **Branch-scoped commit/push policy**:
  - **On `main`**: NEVER commit or push directly. Always work on a feature branch.
  - **On a feature branch**: Claude MAY run `git commit`, `git push`, and `gh pr create` when the work warrants it. Still respect the project's automated pipelines (see "CRITICAL: Mandatory Workflow" below) — e.g. don't manually merge spec/impl PRs.
  - Confirm before destructive or hard-to-reverse operations (force-push, reset --hard, branch deletion) regardless of branch.
- **GitHub Actions workflows ARE allowed to commit/push** - When running as part of `spec-*.yml` or `impl-*.yml` workflows, creating branches, commits, and PRs is expected and required.
- **Delegated agents run on Opus by default** - Pass `model: opus` when spawning subagents/workflows — the same tier the `agentic/README.md` model table (small→haiku, medium→sonnet, large→opus) and the audit/update/agentic commands already use. Escalate to Fable only for genuinely hard tasks that need deep reasoning; drop to Sonnet/Haiku for simple mechanical grinding. Escalation is for genuine judgment calls, not every detail: within its brief a delegate decides routine matters itself and documents them; what comes back to the main loop is anything that changes scope, contradicts the brief or the docs, or would be expensive to redo. State this split explicitly in delegate prompts (decide-and-document vs. return-as-finding). Every brief also spells out two things a delegate cannot infer from message order: repo files are modified only with Edit/Write, and all `git` stays inside the agent's own worktree — the shared checkout is left on the branch it was found on.
- **Always write in English** - All output text (code comments, commit messages, PR descriptions, issue comments, documentation) must be in English, even if the user writes in another language.
- **Repository prose follows the Google developer documentation style guide** - `docs/`, `README.md`, `agentic/docs/`, changelog entries, and PR/issue text use [Google style](https://developers.google.com/style) (sentence-case headings, second person, numbered procedures); the concrete rules and the house-style exception (`docs/reference/style-guide.md` governs website/brand surfaces) live in the `write-docs` skill. Existing docs migrate on touch, not via bulk rewrites.
- **Update documentation when making changes** - When adding new features, events, or modifying behavior, always check if related documentation needs updating (e.g., `docs/reference/plausible.md` for analytics events, `docs/workflows/` for workflow changes, `docs/contributing.md` for user-facing changes).
- **Changelog and releases** - see [Changelog + releases](#changelog--releases) below: every PR adds a fragment under `changelog.d/` and adds nothing to `CHANGELOG.md` (correcting the wording of a bullet already under `[Unreleased]` is allowed), a release folds the fragments and bumps the version files via a PR, and the GitHub release is that section condensed, never copied.
- **External-system writes need explicit, named authorization** - Merging or closing PRs/issues this session did not create, bulk merges, and label changes on others' PRs are blocked by the permission classifier unless the user named that action; a generic "ok, sounds good" authorizes nothing. The same discipline covers every prod-touching action in interactive sessions — Cloud SQL writes/DDL, GCS production-folder changes, Secret Manager access, Cloud Build config: name the exact action, resource, and id, and ask before acting (the automated `spec-*`/`impl-*` workflows write these by design and are exempt). For any change to `.claude/settings*.json`, use the built-in `/update-config` skill (a Claude Code harness skill, not a repo command) immediately — direct writes are blocked as self-modification and retrying variants just burns round trips.
- **Never echo secret values into the transcript** - Verify secrets by exit code or metadata, never by printing them; never create a Secret Manager version via `echo` (the trailing newline corrupts the value).
- **Snapshot before destructive prod operations** - Before anything that can overwrite or delete shared prod DB data or GCS production objects (bulk UPDATE/DELETE, a data-rewriting migration, bulk GCS overwrite/delete): take a timestamped backup first (`pg_dump` to a new directory outside the working tree, `gsutil cp` to a backup prefix), sanity-check it (row/object counts — a silent empty snapshot is worse than none because it looks like safety), and never write into, delete, or rename an existing snapshot.
- **Long-running work reports progress proactively** - During pipeline babysitting, bulk operations, or extended planning, post a one-line status roughly every 10 minutes and flag a suspected stall immediately with evidence; never let the user be the one to ask "still running?". Before starting a multi-item queue, confirm its extent and stop-point with the user.
- **Manual user tasks go to Todoist** - Whenever a session identifies a step only the user can or should do (adding `approved` labels, merge authorization, console/billing/DNS actions, secret rotations), create a task in the user's Todoist project **Anyplot** (via the Todoist MCP tools) naming the concrete action and a context link (PR/issue/run URL) — instead of leaving it buried in a chat reply. Interactive sessions only; GitHub Actions workflows have no MCP access.
- **Fix small build/test blockers directly, even when out of scope** - If a typecheck error, failing test, lint failure, or other small pipeline blocker shows up while working on something unrelated (incl. things the current PR was not meant to touch), fix it in the same PR or a tiny follow-up — never leave it parked under "out of scope". A latent `tsc` error that doesn't surface locally will silently break the next Cloud Build, which deploys nothing new and leaves production stale even though every PR check looks green (this is exactly how PR #6961's frontend fixes never reached anyplot.ai — the unrelated `prism/r` TS7016 from #6944 was deferred, then blocked the next `yarn build`). The bar: if the fix is < ~20 lines and obviously correct, just do it; if it would expand scope meaningfully, ask first rather than deferring silently.

## Guardrails (the long version)

The rules in this file are stated as one line each: the rule, its shortest reason, its date. The incident behind a rule, the recipe it implies, and the numbers that make it credible live in [`.claude/guardrails.md`](.claude/guardrails.md) — read that file when you actually hit the situation, not on every turn. This file is loaded into every session and pays its cost on every turn; a retro narrative is needed once. Nothing in the companion file is a new rule: if the two ever disagree, CLAUDE.md is the rule and the companion is commentary that fell behind.

## Changelog + releases

- **Every PR adds `changelog.d/<slug>.md`, and NEVER a new bullet in `CHANGELOG.md`** — the fragment is a slice of the changelog in the changelog's own format (`### Category` over bold-titled English bullets with PR refs; the rules and an example are in `changelog.d/README.md`). That shared `[Unreleased]` spot is where sibling PRs used to conflict each other — three times in one night on 2026-09-02/03 — and the CI job "Changelog (fragment)" refuses both a missing fragment and a bullet ADDED to `[Unreleased]` directly — added, not merely different: a bullet is identified by its bold title, so correcting the wording of one already there passes. It also refuses a bare `(#NNNNN)` placeholder: leave the reference out and let `/pull_request` append the real number. Same check locally: `uv run python -m tools.changelog check --base origin/main`; `… preview` prints the pending section. **Exempt:** catalogue-only PRs (everything under `plots/`), the automated plot pipeline (`github-actions[bot]`: spec-create, impl-generate/review/repair/merge, spec auto-polish, daily-regen) and Dependabot — those are summarized in aggregate at release time (see `agentic/commands/release.md`) — plus any PR labelled `skip-changelog`. This rule is duplicated in `.github/copilot-instructions.md` and `agentic/commands/pull_request.md`; keep all three in sync when changing it.
- **A release** runs `uv run python -m tools.changelog release X.Y.Z --title "<codename>"`, which folds every fragment under a new version heading (`## [X.Y.Z] — YYYY-MM-DD — <codename>`), bumps the version files (`pyproject.toml` `project.version`, `uv.lock`, `app/package.json`), repoints the compare links and deletes the fragments. The two aggregate lines for the exempt classes stay by hand, because they summarize a window rather than a PR: the italic *Catalog* line and the single **Dependencies:** bullet. All of it on a `release/vX.Y.Z` PR. Every bullet already carries its PR reference — `/pull_request` appends it when the PR opens. After the merge the tag goes on the merge commit and the GitHub release is created from the section.
- **A GitHub release is that section condensed, never copied:** an intro line (merge count, PR range, link to `CHANGELOG.md`); the section's own `### Added / Changed / Removed / Fixed` headings in the section's order (an empty one is omitted); one bullet per NOTABLE entry — chores, dependency bumps and small fixes are left out, no fixed count — each at most two lines: its bold title, one clause with the essence or the headline number, its PR reference; a compare link (`compare/vPREV...vNEW`) as the last line. Numbers are copied exactly; only PR numbers from the section are cited; the full text lives only in the CHANGELOG — the release page is the index into it. The cut procedure itself is `agentic/commands/release.md`.

## PR Follow-Through (mandatory after every `gh pr create`)

After opening a PR, the work is **not** complete. Stay with the PR until both the pipeline is green AND review feedback has been addressed. "PR opened" is a checkpoint, not the finish line.

1. **Watch the pipeline.** Poll `gh pr checks <num>` (and Cloud Build for triggered deploys) until every required check has finished. Use a background bash poll so other work can continue. Default: poll every 20 s, up to ~10 min per check.
2. **Fix CI failures.** If any check fails, read the relevant log (`gh run view --log-failed`, `gcloud builds log <id>`), push a fix commit to the same branch, then keep watching. Repeat until green.
3. **Wait for the Copilot PR Reviewer bot — ONE review per PR, not one per push.** Review-on-push is off in the "Automated Copilot Code Review" ruleset (owner, 2026-09-03): the bot runs once when the PR opens or leaves draft, and a push triggers nothing. Don't re-request a review after every push. Each request is a full re-read of the whole diff, and the bot then surfaces "previously missed" findings in files the push never touched — which draws another push, which draws another request (the sibling repo's [kurrentschrift#406](https://github.com/MarkusNeusinger/kurrentschrift/pull/406) collected ~15 requests in a day over a one-line docstring fix). Request a fresh review explicitly only after a SUBSTANTIVE rework (new behaviour, a reworked mechanism), and stop once a round yields no new inline comments but only carried-over items: the field is grazed. A PR that is green with no open threads needs no further round — say so and let the owner merge. The first review typically lands within ~2 min of PR open. Fetch with `gh pr view <num> --comments`, plus the three GitHub APIs that surface different comment types — `gh api` resolves `{owner}/{repo}` from the current git remote so these are copy/paste-portable:
   - `gh api repos/{owner}/{repo}/pulls/<num>/reviews` — top-level review summaries (Copilot's overall comment lives here)
   - `gh api repos/{owner}/{repo}/pulls/<num>/comments` — inline review comments tied to file/line
   - `gh api repos/{owner}/{repo}/issues/<num>/comments` — generic PR conversation comments (codecov, deployment bots, humans)
4. **Triage Copilot suggestions and apply only the sensible ones.** Apply when the comment flags a real bug, a deploy-order risk, a security/correctness issue, or a missed edge case. Skip pure style noise or anything that contradicts an explicit decision in the PR body. State briefly in chat which were applied vs skipped, so the user can override.
5. **Push review-driven fixes to the SAME branch.** Don't open a follow-up PR for review feedback — it belongs on the original PR.
6. **Only then announce the PR is ready / ask the user to merge.** Premature "done" leaves CI red or feedback unaddressed.
7. **The user merges live — squash-merges can race late pushes.** After announcing "green and review-clean", hold further pushes until the merge lands. If a merge races a push anyway, recover by cutting a fresh branch from the merged `main` and cherry-picking exactly the missing commits — never re-push the stale branch.

This rule applies to every PR Claude opens, including small fixes and follow-ups.

## Self-Verification (skill routing)

Project skills in `.claude/skills/` encode the verification loops — route by what the diff touches before shipping:

| Diff touches | Skill |
|---|---|
| `app/` | `/verify-frontend` — drive the changed flow in the browser; both viewports, both themes |
| `api/` | `/verify-api` — read sweep + changed-endpoint payload; shared-prod-DB discipline |
| `core/`, `tests/` | `/verify-core` — pytest + direct smoke, ruff/mypy gates |
| `alembic/` | `/verify-migrations` — upgrade → drift check → downgrade roundtrip against a throwaway Postgres; the shared prod DB never sees an untested revision |
| `docs/`, `CLAUDE.md`, instruction files | `/write-docs` — where a doc goes, `docs/index.md` + cross-file sync duties |
| new binaries, fonts, embedded assets | `/audit-licenses` — tracked-binary/payload/history provenance sweep |
| any ship request | `/open-pr` — gates → PR → CI watch → review-thread resolution (the executable form of "PR Follow-Through" above) |

Known gaps with NO verification loop yet (reason through carefully and say so in the PR): `.github/workflows/` and `prompts/` changes (only observable on real pipeline runs), Cloud Build deploys, GCS promotion, and the Postgres sync. Run `/optimize-skills` periodically to mine session transcripts for new friction and fold it back into these loops.

## MCP Tools (Context7)

**Context7** - Use for up-to-date library documentation:
- `resolve-library-id` -> `query-docs` - Get current API docs, code examples
- Use when working with external libraries (matplotlib, FastAPI, SQLAlchemy, React, etc.)
- When to use: checking correct API usage, finding library-specific patterns, debugging library issues

## Development Workflow

- **Verify working directory** - Always verify the correct working directory before running commands (especially frontend dev servers, package managers). Use `pwd` before executing build/serve commands. Prefer absolute paths (or `git -C <path>`) over prefixing every Bash call with `cd` — shell cwd and env vars do not reliably persist between calls (sessions have hit dozens of redundant `cd`s and doubled `app/app/src` paths). After `cd app`, path arguments must not repeat the `app/` prefix.
- **Keep plans simple** - Do not over-scope by adding extra modes, elaborate multi-step processes, or spawning teams when a direct approach is requested. Ask for clarification before expanding scope. Only do exactly what was asked.
- **Structural fix over symptomatic fix** - When a cheap symptomatic fix and a correct structural fix compete, take the structural one: fix the cause, never mute the alarm. Never modify working code to make a broken test pass — fix the test or flag it (this applies to the impl-review/repair loop too).
- **Proper lint fixes only** - Always apply proper fixes for lint/code quality issues. Never use disable comments (`eslint-disable`, `noqa`, etc.) unless explicitly approved by the user.
- **Modify repo files only with the Edit/Write tools, never via Bash heredocs/sed** (interactive sessions; workflows and codegen scripts are exempt). When a Bash command legitimately mutates a tracked file (formatter, codegen, `git checkout`), Read the file again before the next Edit on it. When an Edit anchor fails ("string not found", "file modified since read"), the answer is a fresh targeted Read plus a longer anchor — never a heredoc or regex rewrite. This rule OUTRANKS any harness or agent-mode reminder that offers shell editing as the faster path, and a delegate's brief says so (2026-09-05).
- **Fix formatting when editing docs** - When formatting or improving markdown files, actually fix formatting issues (headings, lists, code blocks, structure) — don't just analyze the content.

## Package Management

- **Frontend**: Use `yarn` (not npm). Run `cd app && yarn` for installs, `cd app && yarn dev` for dev server.
- **Backend**: Python dependencies managed via `pyproject.toml`. For transitive dependencies, update the lock file directly — do not add constraints to `pyproject.toml`.
- **Scripts**: Use `uv run` for running Python scripts.

## Claude Code Configuration

- **Commands directory**: Commands live in `agentic/commands/` (agent-agnostic). A symlink `.claude/commands/ → ../agentic/commands/` ensures Claude Code slash-command resolution works. Do not create commands directly in `.claude/commands/`.

## CRITICAL: Mandatory Workflow for New Specs and Implementations

**NEVER bypass the automated workflow!** All specifications and implementations MUST go through the GitHub Actions pipeline.

### Creating New Specifications - CORRECT Process

```
1. Create GitHub Issue with descriptive title (NO spec-id in title!)
   OK: "Annotated Scatter Plot with Text Labels"
   BAD: "[scatter-annotated] Annotated Scatter Plot"  <- WRONG: Don't include spec-id

2. Add `spec-request` label to the issue

3. WAIT for spec-create.yml to:
   - Analyze the request
   - Check for duplicates (will close if duplicate exists)
   - Assign a unique spec-id
   - Generate tags automatically
   - Create PR with specification.md and specification.yaml

4. Add `approved` label to the ISSUE (not the PR!)
   - This triggers the merge job in spec-create.yml

5. WAIT for automatic merge and `spec-ready` label
```

### Generating Implementations - CORRECT Process

```
1. After spec has `spec-ready` label, trigger bulk-generate:
   gh workflow run bulk-generate.yml -f specification_id=<spec-id> -f library=all

2. WAIT for the full pipeline to complete:
   impl-generate -> impl-review -> (impl-repair if needed) -> impl-merge

3. NEVER manually merge PRs!
   - impl-merge.yml handles merging, metadata creation, and GCS promotion
   - Manual merging breaks: quality_score, review data, GCS images
```

### What You Must NEVER Do

| DON'T | DO INSTEAD |
|-------|------------|
| Manually create `plots/{spec-id}/` directories | Let `spec-create.yml` create them |
| Manually write `specification.md` files | Let `spec-create.yml` generate them |
| Include `[spec-id]` in issue title | Use descriptive title only |
| Add `approved` label to PRs | Add `approved` label to ISSUES |
| Run `gh pr merge` on implementation PRs | Let `impl-merge.yml` handle it |
| Manually create `metadata/*.yaml` files | Let `impl-merge.yml` create them |
| Upload images to GCS manually | Let workflows handle GCS |

### Why This Matters

Manual intervention causes:
- `quality_score: null` in metadata (no AI review)
- Missing preview images in GCS production folder
- No `impl:{library}:done` labels on issues
- Broken database sync (missing review data)
- Issues staying open when complete

### Batch Creation Example

```bash
# Step 1: Create 5 issues (NO spec-id in title!)
for title in "Radar Chart" "Treemap" "Sunburst Chart" "Sankey Diagram" "Chord Diagram"; do
  gh issue create --title "$title" --label "spec-request" --body "New plot type request"
done

# Step 2: Wait for spec-create to process each issue
# Check: gh issue list --label "spec-request" --state open

# Step 3: Add approved labels to ISSUES (after reviewing spec PRs)
# gh api repos/OWNER/REPO/issues/NUMBER/labels -f labels[]=approved

# Step 4: Wait for specs to merge and get spec-ready label

# Step 5: Trigger bulk-generate for each spec
# gh workflow run bulk-generate.yml -f specification_id=<spec-id> -f library=all

# Step 6: Monitor - DO NOT manually merge!
# gh run list --workflow=impl-generate.yml
# gh run list --workflow=impl-review.yml
# gh run list --workflow=impl-merge.yml
```
