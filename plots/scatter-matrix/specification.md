# scatter-matrix: Scatter Plot Matrix

## Description

A grid of scatter plots showing all pairwise relationships between multiple variables, with histograms or kernel density estimates on the diagonal. This comprehensive visualization enables simultaneous exploration of correlations and distributions across an entire dataset, making it invaluable for understanding multivariate data structure at a glance. Also known as a pairplot or SPLOM (Scatter Plot Matrix).

## Applications

- Exploratory data analysis to quickly identify correlations, clusters, and outliers across multiple features in a dataset
- Feature selection in machine learning by visually assessing variable relationships before modeling
- Dataset overview and quality checking to understand distributions and detect anomalies in multivariate data

## Data

- `variables` (list of numeric columns) - Multiple continuous variables to compare pairwise
- Variables: 3-6 recommended for clarity (grid grows quadratically)
- Size: 50-500 points recommended per scatter for visual clarity
- Example: Iris dataset or similar multivariate numeric data

## Notes

- Diagonal cells should show univariate distributions (histograms or KDE) for each variable
- Off-diagonal cells show scatter plots for each variable pair
- Variable names should appear along the edges (left and bottom) as axis labels
- Consider using color encoding to show categorical groupings if available
- Keep point size small and use transparency to handle overplotting in dense datasets
- Matrix should be symmetric (upper and lower triangles show same relationships)

## What a good version looks like

- A good version shows: a square grid with one row and one column per variable, a scatter of the pair in every off-diagonal cell and that variable's histogram or density curve on the diagonal, as the Notes ask.
- A good version shows: scatter cells in one column sharing their x range and scatter cells in one row sharing their y range, so a point can be traced across the grid and the upper triangle mirrors the lower, as the Notes ask.
- A good version shows: variable names along the left and bottom edges, as the Notes ask, with tick labels sparse enough that those of neighboring cells do not run into each other.
- A good version shows: small, translucent points, as the Notes ask, so each cell shows the shape of its cloud; categorical coloring, if used as the Notes allow, with the same colors in every cell and one legend for the whole grid.
- Expected, not a defect: every pair appearing twice with its axes swapped, small cells with few tick labels, diagonal shapes that differ from variable to variable, and pairs whose cloud is round and structureless.
