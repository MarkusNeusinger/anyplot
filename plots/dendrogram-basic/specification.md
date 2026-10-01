# dendrogram-basic: Basic Dendrogram

## Description

A dendrogram visualizes hierarchical clustering by showing how data points or clusters merge at different distance levels. The tree-like structure reveals relationships and similarity between items, with branch heights indicating the distance at which clusters merge. This visualization is essential for understanding the hierarchical structure in data and identifying natural groupings.

## Applications

- Visualizing results from hierarchical clustering algorithms (e.g., agglomerative clustering)
- Gene expression analysis showing relationships between samples or genes
- Document clustering to reveal topic hierarchies and content similarity
- Customer segmentation analysis showing how customer groups relate to each other

## Data

- `features` (numeric matrix) - measurement values for each item (e.g., petal length, sepal width), used to compute distances
- `labels` (string) - names or identifiers for each item being clustered
- `linkage_matrix` (numeric) - output from scipy's linkage function containing merge distances, computed from features
- Size: 10-50 items recommended for readable dendrograms
- Example: hierarchical clustering of iris flower species by measurements

## Notes

- Use scipy.cluster.hierarchy for computing linkage and plotting dendrograms
- Vertical orientation is most common, but horizontal works well for long labels
- Branch heights should be proportional to merge distances for accurate interpretation
- Consider using truncation for very large datasets to improve readability

## What a good version looks like

- A good version shows: every merge as a link whose crossbar sits at its merge distance on the height axis, as the Notes ask, so branch heights are the data and are never equalized by tree level or rescaled.
- A good version shows: a height axis with ticks, labeled with the distance or linkage measure, from which the merge distances can be read.
- A good version shows: one labeled leaf per item, or per condensed cluster where the truncation the Notes allow is used, on a common baseline in a vertical or horizontal tree, as the Notes allow; the leaf order comes from the tree, arranged so that branches do not cross, and is not a measured quantity.
- A good version shows: the basic variant's single tree: besides the height axis and the leaf labels, no cut or threshold lines, other reference lines, highlighted clusters or bands, callouts, attached heatmap or second tree.
- Expected, not a defect: merges at very uneven heights, one late merge far above the rest, low merges crowded near the leaves, and a lopsided tree in which single items join one after another.
