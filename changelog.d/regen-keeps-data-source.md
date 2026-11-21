### Changed

- **A regeneration keeps its data source.** The generator no longer brings a
  built-in dataset (`sklearn.datasets`, `sns.load_dataset`) into a regenerated
  file whose previous version did not load one, so a regeneration cannot turn
  a file the site's chat adapts into one its validator refuses for that reason
  alone; a dataset the previous file already loads stays.
