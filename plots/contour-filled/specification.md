# contour-filled: Filled Contour Plot

## Description

A filled contour plot displays colored regions between level curves of a 2D scalar field, creating a smooth gradient visualization of continuous data. Unlike basic contour plots that show only isolines, filled contours use color bands to represent value ranges, making it easier to perceive gradual changes and identify regions of similar magnitude. This visualization is particularly effective for showing how a quantity varies continuously across a 2D surface.

## Applications

- Creating topographic maps with elevation bands showing terrain height ranges
- Visualizing weather data such as temperature gradients, atmospheric pressure fields, or precipitation intensity
- Displaying probability density estimates and statistical distributions in 2D space
- Rendering mathematical functions to understand their behavior across a domain

## Data

- `x` (numeric) - X-axis coordinates forming a regular grid
- `y` (numeric) - Y-axis coordinates forming a regular grid
- `z` (numeric) - Scalar values at each (x, y) grid point representing the surface
- Size: Grid of 30x30 to 100x100 points for smooth color transitions
- Example: Mathematical function z = f(x, y) evaluated on a meshgrid, such as Gaussian peaks or saddle surfaces

## Notes

- Use a sequential or diverging colormap appropriate for the data range
- Include a colorbar to indicate the value mapping
- Consider overlaying contour lines for precise level identification
- Adjust the number of levels (typically 10-20) for appropriate detail
- Ensure grid resolution is sufficient to avoid jagged color boundaries

## What a good version looks like

- A good version shows: the whole grid covered by color bands, each band filling the region between two neighboring levels of the field, with no holes, gaps or unfilled corners inside the data's extent.
- A good version shows: band boundaries that are smooth curves, as the Notes ask, never jagged, stair-stepped or pixelated from a coarse grid.
- A good version shows: enough levels to show the field's detail while neighboring bands stay distinguishable, as the Notes ask, at levels evenly stepped unless the field's range calls for another spacing, so narrow bands read as steep change and broad ones as flat areas.
- A good version shows: a sequential colormap for a single-signed field or a diverging one centered on its meaningful midpoint, with the color bar the Notes ask for showing the same levels and naming the quantity.
- A good version shows: contour lines over the bands, if drawn as the Notes suggest, running along the band boundaries, visible in both themes and thin enough that the fill colors stay the main signal.
- Expected, not a defect: narrow bands crowding on steep slopes and one broad band over a flat area, closed bands around peaks and basins, an hourglass shape at a saddle, and visible color steps between bands, which are the levels rather than banding to smooth away.
