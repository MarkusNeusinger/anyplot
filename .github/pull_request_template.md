<!--
Automated pipeline PRs (spec-create, impl-*, auto-polish, daily-regen) and
Dependabot bumps ignore this template — they are summarized at release time.
-->

## In plain words

<!-- At most 150 words for a reader who does not know the code: what a person
ran into before, what happens now, and how it is solved, without file or
setting names. The rules are in agentic/commands/pull_request.md; catalogue-only
PRs (everything under plots/) leave this section out. -->

**What you would notice:**

## Summary

<!-- 1-3 bullet points describing the changes -->

-

## Test plan

<!-- How were the changes verified? Check the applicable verify loops. -->

- [ ]

## Checklist

- [ ] `changelog.d/<slug>.md` added (Keep-a-Changelog categories, bold-titled
      bullets, no `(#NNNNN)` placeholder — `changelog.d/README.md`), and no new
      bullet in `CHANGELOG.md` (correcting one already there is fine)
      — required for every non-pipeline PR
- [ ] Related documentation updated (e.g. `docs/reference/`, `docs/workflows/`,
      `docs/contributing.md`) if behavior changed
