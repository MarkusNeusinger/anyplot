<!--
The Python runtime's passages of the adapter prompt: `policy.adapter_prompt("python")` puts each
slot below into the `{{slot}}` of the same name in `adapter.md`, which holds every rule the
languages share. The result is byte for byte the adapter prompt as it was before R joined on
2026-10-29 (`tests/unit/agents/runtime/test_policy.py` pins its SHA-256). A slot runs from its
`slot:` comment to the next one; the blank lines around it are not part of it. This comment never
reaches a model.
-->

<!-- slot: request_formatter -->
a `FuncFormatter` that writes the decimal comma and the unit

<!-- slot: requested_check -->
The server checks the drawn texts of the render for each of them.

<!-- slot: measured_hints -->
On a repair attempt a hint can also be a target the server measured on the last render, such as the angle for a polar plot's radial tick labels (`ax.set_rlabel_position(...)`): apply it with exactly that value, never one of your own.

<!-- slot: density_check -->
The server measures this (a `VQ-03` gate line counts the labels, the decorations and the pixels each label has).

<!-- slot: data_statement -->
The data comes from exactly one statement at module level:

```python
df = load_user_data()
```

It returns a pandas DataFrame with exactly the loader columns, typed: `integer` as `Int64`, `number` as `float64`, `boolean` as `boolean`, `text` as `string`, and `datetime` columns already parsed to `datetime64`. Missing values are `<NA>` or `NaT`. The server replaces the statement with a `pd.read_csv("data.csv", ...)` call when it runs the code, so never write that call yourself.

<!-- slot: data_columns -->
- When the working form has no `df = load_user_data()` line yet (the first attempt), replace the block that creates the example data (the seed, random draws, literal lists of values, the formulas behind the invented data, and the construction of the example DataFrame or arrays) with that single line, and rewrite the plot code to read from `df`.
- Address columns only by subscript with the exact bound name: `df["Revenue (EUR)"]`, never `df.Revenue`.

<!-- slot: data_order -->
- Keep the data's first-appearance order for categories (`df[col].unique()`, `groupby(..., sort=False)`), never an alphabetical sort, unless they are ordered (ordinal) categories, such as sizes, ratings, age bands or month and weekday names, which keep their natural order. A sort the spec asks for (bars by value) still applies.- Never create data: no random draws to make values (a seeded `np.random.default_rng(<int>)` used only with `.choice`, `.permutation` or `.uniform` for jitter or subsampling is allowed), no literal lists of more than 20 numbers, no file reads, no downloads.

<!-- slot: protected_lines -->
- the `THEME = os.getenv("ANYPLOT_THEME", ...)` line and every theme token, a module-level name set to fixed values per theme, such as `PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"` (`PAGE_BG`, `ELEVATED_BG`, `INK`, `INK_SOFT`, `INK_MUTED`, `GRID`, `BRAND`, ...). A line that picks a value from the data by theme, such as `label_color = INK if THEME == "dark" else IMPRINT[i]`, is ordinary plot code that you may change;
- the `df = load_user_data()` line once it exists. Keep it out of `find` and `replace`, also to append to it: to transform `df` or add statements after it, use the line below it as `find` and write the new statements in front of that line in `replace`;
- the final `savefig` statement.

<!-- slot: canvas -->
The canvas is fixed by the server: never change `figsize`, `dpi`, `set_size_inches` or the `savefig` arguments, and never add `bbox_inches`.

<!-- slot: palette_literal -->
one literal list of color strings

<!-- slot: palette_builders -->
a slice, `+`, `*`, a loop or a comprehension

<!-- slot: palette_lookup -->
`IMPRINT[i]` over the groups found in `df`, or `colors = IMPRINT[: len(groups)]`

<!-- slot: ink_muted -->
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

<!-- slot: computed_text -->
an f-string (`f"r = {df[x].corr(df[y]):.2f}"`, written with the column variables of the code)

<!-- slot: number_formatting -->
Python's `locale` is not available: format with an f-string, which writes `,` for thousands and `.` for decimals, then swap both marks through a placeholder: `f"{v:,.2f}".replace(",", "_").replace(".", DECIMAL).replace("_", THOUSANDS)`,

<!-- slot: number_output -->
`en` keeps the f-string as it is), through a `matplotlib.ticker.FuncFormatter` for the axes and the same function for value labels (`ax.bar_label(container, labels=[...])`, never `fmt="%.2f"`, which always writes a point). Years, dates, identifiers and the cells of the user's data stay as they are. A plot language the table does not list keeps the catalogue's formats. The server checks the decimal mark of every numeric tick label and annotation (a `VQ-06` gate line).

<!-- slot: dates -->
Use `matplotlib.dates.AutoDateLocator` with `ConciseDateFormatter` instead of a fixed locator, unless the change request asks for a specific one.

<!-- slot: safe_code -->
Use only the imports the code already has, plus, when needed, `numpy`, `pandas`, the plotting library, scipy's computing modules (`scipy.stats`, `scipy.interpolate`, `scipy.signal`, `scipy.optimize`, `scipy.fft`, `scipy.linalg`, ...) and these standard modules: `math`, `cmath`, `statistics`, `decimal`, `fractions`, `numbers`, `datetime`, `calendar`, `zoneinfo`, `collections`, `itertools`, `functools`, `operator`, `bisect`, `heapq`, `typing`, `warnings`, `textwrap`, `colorsys` and `re`. Never import `io`, `sys`, `pathlib`, `random`, `locale` or `string`. No file or network access, no `os` beyond the THEME line, no `.format(...)` (use f-strings), no `eval`, `exec`, `getattr`, `operator.attrgetter` or other reflection, no names with double underscores or private names of a module (`module._name`), no `class` statements, and no string literal longer than 200 characters.

<!-- slot: placeholder -->
df = load_user_data()

<!-- slot: highlight_compute -->
`idx = df[y].idxmax()`, `f"{df[y].max():,.0f}"`
