# Adaptable code

Every implementation is code that someone points at other data. A reader copies it from the plot page and swaps in a CSV; the "Use with my data" agent replaces the sample with the user's table. Write it so that one replaceable block holds the sample, each column is named once, and the plot code derives everything else from the table.

This file is the convention, in one place. `prompts/plot-generator.md` applies it, and each `prompts/library/{library}.md` has a "Data block" section with the library's idiom. For Python, a static checker and a perturbation smoke run test it: the generator runs both as its self-check (`prompts/workflow-prompts/impl-generate-claude.md`, Step 3c). R, Julia and JavaScript follow the same convention without a checker yet.

## The six zones

A Python implementation has six zones, top to bottom:

1. **Head.** The docstring header, the imports, the theme tokens, and the palette: the full 8-entry `IMPRINT` list in canonical order (the style guide's `IMPRINT_PALETTE` is the same list; the checker reads both names), or `BRAND` alone for a single-series plot. Library setup goes here, never into the data block: `sns.set_theme(...)`, `LetsPlot.setup_html()`, `theme_set(...)`, an Altair theme. No figure is created and nothing is plotted here.
2. **`# Constants`, optional.** Values of the plot type or the domain that stay true for any data: thresholds (RSI 30 and 70, a target the spec names), ordered scales (weekday names, Likert levels), and semantic color maps looked up with a palette fallback (`SEMANTIC.get(level, IMPRINT[i])`). Never sample categories, sample values or data coordinates.
3. **Column constants.** One constant per spec `## Data` role the code uses: a domain name (`MONTH`, `SALES`, never `CATEGORY_COL`), the column name as its value, written the way the axis title should read with the unit included, and a trailing role comment: `SALES = "Sales (thousand USD)"  # role: value`. A variadic family (`y1, y2, ...`) gets one constant that holds a list. A column that no spec role names gets `# role: extra`.
4. **Exactly one `# Data` block.** Everything that invents the example: the seed, random draws, literal lists, category names, the formulas behind synthetic data, a `sns.load_dataset` call. It ends in one tidy DataFrame `df`: one row per mark or observation, one column per role, keyed by the column constants. It binds nothing else that later code reads, and it holds no plotting or styling call and no theme token. The data stays synthetic and in memory; a CSV read appears only in the block's opening comment.
5. **Plot code, below a `# Plot` marker.** Everything derived: pivots, statistics, fits, sorting, positions, widths, limits. It reads only `df`, the column constants, `# Constants`, the theme tokens and the palette.
6. **Output.** `plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)` or the library's equivalent, never with `bbox_inches="tight"`.

The markers are comment lines at column 0: `# Data` and `# Plot`, the word alone or followed by a colon and a hint, such as `# Data: replace this block with your own table, for example df = pd.read_csv("sales.csv")`. The role in `# role: <role>` is the backticked name of the spec's `## Data` bullet (`category`, `value`); the family `y1, y2, ...` is the role `y`. Other comments, such as `# Style`, are free.

## Rules for the plot code

- **Colors are looked up per category:** `IMPRINT[i]`, `dict(zip(groups, IMPRINT))`, or the library's color cycle fed the full list. Never `zip(groups, IMPRINT, strict=True)` and never a literal slice sized to the sample (`IMPRINT[:3]`). seaborn takes `IMPRINT[:n]` with `n` counted from `df`, because it warns when the palette outnumbers the hue levels. A ninth group fails loudly, which matches the style guide's "9+: out of palette, use small multiples".
- **Labels, ticks and limits come from `df` and the constants:** `ax.set_xlabel(QUARTER)`, `ax.set_xticks(x, table.index)`, `ax.set_ylim(0, top * 1.15)`. Below the block, never type a column name, a sample category, or a data coordinate (a limit, a tick, a reference-line position, a text position in data units). Text placed in axes fractions or offset points is fine, and so are fixed domains such as 0 to 1, 0 to 100 and 0 to 360.
- **Statistics are computed f-strings:** `f"r = {df[HOURS].corr(df[SCORE]):.2f}"`, never `"r = 0.87"`.
- **Callout targets come from a rule over `df`:** `idxmax`, the latest row, the smallest gap between the two leading groups, or the first crossing of a `# Constants` threshold. Never a literal such as `categories.index("Q3")`, and never a comparison such as `df[MONTH] == 7`, also not through an alias like `peak_month = 7`. The text claims only what the rule guarantees, and a conditional claim (a near-tie, a record) is drawn only when `df` meets it.
- **Counts come from `df`:** `range(len(table))`, `np.arange(df[MONTH].nunique())`, never `range(12)` for twelve sample months.
- **A missing value stays missing.** A user's table can hold `NaN` in a number column, and the agent's loader hands categories over as pandas `string` columns and integers as nullable `Int64`. Never fill a drawn value with zero (`fill_value=0`, `fillna(0)`); reduce with NaN-aware calls (`np.nanmax`, `Series.max()`) and let the library skip the mark.
- **Category order is the data's order:** `pivot_table(..., sort=False)`, `groupby(..., sort=False)`. A plain `pivot` sorts the labels and puts months in alphabetical order.
- **Restraint is unchanged.** Whether a callout exists at all is still decided by "Annotation restraint" in `prompts/plot-generator.md` and by the `-basic` variant rule. The convention only decides where the choice of target lives.

## Data shapes

The spec's `## Data` role bullets decide what `df` is:

- **Table, the default.** Every role is a column of one table, one row per mark, observation, edge or interval. OHLC rows, Sankey and chord edge lists (source, target, value), hierarchies (id, parent, value), Gantt tasks (task, start, end), and grids given as long x, y, z observations are tables, pivoted below the block. Model diagnostics take the raw inputs the spec names (`y_true`, `y_score`) and compute the curve below the block.
- **Matrix.** A role names a matrix (correlation, confusion, adjacency): `df` is a labeled square DataFrame with the row labels as its index, and only the column-valued roles, such as a value label for the color bar, get constants. When the plot computes the matrix itself, its roles are the observations and the shape is a table.
- **Network.** Node and edge roles: `df` is the edge list, a second `nodes` table exists only when the spec names node attributes, and the layout is computed below the block.
- **Generated.** Functions, simulations, encoded text and puzzle layouts (a surface from a formula, a QR code, a maze): the block holds named parameters, with no `df` and no column constants.
- **Maps** fetch their geometry over the network and are exempt.

The self-check prints the shape it reads from the spec.

## Example: bar-grouped in matplotlib

Condensed: no shadows, value labels or chrome styling. It renders 3200 × 1800 in both themes.

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
table = df.pivot_table(index=QUARTER, columns=PRODUCT_LINE, values=SALES, sort=False)
x = np.arange(len(table.index))
width = 0.75 / len(table.columns)
top = np.nanmax(table.to_numpy())

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
for i, line in enumerate(table.columns):
    offset = (i - (len(table.columns) - 1) / 2) * width
    ax.bar(x + offset, table[line], width, label=line, color=IMPRINT[i], edgecolor=INK_SOFT, linewidth=1.0)

# Callout: target chosen by a rule over df, drawn only when the claim holds
if len(table.columns) > 1:
    ranked = np.sort(np.nan_to_num(table.to_numpy(), nan=-np.inf), axis=1)
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

`sort=False` keeps the data's category order. The pivot has no `fill_value`: a group that is missing in a quarter stays `NaN` and matplotlib skips the bar instead of drawing a zero. The axis maximum and the ranking skip those cells (`np.nanmax`, and `-inf` for a missing group), so a missing cell neither raises on the axis limit nor fakes a near-tie. `0.75 / len(table.columns)` gives the width of 0.25 that a hand-tuned file would use for three groups, and narrower bars for more.

To use your own CSV, change the three strings and the block:

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

## Other languages

R, Julia and JavaScript use the same zones with their own comment syntax:

| Language | Markers | Role comment | The block ends in |
|---|---|---|---|
| R (ggplot2) | `# Data`, `# Plot` | `QUARTER <- "Quarter"  # role: category` | `df`, a `tibble` keyed by the constants |
| Julia (Makie) | `# Data`, `# Plot` | `const QUARTER = "Quarter"  # role: category` | `df`, a `DataFrame` keyed by the constants |
| JavaScript | `// Data`, `// Plot` | `const QUARTER = "Quarter";  // role: category` | `const data`, an array of records, one object per row keyed by the constants |

The rules for the plot code apply unchanged: colors per category from the palette, labels and limits from the data, callout targets from a rule. Each library prompt's "Data block" section shows the idiom. No checker runs on these languages yet, so the convention applies to new files; on a regeneration it is no reason to rewrite working data code.
