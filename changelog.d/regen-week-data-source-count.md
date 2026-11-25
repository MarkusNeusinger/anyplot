### Added

- **The weekly regen review counts regenerations that change their data source.**
  The collector reads each regeneration's implementation diff and flags one that
  adds an example-dataset loader its predecessor did not have (seaborn's
  `load_dataset`, scikit-learn's toy loaders, sample-data modules, R `data()`,
  `RDatasets`, or a data file fetched by URL), and the metric table counts them
  with a target of 0. The readiness gate no longer keeps such a regeneration, so
  this count is what still checks the rule that a regeneration keeps its data
  source. Over the 1,352 regenerations since 2026-11-04 it finds two, both
  choropleths that download their map boundaries during the render. (#14256)
