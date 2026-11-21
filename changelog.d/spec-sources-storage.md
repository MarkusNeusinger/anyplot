### Added

- **A spec can name its sources.** An optional `sources` block in
  `specification.yaml` lists the works that gave the idea for a plot
  (`inspired_by`) and the literature whose values it follows
  (`references`), each with a title, an address and an optional DOI or
  ISBN, plus where the example data comes from (`data`: invented,
  computed or real). Two relations only: the catalogue takes ideas from
  other works and never their code, so every implementation stays under
  the MIT License. `core/spec_sources.py` checks the block, a unit test
  runs the check over every spec file, and a pull request that changes
  only `specification.yaml` files now runs the unit tests too. The
  Postgres sync stores the block in a new column `specs.sources`
  (migration `21d93eb1afd4`), NULL for a spec that names none. No spec
  names a source yet; existing specs get theirs in later passes. (#13386)
