### Added

- **The renderer draws plotly and bokeh figures in two steps, not served yet.**
  The render harness forks the plot before it arms anything: the plot runs
  under the plot guard and the exec filter with the Python limits and may write
  only its figure as JSON, and the harness, never armed, then hands the figure
  to the JavaScript row's browser harness, which draws it as data with the
  installed package's own plotly.js or BokehJS in the sandboxed page, with a
  stricter policy that runs no script the figure carries. The figure keeps the
  size its code gave it, and the scale makes the image exactly 3200x1800 or
  2400x2400, so the catalogue's layouts look as published. Failures in either
  step end with the same final error line as a JavaScript render. The renderer
  image now carries plotly and bokeh without their kaleido and Selenium export
  stacks. The agent chat does not offer plotly or bokeh yet. (#12484)

### Fixed

- **No user code runs while a render or data guard is paused.** The harness
  pauses its guard briefly to read a traceback or resolve a path, and code the
  snippet defined could run in that moment and write files the guard refuses:
  an exception class's own `__traceback__` property while a data run printed
  its traceback, and a path that subclasses `str` while a plot's file write was
  checked. The harness now reads the traceback through Python's own
  descriptor, copies a path to a plain string before the check, and compares
  only plain strings while paused. (#12484)
- **A plot can no longer run code of its own as an import.** The render guard
  trusted any code the import machinery ran, so a plot that drove it, with a
  loader of its own or a stock loader on a file it had written, ran a module
  body that read the guard's frames and switched it off. The guard now trusts
  an import only when the interpreter's own loader runs it, refuses every code
  read and every native module load outside the installed packages, and
  refuses changing the flags of the output it shares with the screenshot step.
  The plot validator also refuses the package-data reader, the import spec
  builders and the dynamic class builder that matplotlib's bundled dateutil and
  the standard library's `types` module hand out, found by a new walk over
  everything the validator admits. (#12484)
