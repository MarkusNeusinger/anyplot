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
  negative number becomes an empty cell, never an exception. Every row holds the
  formula for the `x` it shows (the variables are rounded first), and the change line
  quotes only the checked expression. The table is an ordinary dataset version: the
  next one, which `.undo()` takes back, when the session has data, or version 1 when
  it has none, with the default bindings for its columns; the user confirms it like a
  paste, and the plot and its export use it unchanged. `ToolSafety` validates the spec
  against the same model first. (#12134)
- **Formulas pasted into the data field answer `422 formula`.** The dataset route
  refuses text that looks like a formula before the free-text transcriber reads it,
  because that model would compute the rows itself; the BFF passes the code on, and
  the page can point to the chat instead. Text that holds its own values stays data
  ("Mieten von 500 bis 900 Euro pro Quadratmeter: Berlin 12, Hamburg 14, München
  19"), and the transcriber's rubric now says to compute nothing. The `done` event's `dataset` now carries the
  spec's `roles` too, so a first dataset made in the chat has its binding controls. (#12134)
- **The chat page takes a formula from either box.** Until there is data, the data box
  and the chat both name the other source ("or ask for a curve in the chat: y = sin(x),
  x from -pi to pi"), and the chat is open without a paste. A formula pasted into the
  data box gets the server's `422 formula` as a line with `.send()`, not as an error:
  the button sends the text to the chat as a turn and empties the box. The table
  `generate_data` computes arrives like a data change, with its roles: version 1 in a
  session without data, whose `# changed` block names the generated rows and offers no
  `.undo()`, or the next version over data that exists, which `.undo()` takes back. (#12134)
- **Formula cases in the evals.** The scope judge treats a request to draw a function,
  curve or distribution shape as in scope, never `needs_data` (six new English and
  German scope cases), and the prep eval scores `generate_data` calls on four new
  cases (21 in all): two calls match when they compute the same table. The root's
  step-1 rules now read a user who says how a column is meant to be read ("the dates
  are month first") as a request for a change. (#12134)
