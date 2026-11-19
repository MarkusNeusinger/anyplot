# Dependabot Batch Processing

Safely process the open Dependabot PRs: verify, enable auto-merge per PR, and handle the
known GitHub quirks. Every gotcha below cost real session round-trips.

## Instructions

- **Never bulk-merge unverified.** Merging a batch of Dependabot PRs in one sweep without
  per-PR check verification is blocked by the permission classifier and cost ~7 recovery
  cycles once. Process per PR: verify checks, then merge or enable auto-merge.
- Auto-merge is the mechanism of choice while checks are pending: `gh pr merge <num> --auto
  --squash` merges the PR once they pass, with no polling. GitHub refuses `--auto` on a PR that
  is already `CLEAN` ("Pull request is in clean status"); merge that one directly with `gh pr
  merge <num> --squash` after you confirm that no check is failing or pending. On 2026-11-18,
  nine of ten PRs in a batch were in that state.
- Grouped bumps (npm-minor, python-minor, js-render-minor, js-render-browser, actions) are one PR each — treat like any other.
  `js-render-browser` (Playwright, esbuild) changes the Chromium every JavaScript render runs in, so
  after it merges, look at the next JavaScript renders for shifted text or layout.
- **A plotting-library major is not a routine bump.** Minor and patch bumps need no edit: the
  pipeline installs from the locks and the database sync reads the versions from them. A major
  arrives ungrouped and fails "Run Tests" while `prompts/library/<lib>.md` still names the old
  `**API level:**`. Check the prompt against the new API (Context7), update it on the Dependabot
  branch, then enable auto-merge. Dependabot stops rebasing a branch with a foreign commit, so
  merge it before the next bump touches the
  same lock.
- **One lock-file PR at a time, and every `app/` bump checked in the browser.** Of the PRs that
  touch the same lock file (`uv.lock`, `app/yarn.lock`), only one has auto-merge at a time: several
  squash-merged within a minute have duplicated package blocks in `uv.lock`. After an `app/` PR
  merges, wait for its `deploy-app` build and run the site smoke (`/open-pr` skill §4,
  `scripts/site-smoke.mjs`) before the next `app/` PR gets auto-merge. On 2026-10-22 vite 8.1.6
  (#12225), merged inside a batch, passed every check and left every page blank for about 45
  minutes. Comment `@dependabot rebase` on the next PR of a chain before you enable its
  auto-merge, and expect Dependabot to close and regroup a PR now and then ("updatable in another
  way"); list the PRs again when it does.
- **When Dependabot doesn't answer the rebase, check the merge yourself.** On 2026-11-18, #13099
  and #13132 got no reaction to `@dependabot rebase` in over 30 minutes. After about 15 minutes,
  stop waiting: in a scratch worktree on a freshly fetched `origin/main`, run `git fetch origin
  pull/<num>/head` and `git merge FETCH_HEAD`, which gives the tree GitHub's squash produces. For
  `uv.lock`, run `uv lock --check` and the tests of what uses the package. For `app/`, run CI's
  frontend gate in `app/`: `yarn install --frozen-lockfile` (the repository uses yarn classic
  1.22, which ignores `--immutable`; confirm that `git status` shows no lock change), `yarn lint`,
  `yarn fm:check`, `yarn type-check`, `yarn test`, and `yarn build`. A clean result lets you
  merge the PR without the rebase.
- **`CI: Image` is not a required check.** A PR that is red only in "Build renderer image and
  render through the harness" shows `UNSTABLE`, not `BLOCKED`, so auto-merge would merge it. Fix
  it first, and merge by hand once that check is green on the new head. A `js-render-minor` bump
  that moves MUI X fails there until the agents package's copy of the import allowlist is
  regenerated: run `npm ci` at the repository root, then `python3
  agents/renderer/toolchain/import_allowlist.py node_modules >
  agents/anyplot/code/profiles/javascript/import-allowlist.json`, and commit the file on the
  Dependabot branch (#13134).
- **A `claude-code-action` bump also moves `ACTION_SHA`.** `review-retest.yml` repeats the
  action's SHA in its workflow-level `env.ACTION_SHA`, which Dependabot doesn't update, so "Run
  Tests" fails at `test_same_action_pin_as_impl_review`. Set it to the new SHA on the Dependabot
  branch (#13136). Say in the report that retest cells recorded under the old SHA no longer
  resume, and that the next pipeline run is the first real use of the new action, since
  workflows that run Claude have no pre-merge smoke.
- **Exact pins in `python-minor` are the owner's call.** `google-adk`, `tree-sitter`, and
  `tree-sitter-language-pack` are pinned exactly in the `agents` extra, and their pin tests
  (`tests/unit/agents/test_adk_pin.py`, `tests/unit/agents/code/test_treesitter.py`) fail by
  design when the group moves them. Don't move the test constants to get a green run: the
  2.12-to-2.13 bump (#12426) needed production fixes in `VertexClaude`. Ask the owner whether to
  hold the PR for a deliberate upgrade (a Todoist task) or to upgrade now. An upgrade (#13137,
  2.13 to 2.14.1) checks the source, because the release notes don't name what breaks here:
  1. Read the breaking and behavior changes of every release in the range against the agents
     code (`git grep` the APIs they name).
  2. Diff the files `agents/anyplot/models.py` builds on between the two tags (`gh api
     repos/google/adk-python/contents/<path>?ref=<tag>`): `src/google/adk/models/anthropic_llm.py`
     (`_build_anthropic_kwargs`, `generate_content_async`, `_apply_cache_breakpoints`,
     `_OutputSchemaTool`, the usage fields the ledger reads) and
     `src/google/adk/flows/llm_flows/basic.py`, which decides when a request carries
     `response_schema`. In 2.14 that also depends on transfer targets: the adapter and the
     reviewer keep the schema only as `single_turn` agents without a parent.
  3. Check the invariant in `agents/main.py` that `InMemorySessionService.get_session` and
     `append_event` contain no yielding `await`, and name the version in that comment.
  4. Run `test_create_plot_streams_to_an_ok_plot_result` (it drives the real ADK flow with a
     fake Anthropic client) and the full suite. A pack bump needs its grammars first: `uv run
     python -m tools.tree_sitter_grammars`, since the cache directory is per pack version.
  5. Move `ADK_VERSION`, `TREE_SITTER_VERSION`, and the version in
     `docs/concepts/agent-network.md`, put the findings at the top of the PR body, and offer the
     owner a real-model check (`agents.evals.prep` and `agents.evals.scope`, about $0.30), since
     the suites use fakes and the site smoke never touches the chat.
- **Other majors:** read the breaking changes in the PR body against how the repository uses the
  package (`git grep` the import), then run what uses it on the merged tree: the matching tests,
  or a short `yarn dev` for a dev-only Vite plugin (vite-plugin-checker 1.0, #13135, changed its
  overlay).
- Per the changelog contract, individual Dependabot bumps get NO `CHANGELOG.md` entries —
  they are aggregated into one **Dependencies:** bullet at release time (`/release` step 3).

## Run

1. `git fetch origin main` and list: `gh pr list --author "app/dependabot" --json number,title,mergeStateStatus,statusCheckRollup`
2. Per PR, in order:
   - Checks green → `gh pr merge <num> --squash` (`--auto` is refused on a `CLEAN` PR).
   - Checks pending on an up-to-date branch → `gh pr merge <num> --auto --squash`; it fires when
     green. Not on an `UNSTABLE` PR (see `CI: Image` above).
   - **BEHIND branch**: leave it alone. BEHIND does not block the merge — the `main` ruleset is
     not strict (`strict_required_status_checks_policy: false`), so auto-merge fires on a behind
     branch. **Never** run `gh api -X PUT .../pulls/<num>/update-branch` on a Dependabot PR: the
     resulting merge commit is authored by `github-actions[bot]`, GitHub then gates that head's
     workflow runs behind manual approval (`action_required`, so the checks never report), and
     Dependabot permanently stops rebasing a branch once a foreign commit lands on it. PR #9674
     burned 174 runs in 22 h this way, and #12229 collected eight such commits on 2026-10-22
     from `auto-update-pr-branches.yml`, which was retired for it.
   - **Already poisoned** (head commit authored by `github-actions[bot]`, checks stuck at
     `action_required`): approve the gated runs once —
     `gh api -X POST repos/{owner}/{repo}/actions/runs/<id>/approve`. Approved runs do report
     the required contexts on a bot-authored head (verified on #9674), and since no workflow
     updates PR branches any more (only `impl-merge.yml` updates its own `implementation/` PRs)
     the head stays put, so one approval is enough. `@dependabot recreate` also works and additionally restores a
     clean `dependabot[bot]` head, but it re-resolves the versions.
   - `mergeStateStatus` is computed async — after any update, poll it a few seconds until it
     stabilizes before deciding (UNKNOWN → BEHIND/CLEAN/BLOCKED).
3. A dep bump breaking tests/config (e.g. a major with changed exports): consult **Context7**
   for the library's current API (CLAUDE.md MCP tools section) — do not grep `node_modules`
   `.d.ts` files. Fix on the Dependabot branch or note the PR for manual handling.
4. When the last PR has merged and its deploys finished, run the site smoke once more
   (`/open-pr` skill §4). A failure is an incident: report it at once with the merges since the
   last passing run.
5. Check `main`'s own CI on the last merge: take its SHA (`gh pr view <num> --json mergeCommit
   --jq .mergeCommit.oid`), then run `gh run list --commit <sha> --event push --json
   workflowName,status,conclusion`. Each merge cancels the runs of the one before, so only the
   last merge's runs have tested the combined state. A run still in progress is reported as
   pending, never as green, and a red one blocks "done". Then
   **stop — do not leave a background monitor running.** Orphaned monitors fire notifications
   into later sessions. Report the list with each PR's end state instead.

## Report

Per PR: number, title, action taken (merged directly / auto-merge set / fix commit on the branch,
then merged / held + why), and the site smoke's result after the last merge, plus `main`'s CI on
the last merge.
