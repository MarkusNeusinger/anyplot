# dendrogram-radial: Radial Dendrogram

## Description

A radial dendrogram renders hierarchical clustering in a circular layout where the root node sits at the center and branches extend outward, with leaf nodes arranged around the circumference. This layout is a space-efficient alternative to linear dendrograms for large hierarchies, making it well-suited for datasets with hundreds of leaves. Branch lengths are proportional to distance or dissimilarity, preserving the quantitative interpretation of cluster merges.

## Applications

- Displaying phylogenetic trees with hundreds of species in a compact circular form
- Visualizing organizational hierarchies or reporting structures without excessive horizontal/vertical scrolling
- Showing file system or taxonomy structures where many leaf nodes need to be visible simultaneously
- Presenting clustering dendrograms for gene expression data with color-coded cluster assignments

## Data

- `linkage_matrix` (numeric matrix) - hierarchical clustering linkage matrix in scipy format (n-1 × 4), encoding merge indices, distances, and cluster sizes
- `labels` (string[]) - names for each leaf node, displayed around the circumference
- `cluster_colors` (string[] or int[], optional) - cluster assignment for each leaf, used to color branches or an outer metadata ring
- Size: 20-500 leaf nodes recommended; radial layout excels where linear dendrograms become unwieldy

## Notes

- Root is positioned at the center; leaves are placed at equal angular spacing around the circumference
- Branch length (radial distance) should be proportional to merge distance/dissimilarity
- Color branches by cluster assignment using a categorical colormap
- Optional: add a color-coded ring around the outer edge to encode additional metadata (e.g., species family, department)
- Use scipy.cluster.hierarchy for linkage computation; polar projection in matplotlib or dedicated libraries for radial rendering
- Consider adding interactive tooltips for leaf labels when the number of leaves exceeds readable text size

## What a good version looks like

- A good version shows: the root at the center and every leaf on the outer circumference at equal angular spacing, as the Notes ask; the angular order of leaves comes from the tree, arranged so that branches do not cross, and is not a measured quantity.
- A good version shows: every merge at a radial position set by its merge distance, as the Notes ask, so radial distances are the data and are never equalized by tree depth.
- A good version shows: the cluster assignment, where the data carries one, in categorical colors on the branches, as the Notes ask, or on the outer ring, as the Data allows, so each cluster reads as one colored sector of the circle.
- A good version shows: leaf labels, where drawn, outside their leaves around the circumference, oriented so that neighboring labels fan out around the circle instead of colliding, for instance rotated to follow their branches or set along the rim.
- A good version shows: the outer ring the Notes allow, if drawn, as a band of colored segments outside the leaves, each segment aligned with its leaf, with a legend for its colors.
- Expected, not a defect: merges at very uneven radii, junctions crowding toward the rim where similar leaves merge at small distances, long bare branches near the center, and, with hundreds of leaves, leaf labels that are tiny or left out.
