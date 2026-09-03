# Release

Cut a new anyplot release: finalize the changelog, bump the version, tag, and publish the GitHub
release. The release notes are the changelog section **condensed** — never copied verbatim, never
written from scratch (owner rule, 2026-08-28; the shape is in `CLAUDE.md` § "Changelog +
releases", the procedure is step 7 below).

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
4. **Read the diff.** It touches `CHANGELOG.md`, `pyproject.toml`, `uv.lock`, `app/package.json`
   and the deleted fragments — nothing else. Run `uv lock` if the lock needs more than its own
   version line.
5. **Open the release PR** (`release: vX.Y.Z` title) and follow the standard PR follow-through
   from `CLAUDE.md`. Ask the user to merge unless explicitly authorized to merge autonomously.
6. **Tag after merge** (on the updated `main`):
   `git tag -a vX.Y.Z -m "<Codename> (YYYY-MM-DD)" && git push origin vX.Y.Z`
7. **Publish the GitHub release** with the changelog section **condensed** as body — never the
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
8. **Verify:** `gh release view vX.Y.Z` renders correctly; the site masthead picks up the new tag
   automatically (`app/src/hooks/useLatestRelease.ts` fetches `releases/latest` with a 1 h
   localStorage cache — nothing to deploy).

## Report

Return the release URL and a one-line summary of the version, codename, and entry counts.
