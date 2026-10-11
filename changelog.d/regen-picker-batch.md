### Changed

- **A bare `/regen` picks its spec in about 2.5 s instead of 30 s.** The picker
  (`agentic/workflows/modules/regen/picker.py`) now reads the catalogue on
  `origin/main` with one `git ls-tree` and one `git cat-file --batch`, instead of
  one `git ls-tree` per spec and one `git show` per metadata file — about 2,900
  processes per call — and parses the YAML with libyaml's `CSafeLoader` where
  PyYAML has it (2.0 s instead of 19.8 s for the 2,596 files). The pick is
  unchanged: on the live tree, all 325 specs and every metadata file gave the
  same timestamps as before, and `validate-spec` the same answers. The live test
  `test_pick_oldest_returns_real_spec` drops from 30.3 s to 2.9 s locally (mean
  of three runs) and from 63.7 s to 5.2 s under coverage, as CI runs it; new
  fake-git tests pin the listing, batch-parsing and picking rules in
  milliseconds. (#12135)
