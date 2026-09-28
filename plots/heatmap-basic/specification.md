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

- A good version shows: every cell as a filled rectangle colored by its value, tiling the grid without gaps other than an optional thin page-colored separator, with each row and column label at its cells.
- A good version shows: a colormap that fits the data (sequential for single-signed values, diverging and centered on zero with the midpoint visible on the color bar when values cross zero) and a labeled color bar.
- A good version shows: in-cell numbers only when the cells are large enough to read them, switching color with cell darkness so they stay legible in both themes.
- Expected, not a defect: a large matrix without in-cell numbers, and uneven patches, hot spots and near-empty rows in real data, which are not noise to smooth away.
- A good version shows: rows and columns in a logical order so blocks and gradients emerge, with long row or column labels rotated or given room, never truncated or overlapping.
- A good version shows: the basic variant's value grid only: no dendrograms or cluster trees, no marginal bars, no highlight boxes on selected cells, no reference lines, and no callouts or other annotation layer beyond the in-cell numbers the Notes allow.
