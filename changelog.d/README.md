# changelog.d — one fragment per PR

Every PR that changes code adds ONE file here instead of editing
`CHANGELOG.md`: `changelog.d/<slug>.md`, the slug naming the change (the branch
name minus its prefix does fine — `origin-gate-rest.md`, `csp-hashes.md`).
Nothing else touches `CHANGELOG.md` between releases, so two PRs never meet at
the same line again — the reason this directory exists (three conflicts in one
night on 2026-09-02/03, each a hand-resolved rebase for text neither branch
disagreed about; a union merge driver heals only the local rebase, and GitHub's
own mergeability check ignores merge drivers).

A fragment is a slice of the changelog in the changelog's own format:

```markdown
### Added

- **The thing, named as the reader will meet it.** One clause on what it
  does and where, then why it is the right shape — the rationale a diff
  cannot carry. Ends with the PR reference once known (#NNNNN).

### Fixed

- **What was wrong, as a title.** What it did, what it does now (#NNNNN).
```

Rules, all enforced by `uv run python -m tools.changelog check`:

- Headings are `### Added` · `### Changed` · `### Deprecated` · `### Removed`
  · `### Fixed` · `### Security` (Keep a Changelog), each at most once per
  fragment; a fragment has at least one bullet.
- A bullet opens with its bold title and wraps with two-space indentation,
  exactly like the entries already in `CHANGELOG.md`; English (`CLAUDE.md`
  § "Always write in English"), written like the existing entries: what,
  where, why.
- Nothing else in the file — no prose above the first heading, no `##`.

The CI job "Changelog (fragment)" requires a fragment in every PR — except
catalogue-only PRs (everything under `plots/`), PRs labelled `skip-changelog`,
and the two bot authors: the automated plot pipeline (`github-actions[bot]`:
spec-create, impl-generate/review/repair/merge, spec auto-polish, daily-regen)
and Dependabot. Those are exactly the classes `CLAUDE.md` already exempts and
the release summarizes in aggregate. The job also refuses bullets written into
`[Unreleased]` directly.
`uv run python -m tools.changelog check --base origin/main` is the same check
locally; `uv run python -m tools.changelog preview` prints the pending section.

The release cut, `uv run python -m tools.changelog release X.Y.Z --title "…"`,
folds all fragments under the new version heading — newest first within a
category, by the commit that added the fragment — bumps `pyproject.toml`,
`uv.lock` and `app/package.json`, repoints the compare links at the bottom of
the file, and deletes the fragments. This README stays.

The two aggregate lines stay by hand: the italic `*Catalog: …*` at the end of
the section and the single `**Dependencies:**` bullet that stands in for the
window's Dependabot bumps. Both summarize a release window rather than a PR, so
they are written at cut time into the section the tool has just laid out
(`agentic/commands/release.md` step 3 — step 2 is the cut itself).
