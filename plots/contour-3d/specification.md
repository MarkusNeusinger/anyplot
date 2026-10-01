# contour-3d: 3D Contour Plot

## Description

A 3D contour plot displays contour lines or filled contour bands on a three-dimensional surface, showing isolines of a function of two variables in 3D space. Unlike 2D contour plots that flatten the visualization, 3D contour plots preserve the surface geometry while highlighting level curves, making it easier to understand both the overall shape and specific value regions simultaneously. This visualization combines the spatial intuition of 3D surfaces with the precision of contour-based value identification.

## Applications

- Visualizing mathematical functions where both the surface shape and specific level curves matter, such as optimization landscapes with critical points
- Analyzing terrain elevation data with highlighted altitude bands for topographic analysis and route planning
- Displaying electromagnetic field distributions with equipotential surfaces in physics and engineering
- Examining response surfaces in experimental design where understanding both trends and thresholds is important

## Data

- `x` (numeric array) - X-axis grid values, typically uniformly spaced
- `y` (numeric array) - Y-axis grid values, typically uniformly spaced
- `z` (2D numeric array) - Height values at each (x, y) point representing the surface
- Size: 30x30 to 50x50 grid points for clear visualization with visible contour detail

## Notes

- Use a sequential or diverging colormap to distinguish contour levels clearly
- Include contour lines at regular intervals to show level curves on the surface
- Consider projecting contours onto the base plane as well as the surface for reference
- Enable rotation for interactive libraries to explore the 3D structure
- Include a colorbar to indicate the value scale of contour levels

## What a good version looks like

- A good version shows: the field in three dimensions, its level curves lifted to their z heights over the x-y plane, with or without the surface drawn beneath them, seen from an oblique angle with all three axes drawn, so the shape reads as relief rather than as a flat map.
- A good version shows: level curves at regular intervals, as the Notes ask, drawn as lines or as the edges of filled bands, each staying at one height all the way around and, where a surface is drawn, distinguishable from it in both themes.
- A good version shows: contours projected onto the base plane, if drawn as the Notes suggest, lying flat directly below the level curves they repeat and at the same levels.
- A good version shows: a sequential or diverging colormap tied to height, with the color bar the Notes ask for naming the quantity and covering the range of the contour levels.
- A good version shows: a view angle that keeps the main peaks and valleys and their level curves in sight, so a fully hidden feature is the exception rather than the rule.
- Expected, not a defect: parts of the surface and its contours hidden behind nearer relief, level curves that bunch into tight rings near a sharp summit, base-plane contours partly covered by the surface above them, and foreshortening of the far side; they are inherent to a 3D view.
