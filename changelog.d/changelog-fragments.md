### Changed

- **Every PR now adds a `changelog.d/` fragment instead of a bullet in `CHANGELOG.md`** — the
  shared `[Unreleased]` section is the one place sibling PRs reliably conflict each other, and on
  the night of 2026-09-02/03 it did so three times in a row: each time a hand-resolved rebase for
  text neither branch disagreed about. The `.gitattributes` line-ending rules do nothing for it, and
  a union merge driver would not fix it either — GitHub's own mergeability check ignores merge
  drivers, and a branch that MOVES changelog lines comes out of a union rebase with the block
  duplicated. Fragments remove the shared spot rather than healing it: a PR writes
  `changelog.d/<slug>.md` in the changelog's own format (`### Category` over bold-titled bullets)
  and touches `CHANGELOG.md` not at all, so two PRs never meet at the same line. `tools/changelog`
  is the standard-library tool behind it — `check` (also the CI job "Changelog (fragment)", which
  refuses a missing fragment AND a bullet written into `[Unreleased]`), `preview`, and `release`,
  which folds every fragment under the new version heading newest-first, bumps `pyproject.toml`,
  `uv.lock` and `app/package.json`, repoints the compare links at the bottom of the file — a step
  `release.md` called easy to forget, so it is no longer a step — and deletes the fragments. The
  exemptions are the ones this repository already had, now enforced rather than remembered:
  catalogue-only PRs under `plots/`, the automated plot pipeline and Dependabot (both by author, so
  the gate never sits red on a bot batch), and the `skip-changelog` label. What the tool
  deliberately does NOT touch is the release's two aggregate lines — the italic *Catalog* line and
  the single **Dependencies:** bullet — because those summarize a window rather than a PR and are
  written at cut time. Ported from the sibling repo kurrentschrift, where the same tool has run
  since 2026-08-30. (#11215)
