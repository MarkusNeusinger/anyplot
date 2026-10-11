### Added

- **The assistant computes your data from a formula in step 1.** Ask for a function
  or curve instead of a table ("zeichne sin(x) von -pi bis pi", a parabola, a
  parametric circle, a surface `z = sin(x)*cos(y)`), and the root agent's new
  `generate_data` tool chooses a spec, never rows: one or two variable ranges and one
  to ten series, each an expression over them. The agents service computes the table
  with NumPy (`agents/anyplot/data/generate.py`) through a whitelist over Python's
  `ast` (numbers, the variables, `pi`, `e`, `tau`, `+ - * / ** % //` and a fixed set
  of functions), never `eval`, so a forbidden construct is refused with a message that
  names it ("'^' is not a power; write x**2") and an overflow or a logarithm of a
  negative number becomes an empty cell, never an exception. The table is an ordinary
  dataset version: the next one, which `.undo()` takes back, when the session has
  data, or version 1 when it has none; the user confirms it like a paste, and the plot
  and its export use it unchanged. `ToolSafety` validates the spec against the same
  model first.
- **Formulas pasted into the data field answer `422 formula`.** The dataset route
  refuses text that looks like a formula before the free-text transcriber reads it,
  because that model would compute the rows itself; the BFF passes the code on, and
  the page can point to the chat instead. The `done` event's `dataset` now carries the
  spec's `roles` too, so a first dataset made in the chat has its binding controls.
- **Formula cases in the evals.** The scope judge treats a request to draw a function,
  curve or distribution shape as in scope, never `needs_data` (six new English and
  German scope cases), and the prep eval scores `generate_data` calls like
  `prepare_data` operations on four new cases (21 in all).
