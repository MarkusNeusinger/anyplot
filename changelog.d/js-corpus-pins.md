### Fixed

- **The JavaScript catalogue tests hold rules, not the counts of one day.** Four corpus tests pinned the
  catalogue as it stood on 2026-10-30 and 2026-10-31: the readiness split (93 clean MUI X files), the
  detected conventions (1,602 `t` tokens, 1,344 `// Data` markers), the normaliser's rewrites (893 directives
  written out) and which eval specs' MUI X files are clean. Every MUI X 9 regeneration broke them. Main never
  ran them, because a merge that changes only implementation files skips pytest, so every Python PR inherited
  the failure. The tests now check each file:
  - the blocked files are exactly the map specs and the known SECURITY cases;
  - a clean file has the adaptable-code layout, and the `data-block` hint appears exactly when that layout is
    incomplete;
  - `deprecated-api` appears only in MUI X 7 files, and in every file that imports `ChartContainer`;
  - each detected convention matches a plain reading of the file's text and the harness's own orientation
    pattern;
  - the normaliser makes only its known rewrites.
