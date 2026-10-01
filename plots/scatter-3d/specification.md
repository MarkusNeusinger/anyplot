# scatter-3d: 3D Scatter Plot

## Description

A three-dimensional scatter plot that displays the relationship between three numeric variables by plotting points in 3D space. This visualization extends the classic 2D scatter plot to reveal patterns, clusters, and correlations across three dimensions simultaneously, making it invaluable for multivariate data exploration.

## Applications

- Exploring relationships in multivariate datasets with three continuous variables
- Visualizing molecular structures and spatial coordinates in scientific research
- Identifying clusters in 3D feature spaces for machine learning analysis

## Data

- `x` (numeric) - First dimension values plotted on the x-axis
- `y` (numeric) - Second dimension values plotted on the y-axis
- `z` (numeric) - Third dimension values plotted on the z-axis
- `color` (numeric, optional) - Fourth variable for color encoding
- Size: 50-500 points recommended for clear visualization
- Example: Random 3D clustered data demonstrating spatial relationships

## Notes

- Interactive rotation capability is essential for proper 3D exploration (where library supports it)
- Clear axis labels with units help orient the viewer in 3D space
- Consider point transparency for dense datasets to reveal internal structure
- Color encoding can effectively add a fourth dimension to the visualization

## What a good version looks like

- A good version shows: one marker per observation at its exact x, y and z values inside a visible 3D frame, with all three axes labeled, with units, as the Notes ask, so the viewer can tell which direction is which.
- A good version shows: a viewing angle oblique enough that all three axes have visible extent and the clusters separate, rather than a view down one axis that flattens the cloud to two dimensions.
- A good version shows: depth cues that make near and far readable: pane grid lines or box edges, and, where the cloud is dense, translucent markers as the Notes suggest, so interior points show through.
- A good version shows: the optional color variable, if used, on a continuous colormap with a color bar labeled with that variable.
- Expected, not a defect: near points hiding far ones, perspective foreshortening, tick labels at an angle to the page, and, in a static render, a single fixed viewpoint.
