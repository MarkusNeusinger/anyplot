### Changed

- **Copilot reviews a PR once; a second round only after a fixed
  high-severity finding, never a third.** `CLAUDE.md`, the `open-pr`
  skill and `/pull_request` replace "stop once a round yields nothing
  new", which let a round with findings draw the next one, with the
  owner's rule of 2026-10-23: small and medium findings get their fixes
  pushed and their threads resolved with no new round, because every
  round re-reads the whole diff and costs premium requests.
