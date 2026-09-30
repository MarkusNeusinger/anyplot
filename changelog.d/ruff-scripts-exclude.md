### Fixed

- **Ruff lints `automation/scripts/` and its tests again.** The Ruff
  `exclude` entry `"scripts"` matched every directory of that name, so CI's
  `ruff check .` and `ruff format --check .` skipped `automation/scripts/` and
  `tests/unit/automation/scripts/` along with the top-level one-off scripts it
  was meant for. The entry is now `"./scripts"`, anchored to the project root,
  and the one import-order and three format errors it had hidden are fixed.
