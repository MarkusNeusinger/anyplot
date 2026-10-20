### Changed

- **The data box says what it waits for.** While a dropped Parquet, Excel,
  OpenDocument, Feather or NumPy file is read on the server, and while
  `.parse()` runs, the box shows `# reading "x.parquet" on the server … · 4 s`
  or `# parsing your data … · 3 s` over itself: a pulsing `…`, a seconds counter
  and a thin bar along its foot. Before, only the buttons greyed out and a quiet
  line under them changed, so the page looked stuck for the several seconds a
  sandbox read takes. (#12221)
