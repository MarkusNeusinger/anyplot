### Added

- **Eval cases for follow-ups that ask for two changes at once.** Four
  hand-written matrix cases send a follow-up such as "Make the title German
  and use a log scale on the y axis" after an English first plot: a language
  with a log scale, a theme with a grid, a language with a colour, and a log
  scale alone as the control. A new `checks` field in `case.json` measures
  each part in code on the version the follow-up shipped: its plot language
  and theme, patterns its code must add or keep, drawn texts that must
  change, and an empty `requested_not_found`. A run passes only when every
  check holds, and the report lists each failed one under `check_failures`.
  (#12510)

### Fixed

- **A message that asks for a language and another change gets both.** In
  the user test of 2026-11-01, "make the title German and use a log scale"
  reached the plot with the German title only: `root.md` had the root follow
  `set_language` with a fixed rewrite request that ended "change nothing
  else". The rewrite is now the server's job. The adapter already rewrites
  the plot's text when the base version is in another language, so the
  root's change request carries only the user's other changes, and a run with
  none gets the server's own rewrite request. The root also sends a theme only
  as `theme`: written into the change request, "a dark background" made the
  adapter replace the theme tokens with fixed dark colours. (#12510)
