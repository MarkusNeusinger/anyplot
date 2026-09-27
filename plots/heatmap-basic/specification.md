# heatmap-basic: Basic Heatmap

## Description

A heatmap displaying values in a matrix format using color intensity. Each cell's color represents the magnitude of the value, making it easy to identify patterns, clusters, and outliers in two-dimensional data. Essential for visualizing correlations, frequencies, and relationships between variables.

## Applications

- Correlation matrices between variables in statistical analysis
- Website click heatmaps showing user behavior patterns
- Gene expression analysis in bioinformatics research
- Performance metrics across time periods and categories

## Data

- `x` (string/numeric) - column labels for the matrix
- `y` (string/numeric) - row labels for the matrix
- `value` (numeric) - cell values for color mapping
- Size: 5-50 rows, 5-50 columns

## Notes

- Use a diverging colormap for data with positive/negative values
- Add value annotations in cells when readable
- Include a colorbar legend
- Order rows/columns logically (alphabetical, by magnitude, or by similarity)

## What a good version looks like

- Every cell is a filled rectangle colored by its value; cells tile the grid without gaps (a thin page-colored separator is fine) and each row and column label sits at its cells.
- The colormap fits the data — sequential for single-signed values, diverging and centered on zero (with the midpoint visible on the color bar) when values cross zero — and a labeled color bar is always present.
- In-cell numbers appear only when the cells are large enough to read them; a large matrix without numbers is correct, not a missing feature, and shown numbers switch color with cell darkness so they stay legible in both themes.
- Rows and columns follow a logical order so blocks and gradients emerge; uneven patches, hot spots and near-empty rows are expected in real data, not noise to smooth away.
- Long row or column labels are rotated or given room, never truncated or overlapping.
