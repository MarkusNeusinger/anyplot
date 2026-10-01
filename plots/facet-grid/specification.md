# facet-grid: Faceted Grid Plot

## Description

A grid of subplots where each cell shows the same type of plot for a different subset of data, split by one or two categorical variables. Enables systematic comparison across multiple dimensions.

## Applications

- Multi-dimensional data exploration
- Comparing patterns across categories
- Conditional distribution analysis
- Publication-ready multi-panel figures

## Data

- `x` (numeric) - First axis variable for the base plot
- `y` (numeric) - Second axis variable for the base plot
- `row_facet` (categorical) - Variable to split rows
- `col_facet` (categorical) - Variable to split columns
- Size: 100–5000 points minimum (sufficient to show variation across facets)
- Example: Palmer Penguins (split by species and island), or any dataset with 2+ categorical grouping variables

## Notes

- All subplots share the same axes scales by default
- Can facet by row, column, or both
- Base plot can be scatter, line, histogram, etc.
- Labels identify each facet's category

## What a good version looks like

- A good version shows: the same kind of base plot in every panel, each panel holding only the data of its own facet category with the marks at their data values, and the panels arranged by row, by column or by both, as the Notes allow.
- A good version shows: the same axis scales in every panel, the default the Notes name, so a position means the same value in each panel and patterns compare directly; where a scale is freed instead, every panel whose scale differs carries its own tick labels.
- A good version shows: a label on every facet that names its category, as the Notes ask: a strip or title per panel, or column headers and row headers when faceting by both, readable in both themes.
- A good version shows: panels of equal size aligned in rows and columns, with gaps wide enough that the tick labels, facet labels and axis titles of neighboring panels stay apart.
- A good version shows: color, if it encodes a variable, mapped the same way in every panel and explained once for the whole figure instead of once per panel.
- Expected, not a defect: panels with very different numbers of points, a sparse or empty panel for a combination the data lacks, unused room in a panel whose subset covers only part of the shared range, and tick labels and axis titles drawn only on the outer panels when scales are shared.
