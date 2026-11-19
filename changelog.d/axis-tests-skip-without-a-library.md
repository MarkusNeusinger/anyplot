### Fixed

- **Four axis tests of the drawn-text record skip where seaborn or plotnine
  is missing, and fail where CI requires them.** Two imported seaborn
  directly and so failed, instead of skipping, in an environment without the
  plotting libraries; the other two used `pytest.importorskip`, which would
  have skipped silently in CI's test job as well. All four now go through
  `tests.libraries.import_library`, as the other library tests do.
