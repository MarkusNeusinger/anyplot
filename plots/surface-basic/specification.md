# surface-basic: Basic 3D Surface Plot

## Description

A 3D surface plot visualizes a function of two variables as a continuous surface in three-dimensional space. The height (z-axis) represents the function value at each (x, y) point, with color encoding the same information to enhance depth perception. This visualization is ideal for understanding mathematical functions, terrain data, and response surfaces where the relationship between two inputs and one output needs to be explored.

## Applications

- Visualizing mathematical functions like z = sin(x) * cos(y) or Gaussian surfaces
- Displaying terrain elevation data and topographic maps
- Analyzing response surfaces in optimization and experimental design
- Showing temperature, pressure, or other physical fields across a 2D domain

## Data

- `x` (numeric array) - X-axis grid values, typically uniformly spaced
- `y` (numeric array) - Y-axis grid values, typically uniformly spaced
- `z` (2D numeric array) - Height values at each (x, y) point
- Size: 30x30 to 50x50 grid points for clear visualization

## Notes

- Use a smooth colormap (e.g., viridis, coolwarm) to show height variation
- Include axis labels for x, y, and z dimensions
- Consider adding a colorbar to show the value scale
- For interactive libraries, enable rotation to explore the surface from different angles

## What a good version looks like

- A good version shows: one continuous surface over the grid of x and y whose height at each grid point is its z value, without holes, tears or gaps between facets, read against a z axis with ticks.
- A good version shows: color following height through a smooth colormap, as the Notes ask, so color and height tell the same story, with the color bar, if drawn as the Notes suggest, naming the quantity.
- A good version shows: all three axes drawn and labeled, as the Notes ask, from an oblique view that shows peaks and valleys together rather than looking straight down on the surface or at it edge-on.
- A good version shows: a grid fine enough that the surface reads as smooth rather than faceted, with mesh lines or shading, if drawn, light enough to show the curvature without hiding the color.
- Expected, not a defect: far slopes and valleys hidden behind nearer peaks, foreshortening that makes the far side look smaller, and shading that darkens steep faces; they are inherent to a 3D view.
- A good version shows: the basic variant's single surface: besides the color bar the Notes allow, no second surface, contour lines on the surface or projected onto the base plane or walls, reference lines or planes, highlighted regions or bands, markers or callouts on peaks and valleys, or overlaid scatter points.
