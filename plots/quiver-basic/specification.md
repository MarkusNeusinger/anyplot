# quiver-basic: Basic Quiver Plot

## Description

A quiver plot displays vector fields using arrows positioned at grid points. Each arrow represents a vector at that location, with direction indicating the vector's angle and length proportional to its magnitude. This visualization reveals flow patterns, gradients, and field structure in two-dimensional data.

## Applications

- Visualizing wind patterns or ocean currents in meteorology and oceanography
- Displaying electromagnetic field lines in physics simulations
- Showing gradient descent directions in optimization landscapes
- Illustrating fluid flow patterns in computational fluid dynamics

## Data

- `x` (numeric array) - X-coordinates of arrow positions on a grid
- `y` (numeric array) - Y-coordinates of arrow positions on a grid
- `u` (numeric array) - Horizontal component (dx) of each vector
- `v` (numeric array) - Vertical component (dy) of each vector
- Size: Typically 10x10 to 20x20 grid (100-400 arrows) for visual clarity
- Example: A 2D flow field such as `u = -y, v = x` creates a circular rotation pattern

## Notes

- Arrow spacing should be uniform and sufficient to prevent overlap
- Arrow length should be scaled appropriately so vectors are distinguishable
- Consider using a simple mathematical function (like rotation or gradient) to generate sample data
- Optional: color can encode magnitude for additional insight

## What a good version looks like

- A good version shows: one arrow per grid point, attached to that point at the same place on every arrow (its tail, its middle or its tip), pointing in the direction of its vector, with a head that makes the direction readable.
- A good version shows: arrow length proportional to the vector's magnitude on one scale shared by the whole field, scaled as the Notes ask so that stronger and weaker vectors are distinguishable and the longest arrows stay out of their neighbors.
- A good version shows: arrows on a uniformly spaced grid, as the Notes ask, none nudged off its grid point, so the field's pattern (a rotation, a gradient, a convergence) reads from the arrows together.
- A good version shows: color, if used as the Notes allow, encoding magnitude through a sequential colormap with a color bar that names the quantity; otherwise every arrow in one color.
- Expected, not a defect: arrows that shrink to stubs or dots where the field is nearly zero, such as the center of a rotation, arrows of very different lengths across the field, and the regular symmetric pattern of a simple mathematical field.
- A good version shows: the basic variant's single vector field: besides the magnitude coloring the Notes allow and a key arrow that gives the length scale, no streamlines, background scalar field or contours, reference or mean lines, highlighted arrows, rings or regions, callouts or markers on centers, or second field.
