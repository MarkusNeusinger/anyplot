### Changed

- **The Dependabot command covers what the 2026-11-18 batch ran into.** `--auto` is refused on
  a PR that is already clean, so such a PR merges directly after a check review; an unanswered
  `@dependabot rebase` is replaced by a local merge check (`uv lock --check`, or CI's full
  frontend gate for `app/`); a PR red only in the non-required renderer image check is
  never armed; a `claude-code-action` bump also moves `ACTION_SHA` in `review-retest.yml`; exact
  ADK and tree-sitter pins in `python-minor` go to the owner; and the run ends with `main`'s CI on
  the last merge, since each merge cancels the runs before it. (#13194)
