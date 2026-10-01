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

## What a good version looks like

- A good version shows: contours of the estimated point density on the two variables' own axes, nested so that inner contours mark higher density, as the Notes say, and each concentration of points sits inside its own set of rings.
- A good version shows: several density levels, as the Notes ask, with a color bar, legend or labels that say which way density rises whenever color or fill encodes it.
- A good version shows: smoothing that fits the data: contours that do not break into islands around single points, yet do not blur separate clusters into one blob.
- A good version shows: the scatter overlay, if drawn as the Notes allow, as small faint points at their exact values, so the contours stay the main signal and can be checked against the points.
- A good version shows: filled contours, if used as the Notes allow, in a sequential colormap whose strongest color marks the highest density, with the bands distinguishable in both themes.
- Expected, not a defect: several separate peaks, irregular contours that are far from elliptical, outer contours cut off at the plot edge, and sparse tail points lying outside every contour.
