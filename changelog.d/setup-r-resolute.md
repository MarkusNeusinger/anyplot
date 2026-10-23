### Fixed

- **The R setup installs packages built for the Ubuntu 26.04 runner image.** The
  setup-r action installed Posit's `noble` (Ubuntu 24.04) binaries. On the 26.04
  image they install without error, but stringi links ICU 74 while 26.04 ships
  ICU 78, so loading stringr fails. No catalogue implementation reaches stringi
  today: all 325 render the same on both builds. A generated implementation that
  used stringr, or tidyr's `separate()` or `extract()`, would have failed
  mid-run. The action now installs the `resolute` binaries from the same
  2026-10-20 snapshot. Its smoke test also loads tidyr and stringr, so a binary
  built for another Ubuntu release fails the setup step instead of a generation
  run. (#12263)
