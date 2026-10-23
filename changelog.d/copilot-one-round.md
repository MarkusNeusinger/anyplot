### Changed

- **Copilot reviews a PR once; another round only while the previous one
  had high or critical findings.** `CLAUDE.md`, the `open-pr` skill and
  `/pull_request` replace "stop once a round yields nothing new", which let
  a round with any findings draw the next one, with the owner's rule of
  2026-10-23: a round with only low and medium findings gets its fixes
  pushed and its threads resolved, and that is the end, because every round
  re-reads the whole diff and costs premium requests. (#12250)
