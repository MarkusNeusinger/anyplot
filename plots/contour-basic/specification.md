# contour-basic: Basic Contour Plot

## Description

A contour plot displays isolines (level curves) of a 2D scalar field, connecting points of equal value across a surface. It transforms 3D data into an intuitive 2D representation, making it easy to identify regions of high and low values, gradients, and patterns. Contour plots are essential for visualizing continuous surfaces where the relationship between X, Y coordinates and a Z value needs to be understood.

## Applications

- Visualizing topographic elevation maps to show terrain features like hills, valleys, and ridges
- Displaying temperature or pressure distributions across a geographic region in meteorology
- Analyzing probability density functions or statistical distributions in 2D space
- Mapping chemical concentration gradients in scientific experiments

## Data

- `x` (numeric) - X-axis coordinates forming a regular grid
- `y` (numeric) - Y-axis coordinates forming a regular grid
- `z` (numeric) - Scalar values at each (x, y) grid point representing the surface height
- Size: Grid of 20x20 to 100x100 points
- Example: Mathematical function z = f(x, y) evaluated on a meshgrid, or interpolated measurement data

## Notes

- Use a diverging or sequential colormap appropriate for the data (e.g., viridis, coolwarm)
- Include a colorbar to show the value scale
- Consider using both contour lines and filled regions for clarity
- Label key contour levels when practical
- Ensure sufficient grid resolution for smooth contours

## What a good version looks like

- A good version shows: isolines that each follow one constant value of the field through the grid, at levels evenly stepped unless the field's range calls for another spacing, so tightly packed lines read as steep change and widely spaced lines as flat ground.
- A good version shows: smooth curves, as the Notes ask, never angular or stair-stepped from a coarse grid, that never cross each other and either close on themselves or run to the edge of the plot.
- A good version shows: a sequential colormap for a single-signed field or a diverging one centered on its meaningful midpoint, coloring the lines or the fills by level, with the color bar the Notes ask for naming the quantity.
- A good version shows: labels on key levels, when drawn as the Notes suggest, sitting on their own line with the value readable in both themes and spread along the lines rather than bunched in one spot.
- Expected, not a defect: closed rings around peaks and basins, lines that crowd on steep slopes and thin out on flat ground, an hourglass pattern at a saddle, lines cut off at the plot edge, and levels left unlabeled where there is no room.
- A good version shows: the basic variant's single scalar field: besides the isolines, the color bar the Notes ask for and the filled regions and key-level labels the Notes allow, no reference or mean lines, highlighted regions or bands, callouts or markers on extrema, overlaid scatter points, or second field.
