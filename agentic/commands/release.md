# Release

Cut a new anyplot release: finalize the changelog, bump the version, tag, and publish the GitHub
release. The release notes ARE the changelog section — no notes are written from scratch.

## Variables

version: $1 (optional — e.g. `3.1.0`; if omitted, propose one from the `[Unreleased]` content)

## Instructions

- **Versioning policy** (product communication, not library SemVer): major for milestone releases
  (new language/library waves, rebrands, breaking URL/schema changes — v2.0.0 and v3.0.0
  precedent), minor for feature batches, patch for fix-only releases.
- **Never work on `main` directly** — do the changelog/version edits on a `release/vX.Y.Z` branch
  and open a PR.
- The release PR should touch exactly three files: `CHANGELOG.md`, `pyproject.toml`, and
  `uv.lock` (the lock pins the project's own version — v3.0.0 precedent, commit d05e1f2a7). Keep
  the diff tiny and auditable.
- Pick a short **codename** (release theme, a few words) — it appears in three synchronized
  places: the changelog heading, the annotated tag message, and the GitHub release title.

## Run

1. **Verify completeness.** Compare `CHANGELOG.md`'s `[Unreleased]` section against
   `git log v<last>..origin/main --oneline --no-merges`, ignoring the exempt classes (spec-create,
   impl-generate/review/repair/merge, spec auto-polish, daily-regen commits, individual Dependabot
   bumps). Add any missing notable entries first. Run `git fetch origin main` before comparing, and
   check the state of any in-flight PRs the release should include yourself
   (`gh pr view <num> --json state,mergedAt`) — do not rely on the user to report merge status.
2. **Add the aggregate lines.** Summarize the exempt classes for the release window:
   - An italic `*Catalog: ...*` line at the end of the section (counts of new implementations,
     regenerations, coverage milestones — query merged impl PRs or `impl:*:done` labels).
   - Create or update the single `**Dependencies:**` bullet under `### Changed` grouping the
     Dependabot bumps of the window (never one bullet per bump).
3. **Move the section.** Retitle `## [Unreleased]` to `## [X.Y.Z] — YYYY-MM-DD — <Codename>` and
   recreate an empty `## [Unreleased]` heading above it. At the bottom of the file, repoint the
   `[Unreleased]` compare link to `vX.Y.Z...HEAD` and add the new `[X.Y.Z]` compare link — one
   link per bracketed heading, this step is easy to forget.
4. **Bump the version** in `pyproject.toml` to `X.Y.Z`, then run `uv lock` so `uv.lock` picks up
   the project's own version.
5. **Open the release PR** (`release: vX.Y.Z` title) and follow the standard PR follow-through
   from `CLAUDE.md`. Ask the user to merge unless explicitly authorized to merge autonomously.
6. **Tag after merge** (on the updated `main`):
   `git tag -a vX.Y.Z -m "<Codename> (YYYY-MM-DD)" && git push origin vX.Y.Z`
7. **Publish the GitHub release** with the changelog section as body. Write the body to a temp
   file first (it is multiline and contains backticks — do not inline it into `--notes`):
   `gh release create vX.Y.Z --title "vX.Y.Z — <Codename>" --notes-file <tmpfile>` — the body is
   the new version's `###` sections copied verbatim, plus a trailing
   `**Full Changelog:** https://github.com/MarkusNeusinger/anyplot/compare/v<last>...vX.Y.Z` line.
8. **Verify:** `gh release view vX.Y.Z` renders correctly; the site masthead picks up the new tag
   automatically (`app/src/hooks/useLatestRelease.ts` fetches `releases/latest` with a 1 h
   localStorage cache — nothing to deploy).

## Report

Return the release URL and a one-line summary of the version, codename, and entry counts.
