### Fixed

- **Correcting a bullet in `[Unreleased]` no longer reads as adding one.**
  The fragment gate compared bullet SETS, so re-wording an entry the base
  already carried was indistinguishable from writing a new one and got the
  same refusal — "gained a bullet, it belongs in a fragment" — for a change
  that added nothing. A bullet is now identified by its bold title
  (`tools/changelog`, `bullet_title`), collapsed over the line breaks so a
  correction may reflow the very line the title runs over: a title the base
  lacks is an ADDED bullet and is still refused, a title it has is a CHANGED
  one and passes.

### Added

- **`check` refuses a fragment that still says `(#NNNNN)`.** The reference is
  appended by `/pull_request` when the PR opens, so a fragment is written
  without one — but the placeholder shipped as written reads as a reference in
  the released section and points nowhere, and nothing caught it. The
  complaint names the file and the line; a placeholder quoted in backticks is
  prose about the rule, not a reference, and passes. The README example no
  longer hands the writer a placeholder to leave behind.
