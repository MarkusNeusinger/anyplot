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
