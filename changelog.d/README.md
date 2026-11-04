# changelog.d — one fragment per PR

`CHANGELOG.md` covers product, pipeline-infrastructure, and docs changes. Every
PR outside the [exempt classes](#exempt-classes-and-the-aggregate-lines) adds
one file here instead of editing `CHANGELOG.md`: `changelog.d/<slug>.md`, the
slug naming the change (the branch name minus its prefix does fine —
`origin-gate-rest.md`, `csp-hashes.md`). Nothing else is added to
`CHANGELOG.md` between releases, so two PRs never meet at the same line again —
the reason this directory exists (three conflicts in one night on 2026-09-02/03,
each a hand-resolved rebase for text neither branch disagreed about; a union
merge driver heals only the local rebase, and GitHub's own mergeability check
ignores merge drivers).

## Write a fragment

A fragment is a slice of the changelog in the changelog's own format:

```markdown
### Added

- **The thing, named as the reader will meet it.** One clause on what it
  does and where, then why it is the right shape — the rationale a diff
  cannot carry.

### Fixed

- **What was wrong, as a title.** What it did, what it does now.
```

**Leave the PR reference out; `/pull_request` appends it.** The number does
not exist until the PR does, so write the bullet without one and let step 7
of `agentic/commands/pull_request.md` add the real `(#11215)` afterwards. Every
bullet carries its PR reference by the time it is released. What `check`
refuses is the letter N left standing where a number was meant to go:
`(#NNNNN)` shipped as written reads as a reference in the released section and
points nowhere. So: a number, or nothing. (Quoted in backticks it is prose
about the placeholder — this paragraph included — and passes.)

Rules, all enforced by `uv run python -m tools.changelog check`:

- Headings are `### Added` · `### Changed` · `### Deprecated` · `### Removed`
  · `### Fixed` · `### Security` (Keep a Changelog), each at most once per
  fragment; a fragment has at least one bullet.
- A bullet opens with its bold title and wraps with two-space indentation,
  exactly like the entries already in `CHANGELOG.md`; English (`CLAUDE.md`
  § "Always write in English"), written like the existing entries: what,
  where, why. The closing `**` may sit on the continuation line — a long
  title is allowed to wrap — but it has to be there.
- No bare `(#NNNNN)`: fill the number in or leave the reference out.
- Nothing else in the file — no prose above the first heading, no `##`.

## What the CI job checks

The CI job "Changelog (fragment)" requires a fragment in every PR — except
catalogue-only PRs (everything under `plots/`), PRs labelled `skip-changelog`,
and the two bot authors: the automated plot pipeline (`github-actions[bot]`:
impl-generate/review/repair/merge, daily-regen) and Dependabot. Spec-create and
spec auto-polish open their PRs as `claude[bot]` and pass as catalogue-only.
Those are exactly the classes `CLAUDE.md` already exempts and
the release summarizes in aggregate. The job also refuses bullets added to
`[Unreleased]` directly: the shared `[Unreleased]` spot is where sibling PRs
used to conflict.

Added, not merely different: a bullet is identified by its bold title, so
correcting the wording of an entry `[Unreleased]` already carries — a typo in a
shipped line, a sharper clause — passes, and only a title the base does not
have, or one more copy of a title already there, counts as a new entry that
belongs in a fragment.
`uv run python -m tools.changelog check --base origin/main` is the same check
locally; `uv run python -m tools.changelog preview` prints the pending section.

## Cut a release

The release cut, `uv run python -m tools.changelog release X.Y.Z --title "<codename>"`,
folds all fragments under a new version heading,
`## [X.Y.Z] — YYYY-MM-DD — <codename>` — newest first within a category, by
the commit that added the fragment — bumps `pyproject.toml`
(`project.version`), `uv.lock` and `app/package.json`, repoints the compare
links at the bottom of `CHANGELOG.md`, and deletes the fragments. This README
stays. The cut is one commit, via a PR; the procedure is
`agentic/commands/release.md`.

## Exempt classes and the aggregate lines

The automated plot pipeline's routine output (spec-create,
impl-generate/review/repair/merge, spec auto-polish, and daily-regen PRs) and
individual Dependabot bumps get no entry of their own: listing those per entry
would drown the file (900+ automated commits per release window). Where a
release window had such activity, it is summarized in aggregate instead, by two
lines that stay by hand: the italic `*Catalog: …*` at the end of the version
section and the single `**Dependencies:**` bullet under `### Changed` that
stands in for the window's Dependabot bumps. Both summarize a release window
rather than a PR, so they are created or updated at cut time in the section the
tool has just laid out (`agentic/commands/release.md` step 3 — step 2 is the
cut itself).

## Publish the GitHub release

After the release PR merges, the tag goes on the merge commit and the GitHub
release is created from the section — condensed, never copied (rule of
2026-08-28):

- An intro line with the merge count, the PR range, and a link to
  `CHANGELOG.md`.
- The section's own headings in the section's order (an empty one is omitted).
- One bullet per notable entry — chores, dependency bumps, and small fixes are
  left out, and there is no fixed count — at most two lines each: its bold
  title, one clause with the essence or the headline number, its PR reference.
- A compare link as the last line.

Numbers are copied exactly, and only PR numbers from the section are cited. The
full text lives only in `CHANGELOG.md`; the release page is the index into it.
