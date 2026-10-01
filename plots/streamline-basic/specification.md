# streamline-basic: Basic Streamline Plot

## Description

A streamline plot visualizes vector fields using smooth curves that are tangent to the field at every point. Unlike quiver plots that show discrete arrows, streamlines trace continuous paths through the field, revealing flow patterns, circulation, and field topology. This visualization is ideal for understanding fluid dynamics, electromagnetic fields, or gradient fields where the continuous nature of the flow is important.

## Applications

- Visualizing fluid flow patterns in computational fluid dynamics simulations
- Displaying magnetic or electric field lines in physics and electromagnetic studies
- Showing wind flow patterns in meteorological analysis
- Illustrating gradient descent trajectories in optimization and machine learning

## Data

- `x` (numeric array) - X-coordinates of the grid (1D array for meshgrid)
- `y` (numeric array) - Y-coordinates of the grid (1D array for meshgrid)
- `u` (numeric 2D array) - Horizontal velocity component at each grid point
- `v` (numeric 2D array) - Vertical velocity component at each grid point
- Size: Typically 20x20 to 50x50 grid for smooth streamlines
- Example: A vortex flow field such as `u = -y, v = x` creates circular streamlines

## Notes

- Streamline density should be balanced - too few obscures the pattern, too many creates visual clutter
- Color can encode velocity magnitude or another scalar field along the streamlines
- Line width can optionally vary with field strength for emphasis
- Starting points for streamlines should be distributed to capture the full field structure

## What a good version looks like

- A good version shows: smooth curves that follow the field's direction at every point along their length, without kinks or zigzags, and that never cross one another.
- A good version shows: streamlines started across the whole domain, as the Notes ask, so each structure of the field (a vortex, a source or sink, a saddle) is traced, at a density balanced as the Notes ask: enough lines to show the pattern, few enough that neighbors stay separate.
- A good version shows: direction arrows along the lines, if drawn, pointing with the field and sparse enough that the curves stay the main mark.
- A good version shows: color, if used as the Notes allow, encoding speed or another scalar along the lines with a color bar that names it, and line width, if varied, growing with field strength.
- Expected, not a defect: lines that crowd where the flow converges and spread apart where it diverges, lines that end at the domain edge or at a source, a sink or an obstacle, closed loops around a vortex, and a small empty patch at a stagnation point.
- A good version shows: the basic variant's single vector field: besides the color and width encodings the Notes allow, direction arrows and the sources or obstacles that shape the field, no quiver overlay, background scalar field, reference or mean lines, highlighted streamlines or regions, callouts, or second field.
