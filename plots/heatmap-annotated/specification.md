# heatmap-annotated: Annotated Heatmap

## Description

A heatmap with numeric values displayed inside each cell, combining color intensity with exact value labels. Essential for correlation matrices, confusion matrices, and any matrix visualization where both pattern recognition and precise values matter. Text color automatically contrasts with background for readability.

## Applications

- Correlation matrices showing relationships between variables with exact coefficients
- Confusion matrices in machine learning model evaluation
- Performance matrices comparing metrics across categories and time periods
- Statistical analysis requiring both visual patterns and precise values

## Data

- `x` (string/numeric) - column labels for the matrix
- `y` (string/numeric) - row labels for the matrix
- `value` (numeric) - cell values for color mapping and annotation
- Size: 5-20 rows, 5-20 columns (larger matrices may have readability issues)

## Notes

- Text annotations must have sufficient contrast with background color
- Use appropriate number formatting (e.g., 2 decimal places for correlations)
- Include a colorbar legend showing the value scale
- Consider font size relative to cell size for readability
- Diverging colormap recommended for data with positive/negative values

## What a good version looks like

- A good version shows: every cell as a filled rectangle at its row and column, colored by its value, with each row and column label at its cells.
- A good version shows: the value printed inside every cell, in a number format that suits the data and is the same across the matrix, at a size that fits its cell.
- A good version shows: cell text that contrasts with its cell, as the Notes require, switching between dark and light with the cell's darkness so every number stays legible at both ends of the colormap in both themes.
- A good version shows: a colormap that fits the data (sequential for single-signed values; for values of both signs the diverging map the Notes recommend, centered on the midpoint) and the color bar the Notes ask for, showing the value scale.
- Expected, not a defect: numbers that restate what the color already shows, a uniform diagonal and mirrored halves in a symmetric matrix, and a dominant diagonal in a confusion matrix.
