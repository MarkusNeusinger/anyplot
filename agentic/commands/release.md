# Release

Cut a new anyplot release: finalize the changelog, bump the version, tag, and publish the GitHub
release. The release notes are the changelog section **condensed** — never copied verbatim, never
written from scratch (owner rule, 2026-08-28; the shape is in `CLAUDE.md` § "Changelog +
releases", the procedure is step 9 below).

## Variables

version: $1 (optional — e.g. `3.1.0`; if omitted, propose one from the `[Unreleased]` content)

## Instructions

- **Versioning policy** (product communication, not library SemVer): major for milestone releases
  (new language/library waves, rebrands, breaking URL/schema changes — v2.0.0 and v3.0.0
  precedent), minor for feature batches, patch for fix-only releases.
- **Never work on `main` directly** — do the changelog/version edits on a `release/vX.Y.Z` branch
  and open a PR.
- The release PR should touch exactly four files plus the fragments it consumes: `CHANGELOG.md`,
  `pyproject.toml`, `uv.lock` (the lock pins the project's own version — v3.0.0 precedent, commit
  d05e1f2a7), `app/package.json`, and the deleted `changelog.d/*.md`. Keep the diff tiny and
  auditable; `uv run python -m tools.changelog release` produces exactly that set.
- Pick a short **codename** (release theme, a few words) — it appears in three synchronized
  places: the changelog heading, the annotated tag message, and the GitHub release title.

## Run

1. **Verify completeness.** Run `uv run python -m tools.changelog preview` — that is the pending
   section, every fragment in `changelog.d/` merged with whatever `[Unreleased]` still holds — and
   compare it against `git log v<last>..origin/main --oneline --no-merges`, ignoring the exempt
   classes (spec-create, impl-generate/review/repair/merge, spec auto-polish, daily-regen commits,
   individual Dependabot bumps). A missing entry is added as a fragment in `changelog.d/`, never as
   a bullet in `CHANGELOG.md`. Run `git fetch origin main` before comparing, and check the state of
   any in-flight PRs the release should include yourself (`gh pr view <num> --json state,mergedAt`)
   — do not rely on the user to report merge status.
2. **Cut the section.** `uv run python -m tools.changelog release X.Y.Z --title "<Codename>"`
   (`--dry-run` first prints the section it would write and touches nothing). One command folds
   every fragment under `## [X.Y.Z] — YYYY-MM-DD — <Codename>` — newest first within a category, by
   the commit that added the fragment — leaves an empty `## [Unreleased]` above it, repoints the
   compare links at the bottom of the file, bumps `pyproject.toml`, `uv.lock` and
   `app/package.json`, and deletes the fragments. `app/package.json` matters as much as the others:
   the masthead falls back to it whenever the GitHub releases lookup is unavailable, and
   `tests/unit/test_version_sync.py` fails the PR if the two drift.
3. **Add the aggregate lines by hand**, into the section just written. They are the one part the
   tool deliberately leaves alone, because they summarize a release window rather than any PR:
   - An italic `*Catalog: ...*` line at the end of the section (counts of new implementations,
     regenerations, coverage milestones — query merged impl PRs or `impl:*:done` labels).
   - The single `**Dependencies:**` bullet under `### Changed` grouping the Dependabot bumps of
     the window (never one bullet per bump).
4. **Refresh the README showcase**, on the release branch. Run
   `uv run python scripts/readme_showcase.py`: it redraws `docs/assets/readme-showcase.png` from the
   live `/stats` and stops when MonoLisa or a pick's preview is missing; look at the image before
   committing it. Then count the merged pull requests from the owner's account
   (`gh pr list --state merged --author MarkusNeusinger --limit 5000 --json number --jq length`) and
   update three places in one commit:
   - `MERGED_PRS_SNAPSHOT` in `tests/unit/test_readme_claims.py`: the count and today's date.
   - The floor in `README.md` and in `docs/concepts/ai-workflow.md` ("more than N pull requests from
     my account have merged"): the last multiple of 50 below the count (869 merged gave "more than
     850").

   It stays a floor, never an exact number. The test refuses an exact count, a floor that isn't a
   multiple of 50, a floor at or above the snapshot, and one more than 50 below it. Commit the image,
   the snapshot and the wording on the release branch.
5. **Read the diff.** It touches `CHANGELOG.md`, `pyproject.toml`, `uv.lock`, `app/package.json`,
   the deleted fragments and step 4's showcase image, pull-request snapshot and floor — nothing else. Run
   `uv lock` if the lock needs more than its own version line.
6. **Run the agent evals** on `origin/main`. The release branch changes no agent code, so main is
   what the release ships. No CI job runs these suites: they call the real models and cost real
   money. A release is the one fixed point where every prompt and model change of the window is
   measured together. A regression that no single PR's eval caught otherwise ships unnoticed: on
   2026-11-05 one surfaced on main only because a sibling PR ran its eval. The suites use the local
   Vertex AI login (ADC), so they run on the owner's machine, not in a cloud session.
   - **Always:**
     - `uv run --extra agents python -m agents.evals.prep`: the root's step-1 data choices,
       85 cases, about $0.25. Its gate is 80 percent of the cases matched, by the table each turn
       leaves (since 2026-11-08; the summary keeps the key `exact` for it, and `ops_exact` counts the
       cases whose operations were exactly the expected ones).
     - `uv run --extra agents python -m agents.evals.scope`: the scope judge, about $0.05. Its
       gates are adversarial recall and the false-refusal rate; exit code 1 means a gate failed.
   - **When the window changed the plot pipeline:** that is the adapter or reviewer prompts,
     `prompts/library/`, `prompts/quality-criteria.md`, `prompts/default-style-guide.md`, the
     model settings or the pipeline code (`git diff --name-only v<last>..origin/main` shows it).
     Then also run the matrix smoke. The smoke set holds a case for every library, so the run
     needs all of them enabled (`agents/README.md`, "Run the smoke set or the full matrix");
     otherwise the readiness scan blocks those cases as `library-disabled`:

     ```bash
     URL=$(gcloud run services describe anyplot-renderer --region=europe-west4 --format='value(status.url)')
     AGENT_LIBRARIES=matplotlib,seaborn,plotnine,altair,pygal,letsplot,plotly,bokeh,ggplot2,makie,chartjs,d3,echarts,highcharts,muix \
       uv run --extra agents python -m agents.evals.matrix --cases smoke \
       --renderer remote --render-url "$URL" --gcloud-token
     ```

     It renders 25 plots and compares them with the committed baseline; exit code 1 means it fell
     below the baseline's tolerance.
   - **Compare with the previous release** (its PR body's "Agent evals" section). A model answers
     differently from run to run, so a single miss is noise. The release waits when a suite fails
     its own gate, or when prep lands more than three cases below the previous release. Then run
     each new miss five times on the previous tag and five times on `origin/main`:
     - **Prep:** copy the missed cases' files from `agents/evals/fixtures/prep/` on main into a new
       private directory (`D=$(mktemp -d)`), so that both sides read the same cases. Then run
       `uv run --extra agents python -m agents.evals.prep --cases "$D" --out "$D/run-<n>"` five
       times: in the release worktree, and in a detached worktree of the previous tag
       (`git worktree add --detach <path> v<last>`, removed afterwards).
     - **Matrix:** `--cases '<case-id>,<case-id>' --repeats 5`, with the same environment as above,
       on both sides.
     - **Scope:** the whole suite costs a few cents, so run it again on both sides instead of
       selecting cases.

     Read the result per case:
     - A miss that holds on main but not on the tag is a regression. It gets a fix PR before the
       release, unless the owner decides to release anyway. Say so in the PR body.
     - A miss on both sides is a known issue. Name it in the PR body.
   - **Write an "Agent evals" section into the release PR body.** For each suite, give its result
     (prep: exact cases of the answered ones, reply misses; scope: recall and false refusals;
     matrix: the pass rate against the baseline), its cost, and each miss with its verdict. The
     next release compares against this section.
7. **Open the release PR** (`release: vX.Y.Z` title) and follow the standard PR follow-through
   from `CLAUDE.md`. Ask the user to merge unless explicitly authorized to merge autonomously.
8. **Tag after merge** (on the updated `main`):
   `git tag -a vX.Y.Z -m "<Codename> (YYYY-MM-DD)" && git push origin vX.Y.Z`
9. **Publish the GitHub release** with the changelog section **condensed** as body — never the
   section copied (the v3.1.0 page was 640 lines). Write the body to a temp file first (it is
   multiline and contains backticks — do not inline it into `--notes`), then
   `gh release create vX.Y.Z --title "vX.Y.Z — <Codename>" --notes-file <tmpfile>`. The body:
   - **Intro line:** merge count and PR range of the window (`git log v<last>..vX.Y.Z --oneline
     --merges | wc -l` for the count; lowest and highest PR number for the range) and a link to
     `CHANGELOG.md` — "the full record is [CHANGELOG.md](…), and each PR carries its own
     reasoning".
   - **The section's own `###` headings, in the section's order;** an empty heading is omitted.
   - **One bullet per NOTABLE entry** — chores, dependency bumps, small fixes and the aggregate
     lines are left out; there is no fixed count. Each bullet is at most two lines: the entry's
     **bold title** verbatim, one clause with the essence or the headline number, its PR
     reference. Numbers are copied exactly from the entry; only PR numbers that appear in the
     section are cited.
   - **Last line:** `**Full Changelog:** https://github.com/MarkusNeusinger/anyplot/compare/v<last>...vX.Y.Z`.
   The full text lives only in the CHANGELOG; the release page is the index into it.
10. **Verify:** `gh release view vX.Y.Z` renders correctly; the site masthead picks up the new tag
    automatically (`app/src/hooks/useLatestRelease.ts` fetches `releases/latest` with a 1 h
    localStorage cache — nothing to deploy).

## Report

Return the release URL and a one-line summary of the version, codename, and entry counts.
