## Highlights from the user's data

This section replaces the last sentence of "Keep the plot" under "User plots". Most plots need no highlight, and none is the default. You may add **at most one**, and only when the data shows something a reader would likely miss or that changes how the data reads (a clear outlier, a break or turning point, one group far apart from the rest), so that pointing it out plainly makes the plot more useful. An ordinary maximum or the last value is not enough on its own.

- Compute its target and its text from `df` ({{highlight_compute}}), never from literal values, so it stays right for any data.
- Keep it light: one short annotation or one emphasised mark in the existing colors and the style guide's sizes, inside the canvas, without covering data. No new encoding, layer, legend entry or reference line.
- Keep a callout the catalogue code already has only when it follows these rules after your edits; otherwise remove it.
- Name the highlight in `changes`, so the user can ask to remove it.
