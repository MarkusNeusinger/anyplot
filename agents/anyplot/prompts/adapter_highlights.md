## Highlights from the user's data

This section replaces the last sentence of "Keep the plot" under "User plots". You may add **at most one** highlight that points the reader to the most telling feature of the user's data: the maximum or minimum, a clear outlier, a peak, the latest value, the largest group. Add it only when the data has such a feature and pointing it out makes the plot easier to read; a plot without a clear feature gets none.

- Compute its target and its text from `df` (`idx = df[y].idxmax()`, `f"{df[y].max():,.0f}"`), never from literal values, so it stays right for any data.
- Keep it light: one short annotation or one emphasised mark in the existing colors and the style guide's sizes, inside the canvas, without covering data. No new encoding, layer, legend entry or reference line.
- Keep a callout the catalogue code already has only when it follows these rules after your edits; otherwise remove it.
- Name the highlight in `changes`, so the user can ask to remove it.
