### Changed

- **Python 3.14 everywhere.** The project floor (`requires-python`), the pinned
  interpreter (`.python-version`, 3.14.9), mypy's target, every workflow's
  `setup-python`, the three service images (`python:3.14-slim` for the API,
  the agents service and the renderer) and the Python runtime the languages
  table reports move from 3.13 to 3.14. 3.13 receives security fixes only since
  October 2026, while 3.14 gets bug fixes until October 2027; 3.15 waits for a
  lets-plot wheel. `google-crc32c` moves from 1.7.1 to 1.9.0 in the lock, because
  1.7.1 publishes no cp314 wheel and the images carry no compiler to build it.
  (#12247)

### Security

- **The renderer sandbox stays tight on Python 3.14.** 3.14 raises an audit event
  for every ctypes call, so the plot guard refused the `ctypes.cast` that scipy
  makes while it is imported, and with it every plot that uses scipy, statsmodels,
  scikit-learn or seaborn. The plot guard now lets exactly that call through, and
  only from an import; the same cast from plot code, `memmove`, `memset` and every
  other foreign function stay refused, and the data and convert guards allow none
  (narrowed after a Fable review). The sandbox interpreter also runs with
  `-X disable-remote-debug`, and the guards refuse `sys.remote_exec`, so 3.14's
  remote debugging cannot run a script in it. The code validator bans
  `annotationlib` and `typing.evaluate_forward_ref`, which 3.14 added and which
  evaluate annotation strings. (#12247)
