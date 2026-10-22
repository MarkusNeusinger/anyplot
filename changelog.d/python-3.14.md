### Changed

- **Python 3.14 everywhere.** The project floor (`requires-python`), the pinned
  interpreter (`.python-version`, 3.14.9), mypy's target, every workflow's
  `setup-python`, the three service images (`python:3.14-slim` for the API,
  the agents service and the renderer) and the Python runtime the languages
  table reports move from 3.13 to 3.14. 3.13 receives security fixes only since
  October 2026, while 3.14 gets bug fixes until October 2027; 3.15 waits for a
  lets-plot wheel. `google-crc32c` moves from 1.7.1 to 1.9.0 in the lock, because
  1.7.1 publishes no cp314 wheel and the images carry no compiler to build it.
