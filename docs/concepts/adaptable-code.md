# Adaptable catalogue code

> **Status (2026-10-09):** design only; nothing is built yet.

This document describes how catalogue implementations become code that you can point at other data: one replaceable data block, columns named once, and plot code that derives everything else from the table. It covers the convention, the checks that enforce it, the pipeline changes, the rollout through the daily regeneration, and how the planned "Use with my data" agent ([Agent network design](agent-network.md)) uses the result.

It draws on a review panel of 2026-10-09 (three proposals, each tested against the repository by two skeptics). Refuted claims appear as non-goals, and the owner's decisions of that day are fixed inputs ([Decisions](#decisions)).

## Why

On 2026-10-09 the owner asked how the implementations can become easier to adapt to other data, both for the agent and for people who copy code from an example, and placed the answer in the implementation rules and the review process. The same code has two consumers:

- **People who copy code from the plot page's code tab.** They have a CSV and read from the top. Today they meet data spread over several Python structures, labels typed as literals, and callouts tied to one sample value.
- **The "Use with my data" agent.** It replaces the data generation with the user's `data.csv`: its working form holds the placeholder `df = load_user_data()`, and its run form substitutes `df = pd.read_csv("data.csv", dtype=..., parse_dates=[...])` ([agent-network.md](agent-network.md), "Adapt and validate"). Every literal that still describes the sample is code the adapter model has to find and rewrite.

### Catalogue state on 2026-10-09

The catalogue has 325 specs in 15 libraries. A read-only scan of the eight Python libraries:

| Library | Files with a `df =` variable | Files with a palette of fewer than 6 entries |
|---|---|---|
| matplotlib | 16 | 56 |
| seaborn | 157 | 63 |
| plotly | 37 | 59 |
| altair | 201 | 65 |
| plotnine | 213 | 64 |
| bokeh | 35 | 53 |
| pygal | 2 | 34 |
| letsplot | 215 | 71 |

Each Python library also has 96 to 124 files with a literal list of five or more numbers and 35 to 74 files that index the palette by a literal position.

The agent's readiness scan, run after its normalizer on the two phase-1 libraries:

| Library | Blocked | Coupled | Clean |
|---|---|---|---|
| matplotlib | 40 | 268 | 17 |
| seaborn | 38 | 267 | 20 |

Blocked means a map spec (13), no `THEME` block, a savefig target other than `f"plot-{THEME}.png"`, or a security-validator finding. A panel prototype of the stricter rules below found no clean matplotlib file and one clean seaborn file, so conversion is catalogue-wide.

Two typical files:

- **`plots/bar-grouped/implementations/python/matplotlib.py` (score 94):** a dict of lists and no table; a 3-entry `IMPRINT` zipped with `strict=True`, which raises for a fourth group; a callout found through `categories.index("Q3")` that prints "Near-tie in Q3".
- **`plots/line-basic/implementations/python/seaborn.py` (score 91):** a long `df`, but the column names repeat as literals, `peak_month = 7` selects the highlight, 12 month labels are typed by hand, and `savefig` uses `bbox_inches="tight"`.

## Decisions

| Topic | Decision (owner, 2026-10-09) |
|---|---|
| Scoring | Score-neutral first. The adaptability check starts as a metadata flag, a generator self-check, and a repair trigger, with no rubric change. A rubric step that reuses CQ-01 for at most 1 point, never a 25th criterion, is a separate decision after a shadow phase proves the check's precision |
| Constant names | Column constants use domain names (`MONTH`, `SALES`), not generic role names (`CATEGORY_COL`), so the code stays readable; a reader who groups by year instead of month renames the constant. Each constant carries a trailing comment naming its spec role, for example `MONTH = "Month"  # role: x`. The checker verifies that every required role has exactly one constant, and the agent rewrites the string value from its bindings. The implementation PR settles the exact comment grammar |
| Libraries | The convention goes into all 15 library prompts: R with `tibble` and `.data[[X]]`, Julia with `DataFrame`, JavaScript as records (later `window.ANYPLOT_DATA`). The deterministic checker exists for Python first; the other languages convert through their prompts alone and stay unverified until their checkers exist |
| Conversion | Only through the normal daily regeneration, one spec per night with all its libraries. No targeted bulk pass, so token spend stays low and the catalogue improves slowly |
| Daily regen | Paused (workflow disabled manually on 2026-10-09) until the rules PR has merged, so no spec is regenerated under half the rules; re-enabled after it, with the first nights watched through the weekly review skill |
| One source of rules | The generator and the agent's adapter load the same convention text verbatim from the prompts. The checker lives once in `core/`, with a single-file mirror for the workflow runner (the parity pattern of `automation/scripts/regen_gate.py` and `core/defects.py`), and the agent's readiness hints come from the same checker |

## The convention

A Python implementation has six zones, top to bottom:

1. **Head.** The docstring header, imports, theme tokens, and the full 8-entry `IMPRINT` in canonical order (`core/palette.py`, l.64). Library setup such as `LetsPlot.setup_html()` or `sns.set_theme(...)` goes here, never into the data block.
2. **`# Constants` (optional).** Values of the plot type or the domain that stay true for any data: thresholds (RSI 30 and 70, a `TARGET` the spec names), ordered scales (weekday names, Likert levels), and semantic color maps looked up with a palette fallback (`SEMANTIC.get(level, IMPRINT[i])`). Never sample categories, sample values, or data coordinates.
3. **Column constants.** One constant per spec `## Data` role the code uses: a domain name, the column name as value (written as the axis title should read, units included), and a trailing `# role: <role>` comment. A variadic family (`y1, y2, ...`) gets one constant holding a list.
4. **Exactly one `# Data` block.** Everything that invents the example: the seed, random draws, literal lists, category names, the formulas behind synthetic data, a `sns.load_dataset` call. It ends in one tidy DataFrame `df` (one row per mark or observation, one column per role, keyed by the column constants), binds nothing else that later code reads, and contains no plotting or styling call. Synthetic data, `np.random.seed(42)`, and "No external files" (`prompts/plot-generator.md`, l.283) stay; a CSV read appears only in the block's comment.
5. **Plot code.** Everything derived goes below the block: pivots, statistics, fits, sorting, positions, widths, limits. It reads only `df`, the column constants, `# Constants`, the theme tokens, and `IMPRINT`.
6. **Output.** `plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)` or the library's equivalent, without `bbox_inches="tight"`.

Four rules govern the plot code:

- **Colors are looked up per category:** `IMPRINT[i]`, `dict(zip(groups, IMPRINT))`, or the library's color cycle. Never `zip(groups, IMPRINT, strict=True)` and never a literal slice sized to the sample; seaborn takes `IMPRINT[:n]` with `n` counted from `df`, because it warns when the palette outnumbers the hue levels. A ninth group fails loudly, matching the style guide's "9+: out of palette, use small multiples" (`prompts/default-style-guide.md`, l.106).
- **Statistics are computed f-strings:** `f"r = {df[HOURS].corr(df[SCORE]):.2f}"`, never `"r = 0.87"`.
- **Callout targets come from a rule over `df`:** `idxmax`, the latest row, the smallest gap between the two leading groups, or the first crossing of a `# Constants` threshold. The text claims only what the rule guarantees, and a conditional claim (a near-tie, a record) is drawn only when `df` meets it.
- **Restraint is unchanged.** Whether a callout exists at all is still decided by "Annotation restraint" (`prompts/plot-generator.md`, l.529) and the `-basic` variant-creep rule (`prompts/quality-criteria.md`, SC-01, l.341). The convention only decides where the choice of target lives; DE-03 is scored on the render as before.

### Example: bar-grouped in matplotlib

The lines of the live file that couple it to its sample:

```python
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]                      # l.23: 3 of 8 positions
categories = ["Q1", "Q2", "Q3", "Q4"]                            # l.26-33: three structures
groups = ["Electronics", "Clothing", "Home & Garden"]
sales_data = {"Electronics": [245, 312, 287, 425], ...}
bar_width = 0.25                                                 # l.38: fixed for 3 groups
for i, (group, color) in enumerate(zip(groups, IMPRINT, strict=True)):  # l.50: a 4th group raises
q3_idx = categories.index("Q3")                                  # l.90: data without "Q3" raises
    "Near-tie in Q3",                                            # l.101: a claim about the sample
ax.set_xlabel("Quarter", fontsize=10, color=INK)                 # l.114-118: labels and ticks
ax.set_xticklabels(categories, fontsize=8, color=INK_SOFT)       #   typed by hand
```

The same chart under the convention, condensed (no shadows, value labels, or chrome styling). It renders 3200 × 1800 in both themes:

```python
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NEAR_TIE = 0.05  # a gap below this share of the tallest bar counts as a near-tie

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: category
PRODUCT_LINE = "Product line"  # role: group
SALES = "Sales (thousand USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
df = pd.DataFrame(
    {
        QUARTER: ["Q1", "Q2", "Q3", "Q4"] * 3,
        PRODUCT_LINE: ["Electronics"] * 4 + ["Clothing"] * 4 + ["Home & Garden"] * 4,
        SALES: [245, 312, 287, 425, 178, 195, 285, 310, 125, 210, 195, 165],
    }
)

# Plot: reads only df and the constants above
table = df.pivot_table(index=QUARTER, columns=PRODUCT_LINE, values=SALES, sort=False, fill_value=0).astype(float)
x = np.arange(len(table.index))
width = 0.8 / len(table.columns)
top = table.to_numpy().max()

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
for i, line in enumerate(table.columns):
    offset = (i - (len(table.columns) - 1) / 2) * width
    ax.bar(x + offset, table[line], width, label=line, color=IMPRINT[i], edgecolor=INK_SOFT, linewidth=1.0)

# Callout: target chosen by a rule over df, drawn only when the claim holds
if len(table.columns) > 1:
    ranked = np.sort(table.to_numpy(), axis=1)
    gaps = ranked[:, -1] - ranked[:, -2]
    tie = int(np.argmin(gaps))
    if gaps[tie] <= NEAR_TIE * top:
        ax.annotate(
            f"Near-tie in {table.index[tie]}",
            xy=(x[tie], ranked[tie, -1]),
            xytext=(0, 14),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=INK_SOFT,
            style="italic",
        )

# Style
ax.set_title("bar-grouped · python · matplotlib · anyplot.ai", fontsize=13, fontweight="bold", color=INK)
ax.set_xticks(x, table.index)
ax.set_xlabel(QUARTER, color=INK)
ax.set_ylabel(SALES, color=INK)
ax.set_ylim(0, top * 1.15)
ax.legend(title=PRODUCT_LINE, fontsize=8)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
```

`sort=False` keeps the data's category order, because a plain `pivot` sorts labels and puts months in alphabetical order. `fill_value=0` and `.astype(float)` are there because a perturbation run of the first draft crashed on the agent loader's nullable dtypes (see [Perturbation smoke run](#perturbation-smoke-run)).

**What you change to use your own CSV:** the three strings and the block.

```diff
-QUARTER = "Quarter"  # role: category
-PRODUCT_LINE = "Product line"  # role: group
-SALES = "Sales (thousand USD)"  # role: value
+QUARTER = "Region"  # role: category
+PRODUCT_LINE = "Channel"  # role: group
+SALES = "Revenue (k EUR)"  # role: value

 # Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")
-df = pd.DataFrame({...})
+df = pd.read_csv("revenue.csv")
```

Renaming `QUARTER` to `REGION` afterwards is a whole-word replace for readability; the chart runs without it.

**What the agent substitutes:** the statements between `# Data` and `# Plot` become `df = load_user_data()` in the working form, and each constant's string comes from the binding of the role its comment names. The run form reads `df = pd.read_csv("data.csv", dtype={"Region": "string", "Channel": "string", "Revenue (k EUR)": "float64"})`. No model edits the code below the block.

### Other libraries

Each library prompt gets one idiom paragraph:

- **seaborn, plotnine, lets-plot, altair:** `data=df` with the column constants (`x=QUARTER`, `aes(x=QUARTER)`, `alt.X(QUARTER, type="nominal")`). Altair escapes field names, because Vega-Lite reads `.` and `[]` as nested access and `:` as a type suffix.
- **plotly:** `px.bar(df, x=QUARTER, ...)`; **bokeh:** `ColumnDataSource(df)`; **pygal:** `df[SALES].tolist()` below the block.
- **ggplot2:** `df <- tibble(...)` in the block, `QUARTER <- "Quarter"  # role: category` above it, `aes(x = .data[[QUARTER]])`, and an explicit `labs()`.
- **Makie:** `df = DataFrame(...)` and `df[!, QUARTER]`.
- **Chart.js, D3, ECharts, Highcharts, MUI X:** `const data = [{...}, ...]` as records, `const QUARTER = "Quarter";  // role: category`, and `data.map((d) => d[QUARTER])`; the agent later substitutes `window.ANYPLOT_DATA`.

## Data shapes

The spec's `## Data` role bullets decide the shape, not the `data_type` tag, which is inconsistent ("time-series" and "timeseries" both occur). The checker computes the shape from the parsed roles plus a short override list kept next to it, in this order:

1. **Table, the default.** Every role is a column of one table, one row per mark, observation, edge, or interval. Many non-tidy-looking shapes are tables: OHLC, ternary components, Sankey, alluvial, and chord edge lists (source, target, value), hierarchies (id, parent, value, or level columns), Gantt (task, start, end), and grids or fields given as long x, y, z observations, pivoted below the block. Model diagnostics take the raw inputs the spec names (`y_true`, `y_score`) and compute the curve below the block. Chart furniture (a Smith-chart grid, a stereonet net) is plot code or `# Constants`.
2. **Matrix.** A role names a matrix (correlation, confusion, adjacency): `df` is a labeled square DataFrame with the row labels as index. When the plot computes the matrix itself, the roles should be the observations, which makes it a table.
3. **Network.** Node and edge role groups: `df` is the edge list, a second `nodes` table exists only when the spec names node attributes, and the layout is computed below the block.
4. **Generated or parametric.** Functions, simulations, encoded text, puzzle layouts (a surface from a formula, Tanabe-Sugano, QR codes, mazes): the block holds named parameters, with no `df` rule and no column constants.
5. **Excluded.** The 13 map specs, which fetch geometry over the network.

One panel prototype counted 278 tables and 47 other specs; another estimated 260 to 275 tables, 12 to 15 matrices, and 40 to 50 generated specs. Both misfiled specs because the role bullets are inconsistent, so a spec-side audit comes first:

- **Matrix roles:** heatmap-correlation lists `correlation_matrix` while its code computes `.corr()` from observations; heatmap-clustered, learning-curve-basic, and pdp-basic are similar.
- **Derived quantities as required roles:** about 38 specs list values the plot computes (moving averages, bands, control limits, residuals, intervals). They become `Derived` bullets, which the role parser already skips.
- **Wide versus long:** line-multi allows `y1, y2, ...` or a `series` column, and its libraries differ; the spec picks one.
- **Families and incomplete structures:** families get list constants; network `edges` roles without source and target, and roc-curve's curve-versus-raw-inputs ambiguity, need retyping.

Retyping a role is a spec change. It goes through the spec pipeline (the nightly spec polish, `prompts/workflow-prompts/spec-polish-claude.md`, or a spec-create update), never through a hand edit of `specification.md`.

## The checks

### Static checker

`core/adaptability.py` uses only the standard library (`ast`), so the workflow runner can run a single-file mirror of it with its system Python; a unit test pins the mirror to the module, as `tests/unit/core/test_defects.py` does for `regen_gate.py`. Its inputs are the source and the spec's roles; the role parser moves from the agent's data modules (PR #12106) into `core/` so the pipeline and the agent share it. For Python it verifies:

1. **Layout:** one block between column-0 `# Data` and `# Plot` marker lines (the marker alone or followed by a colon and a hint), ending in a statement that binds `df`, with no plotting or styling call and no theme token inside.
2. **Columns:** every required column-valued role has exactly one constant with a `# role:` comment, no comment names an unknown role, and every value is a string (or a list of strings for a family). The rule follows the shape: in a table and in a network's edge list every role is column-valued; in a matrix the matrix role is satisfied by `df` itself, a labeled square DataFrame, and only column-valued roles (such as a value label for the color bar) need constants; generated specs need none.
3. **Interface:** no name bound in the block other than `df` is read below it.
4. **Literals below the block:** no string equal to a column constant's value or to a sample category; no statistic written as text; no numeric literal in a data-coordinate position (limits, ticks, reference lines, data-coordinate text, and the libraries' equivalents such as plotly ranges, `alt.Scale(domain=...)`, plotnine `limits=`, bokeh `Range1d`); no comparison of `df` with a literal, also through one alias such as `peak_month = 7`; no count literal equal to `len(df)` or a role's number of unique values.
5. **Palette:** all eight `IMPRINT` positions in order, and no `zip` with `strict=True` over the palette.
6. **`# Constants`:** no list or dict whose values match sample categories or data coordinates, which closes the loophole of hoisting the sample into the head.

Rules 1 and 3 read the block's structure, and rules 4 and 6 use its values as the sample to compare against, but no rule flags a literal inside the block (values, seeds, sizes, category names). The checker also ignores the head, the mandated title and its font-size arithmetic, `savefig`, `figsize`, `dpi`, style numbers, offsets in points or axes fractions, f-strings, comments, seeded jitter sized from `df`, and data-independent constants inside computations (1.96 in a formula).

It reports at most one line per class in the grammar of `core/defects.py`, with the observed value, the lines, the target, and the likely cause, so repair knows the delta:

```text
CQ-01 (code): line 90 selects the callout by the literal "Q3", a value the Data block defines → derive it from df. Likely cause: categories.index("Q3") below the Data block.
```

The lines name CQ-01 because a later rubric step would use it; while the check is score-neutral, the review never copies them and they deduct nothing.

The panel found four false-positive classes, each needing a unit test before a rule binds:

- **Head setup calls:** `LetsPlot.setup_html()` made 316 of 325 lets-plot files fail in one prototype, so each library gets an allowlist of setup calls in the head.
- **Style keywords:** the agent's limits heuristic flags `fontsize=8` in `ax.set_xticks(x, labels, fontsize=8)`; only positional arguments and data keywords count.
- **Altair field names:** an escaped field string (`"U\\.S\\. sales"`) differs from its column name, so the checker treats an escaped column constant as that constant.
- **Auto-labels from column names:** seaborn, plotnine, altair, plotly express, and lets-plot title axes and legends from column names; the checker never demands explicit label calls.

Unit and percentage domains (0 to 1, 0 to 100, 0 to 360), category words that occur in prose ("Total", "Other"), and coincidental counts need tests too. A rule binds only at 90 % precision on a 30-line sample; below that it stays an advisory hint.

### Perturbation smoke run

The static checker tests proxies. A file can pass every rule and still break on other data: a fixed `bar_width = 0.25` overlaps neighboring clusters with five groups, and indexing the second-largest bar raises on a single group. The smoke run tests the property itself, so it is the real test.

It runs the head and the block, derives tables from the sample `df`, and for each one replaces the block, rewrites the column constants through their role comments, and runs the whole file:

- renamed columns, one with spaces, units, and a dot, and renamed category values;
- one more and one fewer category and group, within eight, and a single group;
- a much smaller and a ten times larger row count, and values scaled by 1,000 and shifted;
- the agent loader's dtypes (`string`, `Int64`, `boolean`) with a missing value.

A run passes when it raises nothing, writes both PNGs on the canvas (`core/canvas.py`), and, for matplotlib and seaborn, leaves no text artist showing a renamed sample category. A prototype run of the example above on 2026-10-09:

| Table | Result |
|---|---|
| Catalogue data | Pass, callout "Near-tie in Q3" |
| 5 regions × 4 channels, renamed, values up to 300,000 | Pass, callout moves to "Near-tie in East" |
| Single group, eight groups | Pass, no callout |
| Loader dtypes with a missing value | First draft: `TypeError: boolean value of NA is ambiguous`; pass after `fill_value=0` and `.astype(float)` |
| Nine groups | `IndexError`, by design |

The first draft passed every static rule; only the smoke run found the crash.

The smoke run belongs in impl-generate, because impl-review has no plotting environment and only downloads the renders from staging (`.github/workflows/impl-review.yml`, l.414). The generator runs it as its self-check, and a workflow step runs it again after the generator finishes and uploads the result next to the renders under `gs://anyplot-images/staging/{spec}/{language}/{library}/` (`.github/workflows/impl-generate.yml`, l.986-1010), which impl-review already downloads. On a regeneration it also runs on the predecessor, so the gate compares like with like; impl-repair runs it after every repair. It costs seconds of CPU and no model calls. Python comes first; the other runtimes get the harness with their checkers.

### Non-goals

- **A static pass does not prove adaptability.** In the panel's adapted test renders the code ran on new data, but a legend covered a bar, a near-tie callout fired on a gap of 11 out of 293, and `{:.0f}` labels rounded values between 2 and 9 to whole numbers. Mechanical substitution guarantees that the code runs and plots the right columns, not that the layout suits the data, so the agent keeps its host gates and its reviewer call.
- **Render-identical conversion is rare.** Derived values move things (the example's bar width changes from 0.25 to 0.8 / 3), and a measurement put about 77 % of non-map matplotlib and seaborn files outside render identity. No conversion mode skips the review: every conversion is a normal regeneration with its single review.
- **Layout robustness stays a review judgment** on the sample render: number formats, legend placement, and margins tuned to the sample's labels.

## Pipeline changes

Line numbers refer to `main` on 2026-10-09.

- **Generator prompt, `prompts/plot-generator.md`:** rewrite the Output template (l.118-170) and Structure (l.220) to the six zones; add the rules to Data Generation Strategy (l.232-283); add rule-chosen callout targets to Data storytelling (l.526-531); remove `bbox_inches='tight'` at l.164, l.459, and l.541 and in `prompts/default-style-guide.md` (l.207), which contradict `prompts/library/matplotlib.md` (l.35) and `prompts/library/seaborn.md` (l.34).
- **All 15 library prompts:** one idiom paragraph each ([Other libraries](#other-libraries)); drop the `[:N]` slice in `prompts/library/matplotlib.md` (l.123). The style guide's Color Restraint section (l.95) gets one sentence: list all eight hues, use the first `n`.
- **Generation and repair prompts:** `prompts/workflow-prompts/impl-generate-claude.md` gets a Step 3c next to the Step 3b canvas self-check (l.218) that runs the checker and the smoke run until both are clean; `prompts/workflow-prompts/impl-repair-claude.md` treats checker lines as real defects, like canvas lines.
- **Regen mindset:** amend the five places in `impl-generate-claude.md` that block a decoupling regeneration (next section), and the same sentence in `impl-repair-claude.md` (l.33).
- **impl-generate:** a step runs the smoke run on the new and, on a regeneration, the previous source, and stages the result.
- **impl-review, record-only:** a step after the canvas dimension gate (l.521-614) runs the checker mirror on both sources, reads the staged smoke results, writes `/tmp/anyplot-adapt-new.json` and `/tmp/anyplot-adapt-prev.json`, and emits `::notice::adapt_check spec=... lib=... status=... rules=...`. It never ends in a raw `exit 1` (the canvas gate's comment, l.517-520, gives the reason), and the reviewer never sees it. The mirror joins the regen-tools copy (l.242-255), with a test that keeps the copy list complete.
- **Repair trigger:** on a first generation, the verdict step (l.1916) routes a PR whose check failed to impl-repair once with the checker's lines, even when the score passes. If the repair does not fix it, the implementation merges with the flag set; adaptability never blocks the catalogue. A regeneration has no repair; its check feeds the gate.
- **Regen gate:** the record gains `adapt: {version, prev, new, counted, why}`, plus the adapt route and adapt regression below.
- **Status, `impls.adaptation` (the decision's metadata flag):** an Alembic migration and a change to `automation/scripts/sync_to_postgres.py`, which already reads each implementation's code (l.323) and stores it (l.372), compute the static record at sync time: version, status, findings, block lines, the role-to-constant map, the color-driving role, and the shape. No metadata YAML field and no backfill; a checker version bump recomputes every row on the next sync. The API and MCP payloads expose it.
- **Later, optional:** the CQ-01 rubric step (at most 1 point) with a `review-retest.yml` candidate arm (`docs/workflows/review-retest.md`).

### Why the current gate cannot carry a decoupling regeneration

The only code-only path in `automation/scripts/regen_gate.py` is CQ-04 (`CODE_RULE`, l.271; `classify_code_improvements`, l.1319). It needs a previous `CQ-04 (code)` weakness, which no stored review has for data coupling, a named call used more often, and a strictly shorter source (l.1346), while a decoupling often adds lines. The review prompt counts code-only changes as no improvement (`prompts/workflow-prompts/ai-quality-review.md`, l.285) and lists only CQ-04 weaknesses as code improvements (l.298). The generator is told to leave data code alone, in five places of `impl-generate-claude.md` that each need an amendment:

- l.85, "Keep the data scenario": re-expressing the same values as `df` and column constants keeps the scenario.
- l.86, "leave computations as they are": checker lines are a named code-quality item, like CQ-04.
- l.89, "Do NOT discard working structure / data generation": the data generation keeps its values, not its form.
- l.90, a kept regeneration is the expected outcome when no defect is listed: a failing check is a listed defect.
- l.319, Final Check item 7, "no added code whose effect does not show": the same exception.

A decouple-only regeneration therefore ends as `no_visible_improvement` and is kept today: one generation and one review, wasted.

### The adapt route

The gate computes the route from the two records, never from a reviewer field. It counts when all of these hold:

- the predecessor fails the check (static or smoke) and the new source passes both, all or nothing, so a half-converted pair never merges;
- the review's `scenario_changed` is not true and `encodings_added` is empty, as for the CQ-04 path;
- the new source has at most `max(1.25 × prev, prev + 15)` lines;
- the score tolerance (`new_score >= prev_rescored - 1`) and every regression rule hold.

In `_judge` (l.1368), the two no-carrier exits (l.1440 and l.1446) accept the adapt route as they accept the code path; the CQ-04 path stays as it is. The **adapt regression** applies on every spec: a predecessor that passes and a new source that fails means keep, so converted pairs stay converted. A missing or malformed record turns the route off and records why; it never counts as a pass.

## Rollout

1. **PR 1, the checker, with no pipeline effect:** `core/adaptability.py`, the role parser in `core/`, the shape rule and override list, the runner mirror with its parity test, unit tests for every rule and ignore class, and a `report` CLI. The PR body carries the catalogue baseline and a 30-line precision sample per rule; rules below 90 % become advisory. The daily regeneration stays paused.
2. **PR 2, the rules, in one PR:** the prompts, the smoke-run step, the record-only impl-review step, the repair trigger, the adapt route and regression, and the Regen gate section of `docs/workflows/overview.md`. The review prompt and the rubric do not change, so no retest arm is needed. Workflow edits have no local verification loop, and claude-code-action refuses branch runs of PRs that change its workflows, so the PR is verified on `main`.
3. **Re-enable the daily regeneration:** dispatch `daily-regen.yml` once with `specification_id` set, read the gate records and notices of its pairs, then enable the schedule (02:17 UTC, one spec per night).
4. **Shadow phase:** from PR 2 on, the check acts through the self-check, the repair trigger, and the gate, while scores stay untouched. The weekly review (`/review-regen-week`) adds: adapt status per pair, prev to new; merges split by path (carrier, CQ-04 code, adapt), keeping the 5 to 50 % merge-rate target for the carrier path only; adapt regressions; adapt-route merges counted as carried in "merges without a carrier"; the self-check's first-attempt pass rate per library; smoke failures by perturbation; and checker lines judged false, which is the precision evidence for the rubric decision.
5. **PR 3, status and display, in parallel with the shadow phase:** `impls.adaptation`, the API and MCP fields, the agent's eligibility, and optionally a band on the code tab marking the data block of passing pairs.
6. **Later:** checkers for R, Julia, and JavaScript, then the optional rubric step.

One spec per night means about 325 nights for a full pass, and matplotlib and seaborn convert at the same pace as the rest; until a pair converts, the agent serves it through its adapter model with the checker's lines as hints. Specs regenerated between the 2026-10-08 restart and the pause wait for the next pass.

The cost shape stays that of the daily regeneration: one generation and one Opus review per pair, no extra generations. The checks add seconds of CPU and no model calls. The adapt route turns some kept regenerations into merges, which adds impl-merge runs and website code changes, not model calls. First generations add at most one repair.

## Agent integration

- **Working form:** the agent finds the block by its markers and the AST on the normalized code, never by stored line numbers, because the normalizer strips the header and the `sys.path` guard. It replaces the block with `df = load_user_data()` and rewrites each column constant from the binding of its role (`default_bindings` and `check_bindings`, PR #12106).
- **Mechanical path:** when `impls.adaptation` says pass, the shape is a table, the bindings check passes, and the color-driving role has at most eight values, the agent's first attempt skips the adapter call, one of the four model calls of a typical "Create plot" ([agent-network.md](agent-network.md), l.128). Because `impls.adaptation` holds only the static record, and a static pass does not prove that the code runs on other data, the render on the user's data is the check: when it fails the host gates, the second attempt goes through the adapter with the error as feedback, as in the existing two-attempt loop. Rendering, the host gates, and the reviewer stay.
- **Adapter path:** otherwise the block and the constants are still substituted deterministically, and the adapter gets the checker's lines as hints in place of the readiness scan's heuristics. Its prompt loads the same convention text as the generator.
- **Eligibility:** tables are eligible in phase 1; networks, generated specs, and the 13 map specs are not, because the loader produces one table. Since the block is replaced before anything runs, the security eligibility check can run on the original without the block, so a dataset loader inside it no longer blocks a pair; the agent's readiness PR decides this.

## Open questions

- **The `# Constants` allowlist:** which values may live there, and how the checker tells an ordered scale (weekday names) from hoisted sample categories that happen to be ordered.
- **Columns that are not spec roles:** candlestick examples carry `volume` and a moving average. Is there an optional `# role: extra` constant, or do such columns move below the block?
- **Scenario text that cannot be computed,** such as an event label at a date: a `# Constants` entry drawn only when the date lies inside the data, or not allowed.
- **`df.to_string(buf=...)`:** it writes a file and is not on the agent validator's banned I/O list (PR #12107), while `to_string()` without `buf` returns text a summary table may want. Ban the `buf` keyword in the checker and the validator, or ban the call; no catalogue file uses it on 2026-10-09.
- **R loader:** base `read.csv(..., check.names = FALSE)` with today's R image, or `readr`, which is missing from the R package list (`prompts/plot-generator.md`, l.35) but is what [agent-network.md](agent-network.md) plans for R.
- **Persisting the smoke result:** should impl-merge write the merged version's smoke result forward, with no backfill, so the mechanical path can require it and a static-pass, smoke-fail pair never spends a render on the mechanical attempt?
- **Constant names in exported code:** after substitution the code reads `QUARTER = "Region"`. Is a deterministic rename to a slug of the bound column worth doing?
