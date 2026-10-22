### Added

- **Adaptability checker for Python implementations.** `core/adaptability.py`
  checks a source against the adaptable-code convention
  (`docs/concepts/adaptable-code.md`): one `# Data` block that ends in `df`,
  one column constant per spec role, no sample literals below the block, and
  the full Imprint palette when a role colors the marks. It writes at most one
  CQ-01 `(code)` line per rule class, and classes under 90 % precision on a
  judged sample of 30 are advisory. `python -m core.adaptability report plots/`
  prints the catalogue baseline, and `automation/scripts/adaptability_check.py`
  is its generated single-file mirror for the workflow runner. The pipeline
  does not run it yet, so this changes no score and no workflow.
- **Perturbation tables and render identity for the smoke run.**
  `core/perturbation.py` builds the tables the smoke run swaps into the block
  (renamed columns and categories, one more and one fewer group, a single group,
  a tenth and ten times the rows, scaled values) and the source to run on each.
  `core/render_identity.py` measures the share of differing pixels between two
  renders against a bound.

### Changed

- **The spec role parser moved to `core/spec_roles.py`.** The agent and the
  checker now read a spec's `## Data` roles through one parser, which also files
  each spec as a table, matrix, network, generated or map spec and names its
  color-driving role.
