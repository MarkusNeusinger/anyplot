# biplot-pca: PCA Biplot with Scores and Loading Vectors

## Description

A PCA biplot simultaneously displays both observation scores (as points) and variable loadings (as arrows) in the principal component space. This dual representation is essential for interpreting PCA results, revealing how observations relate to each other and which original variables drive the separation along each principal component. The length and direction of loading arrows indicate variable importance and correlation with the components.

## Applications

- Exploratory data analysis to understand which variables contribute most to data variance and how samples cluster in reduced dimensionality
- Quality control in manufacturing to visualize relationships between process variables and identify outliers in multivariate measurements
- Gene expression analysis to reveal sample groupings and identify which genes drive biological variation across conditions

## Data

- `features` (numeric matrix) - Multiple continuous variables for PCA decomposition (columns are features, rows are observations)
- `labels` (optional categorical) - Group labels for coloring observations
- Variables: 4-10 original features recommended for readable loading arrows
- Size: 30-200 observations for visual clarity
- Example: Iris dataset or similar multivariate numeric data

## Notes

- Display PC1 vs PC2 (the two components explaining most variance) as the default view
- Show observation scores as points, optionally colored by group labels
- Draw variable loadings as arrows originating from the origin
- Label each loading arrow with the corresponding variable name
- Scale loadings appropriately so arrows are visible alongside score points (often requires separate scaling)
- Include axis labels showing component name and variance explained percentage (e.g., "PC1 (45.2%)")
- Consider adding a unit circle as reference for loading magnitudes when using correlation biplot scaling

## What a good version looks like

- A good version shows: observation scores as points at their PC1 and PC2 coordinates, as the Notes ask, never jittered or displaced, and, where they are colored by group as the Notes allow, a legend naming the groups.
- A good version shows: one arrow per original variable starting at the origin, as the Notes ask, its direction and relative length following that variable's loadings on the two components.
- A good version shows: each arrow labeled with its variable name, as the Notes ask, the name placed at the arrowhead so it is attributable to one arrow even where arrows point the same way.
- A good version shows: loadings scaled so the arrows are visible alongside the score points, as the Notes ask, by one common factor for all arrows, neither shrunk to a knot at the origin nor running out of the plot; the unit circle the Notes suggest, if drawn, is centered on the origin and round.
- A good version shows: axis labels naming each component with its percentage of variance explained, as the Notes ask.
- Expected, not a defect: arrows of very different lengths, arrows bunched together for correlated variables or opposed for negatively correlated ones, arrows and scores on different scales, groups that overlap, and points spread wider along the first component than the second.
