# ternary-density: Ternary Density Plot

## Description

A ternary density plot combines a three-component ternary diagram with kernel density estimation to visualize where compositional data concentrates. Instead of showing individual points, this visualization uses a heatmap overlay to reveal the underlying probability distribution of compositions, making it ideal for identifying clusters, modes, and patterns in large compositional datasets.

## Applications

- Analyzing sediment composition distributions across geological samples (sand/silt/clay)
- Visualizing alloy mixture preferences in materials science research
- Identifying common flavor profiles in food science (sweet/sour/bitter ratios)
- Understanding market positioning patterns among three competing attributes

## Data

- `component_a` (numeric) - Proportion of first component (0-100%)
- `component_b` (numeric) - Proportion of second component (0-100%)
- `component_c` (numeric) - Proportion of third component (0-100%)
- Size: 100-5000 points ideal for density estimation; fewer points may yield sparse density
- Constraint: All three components must sum to 100% (or a constant total)

## Notes

- Use a perceptually uniform colormap (viridis, plasma) for the density overlay
- Grid lines should be visible beneath the density layer with appropriate transparency
- Each vertex should be clearly labeled with component names
- Consider showing contour lines at key density levels for easier interpretation
- Bandwidth selection for KDE affects smoothness; auto-selection methods work well for most cases

## What a good version looks like

- A good version shows: an equilateral triangle with each vertex labeled with its component name, as the Notes ask, and a continuous density surface in ternary coordinates in place of individual points, its peaks lying where the compositions concentrate.
- A good version shows: the density confined to the triangle, with no density color drawn beyond its edges, and smooth rather than visibly tiled or dotted.
- A good version shows: a perceptually uniform colormap for the density, as the Notes ask, with a color bar or legend that tells which end is high density.
- A good version shows: the ternary grid still visible where the density is high, as the Notes ask, its three sets of lines parallel to the triangle's sides and kept inside the triangle.
- A good version shows: contour lines, if drawn as the Notes suggest, following levels of the same density surface, closed around its peaks or ending at the triangle's edges, and readable against the colormap in both themes.
- Expected, not a defect: no individual points, several separate peaks or one elongated ridge, density cut off at an edge where a component is near zero, large areas of low density, fine structure blurred by the smoothing, and a color bar in relative rather than absolute units.
