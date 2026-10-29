<!--
The R runtime's passages of the adapter prompt (ggplot2, since 2026-10-29): `policy.adapter_prompt("r")`
puts each slot below into the `{{slot}}` of the same name in `adapter.md`, which holds every rule the
languages share, so a shared rule changes in one place. These passages tell the adapter R's conventions:
the placeholder `df <- load_user_data()` and how the loader types the columns (`code/profiles/r/loader.py`),
the column constants read through `.data[[...]]` (the convention of `prompts/adaptable-code.md`, which the
library rules' "Data block" section shows in R), the protected statements (`code/profiles/r/regions.py`),
and what the validator refuses (`code/profiles/r/validate.py`: the packages, dataset packages among them,
and the routes to files, processes and evaluation). A slot runs from its `slot:` comment to the next one;
the blank lines around it are not part of it. This comment never reaches a model.
-->

<!-- slot: request_formatter -->
a scales labeller such as `scales::label_number(scale = 1e-6, accuracy = 0.1, decimal.mark = ",", big.mark = ".", suffix = " Mio.")` that writes the decimal comma and the unit

<!-- slot: requested_check -->
An R render has no probe, so the server cannot read its drawn texts back: the result marks the requested texts as not checked, and only your code makes them right.

<!-- slot: measured_hints -->
An R render has no probe, so no hint is ever a target measured on a render: every hint quotes the code.

<!-- slot: density_check -->
An R render has no probe, so no gate counts the labels for you: the host gates judge only its output, the PNG and its canvas, so count the marks from `df` yourself.

<!-- slot: data_statement -->
The code is R. The data comes from exactly one statement at the top level:

```r
df <- load_user_data()
```

It returns a tibble with exactly the loader columns under their exact names, spaces, units and punctuation included, typed: `integer` as integer (a column with whole numbers past 32 bits as double), `number` as double, `boolean` as logical, `text` as character, and `datetime` columns already parsed, plain dates as `Date` and timestamps as `POSIXct` in UTC. Missing values are `NA`. The server replaces the statement with a `readr::read_csv("data.csv", ...)` call when it runs the code, so never write that call, or any other read of a file, yourself.

<!-- slot: data_columns -->
- When the working form has no `df <- load_user_data()` line yet (the first attempt), replace the block that creates the example data (`set.seed()`, random draws, literal vectors of values, the formulas behind the invented data, a dataset package or a built-in dataset, and the construction of the example tibble) with that single line, and rewrite the plot code to read from `df`.
- Name each column once, in a column constant set to its exact bound name, as the library rules' "Data block" below shows: `REVENUE <- "Revenue (EUR)"  # role: y`. Keep the constants the code has, set their values to the bound columns, and add one for a column the code does not name yet. Read every column through its constant, never by a bare name: `.data[[REVENUE]]` inside `aes()`, `vars()` and the dplyr and tidyr verbs, `all_of(c(MONTH, REGION))` where a verb takes several columns, and `df[[REVENUE]]` everywhere else. A bare name (`aes(x = Revenue)`, `df$Revenue`) breaks on a column name with a space or a unit.

<!-- slot: data_order -->
- Keep the data's first-appearance order for categories (`factor(x, levels = unique(x))` before the plot maps the column), never the alphabetical order ggplot2 gives a character column on an axis and in a legend, unless they are ordered (ordinal) categories, such as sizes, ratings, age bands or month and weekday names, which keep their natural order. A sort the spec asks for (bars by value) still applies.
- Never create data: no random draws to make values (`rnorm()` and the other `r*()` draws; `set.seed()` with `sample()`, `runif()` or `jitter()` only for jitter or subsampling is allowed), no literal vectors of more than 20 numbers, no `data()` and no built-in dataset (`mtcars`, `iris`, `economics`, ...), no dataset package (`gapminder`, `palmerpenguins`: its `library()` call goes with the data block, and the server refuses code that keeps it), no file reads, no downloads.

<!-- slot: protected_lines -->
- the `THEME <- Sys.getenv("ANYPLOT_THEME", "light")` line and every theme token, a top-level name set to fixed values per theme, such as `PAGE_BG <- if (THEME == "light") "#FAF8F1" else "#1A1A17"` (`PAGE_BG`, `ELEVATED_BG`, `INK`, `INK_SOFT`, `INK_MUTED`, `GRID`, `BRAND`, ...). A line that picks a value from the data by theme, such as `label_color <- if (THEME == "dark") INK else IMPRINT_PALETTE[i]`, is ordinary plot code that you may change;
- the `df <- load_user_data()` line once it exists. Keep it out of `find` and `replace`, also to append to it: to transform `df` or add statements after it, use the line below it as `find` and write the new statements in front of that line in `replace`;
- the final `ggsave(...)` statement, every line of it.

Each of these statements is assigned once and stands alone on its lines: never assign `THEME` or a theme token again, and never put other code on their lines.

<!-- slot: canvas -->
The canvas is fixed by the server: never change the arguments of the final `ggsave()` (`filename`, `plot`, `device`, `width`, `height`, `units`, `dpi`, `bg`), so the plot it saves keeps its name, never call `ggsave()` again or open another graphics device, and never `print()` the plot.

<!-- slot: palette_literal -->
one literal `c()` of color strings

<!-- slot: palette_builders -->
`rep()`, a subset, `c()` around the name, a replacement such as `IMPRINT_PALETTE[9] <- ...`, a loop or `sapply()`

<!-- slot: palette_lookup -->
`IMPRINT_PALETTE[seq_along(groups)]` over the groups found in `df`, named with `setNames(..., groups)` for `scale_fill_manual(values = ...)`

<!-- slot: ink_muted -->
INK_MUTED <- if (THEME == "light") "#6B6A63" else "#A8A79F"

<!-- slot: computed_text -->
`paste0()` with `scales::number()` (`paste0("r = ", scales::number(cor(df[[X]], df[[Y]], use = "complete.obs"), accuracy = 0.01, decimal.mark = DECIMAL))`, written with the column constants of the code)

<!-- slot: number_formatting -->
R's `sprintf()`, `format()` and `round()` write `.` for decimals: format through scales, which takes both marks,

<!-- slot: number_output -->
`en`: `"."` and `","`): `scales::label_number(accuracy = 0.01, decimal.mark = DECIMAL, big.mark = THOUSANDS)` as the `labels =` of an axis scale, and `scales::number(x, accuracy = 0.01, decimal.mark = DECIMAL, big.mark = THOUSANDS)` for value labels and annotations, never `sprintf("%.2f", x)`, which always writes a point. Years, dates, identifiers and the cells of the user's data stay as they are. A plot language the table does not list keeps the catalogue's formats. No gate checks the decimal marks of an R render, which has no probe, so the code alone keeps them right.

<!-- slot: dates -->
Use `scale_x_date()` (`scale_x_datetime()` for timestamps) with `breaks = scales::breaks_pretty()` and `labels = scales::label_date_short()` instead of fixed breaks or a fixed `date_breaks`, unless the change request asks for specific ones.

<!-- slot: safe_code -->
Attach only the packages the code already has, plus, when needed, `ggplot2`, `dplyr`, `tidyr`, `tibble`, `scales`, `patchwork`, `grid`, `gridExtra`, `MASS`, `cluster`, `survival`, `class` and R's own `stats`, `grDevices`, `graphics` and `splines`, each with `library()` and its bare name; use `pkg::name` only for those packages, `utils::head` and `tools::toTitleCase`, and never `:::`. Never use `readr` (only the server's loader reads with it), a dataset package or any other package. No file, network or process access and no settings or environment variables: no `system()`, `file()`, `url()`, `download.file()`, `source()`, `load()`, `readRDS()`, `readLines()`, `read.*`, `write*`, `file.*`, `sink()` or `options()`, no `file =` argument, no `Sys.*` but `Sys.time()` and `Sys.Date()` (`Sys.getenv()` only in the THEME line), and no graphics device but the final save (`pdf(NULL)` for measuring text is fine). No evaluation or reflection: no `eval()`, `parse()`, `get()`, `exists()`, `assign()`, `match.fun()`, environments, `<<-`, or `do.call()` beyond `rbind`, `cbind`, `c`, `paste` and `paste0`. Call a function by its name, never through a string, an index or a field (`f[[1]](x)`, `obj$f(x)`), and where an argument takes a function (`FUN`, `.f`, `labeller`, `transform`) pass a function literal, `\(x)`, a `~` lambda or a function's name. Tidy evaluation only on column constants: `!!` and the left side of `:=` take a constant bound once to a string, `.names` only `{.col}` or `{.fn}`, and a facet takes `vars(.data[[GROUP]])`. Write a formula (`y ~ x`) out, never build one with `paste0()` or `sprintf()`. No URL and no string literal longer than 200 characters.

<!-- slot: placeholder -->
df <- load_user_data()

<!-- slot: highlight_compute -->
`idx <- which.max(df[[Y]])`, `scales::number(max(df[[Y]], na.rm = TRUE), accuracy = 1, big.mark = THOUSANDS)`
