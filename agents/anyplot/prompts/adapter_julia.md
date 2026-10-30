<!--
The Julia runtime's passages of the adapter prompt (Makie, since 2026-10-30, J2b of step 5):
`policy.adapter_prompt("julia")` puts each slot below into the `{{slot}}` of the same name in `adapter.md`,
which holds every rule the languages share, so a shared rule changes in one place. These passages tell the
adapter Julia's conventions: the placeholder `df = load_user_data()` and how the loader types the columns
(`code/profiles/julia/loader.py`; `CSV` and `TimeZones` are the loader's alone), the column constants read as
`df[!, COL]` (the "Data block" of `prompts/library/makie.md`; no catalogue Makie file builds a DataFrame, so
every adaptation introduces it), the protected statements (`code/profiles/julia/regions.py`), what the
validator refuses (`code/profiles/julia/validate.py`), and what Makie 0.24 refuses that the catalogue never
meets: a time column with a `missing` cell, spans and bands on a time axis, text as `barplot!`'s x (measured
in the J1 image on 2026-10-29 and 2026-10-30). `tests/unit/agents/runtime/test_policy.py` runs the idioms
through both validator profiles, and `tests/unit/agents/code/test_profile_julia_image.py` renders them. A slot
runs from its `slot:` comment to the next one; the blank lines around it are not part of it. This comment
never reaches a model.
-->

<!-- slot: request_formatter -->
a tick format such as `ytickformat = values -> [fmt(v / 1e6; digits = 1) * " Mio." for v in values]` (`fmt` as under **Numbers** below) that writes the decimal comma and the unit

<!-- slot: requested_check -->
A Julia render has no probe, so the server cannot read its drawn texts back: the reviewer looks for each requested text in the image instead, and reports one it cannot find, which then comes back to you as a finding.

<!-- slot: measured_hints -->
A Julia render has no probe, so no hint is ever a target measured on a render: every hint quotes the code.

<!-- slot: density_check -->
A Julia render has no probe, so no gate counts the labels for you: the host gates judge only its output, the PNG and its canvas, so count the marks from `df` yourself.

<!-- slot: data_statement -->
The code is Julia (Makie 0.24 with CairoMakie). The data comes from exactly one statement at the top level:

```julia
df = load_user_data()
```

It returns a DataFrame with exactly the loader columns under their exact names, spaces, units and punctuation included, typed: `integer` as `Int64`, `number` as `Float64`, `boolean` as `Bool`, `text` as `String`, and `datetime` columns already parsed, plain dates as `Date` and timestamps as `DateTime` in UTC (an offset converted, digits below the millisecond cut, since a `DateTime` holds milliseconds). A missing cell is `missing`, and its column's type admits it (`Union{Missing, Float64}`). The server replaces the statement with a `CSV.read("data.csv", ...)` read when it runs the code, so never write that read, or any other read of a file, yourself, and never load `CSV` or `TimeZones`: they belong to that read.

<!-- slot: data_columns -->
- When the working form has no `df = load_user_data()` line yet (the first attempt), replace the block that creates the example data (`Random.seed!`, random draws, literal vectors of values, the formulas behind the invented data, a dataset package, and the construction of the example vectors) with that single line, and rewrite the plot code to read from `df`. The catalogue's Makie files draw from plain vectors (`x`, `y`, `sales`), never from a DataFrame, so rewrite every use of such a vector to the column it stands for.
- Name each column once, in a column constant set to its exact bound name, as the library rules' "Data block" below shows: `const REVENUE = "Revenue (EUR)"  # role: y`. Keep the constants the code has, set their values to the bound columns, and add one for a column the code does not name yet. Write the name as a Julia string, with `\"`, `\\` and `\$` for a quote, a backslash and a dollar sign: a bare `$` interpolates. Read every column through its constant, as `df[!, REVENUE]`, never by a field (`df.Revenue`) or a bare name, which break on a column name with a space or a unit. Add `using DataFrames` to the `using` lines when the code calls its functions (`dropmissing`, `groupby`, `combine`, `nrow`).

<!-- slot: data_order -->
- Keep the data's first-appearance order for categories (`unique(df[!, GROUP])`, `groupby(df, GROUP; sort = false)`), never a sorted order, unless they are ordered (ordinal) categories, such as sizes, ratings, age bands or month and weekday names, which keep their natural order. A sort the spec asks for (bars by value) still applies.
- Categories go on an axis as integer positions with their labels as ticks, as the catalogue draws them: `barplot!(ax, 1:length(groups), values)` with `xticks = (1:length(groups), groups)`, and each row's position as `[findfirst(==(g), groups) for g in df[!, GROUP]]`. `barplot!` refuses text as x.
- A column with a missing cell keeps `missing` there. Drop the rows a mark needs with `dropmissing(df, [X, Y])`, which also narrows the columns' types, never with `filter`, which leaves them as they are, and reduce with `skipmissing` (`maximum(skipmissing(df[!, Y]))`). A number column with a gap plots, but a `Date` or `DateTime` column with a `missing` cell fails the render (`MethodError: no method matching create_dim_conversion(::Type{Union{Missing, Dates.Date}})`), so drop those rows and say so in `changes`.
- Never create data: no random draws to make values (`randn`, `randexp`; `Random.seed!` with `rand`, `shuffle` or `randperm` only for jitter or subsampling is allowed), no literal vectors of more than 20 numbers, no dataset package (`RDatasets`, `PalmerPenguins`: its `using` line goes with the data block, and the server refuses code that keeps it), no file reads, no downloads.

<!-- slot: protected_lines -->
- the `const THEME = get(ENV, "ANYPLOT_THEME", "light")` line (with or without `const`) and every theme token, a top-level name set to fixed values per theme, such as `const PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"` (`PAGE_BG`, `ELEVATED_BG`, `INK`, `INK_SOFT`, `INK_MUTED`, `GRID`, `BRAND`, ...). A line that picks a value from the data by theme, or one whose branches call a function such as `RGBAf(...)`, is ordinary plot code that you may change;
- the `df = load_user_data()` line once it exists. Keep it out of `find` and `replace`, also to append to it: to transform `df` or add statements after it, use the line below it as `find` and write the new statements in front of that line in `replace`;
- the final `save("plot-$(THEME).png", fig; px_per_unit = ...)` statement, every line of it.

Each of these statements is assigned once and stands alone on its lines: never assign `THEME` or a theme token again, never put other code on their lines, and never define a function or a variable named `save` or `get`.

<!-- slot: canvas -->
The canvas is fixed by the server: never change the `size` of the `Figure` or the arguments of the final `save` (its file name, the figure and `px_per_unit`), so the plot it saves keeps its name and its pixels, never use the old `resolution` keyword, never call `save` again, `display(fig)` or `resize_to_layout!`, and keep the title in the call that shows it (the axis's `title =` or a `Label`).

<!-- slot: palette_literal -->
one literal vector of colour literals in the form the code writes them (`colorant"#009E73"`, or plain `"#009E73"` strings)

<!-- slot: palette_builders -->
`vcat`, `repeat`, an index or a range, `push!` or `append!`, a comprehension or a loop

<!-- slot: palette_lookup -->
`IMPRINT_PALETTE[i]` over the groups found in `df`: `colors = IMPRINT_PALETTE[1:length(groups)]`, or `color = IMPRINT_PALETTE[group]` with each row's group position

<!-- slot: ink_muted -->
const INK_MUTED = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

<!-- slot: computed_text -->
a string built with `fmt` (under **Numbers** below: `"r = " * fmt(cor(df[!, X], df[!, Y]))`, written with the column constants of the code, `cor` from `Statistics`)

<!-- slot: number_formatting -->
Julia's `@sprintf` and `string` write `.` for decimals and no thousands mark, and `Printf` has no grouping flag: format through one function,

<!-- slot: number_output -->
`en`: `"."` and `","`): `fmt(v; digits = 2) = (v < 0 ? "-" : "") * replace(@sprintf("%.*f", digits, abs(v)), r"(?<=\d)(?=(?:\d{3})+(?:\.|$))" => THOUSANDS, "." => DECIMAL)` (with `using Printf`), as the axis's `ytickformat = values -> fmt.(values)` and for value labels and annotations (`text = fmt(v)`), never a bare `@sprintf("%.2f", v)` or `string(v)`, which always write a point. Years, dates, identifiers and the cells of the user's data stay as they are. A plot language the table does not list keeps the catalogue's formats. No gate checks the decimal marks of a Julia render, which has no probe, so the code alone keeps them right.

<!-- slot: dates -->
A `Date` or `DateTime` column goes on an axis as it is for `lines!`, `scatter!`, `barplot!`, `text!` and `hlines!`: Makie writes the date ticks itself, so give it no fixed ticks unless the change request asks for specific ones. Spans, bands and vertical lines (`vspan!`, `hspan!`, `vlines!`, `band!`) fail the render on such an axis in any order ("Cannot change dim conversion"): when the plot draws one, put the time on the axis as numbers, as the catalogue does (`days = Dates.value.(df[!, DAY] .- first(df[!, DAY]))`: days for a `Date`, milliseconds for a `DateTime`), with ticks taken from the data (`xticks = (days[1:step:end], Dates.format.(df[!, DAY][1:step:end], "yyyy-mm-dd"))`, a `step` that leaves about six). `Dates.format` writes month and weekday names in English, so use numeric formats unless the plot language is English.

<!-- slot: safe_code -->
Load only the packages the code already has, plus, when needed, `CairoMakie`, `Makie`, `Colors`, `ColorSchemes`, `DataFrames`, `Statistics`, `Random`, `Dates`, `Printf` and `LinearAlgebra`, each with `using` and its single name (`using Statistics: mean` may select names); never `import X as Y`, a dotted path (`using CairoMakie.Cairo`), `CSV` or `TimeZones` (only the server's loader reads with them), a dataset package or any other package. No file, network or process access and no environment: no `run`, backtick commands, `open`, `read`, `write`, `readlines`, `download`, `include`, `rm`, `cp`, `mkdir`, `cd`, file tests such as `isfile`, `ENV` beyond the THEME line, `display`, `load` or `record`, and no `save` but the final one. No evaluation or reflection: no `eval`, `@eval`, `Meta.parse`, `include_string`, `invokelatest`, `getfield`, `getproperty`, `setfield!`, `ccall`, `unsafe_*`, `Core`, `Main`, `Sys` or `Base.Libc`, and no `macro` or `module` definition. Call a function by its name or as `Package.name` (`Random.seed!`, `Dates.value`), never through a value in parentheses, an index or a field (`(f)(x)`, `fs[1](x)`, `obj.f(x)`); the only macros are `@.`, `@sprintf`, `@printf`, `@views`, `@view`, `@inbounds`, `@assert` and the logging ones, and the only string macros `colorant"..."`, `L"..."` (without `%$`), `dateformat"..."`, `r"..."` and `raw"..."`. String interpolation (`"$(...)"`) runs code, so the same rules hold inside it. No URL and no string literal longer than 200 characters.

<!-- slot: placeholder -->
df = load_user_data()

<!-- slot: highlight_compute -->
`peak, idx = findmax(skipmissing(df[!, Y]))`, `fmt(peak; digits = 0)`
