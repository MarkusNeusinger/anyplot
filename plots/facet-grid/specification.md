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
