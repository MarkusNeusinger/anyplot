# contour-density: Density Contour Plot

## Description

A density contour plot (also known as a 2D KDE contour plot) displays the concentration of points in a 2D scatter plot using contour lines. The contours connect points of equal density, revealing clusters, patterns, and the overall bivariate distribution shape.

## Applications

- Visualizing bivariate distributions
- Finding clusters and patterns in large scatter datasets
- Geographic point concentration analysis
- Quality control (identifying process clusters)
- Scientific data where density matters more than individual points

## Data

- `x` (numeric, continuous) — First variable for the X-axis
- `y` (numeric, continuous) — Second variable for the Y-axis
- Size: 100–10,000 points recommended (larger datasets benefit from density visualization)
- Example: Bivariate measurements (e.g., height vs. weight, temperature vs. pressure, geographic coordinates)

## Notes

- Alternative to scatter plot for very large datasets (avoids overplotting)
- Kernel density estimation (KDE) is used to compute density
- Multiple contour levels show density gradients (inner = higher density)
- Can be combined with scatter plot overlay for context
- Filled contours (contourf) can also be used for stronger visual impact
- Consider bandwidth/smoothing parameter for optimal results
